class SemantleException(Exception):
    pass


class InvalidWord(SemantleException):
    pass


class DatabaseException(SemantleException):
    pass


class NotFound(DatabaseException):
    pass
