class SimilariumException(Exception):
    pass


class InvalidWord(SimilariumException):
    pass


class ParseException(SimilariumException):
    pass


class SlackException(SimilariumException):
    pass


class ChannelNotFound(SlackException):
    pass


class NotInChannel(SlackException):
    pass


class DatabaseException(SimilariumException):
    pass


class NotFound(DatabaseException):
    pass
