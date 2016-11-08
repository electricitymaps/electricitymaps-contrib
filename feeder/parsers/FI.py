from ENTSOE import fetch_ENTSOE

COUNTRY_CODE = 'FI'
ENTSOE_DOMAIN = '10YFI-1--------U'

def fetch_FI(session=None):
    return fetch_ENTSOE(ENTSOE_DOMAIN, COUNTRY_CODE, session)

if __name__ == '__main__': print(fetch_FI())
