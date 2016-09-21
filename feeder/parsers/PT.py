import requests, dateutil, arrow
from bs4 import BeautifulSoup

COUNTRY_CODE = 'PT'

def GWh_per_day_to_MW(energy_day_gwh):
	hours_in_a_day = 24;

	power_mw = energy_day_gwh / 24 * 1000;

	return power_mw

def fetch_PT():

	r = requests.get('http://www.centrodeinformacao.ren.pt/EN/InformacaoExploracao/Pages/EstatisticaDiaria.aspx')
	soup = BeautifulSoup(r.text, 'html.parser')

	trs = soup.find_all("tr", { "class" : "grid_row" })
	daily_values = []

	for tr in trs:
		value = tr.find_all("td")[2].string # Daily values are in column 3
		value = GWh_per_day_to_MW(float(value)) # str -> float
		daily_values.append(value)

	date_str = soup.find(id="ctl00_m_g_5e80321e_76aa_4894_8c09_4e392fc3dc7d_txtDatePicker_foo")['value']
	date = arrow.get(date_str + " 23:59:59", "DD-MM-YYYY HH:mm:ss").replace(tzinfo=dateutil.tz.gettz('Europe/Lisbon')).datetime


	data = {
		'countryCode': COUNTRY_CODE,
		'datetime': date, # UTC
		'production': {
		    'wind': daily_values[9],
		    'solar': daily_values[10],
		    'hydro': daily_values[0] + daily_values[7], # There are 2 different production regimes
		    'coal': daily_values[1] + daily_values[8], # There are 2 different production regimes
		    'nuclear': 0
		},
		'consumption': {
		    'unknown': daily_values[13]
		},
		'exchange':{
			'ES': daily_values[3] - daily_values[4]
		}

	}

	return data

if __name__ == '__main__':
    print fetch_PT()
