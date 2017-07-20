#!/usr/bin/env python3

import arrow
import string
import requests
from bs4 import BeautifulSoup
import re
import itertools


#This parser gets hourly electricity generation data from portalweb.cammesa.com/Memnet1/default.aspx
#for Argentina.  Currently wind and solar power are small contributors and not monitored but this is
#likely to change in the future.

#TODO
#Improve plant mapping for oil, coal and biomass.  Mention EMBALSE nuclear plant.
#Understand if there is a way to get hydro storage.
#Integrate price MW/MWh, seems to be present in data.
#Research hydro sharing with Uruguay and Paraguay

#Useful links.
#https://en.wikipedia.org/wiki/Electricity_sector_in_Argentina
#https://en.wikipedia.org/wiki/List_of_power_stations_in_Argentina
#http://globalenergyobservatory.org/countryid/10#
#http://www.industcards.com/st-other-argentina.htm


#Map of power plants to generation type.

power_plant_type = {
                     'ABRODI01': 'gas',
                     'ACAJTG01': 'gas',
                     'ACAJTG02': 'gas',
                     'ACAJTG04': 'gas',
                     'ACAJTG05': 'gas',
                     'ACAJTG06': 'gas',
                     'ACAJTV07': 'gas',
                       'ADTOHI': 'hydro',
                     'AESPTG01': 'gas',
                     'AESPTG02': 'gas',
                     'AESPTV01': 'gas',
                       'ALICHI': 'hydro',
                     'ALOMDI01': 'gas',
                     'ALUMDI01': 'gas',
                       'AMEGHI': 'hydro',
                     'ANATDI01': 'gas',
                     'ANATDI02': 'gas',
                       'ARA2EO': 'hydro',
                       'ARAUEO': 'hydro',
                     'ARGETG01': 'gas',
                     'ARISDI01': 'gas',
                     'ARMATG01': 'gas',
                     'ARMATG02': 'gas',
                     'ARMATG03': 'gas',
                     'ARREDI01': 'gas',
                       'ARROHI': 'hydro',
                     'ATUCNUCL': 'nuclear',
                     'ATU2NUCL': 'nuclear'    
                     'AVALTG21': 'gas',
                     'AVALTG22': 'gas',
                     'AVALTG23': 'gas',
                     'AVALTV11': 'gas',
                     'AVALTV12': 'gas',
                     'BAMODI01': 'gas',
                     'BANDDI01': 'gas',
                     'BARDDI01': 'gas',
                     'BBLATV29': 'gas',
                     'BBLATV30': 'gas',
                     'BERIDI01': 'gas',
                     'BLOPTG01': 'gas',
                     'BRAGTG01': 'gas',
                     'BRAGTG02': 'gas',
                     'BRAGTG03': 'gas',
                     'BRAGTG04': 'gas',
                     'BRAGTG05': 'gas',
                     'BRAGTG06': 'gas',
                     'BROWTG01': 'gas',
                     'BROWTG02': 'gas',
                     'BSASTG01': 'gas',
                     'BSASTV01': 'gas',
                     'BVILDI01': 'gas',
                     'CACHDI01': 'gas',
                       'CACHHI': 'hydro',
                       'CADIHI': 'hydro',
                     'CAFADI01': 'gas',
                     'CAIMDI01': 'gas',
                     'CAIMDI02': 'gas',
                     'CAIMDI03': 'gas',
                     'CAIMDI04': 'gas',
                     'CAIMDI05': 'gas',
                     'CARLDI01': 'gas',
                       'CARRHI': 'hydro',
                       'CASSHI': 'hydro',
                     'CASTDI01': 'oil',
                     'CATADI01': 'gas',
                     'CATDDI01': 'gas',
                     'CAVIDI01': 'gas',
                       'CCOLHI': 'hydro',
                       'CCORHI': 'hydro',
                     'CEMODI01': 'gas',
                     'CEPUTG11': 'gas',
                     'CEPUTG12': 'gas',
                     'CEPUTV10': 'gas',
                     'CEREDI01': 'gas',
                     'CERITV01': 'gas',
                       'CESPHI': 'hydro',
                     'CHARDI01': 'oil',
                     'CHARDI02': 'oil',
                     'CHEPDI01': 'gas',
                     'CHLEDI01': 'gas',
                       'CHOCHI': 'hydro',
                     'CIPODI01': 'gas',
                       'CIPOHI': 'hydro',
                     'COLBDI01': 'gas',
                     'COMODI01': 'gas',
                       'CONDHI': 'hydro',
                       'COROHI': 'hydro',
                     'CORRDI01': 'gas',
                     'COSMDI11': 'gas',
                     'COSTTG08': 'gas',
                     'COSTTG09': 'gas',
                     'COSTTV01': 'gas',
                     'COSTTV02': 'gas',
                     'COSTTV03': 'gas',
                     'COSTTV04': 'gas',
                     'COSTTV06': 'gas',
                     'COSTTV07': 'gas',
                     'COSTTV10': 'gas',
                       'CPIEHI': 'hydro',
                     'CSARDI01': 'oil',
                     'CUMODI01': 'gas',
                     'CURUTG01': 'gas',
                     'CURUTG02': 'gas',
                     'DFUNTG02': 'gas',
                       'DIADEO': 'hydro',
                     'DIQUTG02': 'gas',
                     'DIQUTG03': 'gas',
                     'DSUDTG07': 'gas',
                     'DSUDTG08': 'gas',
                     'DSUDTG09': 'gas',
                     'DSUDTG10': 'gas',
                     'DSUDTV11': 'gas',
                     'EBARTG01': 'gas',
                     'EBARTG02': 'gas',
                     'ELOMDI01': 'gas',
                     'ENSETG01': 'gas',
                     'EMBANUCL': 'nuclear',
                       'ESCAHI': 'hydro',
                     'ESQDDI01': 'gas',
                     'FORDDI01': 'gas',
                     'FORDDI02': 'gas',
                     'FRIATG01': 'gas',
                       'FSIMHI': 'hydro',
                     '  FUTAHI': 'hydro',
                     'GBELTG01': 'gas',
                     'GBELTG02': 'gas',
                     'GBELTV01': 'gas',
                     'GBMODI01': 'gas',
                     'GEBATG01': 'gas',
                     'GEBATG02': 'gas',
                     'GEBATG03': 'gas',
                     'GEBATV01': 'gas',
                     'GOYDDI01': 'gas',
                     'GUEMTG01': 'gas',
                     'GUEMTV11': 'gas',
                     'GUEMTV12': 'gas',
                     'GUEMTV13': 'gas',
                       'HON1FV': 'hydro',
                     'HUEMDI01': 'gas',
                     'INDETG01': 'gas',
                     'INDETG02': 'gas',
                     'INTADI01': 'gas',
                     'ISBATV01': 'gas',
                     'ISVEDI01': 'gas',
                     'ITATDI01': 'gas',
                     'JUARDI01': 'gas',
                     'JUNIDI01': 'gas',
                     'LBANTG21': 'gas',
                     'LBANTG22': 'gas',
                     'LBLADI01': 'gas',
                       'LDCUHI': 'hydro',
                     'LDCUTG22': 'gas',
                     'LDCUTG23': 'gas',
                     'LDCUTG24': 'gas',
                     'LDCUTG25': 'gas',
                     'LDCUTV11': 'gas',
                     'LDCUTV12': 'gas',
                     'LDCUTV14': 'gas',
                     'LDCUTV15': 'gas',
                     'LDLATG01': 'gas',
                     'LDLATG02': 'gas',
                     'LDLATG03': 'gas',
                     'LDLATG04': 'gas',
                     'LDLATV01': 'gas',
                     'LEDETV01': 'biomass'
                     'LEVATG01': 'gas',
                     'LEVATG02': 'gas',
                     'LIBEDI01': 'gas',
                     'LINCDI01': 'gas',
                       'LMADHI': 'hydro',
                       'LMO1HI': 'hydro',
                       'LMO2HI': 'hydro',
                       'LOM1EO': 'hydro',
                     'LOBODI01': 'oil',
                     'LPALDI01': 'gas',
                     'LPAZDI01': 'gas',
                     'LPLADI01': 'gas',
                       'LQUIHI': 'hydro',
                       'LREYHB': 'hydro',
                     'LRIDDI01': 'gas',
                     'LRIOTG21': 'gas',
                     'LRIOTG22': 'gas',
                     'LRIOTG23': 'gas',
                     'LRIOTG24': 'gas',
                     'LRISDI01': 'gas',
                       'LVINHI': 'hydro',
                     'MAGDDI01': 'gas',
                     'MATHTG01': 'gas',
                     'MATHTG02': 'gas',
                     'MDAJTG17': 'gas',
                     'MDPATG12': 'gas',
                     'MDPATG13': 'gas',
                     'MDPATG19': 'gas',
                     'MDPATG20': 'gas',
                     'MDPATG22': 'gas',
                     'MDPATG23': 'gas',
                     'MDPATG24': 'gas',
                     'MDPATV08': 'gas'
                     'MIR1DI01': 'gas',
                     'MJUADI01': 'gas',
                     'MMARTG01': 'gas',
                     'MMARTG02': 'gas',
                     'MMARTG03': 'gas',
                     'MMARTG04': 'gas',
                     'MMARTG05': 'gas',
                     'MMARTG06': 'gas',
                     'MMARTG07': 'gas',
                     'MSEVTG01': 'gas',
                       'NECOEO': 'hydro',
                     'NECOTV01': 'gas',
                     'NECOTV02': 'gas',
                     'NECOTV03': 'gas',
                     'NECOTV04': 'gas',
                       'NIH1HI': 'hydro',
                       'NIH4HI': 'hydro',
                     'NOMODI01': 'gas',
                     'NPOMDI01': 'unknown'
                     'NPUETV05': 'gas',
                     'NPUETV06': 'gas',
                     'OBERTG01': 'gas',
                     'OCAMDI01': 'oil',
                     'OCAMDI02': 'oil',
                     'OCAMDI03': 'oil',
                     'OCAMDI04': 'oil',
                     'OCAMDI05': 'oil',
                     'OLADTG01': 'gas',
                     'OLADTG02': 'gas',
                     'OLPADI01': 'gas',
                     'ORADDI01': 'gas',
                       'PAGUHI': 'hydro',
                     'PAMODI01': 'gas',
                     'PARATG01': 'gas',
                     'PARATG02': 'gas',
                     'PATATG01': 'gas',
                     'PATATG02': 'gas',
                     'PATATV01': 'gas',
                       'PBANHI': 'hydro',
                     'PEHUDI01': 'gas',
                     'PERZDI01': 'oil',
                     'PERZDI02': 'oil',
                     'PERZDI03': 'oil',
                     'PERZDI04': 'oil',
                     'PERZDI05': 'oil',
                     'PERZDI06': 'oil',
                     'PERZDI07': 'oil',
                     'PERZDI08': 'oil',
                     'PHDZTG01': 'gas',
                     'PHUITG01': 'gas',
                     'PICADI01': 'gas',
                     'PILATG11': 'gas',
                     'PILATG12': 'gas',
                     'PILATV01': 'gas',
                     'PILATV02': 'gas',
                     'PILATV03': 'gas',
                     'PILATV04': 'gas',
                     'PILATV10': 'gas',
                     'PINATG07': 'gas',
                     'PINATG08': 'gas',
                     'PINATG09': 'gas',
                     'PINATG10': 'gas',
                     'PIQIDI01': 'gas',
                     'PIRADI01': 'gas',
                       'PMORHI': 'hydro',
                       'PNEGHI': 'hydro',
                     'PNUETV07': 'gas',
                     'PNUETV08': 'gas',
                     'PNUETV09': 'gas',
                       'POSAIN': 'hydro',
                     'PPATDI01': 'gas',
                       'PPLEHI': 'hydro',
                     'PPNOTG01': 'gas',
                     'PPNOTG02': 'gas',
                     'PROCDI01': 'gas',
                     'PROVTV01': 'gas',
                     'PUPITV01': 'gas',
                       'PVIEHI': 'hydro',
                     'PZUEDI01': 'gas',
                       'QULLHI': 'hydro',
                     'RAFADI01': 'gas',
                       'RAW1EO': 'hydro',
                       'RAW2EO': 'hydro',
                     'RCUATG02': 'gas',
                     'REALDI01': 'gas',
                       'REOLHI': 'hydro',
                     'RESCDI01': 'gas',
                       'RGDEHB': 'hydro',
                       'RHONHI': 'hydro',
                     'ROCATG01': 'gas',
                     'ROJOTG01': 'gas',
                     'ROJOTG02': 'gas',
                     'ROJOTG03': 'gas',
                       'ROMEHI': 'hydro',
                       'RREYHI': 'hydro',
                     'RSAUDI01': 'gas',
                     'RTERTG01': 'gas',
                     'RTERTG02': 'gas',
                       'SALOHI': 'hydro',
                     'SANADI01': 'gas',
                       'SANDHI': 'hydro',
                     'SARCTG21': 'gas',
                     'SARCTG22': 'gas',
                     'SARCTG23': 'gas',
                     'SCHADI01': 'gas',
                     'SERTTG01': 'gas',
                     'SFRATG01': 'gas',
                     'SFRATG02': 'gas',
                     'SGDEHIAR': 'hydro',
                       'SGUIHI': 'hydro',
                     'SHELTG01': 'gas',
                       'SJUAFV': 'hydro',
                     'SLTODI01': 'gas',
                     'SMANDI01': 'gas',
                     'SMIGDI01': 'gas',
                     'SMTUTG01': 'gas',
                     'SMTUTG02': 'gas',
                     'SMTUTV01': 'gas',
                     'SNICTV11': 'coal',
                     'SNICTV12': 'coal',
                     'SNICTV13': 'coal',
                     'SNICTV14': 'coal',
                     'SNICTV15': 'coal',
                     'SOESTG03': 'gas',
                     'SOLATG01': 'gas',
                     'SORRTV13': 'gas',
                     'SPE2DI01': 'oil',
                     'SPENDI01': 'oil',
                       'SROQHI': 'hydro',
                     'SSALDI01': 'gas',
                     'TABATV01': 'gas',
                     'TANDTG01': 'gas',
                     'TANDTG02': 'gas',
                     'TANDTV01': 'gas',
                     'TARDDI01': 'gas',
                     'TELLDI01': 'gas',
                     'TERVDI01': 'gas',
                     'TIMBTG01': 'gas',
                     'TIMBTG02': 'gas',
                     'TIMBTV01': 'gas',
                     'TINODI01': 'gas',
                       'TORDEO': 'hydro',
                     'TUCUTG01': 'gas',
                     'TUCUTG02': 'gas',
                     'TUCUTV01': 'gas',
                       'TUNAHI': 'hydro',
                       'ULLUHI': 'hydro',
                     'VANGDI01': 'oil'
                     'VGADDI01': 'gas',
                     'VGESTG11': 'gas',
                     'VGESTG14': 'gas',
                     'VGESTG18': 'gas',
                     'VIALDI01': 'gas',
                     'VMARTG01': 'gas',
                     'VMARTG02': 'gas',
                     'VMARTG03': 'gas',
                     'VOBLTG01': 'gas',
                     'VOBLTG02': 'gas',
                       'YACYHI': 'hydro',
                     'YPFATG01': 'gas',
                     'ZAPATG01': 'gas',
                     'ZAPATG02': 'gas',
                     'ZAPATG03': 'gas',
                     'ZAPATG04': 'gas'
                     }


