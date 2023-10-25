import math
import os

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


def nan_to_zero(v):
    if math.isnan(v):
        return 0
    return v
