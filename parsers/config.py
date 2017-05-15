from parsers import AU
from parsers import CA_AB, CA_BC, CA_NB, CA_NS, CA_ON, CA_PE
from parsers import IS
from parsers import FR
from parsers import ENTSOE
from parsers import NZ
from parsers import TR
from parsers import US

# 
# Ideally, we would merge this file with a json file in the config directory
#

# Define all production parsers
CONSUMPTION_PARSERS = {
    'AT': ENTSOE.fetch_consumption,
    'BE': ENTSOE.fetch_consumption,
    'BG': ENTSOE.fetch_consumption,
    'CH': ENTSOE.fetch_consumption,
    'CZ': ENTSOE.fetch_consumption,
    'DE': ENTSOE.fetch_consumption,
    'DK': ENTSOE.fetch_consumption,
    'EE': ENTSOE.fetch_consumption,
    'ES': ENTSOE.fetch_consumption,
    'FI': ENTSOE.fetch_consumption,
    # 'FR': FR.fetch_consumption,
    'GB': ENTSOE.fetch_consumption,
    'GB-NIR': ENTSOE.fetch_consumption,
    'GR': ENTSOE.fetch_consumption,
    'HU': ENTSOE.fetch_consumption,
    'IE': ENTSOE.fetch_consumption,
    'IT': ENTSOE.fetch_consumption,
    'LT': ENTSOE.fetch_consumption,
    'LU': ENTSOE.fetch_consumption,
    'LV': ENTSOE.fetch_consumption,
    'ME': ENTSOE.fetch_consumption,
    'NL': ENTSOE.fetch_consumption,
    'NO': ENTSOE.fetch_consumption,
    'PL': ENTSOE.fetch_consumption,
    'PT': ENTSOE.fetch_consumption,
    'RO': ENTSOE.fetch_consumption,
    'RS': ENTSOE.fetch_consumption,
    'SE': ENTSOE.fetch_consumption,
    'SI': ENTSOE.fetch_consumption,
    'SK': ENTSOE.fetch_consumption,
}
PRODUCTION_PARSERS = {
    'AT': ENTSOE.fetch_production,
    'BE': ENTSOE.fetch_production,
    'BG': ENTSOE.fetch_production,
    'CH': ENTSOE.fetch_production,
    'CZ': ENTSOE.fetch_production,
    'DE': ENTSOE.fetch_production,
    'DK': ENTSOE.fetch_production,
    'EE': ENTSOE.fetch_production,
    'ES': ENTSOE.fetch_production,
    'FI': ENTSOE.fetch_production,
    'FR': FR.fetch_production,
    'GB': ENTSOE.fetch_production,
    'GB-NIR': ENTSOE.fetch_production,
    'GR': ENTSOE.fetch_production,
    'HU': ENTSOE.fetch_production,
    'IE': ENTSOE.fetch_production,
    'IS': IS.fetch_production,
    'IT': ENTSOE.fetch_production,
    'LT': ENTSOE.fetch_production,
    'LU': ENTSOE.fetch_production,
    'LV': ENTSOE.fetch_production,
    'ME': ENTSOE.fetch_production,
    'NL': ENTSOE.fetch_production,
    'NO': ENTSOE.fetch_production,
    'PL': ENTSOE.fetch_production,
    'PT': ENTSOE.fetch_production,
    'RO': ENTSOE.fetch_production,
    'RS': ENTSOE.fetch_production,
    'SE': ENTSOE.fetch_production,
    'SI': ENTSOE.fetch_production,
    'SK': ENTSOE.fetch_production,
    'TR': TR.fetch_production,
    'US': US.fetch_production,
    # ** Canada
    'CA-AB': CA_AB.fetch_production,
    'CA-NB': CA_NB.fetch_production,
    'CA-NS': CA_NS.fetch_production,
    'CA-ON': CA_ON.fetch_production,
    'CA-PE': CA_PE.fetch_production,
    # ** Oceania
    'AUS-NSW': AU.fetch_production,
    'AUS-QLD': AU.fetch_production,
    'AUS-SA': AU.fetch_production,
    'AUS-TAS': AU.fetch_production,
    'AUS-VIC': AU.fetch_production,
    'NZ-NZN': NZ.fetch_production,
    'NZ-NZS': NZ.fetch_production,
}
# Keys are unique because both countries are sorted alphabetically
EXCHANGE_PARSERS = {
    # AL
    'AL->GR':     ENTSOE.fetch_exchange,
    'AL->ME':     ENTSOE.fetch_exchange,
    'AL->RS':     ENTSOE.fetch_exchange,
    # AT
    'AT->CH':     ENTSOE.fetch_exchange,
    'AT->CZ':     ENTSOE.fetch_exchange,
    'AT->DE':     ENTSOE.fetch_exchange,
    'AT->HU':     ENTSOE.fetch_exchange,
    'AT->IT':     ENTSOE.fetch_exchange,
    'AT->SI':     ENTSOE.fetch_exchange,
    # BA
    'BA->ME':     ENTSOE.fetch_exchange,
    'BA->RS':     ENTSOE.fetch_exchange,
    # BE
    'BE->FR':     ENTSOE.fetch_exchange,
    'BE->NL':     ENTSOE.fetch_exchange,
    # BG
    'BG->GR':     ENTSOE.fetch_exchange,
    'BG->MK':     ENTSOE.fetch_exchange,
    'BG->RO':     ENTSOE.fetch_exchange,
    'BG->RS':     ENTSOE.fetch_exchange,
    'BG->TR':     ENTSOE.fetch_exchange,
    # BY
    'BY->LT':     ENTSOE.fetch_exchange,
    # CH
    'CH->DE':     ENTSOE.fetch_exchange,
    'CH->FR':     ENTSOE.fetch_exchange,
    'CH->IT':     ENTSOE.fetch_exchange,
    # CZ
    'CZ->SK':     ENTSOE.fetch_exchange,
    'CZ->PL':     ENTSOE.fetch_exchange,
    'CZ->DE':     ENTSOE.fetch_exchange,
    # DE
    'DE->DK':     ENTSOE.fetch_exchange,
    'DE->FR':     ENTSOE.fetch_exchange,
    'DE->PL':     ENTSOE.fetch_exchange,
    'DE->NL':     ENTSOE.fetch_exchange,
    'DE->SE':     ENTSOE.fetch_exchange,
    # DK
    'DK->NO':     ENTSOE.fetch_exchange,
    'DK->SE':     ENTSOE.fetch_exchange,
    # EE
    'EE->FI':     ENTSOE.fetch_exchange,
    'EE->LV':     ENTSOE.fetch_exchange,
    'EE->RU':     ENTSOE.fetch_exchange,
    # ES
    'ES->FR':     ENTSOE.fetch_exchange,
    'ES->PT':     ENTSOE.fetch_exchange,
    # FI
    'FI->NO':     ENTSOE.fetch_exchange,
    'FI->RU':     ENTSOE.fetch_exchange,
    'FI->SE':     ENTSOE.fetch_exchange,
    # FR
    'FR->GB':     ENTSOE.fetch_exchange,
    'FR->IT':     ENTSOE.fetch_exchange,
    # GB
    'GB->IE':     ENTSOE.fetch_exchange,
    'GB->GB-NIR': ENTSOE.fetch_exchange,
    'GB->NL':     ENTSOE.fetch_exchange,
    # GB-NIR
    'GB-NIR->IE': ENTSOE.fetch_exchange,
    # GR
    'GR->IT':     ENTSOE.fetch_exchange,
    'GR->MK':     ENTSOE.fetch_exchange,
    'GR->TR':     ENTSOE.fetch_exchange,
    # HR
    'HR->HU':     ENTSOE.fetch_exchange,
    'HR->RS':     ENTSOE.fetch_exchange,
    # HU
    'HU->RO':     ENTSOE.fetch_exchange,
    'HU->RS':     ENTSOE.fetch_exchange,
    'HU->SK':     ENTSOE.fetch_exchange,
    'HU->UA':     ENTSOE.fetch_exchange,
    # IT
    'IT->MT':     ENTSOE.fetch_exchange,
    'IT->SI':     ENTSOE.fetch_exchange,
    # LT
    'LT->LV':     ENTSOE.fetch_exchange,
    'LT->PL':     ENTSOE.fetch_exchange,
    'LT->RU':     ENTSOE.fetch_exchange,
    'LT->SE':     ENTSOE.fetch_exchange,
    # LV
    'LV->RU':     ENTSOE.fetch_exchange,
    # ME
    'ME->RS':     ENTSOE.fetch_exchange,
    # MD
    # 'MD->RO':     ENTSOE.fetch_exchange,
    # MK
    'MK->RS':     ENTSOE.fetch_exchange,
    # NL
    'NL->NO':     ENTSOE.fetch_exchange,
    # NO
    'NO->SE':     ENTSOE.fetch_exchange,
    # PL
    'PL->SE':     ENTSOE.fetch_exchange,
    'PL->SK':     ENTSOE.fetch_exchange,
    'PL->UA':     ENTSOE.fetch_exchange,
    # RO
    'RO->RS':     ENTSOE.fetch_exchange,
    'RO->UA':     ENTSOE.fetch_exchange,
    # SK
    'SK->UA':     ENTSOE.fetch_exchange,
    # ** Canada
    'CA-AB->CA-BC': CA_AB.fetch_exchange,
    'CA-AB->CA-SK': CA_AB.fetch_exchange,
    'CA-AB->US': CA_AB.fetch_exchange,
    'CA-BC->US':    CA_BC.fetch_exchange,
    'CA-MB->CA-ON': CA_ON.fetch_exchange,
    'CA-ON->CA-QC': CA_ON.fetch_exchange,
    'CA-ON->US':    CA_ON.fetch_exchange,
    'CA-NB->CA-NS': CA_NB.fetch_exchange,
    'CA-NB->CA-PE': CA_NB.fetch_exchange,
    'CA-NB->CA-QC': CA_NB.fetch_exchange,
    'CA-NB->US':    CA_NB.fetch_exchange,
    # ** Oceania
    'AUS-NSW->AUS-QLD': AU.fetch_exchange,
    'AUS-NSW->AUS-VIC': AU.fetch_exchange,
    'AUS-SA->AUS-VIC':  AU.fetch_exchange,
    'AUS-TAS->AUS-VIC': AU.fetch_exchange,
    'NZ-NZN->NZ-NZS': NZ.fetch_exchange,
}