#URL's for thermal and hydro pages and data sources respectively. 

url = ('http://portalweb.cammesa.com/MEMNet1/Pages/Informes%20por'
       '%20Categor%C3%ADa/Operativos/VisorReporteSinComDesp_minimal.aspx'
       '?hora=0&titulo=Despacho%20Generacion%20Termica&reportPath='
       'http://lauzet:5000/MemNet1/ReportingServices/DespachoGeneracion'
       'Termica.rdl--0--Despacho+Generaci%c3%b3n+T%c3%a9rmica')

turl = ('http://portalweb.cammesa.com/Reserved.ReportViewerWebControl.'
        'axd?Culture=3082&UICulture=3082&ReportStack=1'
        '&OpType=ReportArea&Controller=ClientController'
        'ctl00_ctl04_g_a581304b_aafc_4818_a4a1_e96f27a22246_ctl00_RepViewer'
        '&ZoomMode=Percent&ZoomPct=100&ReloadDocMap='
        'true&SearchStartPage=0&LinkTarget=_top')

hurl = ('http://portalweb.cammesa.com/memnet1/Pages/Informes%20por%20Categor'
        '%C3%ADa/Operativos/VisorReportesSinCom_minimal.aspx?hora=0&'
        'titulo=Despacho%20Generacion%20Hidraulica&reportPath='
        'http://lauzet:5000/MemNet1/ReportingServices/'
        'DespachoGeneracionHidraulica.rdl--0--Despacho+Generaci%c3%b3n+Zona+'
        'Hidr%c3%a1ulica')

