from ENTSOE import fetch_ENTSOE

COUNTRY_CODE = 'PT'
ENTSOE_DOMAIN = '10YPT-REN------W'

def fetch_PT(): return fetch_ENTSOE(ENTSOE_DOMAIN, COUNTRY_CODE)

if __name__ == '__main__': print(fetch_PT())
