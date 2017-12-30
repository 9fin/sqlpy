import os
from errno import ENOENT


class SQLpyException(Exception):
    """Base Exception for sqlpy exceptions."""
    pass


class SQLLoadException(SQLpyException, IOError):
    """Exception raised when errors occur in file IO."""
    def __init__(self, msg, filename):
        super(SQLLoadException, self).__init__(os.strerror(ENOENT), msg, filename)


class SQLParseException(SQLpyException, ValueError):
    """Exception raised when errors occur in building SQL strings."""
    def __init__(self, msg, string):
        super(SQLParseException, self).__init__('{}"{}"'.format(msg, string))


class SQLArgumentException(SQLpyException, ValueError):
    """Exception raised when errors occur arguments passed to function partial."""
    def __init__(self, msg, key=None):
        super(SQLArgumentException, self).__init__('{}{}'.format(msg, key if key else ''))
