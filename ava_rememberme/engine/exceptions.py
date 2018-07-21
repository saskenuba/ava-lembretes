class ScraperError(Exception):
    """
    Base exception for errors raised by the scraper
    """

    def __init__(self, msg=None):
        "docstring"
        self.msg = msg


class LoginError(ScraperError):
    """
    Error while logging in into AVA Platform
    """


class DriverInstanceError(ScraperError):
    """
    Error while instantiating new driver
    """


class WrongPageError(ScraperError):
    """
    Not the correct location to complete action.
    """


class RegisterError(Exception):
    """
    Base exception for errors raised at the user registration
    """
