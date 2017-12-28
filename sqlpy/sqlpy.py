import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import quote_ident
from functools import partial
import logging
from errno import ENOENT
from enum import Enum

# get the module logger
module_logger = logging.getLogger(__name__)
# add default NullHandler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())


class SQLpyException(Exception):
    pass


class SQLLoadException(SQLpyException, IOError):
    """Exception raised when errors occur in file IO"""
    def __init__(self, msg, filename):
        super(SQLLoadException, self).__init__(os.strerror(ENOENT), msg, filename)


class SQLParseException(SQLpyException, ValueError):
    """Exception raised when errors occur in building sql strings"""
    def __init__(self, msg, string):
        super(SQLParseException, self).__init__('{}"{}"'.format(msg, string))


class SQLArgumentException(SQLpyException, ValueError):
    pass


class QueryType(Enum):
    SELECT = 1
    INSERT_UPDATE_DELETE = 2
    SELECT_BUILT = 3
    RETURN_ID = 4


STRICT_BUILT_PARSE = False


class Queries(object):
    def __init__(self, filepath, strict_parse=False, queries=list()):
        self.available_queries = []
        if strict_parse:
            global STRICT_BUILT_PARSE
            STRICT_BUILT_PARSE = True
        for name, fn in load_queires(filepath):
            self.add_query(name, fn)
        module_logger.info('Found and loaded {} sql queires'.format(len(self.available_queries)))

    def __repr__(self):
        return "sqlpy.Queries("+self.available_queries.__repr__()+")"

    def add_query(self, name, fn):
        setattr(self, name, fn)
        if name not in self.available_queries:
            self.available_queries.append(name)


def get_fn_name(line):
    name = line.split('-- name:')[1].strip().upper()
    return name


def parse_args(s):
    '''
    Function which scans a line of raw input sql and looks for and extracts out named
    arguments for psycopg2. Found between %(...)s tokens. Returns a set ensuring no
    duplicates are entered for repeating multiple arguments in the same line.
    '''
    if '%(' not in s:
        return None
    arg_start = []
    arg_end = []
    out = set()
    for ii, c in enumerate(s):
        if c != '%' and c != ')':
            # normal uninteresting character
            continue
        elif c == '%' and s[ii+1] == '(':
            # start of argument name
            arg_start.append(ii+2)
        elif c == ')' and False if ii+1 == len(s) else s[ii+1] == 's':
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
    query_arr = []
    query_dict = {'#': []}
    arg_offset = 0  # value which tracks the total offset in the array caused by multiple args in a line
    for i, line in enumerate(in_arr):
        args = parse_args(line)
        if not args:
            query_arr.append({'#': {'idx': i+arg_offset, 'query_line': line}})
            query_dict['#'].append(i+arg_offset) 
            continue
        if len(args) > 1:
            for arg in args:
                query_arr.append({arg: {'idx': i+arg_offset, 'query_line': line}})
                query_dict[arg] = i+arg_offset
                arg_offset += 1
            arg_offset -= 1
        else:
            arg = args.pop()
            query_arr.append({arg: {'idx': i+arg_offset, 'query_line': line}})
            query_dict[arg] = i+arg_offset
    return (query_arr, query_dict)


def arg_key_diff(s1, s2):
    return s1-s2


