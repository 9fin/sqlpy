import logging
from .sqlpy import *


__description__ = 'Write actual SQL to retrieve your data.'

# add default NullHandler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())
