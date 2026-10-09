import os
from datetime import datetime, timezone

TOKEN_WIKI_URL = (
    "https://github.com/electricitymaps/electricitymaps-contrib/wiki/Create-tokens"
)


def get_token(token):
    """
    Get a token from the environment variables.

    Raises:
        Exception: if the token variable does not exists or if its value is null
    """
    if not os.environ.get(token):
        raise Exception(
            f"Environment variable {token} not found !\n"
            f"Please visit {TOKEN_WIKI_URL}#{token} for more information about how to create "
            "tokens."
        )
    return os.environ[token]


def to_utc(dt: datetime | None) -> datetime:
    """Returns `dt` as an aware UTC datetime: now if None, naive values assumed UTC."""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
