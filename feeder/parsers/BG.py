from ENTSOE import fetch_ENTSOE

COUNTRY_CODE = 'BG'
ENTSOE_DOMAIN = '10YCA-BULGARIA-R'

def fetch_BG(session=None):
    return fetch_ENTSOE(ENTSOE_DOMAIN, COUNTRY_CODE, session)

if __name__ == '__main__': print(fetch_BG())