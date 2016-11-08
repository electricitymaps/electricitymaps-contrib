from ENTSOE import fetch_ENTSOE

COUNTRY_CODE = 'NO'
ENTSOE_DOMAIN = '10YNO-0--------C'

def fetch_NO(session=None): 
    return fetch_ENTSOE(ENTSOE_DOMAIN, COUNTRY_CODE, session)

if __name__ == '__main__': print(fetch_NO())
