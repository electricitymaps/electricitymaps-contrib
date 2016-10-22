from ENTSOE import fetch_ENTSOE

COUNTRY_CODE = 'PL'
ENTSOE_DOMAIN = '10YPL-AREA-----S'

def fetch_PL(): return fetch_ENTSOE(ENTSOE_DOMAIN, COUNTRY_CODE)

if __name__ == '__main__': print(fetch_PL())
