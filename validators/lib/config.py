def validator(kind: str):
    """
    Decorator function to mark a function as a validator.
    The backend will run all functions marked as validators.

    A validator function is expected to return as a pandas Series of values between 0 and 1,
    where 1 means that no problems was found and 0 means that the data point is invalid.
    Floating points between 0 and 1 can be used to indicate suspicious data points.
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
        ]  # List of argument names

        return wrapped_f

    return wrap
