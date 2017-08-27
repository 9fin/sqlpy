from __future__ import print_function
import pytest
import os
import functools
from sqlpy.sqlpy import Queries, load_queires


@pytest.fixture
def queries_file():
    return os.path.join(os.getcwd(), 'test_queries.sql')


@pytest.fixture
def queries_file_arr():
    return [os.path.join(os.getcwd(), 'test_queries.sql')]


class TestParse:
    def test_parse(self, queries_file):
        parsed = load_queires(queries_file)
        assert isinstance(parsed, list)

    def test_parse_name(self, queries_file):
        parsed = load_queires(queries_file)
        assert parsed[0][0] == 'TEST_SELECT'

    def test_parse_fcn(self, queries_file):
        parsed = load_queires(queries_file)
        assert isinstance(parsed[0][1], functools.partial)

    def test_parse_fcn_name(self, queries_file):
        parsed = load_queires(queries_file)
        fcn = parsed[0][1]
        assert fcn.__name__ == 'TEST_SELECT'

    def test_parse_fcn_doc(self, queries_file):
        parsed = load_queires(queries_file)
        fcn = parsed[0][1]
        assert fcn.__doc__ == 'testing the sqlpi module pls work'
