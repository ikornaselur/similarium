class SemantleException(Exception):
    pass


class DatabaseException(SemantleException):
    pass


class NotFound(DatabaseException):
    pass
