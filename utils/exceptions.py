from enum import Enum

class GenshinGrabException(Exception):
    """
    The base exception class for genshingrab.
    """
    pass

class IMPROPER_ARGUMENT_TYPE(Enum):
    """
    Enumeration for `ImproperArgumentError` `error_type` attribute.

    Enumerations:
        `NONE_GIVEN` -- No argument is given
        `NOT_MUCH` -- Not much argument
        `TOO_MUCH` -- Too much argument than allowed
    """
    DEFAULT = 'There is at least one improper argument passing'
    NONE_GIVEN = 'No argument is given'
    NOT_MUCH = 'Not much argument '
    TOO_MUCH = 'Too much argument than allowed'
    WRONG_FORMAT = 'Argument given is in wrong format'
    OTHER = 'Irregular form of improper argument passing'

class ImproperArgumentError(GenshinGrabException):
    """
    A genshingrab exception for calling a function with 
    wrong argument setup, especially for functions using
    asterisk arguments such as `*args` and `**kwargs`.

    Attributes
    ----------

    `error_type` : `IMPROPER_ARGUMENT_TYPE(Enum)` -- The enumeration of improper argument type

    `message` : `str` -- Error message

    `args` : `tuple` or `list` or `dict` or combinations of them -- Passed arguments. Usually the `*args` or `**kwargs` are just passed as-is
    """
    def __init__(self, error_type=IMPROPER_ARGUMENT_TYPE.DEFAULT, message=IMPROPER_ARGUMENT_TYPE.DEFAULT.value, args=None):
        self.error_type = error_type
        self.message = message
        self.args = args

    def __str__(self):
        return f'{self.message}\n\n{self.error_type}\nargs: {self.args}'

class SettingsError(GenshinGrabException):
    """
    A genshingrab exception for having invalid data on a settings JSON file.
    """
    pass