PRICE_PARSERS = {
    'AT': ENTSOE.fetch_price,
    'BE': ENTSOE.fetch_price,
    'BG': ENTSOE.fetch_price,
    'CH': ENTSOE.fetch_price,
    'CZ': ENTSOE.fetch_price,
    'DE': ENTSOE.fetch_price,
    'DK': ENTSOE.fetch_price,
    'EE': ENTSOE.fetch_price,
    'ES': ENTSOE.fetch_price,
    'FI': ENTSOE.fetch_price,
    'FR': FR.fetch_price,
    'GB': ENTSOE.fetch_price,
    'GB-NIR': ENTSOE.fetch_price,
    'GR': ENTSOE.fetch_price,
    'HU': ENTSOE.fetch_price,
    'IE': ENTSOE.fetch_price,
    'IT': ENTSOE.fetch_price,
    'LT': ENTSOE.fetch_price,
    'LU': ENTSOE.fetch_price,
    'LV': ENTSOE.fetch_price,
    'NL': ENTSOE.fetch_price,
    'NO': ENTSOE.fetch_price,
    'PL': ENTSOE.fetch_price,
    'PT': ENTSOE.fetch_price,
    'RO': ENTSOE.fetch_price,
    'RS': ENTSOE.fetch_price,
    'SE': ENTSOE.fetch_price,
    'SI': ENTSOE.fetch_price,
    'SK': ENTSOE.fetch_price,
    # Canada
    'CA-AB': CA_AB.fetch_price,
    'CA-ON': CA_ON.fetch_price,
    # * Oceania
    'AUS-NSW': AU.fetch_price,
    'AUS-QLD': AU.fetch_price,
    'AUS-SA': AU.fetch_price,
    'AUS-TAS': AU.fetch_price,
    'AUS-VIC': AU.fetch_price,
}

GENERATION_FORECAST_PARSERS = {
    'DK': ENTSOE.fetch_generation_forecast
}

EXCHANGE_FORECAST_PARSERS = {
    'DE->DK': ENTSOE.fetch_exchange_forecast,
    'DK->NO': ENTSOE.fetch_exchange_forecast,
    'DK->SE': ENTSOE.fetch_exchange_forecast
}
