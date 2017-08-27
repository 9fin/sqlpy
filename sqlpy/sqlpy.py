import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import quote_ident
from functools import partial
import logging

# get the module logger
module_logger = logging.getLogger(__name__)


class SQLLoadException(Exception):
    pass


class SQLParseException(Exception):
    pass


class SQLArgumentException(Exception):
    pass


SELECT = 1
INSERT_UPDATE_DELETE = 2
SELECT_BUILT = 3
RETURN_ID = 4
STRICT_BUILT_PARSE = False


class Queries(object):
    def __init__(self, filepath, strict_parse=False, queries=list()):
        self.available_queries = []
        if strict_parse:
            STRICT_BUILT_PARSE = True
        for name, fn in load_queires(filepath):
            self.add_query(name, fn)

    def __repr__(self):
        return "sqlpy.Queries("+self.available_queries.__repr__()+")"

    def init_app(self, app, sql_file):
        '''
        Configures a flask application.
        Loads the sql file and prepares all the queires.
        '''
        app.logger.info('Configuring SQLpy for application use.')
        app.logger.info('Loading sql queries from file: {}'.format(sql_file))
        queries = load_queires(sql_file)
        app.logger.info('Found {} sql queries in file: {}'.format(len(queries), sql_file))
        for name, fn in queries:
            self.add_query(name, fn)
        app.queries = self

    def add_query(self, name, fn):
        setattr(self, name, fn)
        if name not in self.available_queries:
            self.available_queries.append(name)


def get_fn_name(line):
    line = line.upper()
    return line[9:]


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
        else:
            # just a normal )
            pass
    if len(arg_start) != len(arg_end):
        raise SQLParseException('parse error, arg numbers do not match in string s', s)
    for i in range(len(arg_start)):
        if arg_end[i] - arg_start[i] < 1:
            raise SQLParseException('parse error, no argument found between (...)', s)
        out.add(s[arg_start[i]:arg_end[i]])
    return out


def built_query_tuple(in_arr):
    out_arr = []
    out_d = {'#': []}
    arg_offset = 0  # value which tracks the total offset in the array caused by multiple args in a line
    for i, line in enumerate(in_arr):
        args = parse_args(line)
        if not args:
            out_arr.append({'#': {'idx': i+arg_offset, '_q': line}})
            out_d['#'].append(i+arg_offset) 
            continue
        if len(args) > 1:
            for arg in args:
                out_arr.append({arg: {'idx': i+arg_offset, '_q': line}})
                out_d[arg] = i+arg_offset
                arg_offset += 1
            arg_offset -= 1
        else:
            arg = args.pop()
            out_arr.append({arg: {'idx': i+arg_offset, '_q': line}})
            out_d[arg] = i+arg_offset
    return (out_arr, out_d)


def arg_key_diff(s1, s2):
    return s1-s2


def parse_sql_entry(entry):
    lines = entry.split('\n')
    if not lines[0].startswith('-- name: '):
        raise SQLParseException('Query does not start with "-- name:".', lines[0])
    name = get_fn_name(lines[0])
    doc = None
    if ' ' in name:
        raise SQLParseException('Query name has spaces in it. "{}"'.format(lines[0]))
    elif '<!>' in name:
        sql_type = RETURN_ID
        name = name.replace('<!>', '')
    elif '!' in name:
        sql_type = INSERT_UPDATE_DELETE
        name = name.replace('!', '')
    elif '$' in name:
        sql_type = SELECT_BUILT
        name = name.replace('$', '')
    else:
        sql_type = SELECT
    if lines[1].startswith('-- '):
        doc = lines[1][3:]
    if doc:
        query = lines[2:]
    else:
        query = lines[1:]
    query_dict = None
    query_arr = None
    if sql_type == SELECT_BUILT:
        query_arr, query_dict = built_query_tuple(query)
    query = '\n'.join(query)

    def fn(query, query_dict, query_arr, sql_type, cur, fetchone, args=None, identifers=None, **kwargs):
        module_logger.info('Executing: {}'.format(name))
        results = None
        if identifers:
            identifers = map(lambda i: quote_ident(i, cur), identifers)
            query = sql.SQL(query.format(*identifers))
        if sql_type == RETURN_ID:
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
        if sql_type == INSERT_UPDATE_DELETE:
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
        if sql_type == SELECT and not fetchone:
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
        elif sql_type == SELECT and fetchone:
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
        if sql_type == SELECT_BUILT:
            query_built_arr = []
            query_built = ''
            query_args_set = set()
            # throw all the non arg containing lines in first
            noarg_idx = query_dict.get('#')
            for idx in noarg_idx:
                query_built_arr.append(query_arr[idx]['#'])
            # now add lines with args into the mix
            for key, value in kwargs.items():
                arg_idx = query_dict.get(key)
                if arg_idx:
                    # check if dict line item has already been added
                    if query_arr[arg_idx][key] not in query_built_arr:
                        query_built_arr.append(query_arr[arg_idx][key])
                        # add the args required by this line to tracker
                        query_args_set.update(parse_args(query_arr[arg_idx][key]['_q']))
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
                if q.get('_q') not in query_built:
                    query_built = "{}\n{}".format(query_built, q.get('_q'))
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
