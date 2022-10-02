from typing import Callable


def validator(
    kind: str, zone_keys: list[str] = None, not_zone_keys: list[str] = None
) -> Callable:
    """
    Decorator function to mark a function as a validator.
    The backend will run all functions marked as validators.

    A validator function is expected to return as a pandas Series of values between 0 and 1,
    where 1 means that no problems was found and 0 means that the data point is invalid.
    Floating points between 0 and 1 can be used to indicate suspicious data points.

    Parameters
    ----------
    kind : str
        The kind of data that validator supports. e.g. "production", "exchange"
    zone_keys : list[str]
        If this is included, the validator will only be run for the given zone keys.
    not_zone_keys : list[str]
        If this is included, the validator will run for ALL OTHER zones.
    """
    assert isinstance(kind, str)

    def wrap(f):
        def wrapped_f(*args, **kwargs):
            result = f(*args, **kwargs)
            return result

        wrapped_f.IS_VALIDATOR = True
        wrapped_f.VALIDATOR_KIND = kind
        wrapped_f.args = f.__code__.co_varnames[
            : f.__code__.co_argcount
        ]  # list of argument names

        wrapped_f.zone_keys = zone_keys
        wrapped_f.not_zone_keys = not_zone_keys

        return wrapped_f

    return wrap
