from enum import Enum

#: Detect if psycopg2 driver is being used
#: import quote_ident else set to None
try:
    from psycopg2.extensions import quote_ident
except ImportError:  # pragma: no cover
    quote_ident = None

#: Detect if psycopg2 driver is being used
#: import execute_values else set to None
try:
    from psycopg2.extras import execute_values
except ImportError:  # pragma: no cover
    execute_values = None

#: The default value for strictly parsing built SQL queries
#: matching the number of parameters supplied to the SQL code
STRICT_BUILT_PARSE = False

#: The default value for uppercasing the names of SQL queries
#: prepared functions
UPPERCASE_QUERY_NAME = True

#: The default value for controlling logging of SQL
#: query parameters in case of sensitive content
LOG_QUERY_PARAMS = True


class QueryType(Enum):
    """
    Enum object of the different SQL statement types
    """
    SELECT = 1
    INSERT_UPDATE_DELETE = 2
    SELECT_BUILT = 3
    RETURN_ID = 4
    CALL_PROC = 5
