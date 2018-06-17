from __future__ import print_function, absolute_import
import logging
from .sqlpy import Queries, load_queries, parse_sql_entry, QueryType
from .exceptions import (SQLpyException, SQLLoadException,
                         SQLParseException, SQLArgumentException)


__description__ = 'Write actual SQL to retrieve your data.'

# add default NullHandler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())


__all__ = [
    'Queries',
    'load_queries',
    'parse_sql_entry',
    'QueryType',
    'SQLpyException',
    'SQLLoadException',
    'SQLParseException',
    'SQLArgumentException'
]
