from datetime import timedelta


def refetch_frequency(frequency: timedelta):
    """Specifies the refetch frequency of a parser.
    The refetch frequency is used to determine the how much data is returned by the parser.

    i.e. if we refetch from d1 to d2 and the frequency is timedelta(days=1), then we will only
    call the function once every day between d1 and d2.
    """
    assert isinstance(frequency, timedelta)

    def wrap(f):
        def wrapped_f(*args, **kwargs):
            result = f(*args, **kwargs)
            return result

        wrapped_f.REFETCH_FREQUENCY = frequency
        return wrapped_f

    return wrap
