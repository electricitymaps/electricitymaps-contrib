from ENTSOE import fetch_ENTSOE

COUNTRY_CODE = 'LT'
ENTSOE_DOMAIN = '10YLT-1001A0008Q'

def fetch_LT(session=None): 
    return fetch_ENTSOE(ENTSOE_DOMAIN, COUNTRY_CODE, session)

if __name__ == '__main__': print(fetch_LT())
