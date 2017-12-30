import logging
from enum import Enum

# get the module logger
logger = logging.getLogger(__name__)


#: Detect if psycopg2 driver is being used
#: import quote_ident else set to None
try:
    from psycopg2.extensions import quote_ident
except ImportError:  # pragma: no cover
    quote_ident = None

#: The default value for strictly parsing built SQL queries
#: matching the number of parameters supplied to the SQL code
STRICT_BUILT_PARSE = False

#: The default value for controlling logging of SQL
#: query parameters in case of sensitive content
LOG_QUERY_PARAMS = True


def log_query(query, args, kwargs, log_query_params):
    """
    Helper function to avoid repeating query log block
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug('SQL: {}'.format(query))
    if log_query_params:
        logger.info('Arguments: {}'.format(kwargs if len(kwargs) > 0 else args))


class QueryType(Enum):
    """
    Enum object of the different SQL statement types
    """
    SELECT = 1
    INSERT_UPDATE_DELETE = 2
    SELECT_BUILT = 3
    RETURN_ID = 4
