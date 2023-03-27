from datetime import timedelta
from typing import Optional

from requests import Session
from requests.adapters import HTTPAdapter, Retry


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


def retry_policy(retry_policy: Retry):

    assert isinstance(retry_policy, Retry)

    def wrap(f):
        def wrapped_f(*args, **kwargs):
            session = args[1] if len(args) > 2 else kwargs.get("session")
            session = Session() if session is None else session
            session.mount("https://", HTTPAdapter(max_retries=retry_policy))
            result = f(*args, **kwargs)
            del session.adapters["https://"]
            return result

        return wrapped_f

    return wrap
