class SimilariumException(Exception):
    pass


class InvalidWord(SimilariumException):
    pass


class DatabaseException(SimilariumException):
    pass


class NotFound(DatabaseException):
    pass
