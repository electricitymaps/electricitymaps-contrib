from ENTSOE import fetch_ENTSOE

COUNTRY_CODE = 'LV'
ENTSOE_DOMAIN = '10YLV-1001A00074'

def fetch_LV(session=None): 
    return fetch_ENTSOE(ENTSOE_DOMAIN, COUNTRY_CODE, session)

if __name__ == '__main__': print(fetch_LV())
