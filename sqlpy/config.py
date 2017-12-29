import logging

# get the module logger
logger = logging.getLogger(__name__)


#: Detect if psycopg2 driver is being used
#: import quote_ident else set to None
try:
    from psycopg2.extensions import quote_ident
except ImportError:  # pragma: no cover
    quote_ident = None

#: The default value for strictly parsing built SQL queires
#: matching the number of arguments supplied to the SQL code
STRICT_BUILT_PARSE = False

#: The default value for controlling logging of SQL
#: query parameters in case of sensitive content
LOG_QUERY_PARAMS = True


#: Helper function to avoid repeating query log
#: block at the start of each execution try block
def log_query(query, args, kwargs, log_query_params):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug('SQL: {}'.format(query))
    if log_query_params:
        logger.info('Arguments: {}'.format(kwargs if len(kwargs) > 0 else args))
