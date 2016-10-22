from ENTSOE import fetch_ENTSOE

COUNTRY_CODE = 'BE'
ENTSOE_DOMAIN = '10YBE----------2'

def fetch_BE(): return fetch_ENTSOE(ENTSOE_DOMAIN, COUNTRY_CODE)

if __name__ == '__main__': print(fetch_BE())
