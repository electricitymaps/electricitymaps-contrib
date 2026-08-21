"""Shared transport-layer helpers for parser HTTP sessions."""

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 3 retries on 429 + transient 5xx, 0/2/4 s exponential backoff. urllib3
# honours `Retry-After` for free. Pass a custom `Retry` to `mount_retry`
# to widen `allowed_methods` (e.g. POST for OAuth token endpoints).
#
# Does NOT reliably cover `ConnectTimeoutError` — #8616 tried `connect=N`,
# #8617 reverted it. Parsers needing that add an app-level loop on top
# (see ESIOS.fetch_exchange).
DEFAULT_RETRY = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)


def mount_retry(session: Session, retry: Retry = DEFAULT_RETRY) -> Session:
    """Mount a retrying HTTPAdapter on `session` for http(s)://.

    Idempotent — re-mounting overrides the previous adapter with one
    carrying the same Retry config, so calling this multiple times is
    safe (each public fetcher can call it without coordinating).
    Returns `session` so the call composes with `session or Session()`.
    """
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
