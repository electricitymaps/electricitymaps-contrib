from ENTSOE import fetch_ENTSOE

COUNTRY_CODE = 'SI'
ENTSOE_DOMAIN = '10YSI-ELES-----O'

def fetch_SI(session=None):
    return fetch_ENTSOE(ENTSOE_DOMAIN, COUNTRY_CODE, session)

if __name__ == '__main__': print(fetch_SI())