thurl = ('http://portalweb.cammesa.com/Reserved.ReportViewerWebControl.'
         'axd?Culture=3082&UICulture=3082&ReportStack=1'
         '&OpType=ReportArea&Controller=ClientController'
         'ctl00_ctl04_g_966166c3_db78_453e_9a34_83d2bb263ee4_''ctl00_RepViewer'
         '&ZoomMode=Percent&ZoomPct=100&ReloadDocMap='
         'true&SearchStartPage=0&LinkTarget=_top')


def webparser(req):
    """Takes content from webpage and returns all text as a list of strings"""

    soup = BeautifulSoup(req.content, 'html.parser')
    figs = soup.find_all("div", class_="r11")
    data_table = [str(tag.get_text()) for tag in figs]

    return data_table


def get_datetime():
    """
    Generation data is updated hourly.  Makes request then finds most recent hour available.
    Returns an arrow datetime object using UTC-3 for timezone and zero for minutes and seconds.
    """

    #Argentina does not currently observe daylight savings time.  This may change from year to year!
    #https://en.wikipedia.org/wiki/Time_in_Argentina
    rt = requests.get(url)
    timesoup = BeautifulSoup(rt.content, 'html.parser')
    find_hour = timesoup.find("option", selected = "selected", value = "1" ).getText()
    at = arrow.now('UTC-3')
    datetime = (at.replace(hour = int(find_hour), minute = 0, second = 0)).format('YYYY-MM-DD HH:mm:ss')

    return {'datetime': datetime}


