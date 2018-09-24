from __future__ import print_function, absolute_import
import os
from .config import (quote_ident, STRICT_BUILT_PARSE, UPPERCASE_QUERY_NAME,
                     LOG_QUERY_PARAMS, QueryType, execute_values)
from functools import partial
from itertools import takewhile
from .exceptions import (SQLpyException, SQLLoadException,
                         SQLParseException, SQLArgumentException)
import logging

# get the module logger
logger = logging.getLogger(__name__)


def log_query(query, args, log_query_params):
    """
    Helper function to avoid repeating query log block
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug('SQL: {}'.format(query))
    if log_query_params:
        logger.info('Arguments: {}'.format(args))


class Queries(object):
    """
    Builds the prepared functions of SQL statements for execution.

    Creates Python :obj:`functools.partial` functions, attached to the class as
    methods.

    Args:
        filepath (:obj:`list` of :obj:`str` or :obj:`str`): List of file locations containing
            the SQL statements or a single filepath to the queries file.
        strict_parse (:obj:`bool`, optional): Weather to strictly enforce matching
            the expected and supplied parameters to a SQL statement function.
        uppercase_name (:obj:`bool`, optional): Weather to cast the names of the SQL
            statement functions to uppercase.
    """
    def __init__(self, filepath, strict_parse=False, uppercase_name=True, log_query_params=True):
        self.available_queries = []
        global STRICT_BUILT_PARSE
        STRICT_BUILT_PARSE = strict_parse
        global UPPERCASE_QUERY_NAME
        UPPERCASE_QUERY_NAME = uppercase_name
        global LOG_QUERY_PARAMS
        LOG_QUERY_PARAMS = log_query_params
        for name, sql_type, fn in load_queries(filepath):
            self.add_query(name, fn)
        logger.info('Found and loaded {} sql queires'.format(len(self.available_queries)))

    def __repr__(self):
        """
        Prints a list of available SQL statement function by name.
        """
        return "sqlpy.Queries(" + self.available_queries.__repr__() + ")"

    def add_query(self, name, fn):
        """
        Adds a function partial to the class object.

        Args:
            name (:obj:`str`)
            fn (:obj:`functools.partial`)
        """
        setattr(self, name, fn)
        if name not in self.available_queries:
            self.available_queries.append(name)


def get_fn_name(line):
    """
    Extracts the name of a SQL statement

    Args:
        line (:obj:`str`): First line of a SQL statement

    Returns:
        :obj:`str`: Uppercase name of the SQL statement
    """
    name = line.split('-- name:')[1].strip()
    if UPPERCASE_QUERY_NAME:
        return name.upper()
    return name


def parse_args(s):
    """
    Sans a string of SQL and parses out named parameters.

    Function which scans a line of raw input SQL and looks for and extracts out named
    parameters in `pyformat`. Found between %(...)s tokens. Returns a set ensuring no
    duplicates are entered for repeating multiple parameters in the same line.

    Args:
        s (:obj:`str`): Input string

    Returns:
        :obj:`set` of :obj:`list` of :obj:`str`: A :obj:`set` of strings forming the
            names of the parameters to be used in the SQL statement.

    Raises:
        SQLParseException: When the number of parameters found do not match.
        SQLParseException: When no name is found within the argument while parsing.
    """
    if '%(' not in s:
        return None
    arg_start = []
    arg_end = []
    out = set()
    for ii, c in enumerate(s):
        if c != '%' and c != ')':
            # normal uninteresting character
            continue
        elif c == '%' and s[ii + 1] == '(':
            # start of argument name
            arg_start.append(ii + 2)
        elif c == ')' and False if ii + 1 == len(s) else s[ii + 1] == 's':
            # end of argument name
            arg_end.append(ii)
        else:  # pragma: no cover
            # just a normal )
            pass
    if len(arg_start) != len(arg_end):
        raise SQLParseException('parse error, arg numbers do not match in string s: ', s)
    for i in range(len(arg_start)):
        if arg_end[i] - arg_start[i] < 1:
            raise SQLParseException('parse error, no argument found between (...): ', s)
        out.add(s[arg_start[i]:arg_end[i]])
    return out


def built_query_tuple(in_arr):
    """
    Prepares a built query :obj:`list` and :obj:`dict`.

    Builds a :obj:`list` of query parameters and a :obj:`dict` of query line parts, keyed
    by the parameters within that line.

    Args:
        in_arr (:obj:`list` of :obj:`str`): List of SQL statement lines

    Returns:
        :obj:`tuple`: ``(query_arr, query_dict)``
    """
    query_arr = []
    query_dict = {'#': []}
    arg_offset = 0  # value which tracks the total offset in the array caused by multiple args in a line
    for i, line in enumerate(in_arr):
        args = parse_args(line)
        if not args:
            query_arr.append({'#': {'idx': i + arg_offset, 'query_line': line}})
            query_dict['#'].append(i + arg_offset)
            continue
        if len(args) > 1:
            for arg in args:
                query_arr.append({arg: {'idx': i + arg_offset, 'query_line': line}})
                query_dict[arg] = i + arg_offset
                arg_offset += 1
            arg_offset -= 1
        else:
            arg = args.pop()
            query_arr.append({arg: {'idx': i + arg_offset, 'query_line': line}})
            query_dict[arg] = i + arg_offset
    return (query_arr, query_dict)


def arg_key_diff(s1, s2):
    """
    Finds the difference between two sets of strings.

    Args:
        s1 (:obj:`set`): Set 1
        s2 (:obj:`set`): Set 2

    Returns:
        :obj:`set`
    """
    return s1 - s2


def parse_sql_entry(entry):
    """
    Creates a prepared function for a SQL statement.

    For a given SQL statement its :class:`QueryType` is matched to its name ending in
    any of ``<!>, !, $``, for a `RETURN_ID, INSERT_UPDATE_DELETE, SELECT_BUILT` query
    type respectively. If no end token is found, the query is a `SELECT` query.

    Comments are detected and added to the ``__doc__`` attribute of the returned function

    Returns:
        :obj:`str`: name of the prepared function in UPPERCASE
        :obj:`functools.partial`: ```fn_partial`` the prepared function
            the ``fn_partial`` also has these attributes set
                - ``fn_partial.__doc__``: The comments found on the SQL statement if any
                - ``fn_partial.__query__``: The string representation of the SQL statement
                - ``fn_partial.__name__``: The name of the prepared function in UPPERCASE
    """
    lines = entry.split('\n')
    if not lines[0].startswith('-- name:'):
        raise SQLParseException('Query does not start with "-- name:": ', lines[0])
    name = get_fn_name(lines[0])
    doc = None
    if ' ' in name:
        raise SQLParseException('Query name has spaces: ', lines[0])
    elif '<!>' in name:
        sql_type = QueryType.RETURN_ID
        name = name.replace('<!>', '')
    elif '!' in name:
        sql_type = QueryType.INSERT_UPDATE_DELETE
        name = name.replace('!', '')
    elif '@' in name:
        sql_type = QueryType.CALL_PROC
        name = name.replace('@', '')
    elif '$' in name:
        sql_type = QueryType.SELECT_BUILT
        name = name.replace('$', '')
    else:
        sql_type = QueryType.SELECT
    # collect comments only at the start of the query block
    comments = list(line.strip('-').strip() for line in takewhile(lambda l: l.startswith('--'), lines[1:]))
    if comments:
        doc = '\n'.join(comments)
        query = lines[len(comments) + 1:]
    else:
        query = lines[1:]
    query_dict = None
    query_arr = None
    if sql_type == QueryType.SELECT_BUILT:
        query_arr, query_dict = built_query_tuple(query)
    query = '\n'.join(query)

    fn_partial = QueryFnFactory.make_query(query, query_dict, query_arr, sql_type, name, doc)

    return name, sql_type, fn_partial


def format_query_identifiers(query, identifiers, id_quote_fcn, cur):
    """
    Safely tokenizes SQL identifiers to be used in a SQL statement.

    When ``identifiers`` are passed into a SQLpy query, they are substituted into
    the SQL string at their defined locations. This is done in a safe way using a
    parameter escaping function provided by the underlying DB API library. A SQL statement
    with identifier tokens replaced is returned to be later bound to argument parameters.

    To use multiple identifiers in different parts of the query "identifier groups", you must
    use a dict type.

    Args:
        query (:obj:`string`): the unprepared query string
        identifers (:obj:`list` or :obj:`dict`): iterable or dictionary of iterables
        id_quote_fcn (:func:`id_quote_fcn`): function for safely escaping values
        cur (:obj:`cursor`): cursor object

    Returns:
        :obj:`str`: query string
    """
    def normalise(v):
        return [v] if isinstance(v, str) else v

    if isinstance(identifiers, dict):
        ids = {k: ','.join(list(id_quote_fcn(i, cur) for i in normalise(v))) for k, v in identifiers.items()}
        return query.format(**ids)
    elif isinstance(identifiers, (list, tuple)):
        ids = list(id_quote_fcn(i, cur) for i in identifiers)
        return query.format(*ids)
    else:
        raise SQLParseException("Invalid data type passed as identifiers. Must be dict of iterables, dict of strings, list or tuple", identifiers)


class QueryFnFactory:
    @staticmethod
    def make_query(query, query_dict, query_arr, sql_type, name, doc):

        if sql_type == QueryType.INSERT_UPDATE_DELETE:
            def fn(query, cur, args=tuple(), many=None, identifiers=None, log_query_params=LOG_QUERY_PARAMS, **kwargs):
                if identifiers:  # pragma: no cover
                    if not quote_ident:
                        raise SQLpyException('"quote_ident" is not supported')
                    query = format_query_identifiers(query, identifiers, quote_ident, cur)
                logger.info('Executing: {}'.format(name))
                log_query(query, args, log_query_params)
                try:
                    if many and execute_values:
                        execute_values(cur, query, args)
                    elif many and not execute_values:
                        cur.executemany(query, args)
                    else:
                        cur.execute(query, args)
                except Exception as e:
                    logger.error('Exception Type "{}" raised, on executing query "{}"\n____\n{}\n____'
                                 .format(type(e), name, query), exc_info=True)
                    raise
                else:
                    return True

            fn_partial = partial(fn, query)

        elif sql_type == QueryType.RETURN_ID:
            def fn(query, cur, args=tuple(), n=None, many=None, identifiers=None, log_query_params=LOG_QUERY_PARAMS, **kwargs):
                if n and (not isinstance(n, int) or n < 1):
                    raise SQLpyException('"n" must be an Integer >= 1')
                if identifiers:  # pragma: no cover
                    if not quote_ident:
                        raise SQLpyException('"quote_ident" is not supported')
                    query = format_query_identifiers(query, identifiers, quote_ident, cur)
                logger.info('Executing: {}'.format(name))
                log_query(query, args, log_query_params)
                try:
                    if many and execute_values:
                        execute_values(cur, query, args)
                    elif many and not execute_values:
                        cur.executemany(query, args)
                    else:
                        cur.execute(query, args)
                except Exception as e:
                    logger.error('Exception Type "{}" raised, on executing query "{}"\n____\n{}\n____'
                                 .format(type(e), name, query), exc_info=True)
                    raise
                else:
                    if not n:
                        return cur.fetchall()
                    if n == 1:
                        return cur.fetchone()
                    else:
                        return cur.fetchmany(n)

            fn_partial = partial(fn, query)

        elif sql_type == QueryType.CALL_PROC:
            def fn(query, cur, args=tuple(), n=None, identifiers=None, log_query_params=LOG_QUERY_PARAMS, **kwargs):
                if n and (not isinstance(n, int) or n < 1):
                    raise SQLpyException('"n" must be an Integer >= 1')
                if identifiers:  # pragma: no cover
                    if not quote_ident:
                        raise SQLpyException('"quote_ident" is not supported')
                    query = format_query_identifiers(query, identifiers, quote_ident, cur)
                logger.info('Executing: {}'.format(name))
                log_query(query, args, log_query_params)
                try:
                    cur.callproc(query, args)
                except Exception as e:
                    logger.error('Exception Type "{}" raised, on executing procedure "{}"\n____\n{}\n____'
                                 .format(type(e), name, query), exc_info=True)
                    raise
                else:
                    if not n:
                        return cur.fetchall()
                    if n == 1:
                        return cur.fetchone()
                    else:
                        return cur.fetchmany(n)

            fn_partial = partial(fn, query)

        elif sql_type == QueryType.SELECT:
            def fn(query, cur, args=tuple(), n=None, identifiers=None, log_query_params=LOG_QUERY_PARAMS, **kwargs):
                if n and (not isinstance(n, int) or n < 1):
                    raise SQLpyException('"n" must be an Integer >= 1')
                if identifiers:  # pragma: no cover
                    if not quote_ident:
                        raise SQLpyException('"quote_ident" is not supported')
                    query = format_query_identifiers(query, identifiers, quote_ident, cur)
                logger.info('Executing: {}'.format(name))
                log_query(query, args, log_query_params)
                try:
                    cur.execute(query, args)
                except Exception as e:
                    logger.error('Exception Type "{}" raised, on executing query "{}"\n____\n{}\n____'
                                 .format(type(e), name, query), exc_info=True)
                    raise
                else:
                    if not n:
                        return cur.fetchall()
                    if n == 1:
                        return cur.fetchone()
                    else:
                        return cur.fetchmany(n)

            fn_partial = partial(fn, query)

        elif sql_type == QueryType.SELECT_BUILT:
            def fn(query, query_dict, query_arr, cur, args=dict(), n=None, identifiers=None, log_query_params=LOG_QUERY_PARAMS, **kwargs):
                if n and (not isinstance(n, int) or n < 1):
                    raise SQLpyException('"n" must be an Integer >= 1')
                if not isinstance(args, dict):
                    raise SQLpyException('Only dict args are supported for built SQL. {} supplied'
                                         .format(type(args)))
                logger.info('Executing: {}'.format(name))
                query_built = ''
                query_args_set = set()
                # throw all the non arg containing lines in first
                noarg_idx = query_dict.get('#')
                query_built_arr = list(query_arr[idx]['#'] for idx in noarg_idx)
                # now add lines with args into the mix
                for key, value in args.items():
                    arg_idx = query_dict.get(key)
                    if arg_idx:
                        # check if dict line item has already been added
                        if query_arr[arg_idx][key] not in query_built_arr:
                            query_built_arr.append(query_arr[arg_idx][key])
                            # add the args required by this line to tracker
                            query_args_set.update(parse_args(query_arr[arg_idx][key]['query_line']))
                    else:
                        if STRICT_BUILT_PARSE:
                            raise SQLArgumentException('Named argument supplied which does not match a SQL clause: ', key=key)
                # do a diff of the keys in input args and query_built
                # set anything missing to None
                diff = arg_key_diff(query_args_set, set(args.keys()))
                if diff:
                    for key in diff:
                        args.setdefault(key, None)
                # sort the final built up query array and reduce query into string
                query_built_arr = sorted(query_built_arr, key=lambda x: x.get('idx'))
                for q in query_built_arr:
                    if q.get('query_line') not in query_built:
                        query_built = "{}\n{}".format(query_built, q.get('query_line'))
                if identifiers:  # pragma: no cover
                    if not quote_ident:
                        raise SQLpyException('"quote_ident" is not supported')
                    query_built = format_query_identifiers(query_built, identifiers, quote_ident, cur)
                log_query(query_built, args, log_query_params)
                try:
                    cur.execute(query_built, args)
                except Exception as e:
                    logger.error('Exception Type "{}" raised, on executing query "{}"\n____\n{}\n____'
                                 .format(type(e), name, query_built), exc_info=True)
                    raise
                else:
                    if not n:
                        return cur.fetchall()
                    if n == 1:
                        return cur.fetchone()
                    else:
                        return cur.fetchmany(n)

            fn_partial = partial(fn, query, query_dict, query_arr)

        fn_partial.__doc__ = doc
        fn_partial.__query__ = query
        fn_partial.__name__ = name
        fn_partial.func_name = name

        return fn_partial


def parse_queires_string(s):
    """Splits and processes SQL file into individual expressions"""
    return [parse_sql_entry(expression.strip('\n')) for expression in s.split('\n\n') if expression]


def load_queries(filepath):
    """Loads SQL statements as ``strings`` from files"""
    if type(filepath) != list:
        filepath = [filepath]
    f = ''
    for file in filepath:
        if not os.path.exists(file):
            raise SQLLoadException('Could not find file', file)
        with open(file, 'rU') as queries_file:
            f = f + '\n\n' + queries_file.read().strip('\n')
    return parse_queires_string(f)
