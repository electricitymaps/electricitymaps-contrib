"""Shared transport-layer helpers for parser HTTP sessions."""

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Default retry policy: 3 retries, exponential backoff `2 * 2^(n-1)` s
# between attempts (0, 2, 4 s), on rate-limit (429) and transient 5xx.
# urllib3 honours `Retry-After` automatically when the server sends it.
# Bounded so a sustained throttle still fails the task within Cloud Run's
# budget and lets the queue retry.
#
# `allowed_methods=["GET"]` matches the urllib3 default for safe-by-default
# behaviour; parsers that need POST retried (e.g. OAuth token endpoints
# where a replayed request just acquires a fresh token) should build their
# own `Retry` with a widened allow-list and pass it to `mount_retry`.
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
