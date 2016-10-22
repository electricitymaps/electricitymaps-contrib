from ENTSOE import fetch_ENTSOE

COUNTRY_CODE = 'CH'
ENTSOE_DOMAIN = '10YNL----------L'

def fetch_CH(): return fetch_ENTSOE(ENTSOE_DOMAIN, COUNTRY_CODE)

if __name__ == '__main__': print(fetch_CH())
