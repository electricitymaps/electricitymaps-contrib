import os
from copy import deepcopy
from datetime import timedelta
from inspect import signature
from logging import getLogger

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
            logger = kwargs.get("logger", getLogger(__name__))
            session = Session() if session is None else session
            old_adapters = None
            if "https://" in session.adapters or "http://" in session.adapters:
                logger.warning("Session already has adapters, they will be overriden.")
                old_adapters = deepcopy(session.adapters)
            session.mount("https://", HTTPAdapter(max_retries=retry_policy))
            session.mount("http://", HTTPAdapter(max_retries=retry_policy))
            result = f(*args, **kwargs)
            del session.adapters["https://"]
            del session.adapters["http://"]
            if old_adapters is not None:
                session.adapters.update(old_adapters)
            return result

        return wrapped_f

    return wrap


def use_proxy(country_code: str):
    """
    Decorator to route requests through webshare.io proxies for a specific country.

    This decorator should be used as a last resort when the data provider is non-responsive
    and other proxy methods (like cloud run datacenter proxies) do not work. Note that this
    proxy service is not free and is charged per GB.

    Args:
        country_code (str): The ISO 3166-1 alpha-2 code of the country for which the proxy should be used.

    Usage:
    ```
        @use_proxy(country_code='MY')
        def fetch_production(zone_key, session, target_datetime, logger):
            ...
    ```
    """

    def wrap(f):
        def wrapped_f(*args, **kwargs):
            WEBSHARE_USERNAME = os.environ.get("WEBSHARE_USERNAME")
            WEBSHARE_PASSWORD = os.environ.get("WEBSHARE_PASSWORD")

            sig = signature(f)

            is_exchange_parser = (
                "zone_key1" in sig.parameters or "zone_key2" in sig.parameters
            )
            is_production_parser = "zone_key" in sig.parameters

            zone_keys = None
            if is_exchange_parser:
                zone_key1 = args[0] if len(args) > 0 else kwargs.get("zone_key1")
                zone_key2 = args[1] if len(args) > 1 else kwargs.get("zone_key2")
                session = args[2] if len(args) > 2 else kwargs.get("session")
                target_datetime = (
                    args[3] if len(args) > 3 else kwargs.get("target_datetime")
                )
                logger = (
                    args[4]
                    if len(args) > 4
                    else kwargs.get("logger") or getLogger(__name__)
                )
                zone_keys = [zone_key1, zone_key2]
            elif is_production_parser:
                zone_key = args[0] if len(args) > 0 else kwargs.get("zone_key")
                session = args[1] if len(args) > 1 else kwargs.get("session")
                target_datetime = (
                    args[2] if len(args) > 2 else kwargs.get("target_datetime")
                )
                logger = (
                    args[3]
                    if len(args) > 3
                    else kwargs.get("logger") or getLogger(__name__)
                )
                zone_keys = [zone_key]
            else:
                raise ValueError(
                    "Invalid function signature. Maybe you added the @decorators in the wrong order? The use_proxy decorator should be the bottom decorator."
                )

            if WEBSHARE_USERNAME is None or WEBSHARE_PASSWORD is None:
                logger.error(
                    "Proxy environment variables are not set. Continuing without proxy...\nAdd WEBSHARE_USERNAME and WEBSHARE_PASSWORD to use the proxy."
                )
                return f(*args, **kwargs)

            session = Session() if session is None else session
            old_proxies = session.proxies
            new_proxies = {
                "http": f"http://{WEBSHARE_USERNAME}-{country_code}-rotate:{WEBSHARE_PASSWORD}@p.webshare.io:80/",
                "https": f"http://{WEBSHARE_USERNAME}-{country_code}-rotate:{WEBSHARE_PASSWORD}@p.webshare.io:80/",
            }

            session.proxies.update(new_proxies)
            result = f(*zone_keys, session, target_datetime, logger)
            session.proxies.update(old_proxies)
            return result

        return wrapped_f

    return wrap
