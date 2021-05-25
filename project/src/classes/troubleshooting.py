# pylint:disable=no-name-in-module
from unicon.core.errors import SubCommandFailure


def retry_on_unicon_error(func):
    """Decorator to work around unicon `SubCommandFailure` error."""

    def wrapper(self, *args, **kwargs):
        res = None
        for _ in range(3):
            try:
                res = func(self, *args, **kwargs)
            except SubCommandFailure:
                pass
            else:
                break
        return res

    return wrapper
