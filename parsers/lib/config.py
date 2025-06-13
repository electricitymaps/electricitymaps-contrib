import functools
import os
from collections.abc import ItemsView, KeysView, ValuesView
from copy import deepcopy
from datetime import timedelta
from enum import Enum
from inspect import signature
from logging import getLogger
from typing import TypeVar

import requests
from requests import Session
from requests.adapters import HTTPAdapter, Retry

ModeEnumType = TypeVar("ModeEnumType", bound="BaseModeEnum")


# TODO: Switch this to StringEnum when we migrate to Python 3.11
class BaseModeEnum(str, Enum):
    """Base class for Mode enums."""

    def __str__(self) -> str:
        return self.value

    @classmethod
    def values(cls: type[ModeEnumType]) -> ValuesView[ModeEnumType]:
        """Return a Values View of all enum members."""
        return cls.__members__.values()

    @classmethod
    def names(cls) -> KeysView[str]:
        """Return a Keys View of all enum names."""
        return cls.__members__.keys()

    @classmethod
    def items(cls: type[ModeEnumType]) -> ItemsView[str, ModeEnumType]:
        """Return an Items View of (name, member) tuples."""
        return cls.__members__.items()


class ProductionModes(BaseModeEnum):
    """Energy production modes/sources used throughout the parsers."""

    # TODO: When we migrate to StringEnum, we should use the `auto()` method
    BIOMASS = "biomass"
    COAL = "coal"
    GAS = "gas"
    GEOTHERMAL = "geothermal"
    HYDRO = "hydro"
    NUCLEAR = "nuclear"
    OIL = "oil"
    SOLAR = "solar"
    WIND = "wind"
    UNKNOWN = "unknown"


class StorageModes(BaseModeEnum):
    """Energy storage modes/sources used throughout the parsers."""

    # TODO: When we migrate to StringEnum, we should use the `auto()` method
    BATTERY = "battery"
    HYDRO = "hydro"


def refetch_frequency(frequency: timedelta):
    """Specifies the refetch frequency of a parser.
    The refetch frequency is used to determine the how much data is returned by the parser.

    i.e. if we refetch from d1 to d2 and the frequency is timedelta(days=1), then we will only
    call the function once every day between d1 and d2.
    """
    assert isinstance(frequency, timedelta)

    def wrap(f):
        @functools.wraps(f)
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


def use_proxy(country_code: str, monkeypatch_for_pydataxm: bool = False):
    """
    Decorator to route requests through webshare.io proxies for a specific country.

    This decorator should be used as a last resort when the data provider is non-responsive
    and other proxy methods (like cloud run datacenter proxies) do not work. Note that this
    proxy service is not free and is charged per GB.

    If you create an account with webshare.io to develop parsers for this
    project, you should subscribe to the "residential" proxy type (not "static
    residential"), as this choice includes most countries. As a practical
    example, South Korea proxies are only available using this subscription.

    Args:
        country_code (str):
            The ISO 3166-1 alpha-2 code of the country for which the proxy
            should be used.
        monkeypatch_for_pydataxm (bool):
            The CO parser specifically makes use both requests.post and
            aiohttp.ClientSession via a API specific third party library called
            pydataxm that isn't configurable to use a proxy. By setting this to
            True, we temporarily monkeypatch whats needed to get setup the
            proxy.

            See

    Usage:
    ```
        @use_proxy(country_code='MY')
        def fetch_production(zone_key, session, target_datetime, logger):
            ...
    ```
    """

    def wrap(f):
        sig = signature(f)
        if "zone_key" in sig.parameters:
            exchange_signature = False
        elif "zone_key1" in sig.parameters and "zone_key2" in sig.parameters:
            exchange_signature = True
        else:
            raise ValueError(
                "Invalid function signature. Maybe you added the @decorators in "
                "the wrong order? The use_proxy decorator should be the bottom decorator."
            )

        def wrapped_f(*args, **kwargs):
            WEBSHARE_USERNAME = os.environ.get("WEBSHARE_USERNAME")
            WEBSHARE_PASSWORD = os.environ.get("WEBSHARE_PASSWORD")
            if not WEBSHARE_USERNAME or not WEBSHARE_PASSWORD:
                logger = kwargs.get("logger", getLogger(__name__))
                logger.warning(
                    "Proxy environment variables are not set. "
                    "Attempting without proxy...\n"
                    "Add WEBSHARE_USERNAME and WEBSHARE_PASSWORD to use the proxy."
                )
                return f(*args, **kwargs)

            # get an existing Session object from args or kwargs, or create a
            # new one, so it can be temporarily re-configured
            if exchange_signature and len(args) >= 3:
                session = args[2]
            elif not exchange_signature and len(args) >= 2:
                session = args[1]
            else:
                session = kwargs.setdefault("session", Session())

            requests_proxy_dict = {
                "http": f"http://{WEBSHARE_USERNAME}-{country_code}-rotate:{WEBSHARE_PASSWORD}@p.webshare.io:80/",
                "https": f"http://{WEBSHARE_USERNAME}-{country_code}-rotate:{WEBSHARE_PASSWORD}@p.webshare.io:80/",
            }

            if monkeypatch_for_pydataxm:
                from aiohttp import BasicAuth, ClientSession

                aiohttp_old_post = ClientSession.post
                requests_old_post = requests.post

                ClientSession.post = functools.partialmethod(
                    ClientSession.post,
                    proxy="http://p.webshare.io",
                    proxy_auth=BasicAuth(
                        f"{WEBSHARE_USERNAME}-{country_code}-rotate",
                        WEBSHARE_PASSWORD,
                    ),
                )
                requests.post = functools.partial(
                    requests.post,
                    proxies=requests_proxy_dict,
                )

            old_proxies = session.proxies
            session.proxies = requests_proxy_dict
            try:
                return f(*args, **kwargs)
            finally:
                session.proxies = old_proxies
                if monkeypatch_for_pydataxm:
                    ClientSession.post = aiohttp_old_post
                    requests.post = requests_old_post

        return wrapped_f

    return wrap