def dataformat(junk):
    """Takes string data with only digits and returns it as a float."""

    formatted=[]
    for item in junk:
        if not any(char in item for char in string.ascii_letters):
            item = float(item.replace(',','.'))
        formatted.append(item)       

    return formatted


def get_thermal():
    """
    Requests thermal generation data then parses and sorts by type.  Nuclear is included.
    Returns a dictionary.
    """

    #Need to persist session in order to get ControlID and ReportSession so we can send second request
    #for table data.  Both these variables change on each new request.
    s = requests.Session()
    r = s.get(url)
    pat = re.search("ControlID=[^&]*", r.text).group()
    spat = re.search("ReportSession=[^&]*", r.text).group()
    cid = pat.rpartition('=')[2]
    rs = spat.rpartition('=')[2]
    full_table = []

    #'En Reserva' plants are not generating and can be ignored.

    for pagenumber in range(1,8,1):
        t = s.get(turl, params = {'ControlID': cid, 'ReportSession': rs, 'PageNumber': '{}'.format(pagenumber)})
        text_only = webparser(t)
        if 'En Reserva' in text_only:
            break
        full_table.append(text_only)

    data = list(itertools.chain.from_iterable(full_table))
    formatted_data = dataformat(data)
    mapped_data = [power_plant_type.get(x,x) for x in formatted_data]
    
    find_totals = [i+1 for i,x in enumerate(mapped_data) if x == 'Totales ']
    total_thermal_generation = sum([mapped_data[i] for i in find_totals])
    find_nuclear = [i+2 for i, x in enumerate(mapped_data) if x == 'nuclear']
    total_nuclear_generation = sum([mapped_data[i] for i in find_nuclear])
    #find_oil = [i+2 for i, x in enumerate(mapped_data) if x == 'oil']
    #total_oil_generation = sum([mapped_data[i] for i in find_oil])

    #Assume thermal generation is gas unless specifically mapped to another type.
    #https://en.wikipedia.org/wiki/Electricity_sector_in_Argentina#Generation
    total_gas_generation = total_thermal_generation - total_nuclear_generation

    return {'gas': total_gas_generation, 'nuclear': total_nuclear_generation}



