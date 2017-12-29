#: Detect if psycopg2 driver is being used
#: import quote_ident else set to None
try:
    from psycopg2.extensions import quote_ident
except ImportError:  # pragma: no cover
    quote_ident = None

#: The default value for strictly parsing built SQL queires
#: matching the number of arguments supplied to the SQL code
STRICT_BUILT_PARSE = False