def parse_sql_entry(entry):
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
    elif '$' in name:
        sql_type = QueryType.SELECT_BUILT
        name = name.replace('$', '')
    else:
        sql_type = QueryType.SELECT
    comments = list(line.strip('-').strip() for line in lines[1:] if line.startswith('--'))
    if comments:
        doc = '\n'.join(comments)
        query = lines[len(comments)+1:]
    else:
        query = lines[1:]
    query_dict = None
    query_arr = None
    if sql_type == QueryType.SELECT_BUILT:
        query_arr, query_dict = built_query_tuple(query)
    query = '\n'.join(query)

    def fn(query, query_dict, query_arr, sql_type, cur, fetchone, args=None, identifers=None, **kwargs):
        module_logger.info('Executing: {}'.format(name))
        results = None
        if identifers:
            identifers = map(lambda i: quote_ident(i, cur), identifers)
            query = sql.SQL(query.format(*identifers))
        if sql_type == QueryType.RETURN_ID:
            try:
                cur.execute(query, kwargs if len(kwargs) > 0 else args)
                if module_logger.isEnabledFor(logging.DEBUG):
                    module_logger.debug('SQL: {}'.format(query))
                module_logger.info('Arguments: {}'.format(kwargs if len(kwargs) > 0 else args))
            except psycopg2.Error:
                module_logger.exception("Psycopg2 Error")
                raise
            else:
                results = cur.fetchone()
        if sql_type == QueryType.INSERT_UPDATE_DELETE:
            try:
                cur.execute(query, kwargs if len(kwargs) > 0 else args)
                if module_logger.isEnabledFor(logging.DEBUG):
                    module_logger.debug('SQL: {}'.format(query))
                module_logger.info('Arguments: {}'.format(kwargs if len(kwargs) > 0 else args))
            except psycopg2.Error:
                module_logger.exception("Psycopg2 Error")
                raise
            else:
                results = True
        if sql_type == QueryType.SELECT and not fetchone:
            try:
                cur.execute(query, kwargs if len(kwargs) > 0 else args)
                if module_logger.isEnabledFor(logging.DEBUG):
                    module_logger.debug('SQL: {}'.format(query))
                module_logger.info('Arguments: {}'.format(kwargs if len(kwargs) > 0 else args))
            except psycopg2.Error:
                module_logger.exception("Psycopg2 Error")
                raise
            else:
                results = cur.fetchall()
        elif sql_type == QueryType.SELECT and fetchone:
            try:
                cur.execute(query, kwargs if len(kwargs) > 0 else args)
                if module_logger.isEnabledFor(logging.DEBUG):
                    module_logger.debug('SQL: {}'.format(query))
                module_logger.info('Arguments: {}'.format(kwargs if len(kwargs) > 0 else args))
            except psycopg2.Error:
                module_logger.exception("Psycopg2 Error")
                raise
            else:
                results = cur.fetchone()
        if sql_type == QueryType.SELECT_BUILT:
            query_built = ''
            query_args_set = set()
            # throw all the non arg containing lines in first
            noarg_idx = query_dict.get('#')
            query_built_arr = list(query_arr[idx]['#'] for idx in noarg_idx)
            # now add lines with args into the mix
            for key, value in kwargs.items():
                arg_idx = query_dict.get(key)
                if arg_idx:
                    # check if dict line item has already been added
                    if query_arr[arg_idx][key] not in query_built_arr:
                        query_built_arr.append(query_arr[arg_idx][key])
                        # add the args required by this line to tracker
                        query_args_set.update(parse_args(query_arr[arg_idx][key]['query_line']))
                else:
                    if STRICT_BUILT_PARSE:
                        raise SQLArgumentException('Named argument supplied which does not match a SQL clause', key)
            # do a diff of the keys in input kwargs and query_built
            # set anything missing to None
            diff = arg_key_diff(query_args_set, set(kwargs.keys()))
            if diff:
                for key in diff:
                    kwargs.setdefault(key, None)
            # sort the final built up query array and reduce query into string
            query_built_arr = sorted(query_built_arr, key=lambda x: x.get('idx'))
            for q in query_built_arr:
                if q.get('query_line') not in query_built:
                    query_built = "{}\n{}".format(query_built, q.get('query_line'))
            if fetchone:
                try:
                    cur.execute(query_built, kwargs)
                    if module_logger.isEnabledFor(logging.DEBUG):
                        module_logger.debug('SQL: {}'.format(query_built))
                    module_logger.info('Arguments: {}'.format(kwargs if len(kwargs) > 0 else args))
                except psycopg2.Error:
                    module_logger.exception("Psycopg2 Error")
                    raise
                else:
                    results = cur.fetchone()
            else:
                try:
                    cur.execute(query_built, kwargs)
                    if module_logger.isEnabledFor(logging.DEBUG):
                        module_logger.debug('SQL: {}'.format(query_built))
                    module_logger.info('Arguments: {}'.format(kwargs if len(kwargs) > 0 else args))
                except psycopg2.Error:
                    module_logger.exception("Psycopg2 Error")
                    raise
                else:
                    results = cur.fetchall()
        return results

    fn_partial = partial(fn, query, query_dict, query_arr, sql_type)

    fn_partial.__doc__ = doc
    fn_partial.__query__ = query
    fn_partial.__name__ = name
    fn_partial.func_name = name

    return name, fn_partial


def parse_queires_string(s):
    return [parse_sql_entry(expression.strip('\n')) for expression in s.split('\n\n') if expression]


def load_queires(filepath):
    if type(filepath) != list:
        filepath = [filepath]
    f = ''
    for file in filepath:
        if not os.path.exists(file):
            raise SQLLoadException('Could not find file', file)
        with open(file, 'rU') as queries_file:
            f = f + '\n' + queries_file.read()
    return parse_queires_string(f)