def get_hydro():
    """Requests hydro generation data then parses, returns a dictionary."""

    s = requests.Session()
    r = s.get(hurl)
    pat = re.search("ControlID=[^&]*", r.text).group()
    spat = re.search("ReportSession=[^&]*", r.text).group()
    cid = pat.rpartition('=')[2]
    rs = spat.rpartition('=')[2]
    full_table = []
    

    for pagenumber in range(1,2,1):
        t = s.get(thurl, params = {'ControlID': cid, 'ReportSession': rs, 'PageNumber': '{}'.format(pagenumber)})
        text_only = webparser(t)
        if 'En Reserva' in text_only:
            break
        full_table.append(text_only)

    data = list(itertools.chain.from_iterable(full_table))
    formatted_data = dataformat(data)
    find_hydro = [i+1 for i,x in enumerate(formatted_data) if x == 'Totales ']
    total_hydro_generation = sum([formatted_data[i] for i in find_hydro])

    return {'hydro': total_hydro_generation}



def fetch_production(country_code='AR'):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    Return:
    A dictionary in the form:
    {
      'countryCode': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    """
    gdt = get_datetime()
    thermal = get_thermal()
    hydro = get_hydro()
    production_mix = {
      'countryCode': country_code,
      'datetime': gdt['datetime'],
      'production': {
          'biomass': None,
          'coal': None,
          'gas': thermal['gas'],
          'hydro': hydro['hydro'],
          'nuclear': thermal['nuclear'],
          'oil': None,
          'solar': None,
          'wind': None,
          'geothermal': None,
          'unknown': None
      },
      'storage': {
          'hydro': None,
      },
      'source': 'portalweb.cammesa.com/Memnet1/default.aspx'
    }

    return production_mix


if __name__ ==  '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    
