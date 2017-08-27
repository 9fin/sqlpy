from __future__ import print_function
import pytest
import os
import functools
from sqlpy.sqlpy import Queries, load_queires, SQLLoadException,\
    SQLParseException, SQLArgumentException, parse_sql_entry, SELECT,\
    INSERT_UPDATE_DELETE, SELECT_BUILT, RETURN_ID


@pytest.fixture
def queries_file():
    return os.path.join(os.getcwd(), 'test_queries.sql')


@pytest.fixture
def queries_file_arr():
    return [os.path.join(os.getcwd(), 'test_queries.sql')]


@pytest.fixture
def invalid_file_path():
    return 'path_that_does_not_exist.sql'


@pytest.fixture
def invalid_sql_name_start():
    return """
-- nam: test_select
-- testing the sqlpi module pls work
SELECT * FROM testdb
""".strip('\n')


@pytest.fixture
def invalid_sql_name_spaces():
        return """
-- name: test select
-- testing the sqlpi module pls work
SELECT * FROM testdb
""".strip('\n')


@pytest.fixture
def invalid_sql_built():
        return """
-- name: test_built$
-- testing the sqlpi module pls work
SELECT * FROM testdb
WHERE 1=1
AND col_1 = %()s
""".strip('\n')


@pytest.fixture
def sql_bang():
        return """
-- name: test_delete!
DELETE FROM testdb
""".strip('\n')


@pytest.fixture
def sql_bang_return():
        return """
-- name: test_return<!>
INSERT INTO test (col_1) VALUES ('A') RETURNING col_1
""".strip('\n')


@pytest.fixture
def sql_built():
        return """
-- name: test_built$
-- testing the sqlpi module pls work
SELECT * FROM testdb
WHERE 1=1
AND col_1 = %(val_1)s
""".strip('\n')


class TestLoad:
    def test_load(self, queries_file):
        parsed = load_queires(queries_file)
        assert isinstance(parsed, list)

    def test_load_arr(self, queries_file_arr):
        parsed = load_queires(queries_file_arr)
        assert isinstance(parsed, list)

    def test_load_name(self, queries_file):
        parsed = load_queires(queries_file)
        assert parsed[0][0] == 'TEST_SELECT'

    def test_load_fcn(self, queries_file):
        parsed = load_queires(queries_file)
        assert isinstance(parsed[0][1], functools.partial)

    def test_load_fcn_name(self, queries_file):
        parsed = load_queires(queries_file)
        fcn = parsed[0][1]
        assert fcn.__name__ == 'TEST_SELECT'

    def test_load_fcn_doc(self, queries_file):
        parsed = load_queires(queries_file)
        fcn = parsed[0][1]
        assert fcn.__doc__ == 'testing the sqlpi module pls work'


class TestQuery:
    def test_query(self, queries_file):
        sql = Queries(queries_file)
        assert isinstance(sql, Queries)

    def test_query_fcn(self, queries_file):
        sql = Queries(queries_file)
        assert isinstance(sql.TEST_SELECT, functools.partial)

    def test_query_fcn_args(self, queries_file):
        sql = Queries(queries_file)
        assert len(sql.TEST_SELECT.args) == 4


class TestExceptions:
    def test_load_exception(self, invalid_file_path):
        with pytest.raises(SQLLoadException):
            load_queires(invalid_file_path)

    def test_parse_exception(self, invalid_sql_name_start):
        with pytest.raises(SQLParseException):
            parse_sql_entry(invalid_sql_name_start)

    def test_parse_exception2(self, invalid_sql_name_spaces):
        with pytest.raises(SQLParseException):
            parse_sql_entry(invalid_sql_name_spaces)

    def test_parse_exception3(self, invalid_sql_built):
        with pytest.raises(SQLParseException):
            parse_sql_entry(invalid_sql_built)


class TestQueryTypes:
    def test_type_bang(self, sql_bang):
        name, fcn = parse_sql_entry(sql_bang)
        assert fcn.args[3] == INSERT_UPDATE_DELETE

    def test_type_bang_return(self, sql_bang_return):
        name, fcn = parse_sql_entry(sql_bang_return)
        assert fcn.args[3] == RETURN_ID

    def test_type_built(self, sql_built):
        name, fcn = parse_sql_entry(sql_built)
        assert fcn.args[3] == SELECT_BUILT
