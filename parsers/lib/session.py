import ssl

import urllib3
from requests import Session, adapters


class LegacyHttpAdapter(adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, ssl_context=ctx
        )


# Use a LegacyHttpAdapter to avoid "unsafe legacy renegotiation disabled" error
# Original code source: https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled
def get_session_with_legacy_adapter():
    session = Session()
    session.mount("https://", LegacyHttpAdapter())
    session.mount("http://", LegacyHttpAdapter())
    return session
