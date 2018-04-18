#!/usr/bin/env python3

import itertools
import re
import string

import arrow
import requests
from bs4 import BeautifulSoup

try:
    unicode  # Python 2
except NameError:
    unicode = str  # Python 3

# This parser gets hourly electricity generation data from portalweb.cammesa.com/Memnet1/default.aspx
# for Argentina.  Currently wind and solar power are small contributors and not monitored but this is
# likely to change in the future.

# Useful links.
# https://en.wikipedia.org/wiki/Electricity_sector_in_Argentina
# https://en.wikipedia.org/wiki/List_of_power_stations_in_Argentina
# http://globalenergyobservatory.org/countryid/10#
# http://www.industcards.com/st-other-argentina.htm


# Map of power plants to generation type.
# http://portalweb.cammesa.com/memnet1/revistas/estacional/base_gen.html

power_plant_type = {
    'ABRODI01': 'gas',
    'ACAJTG01': 'gas',
    'ACAJTG02': 'gas',
    'ACAJTG03': 'gas',
    'ACAJTG04': 'gas',
    'ACAJTG05': 'gas',
    'ACAJTG06': 'gas',
    'ACAJTV07': 'gas',
    'ADTOHI': 'hydro',
    'AESPTG01': 'gas',
    'AESPTG02': 'gas',
    'AESPTV01': 'gas',
    'ALEMDI01': 'oil',
    'ALICHI': 'hydro',
    'ALOMDI01': 'gas',
    'ALUATG06': 'gas',
    'ALUATG07': 'gas',
    'ALUATG08': 'gas',
    'ALUATV01': 'gas',
    'ALUMDI01': 'oil',
    'AMEGHI': 'hydro',
    'ANATDI01': 'gas',
    'ANATDI02': 'gas',
    'ANCHDI01': 'oil',
    'ANCHDI02': 'oil',
    'ANCHDI03': 'oil',
    'ANCHDI04': 'oil',
    'APARTV01': 'gas',
    'ARA2EO': 'hydro',
    'ARAUEO': 'hydro',
    'ARGETG01': 'gas',
    'ARISDI01': 'oil',
    'ARMATG01': 'gas',
    'ARMATG02': 'gas',
    'ARMATG03': 'gas',
    'ARREDI01': 'gas',
    'ARROHI': 'hydro',
    'ATUCNUCL': 'nuclear',
    'ATU2NUCL': 'nuclear',
    'AVALTG21': 'gas',
    'AVALTG22': 'gas',
    'AVALTG23': 'gas',
    'AVALTV11': 'gas',
    'AVALTV12': 'gas',
    'BAMODI01': 'gas',
    'BANDDI01': 'oil',
    'BARDDI01': 'oil',
    'BBLATV29': 'gas',
    'BBLATV30': 'gas',
    'BBLMDI01': 'oil',
    'BBLMDI02': 'oil',
    'BBLMDI03': 'oil',
    'BBLMDI04': 'oil',
    'BBLMDI05': 'oil',
    'BBLMDI06': 'oil',
    'BERIDI01': 'gas',
    'BLOPTG01': 'gas',
    'BRAGTG01': 'gas',
    'BRAGTG02': 'gas',
    'BRAGTG03': 'gas',
    'BRAGTG04': 'gas',
    'BRAGTG05': 'gas',
    'BRAGTG06': 'gas',
    'BRC1DI01': 'oil',
    'BRCHTG01': 'gas',
    'BRKETG01': 'gas',
    'BRKETG02': 'gas',
    'BRKETG03': 'gas',
    'BRKETG04': 'gas',
    'BROWTG01': 'gas',
    'BROWTG02': 'gas',
    'BSASTG01': 'gas',
    'BSASTV01': 'gas',
    'BVILDI01': 'oil',
    'CACHDI01': 'gas',
    'CACHHI': 'hydro',
    'CADIHI': 'hydro',
    'CAFADI01': 'gas',
    'CAIMDI01': 'oil',
    'CAIMDI02': 'oil',
    'CAIMDI03': 'oil',
    'CAIMDI04': 'oil',
    'CAIMDI05': 'oil',
    'CARLDI01': 'oil',
    'CARRHI': 'hydro',
    'CASSHI': 'hydro',
    'CASTDI01': 'oil',
    'CATADI01': 'oil',
    'CATDDI01': 'oil',
    'CAVIDI01': 'oil',
    'CCOLHI': 'hydro',
    'CCORHI': 'hydro',
    'CEMODI01': 'gas',
    'CEPUTG11': 'gas',
    'CEPUTG12': 'gas',
    'CEPUTV10': 'gas',
    'CEREDI01': 'oil',
    'CERITV01': 'gas',
    'CESPHI': 'hydro',
    'CGOMDI01': 'oil',
    'CGOMDI02': 'oil',
    'CGOMDI03': 'oil',
    'CGOMDI04': 'oil',
    'CHARDI01': 'oil',
    'CHARDI02': 'oil',
    'CHEPDI01': 'oil',
    'CHILDI01': 'oil',
    'CHLEDI01': 'oil',
    'CHOCHI': 'hydro',
    'CIPODI01': 'oil',
    'CIPOHI': 'hydro',
    'COLBDI01': 'oil',
    'COMODI01': 'gas',
    'CONDHI': 'hydro',
    'COROHI': 'hydro',
    'CORRDI01': 'gas',
    'COSMDI11': 'oil',
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
    'DFUNDI01': 'oil',
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
    'ESQDDI01': 'oil',
    'EZEITG01': 'gas',
    'EZEITG02': 'gas',
    'EZEITG03': 'gas',
    'FORDDI01': 'oil',
    'FORDDI02': 'oil',
    'FRIATG01': 'gas',
    'FSIMHI': 'hydro',
    'FUTAHI': 'hydro',
    'GBELTG01': 'gas',
    'GBELTG02': 'gas',
    'GBELTV01': 'gas',
    'GBMODI01': 'gas',
    'GEBATG01': 'gas',
    'GEBATG02': 'gas',
    'GEBATG03': 'gas',
    'GEBATV01': 'gas',
    'GOYDDI01': 'oil',
    'GUEMTG01': 'gas',
    'GUEMTV11': 'gas',
    'GUEMTV12': 'gas',
    'GUEMTV13': 'gas',
    'HON1FV': 'hydro',
    'HRENDI01': 'oil',
    'HUMADI01': 'oil',
    'HUEMDI01': 'gas',
    'INDETG01': 'gas',
    'INDETG02': 'gas',
    'INDETG03': 'gas',
    'INDETG04': 'gas',
    'INTADI01': 'oil',
    'ISBATV01': 'gas',
    'ISVEDI01': 'oil',
    'ITATDI01': 'oil',
    'JUARDI01': 'oil',
    'JUNIDI01': 'oil',
    'LBANTG21': 'gas',
    'LBANTG22': 'gas',
    'LBLADI01': 'oil',
    'LCA2TG01': 'gas',
    'LCAMTG01': 'gas',
    'LDCUHI': 'hydro',
    'LDCUTG22': 'gas',
    'LDCUTG23': 'gas',
    'LDCUTG24': 'gas',
    'LDCUTG25': 'gas',
    'LDCUTV11': 'gas',
    'LDCUTV12': 'gas',
    'LDCUTV14': 'gas',
    'LDCUTV15': 'gas',
    'LDLADI01': 'oil',
    'LDLATG01': 'gas',
    'LDLATG02': 'gas',
    'LDLATG03': 'gas',
    'LDLATG04': 'gas',
    'LDLATG05': 'gas',
    'LDLATV01': 'gas',
    'LEDETV01': 'biomass',
    'LEVADI01': 'oil',
    'LEVATG01': 'gas',
    'LEVATG02': 'gas',
    'LIBEDI01': 'oil',
    'LINCDI01': 'oil',
    'LMADHI': 'hydro',
    'LMO1HI': 'hydro',
    'LMO2HI': 'hydro',
    'LOM1EO': 'hydro',
    'LOBODI01': 'oil',
    'LPALDI01': 'oil',
    'LPAZDI01': 'oil',
    'LPLADI01': 'oil',
    'LQUIHI': 'hydro',
    'LREYHB': 'hydro',
    'LRIDDI01': 'oil',
    'LRIODI': 'oil',
    'LRIOTG21': 'gas',
    'LRIOTG22': 'gas',
    'LRIOTG23': 'gas',
    'LRIOTG24': 'gas',
    'LRIPDI01': 'oil',
    'LRISDI01': 'oil',
    'LROBDI01': 'oil',
    'LVARDI01': 'oil',
    'LVINHI': 'hydro',
    'MAGDDI01': 'oil',
    'MATETG01': 'gas',
    'MATETG02': 'gas',
    'MATETG03': 'gas',
    'MATETG04': 'gas',
    'MATETG05': 'gas',
    'MATETG06': 'gas',
    'MATETG07': 'gas',
    'MATETG08': 'gas',
    'MATETG09': 'gas',
    'MATETG10': 'gas',
    'MATHTG01': 'gas',
    'MATHTG02': 'gas',
    'MDAJTG15': 'oil',
    'MDAJTG17': 'oil',
    'MDPATG12': 'gas',
    'MDPATG13': 'gas',
    'MDPATG19': 'gas',
    'MDPATG20': 'gas',
    'MDPATG21': 'gas',
    'MDPATG22': 'gas',
    'MDPATG23': 'gas',
    'MDPATG24': 'gas',
    'MDPATV07': 'gas',
    'MDPATV08': 'gas',
    'MESEDI01': 'oil',
    'MIR1DI01': 'oil',
    'MJUADI01': 'oil',
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
    'NESPDI02': 'oil',
    'NIH1HI': 'hydro',
    'NIH4HI': 'hydro',
    'NOMODI01': 'gas',
    'NPOMDI01': 'gas',
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
    'OLPADI01': 'oil',
    'ORADDI01': 'oil',
    'PAGUHI': 'hydro',
    'PAMODI01': 'oil',
    'PARATG01': 'gas',
    'PARATG02': 'gas',
    'PATATG01': 'gas',
    'PATATG02': 'gas',
    'PATATV01': 'gas',
    'PBANHI': 'hydro',
    'PEDRTG01': 'gas',
    'PEDRTG02': 'gas',
    'PEDRTG03': 'gas',
    'PEHUDI01': 'oil',
    'PERZDI01': 'oil',
    'PERZDI02': 'oil',
    'PERZDI03': 'oil',
    'PERZDI04': 'oil',
    'PERZDI05': 'oil',
    'PERZDI06': 'oil',
    'PERZDI07': 'oil',
    'PERZDI08': 'oil',
    'PESPTV01': 'gas',
    'PHDZTG01': 'gas',
    'PHUITG01': 'gas',
    'PICADI01': 'oil',
    'PILBDI01': 'oil',
    'PILBDI02': 'oil',
    'PILBDI03': 'oil',
    'PILBDI04': 'oil',
    'PILBDI05': 'oil',
    'PILBDI06': 'oil',
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
    'PIQIDI01': 'oil',
    'PIRADI01': 'oil',
    'PMORHI': 'hydro',
    'PNEGHI': 'hydro',
    'PNUETV07': 'gas',
    'PNUETV08': 'gas',
    'PNUETV09': 'gas',
    'POSAIN': 'hydro',
    'PPATDI01': 'oil',
    'PPLEHI': 'hydro',
    'PPNOTG01': 'gas',
    'PPNOTG02': 'gas',
    'PROCDI01': 'oil',
    'PROVTV01': 'gas',
    'PTR1TG23': 'gas',
    'PTR1TG24': 'gas',
    'PTR1TG25': 'gas',
    'PUPITV01': 'gas',
    'PVIEHI': 'hydro',
    'PZUEDI01': 'oil',
    'QULLHI': 'hydro',
    'RAFADI01': 'oil',
    'RAW1EO': 'hydro',
    'RAW2EO': 'hydro',
    'RCEPDI01': 'oil',
    'RCUATG02': 'gas',
    'REALDI01': 'oil',
    'REOLHI': 'hydro',
    'RESCDI01': 'oil',
    'RGDEHB': 'hydro',
    'RHONHI': 'hydro',
    'RICADI01': 'oil',
    'ROCATG01': 'gas',
    'ROJOTG01': 'gas',
    'ROJOTG02': 'gas',
    'ROJOTG03': 'gas',
    'ROMEHI': 'hydro',
    'RREYHI': 'hydro',
    'RSAUDI01': 'oil',
    'RTERTG01': 'gas',
    'RTERTG02': 'gas',
    'RUFIDI01': 'oil',
    'SALOHI': 'hydro',
    'SANADI01': 'oil',
    'SANDHI': 'hydro',
    'SARCTG21': 'gas',
    'SARCTG22': 'gas',
    'SARCTG23': 'gas',
    'SCHADI01': 'oil',
    'SCTPDI01': 'oil',
    'SERTTG01': 'gas',
    'SFR2DI01': 'oil',
    'SFRATG01': 'gas',
    'SFRATG02': 'gas',
    'SGDEHIAR': 'hydro',
    'SGUIHI': 'hydro',
    'SHELTG01': 'gas',
    'SJUAFV': 'hydro',
    'SLTODI01': 'oil',
    'SMANDI01': 'oil',
    'SMARDI01': 'oil',
    'SMIGDI01': 'oil',
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
    'SPEVDI01': 'oil',
    'SROQHI': 'hydro',
    'SROSDI01': 'oil',
    'SSALDI01': 'oil',
    'SVICDI01': 'oil',
    'TABATV01': 'gas',
    'TANDTG01': 'gas',
    'TANDTG02': 'gas',
    'TANDTV01': 'gas',
    'TARDDI01': 'oil',
    'TELLDI01': 'oil',
    'TERVDI01': 'oil',
    'TIMBTG01': 'gas',
    'TIMBTG02': 'gas',
    'TIMBTV01': 'gas',
    'TINODI01': 'oil',
    'TORDEO': 'hydro',
    'TUCUTG01': 'gas',
    'TUCUTG02': 'gas',
    'TUCUTV01': 'gas',
    'TUNAHI': 'hydro',
    'ULLUHI': 'hydro',
    'VANGDI01': 'oil',
    'VGADDI01': 'oil',
    'VGEPDI01': 'oil',
    'VGESTG11': 'gas',
    'VGESTG14': 'gas',
    'VGESTG16': 'gas',
    'VGESTG18': 'gas',
    'VIALDI01': 'oil',
    'VMA2TG01': 'gas',
    'VMA2TG02': 'gas',
    'VMA2TG03': 'gas',
    'VMA2TG04': 'gas',
    'VMARTG01': 'gas',
    'VMARTG02': 'gas',
    'VMARTG03': 'gas',
    'VOBLTG01': 'gas',
    'VOBLTG02': 'gas',
    'VOBLTV01': 'gas',
    'VTUDDI01': 'oil',
    'VTUEDI01': 'oil',
    'YACYHI': 'hydro',
    'YANQDI01': 'oil',
    'YPFATG01': 'gas',
    'ZAPATG01': 'gas',
    'ZAPATG02': 'gas',
    'ZAPATG03': 'gas',
    'ZAPATG04': 'gas',
    'ZARATG01': 'gas',
    'ZARATG02': 'gas',
    'ZARATG03': 'gas',
    'ZARATG04': 'gas'
}

# URL's for thermal and hydro pages and data sources respectively.

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

cammesa_url = 'http://portalweb.cammesa.com/default.aspx'

tie_mapping = {'CL-SING': "position:absolute; top:349; left:585",
               'PY': "position:absolute; top:67; left:649",
               'UY_1': "position:absolute; top:203; left:533",
               'UY_2': "position:absolute; top:226; left:515"
               }


def webparser(req):
    """Takes content from webpage and returns all text as a list of strings"""

    soup = BeautifulSoup(req.content, 'html.parser')
    figs = soup.find_all("div", class_="r11")
    data_table = [unicode(tag.get_text()) for tag in figs]

    return data_table


def fetch_price(zone_key='AR', session=None, target_datetime=None, logger=None):
    """
    Requests the last known power price of a given country
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'currency': EUR,
      'datetime': '2017-01-01T00:00:00Z',
      'price': 0.0,
      'source': 'mysource.com'
    }
      """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    s = session or requests.Session()
    price_req = s.get(cammesa_url)
    psoup = BeautifulSoup(price_req.content, 'html.parser')
    find_price = psoup.find('td', class_="cssFuncionesLeft", align="left")

    try:
        price_text = find_price.getText()

        # Strip all whitespace and isolate number.  Convert to float.
        price_nws = "".join(price_text.split())
        lprice = price_nws.rpartition(':')[2]
        rprice = lprice.split('[')[0]
        price = float(rprice.replace(',', '.'))

    except (AttributeError, ValueError):
        # Price element not present or no price stated.
        price = None

    datetime = arrow.now('UTC-3').floor('hour').datetime

    data = {
        'zoneKey': zone_key,
        'currency': 'ARS',
        'datetime': datetime,
        'price': price,
        'source': 'portalweb.cammesa.com'
    }

    return data


def get_datetime(session=None):
    """
    Generation data is updated hourly.  Makes request then finds most recent hour available.
    Returns an arrow datetime object using UTC-3 for timezone and zero for minutes and seconds.
    """

    # Argentina does not currently observe daylight savings time.  This may change from year to year!
    # https://en.wikipedia.org/wiki/Time_in_Argentina
    s = session or requests.Session()
    rt = s.get(url)
    timesoup = BeautifulSoup(rt.content, 'html.parser')
    find_hour = timesoup.find("option", selected="selected", value="1").getText()
    at = arrow.now('UTC-3').floor('hour')
    datetime = (at.replace(hour=int(find_hour), minute=0, second=0)).datetime

    return {'datetime': datetime}


def dataformat(junk):
    """Takes string data with only digits and returns it as a float."""

    formatted = []
    for item in junk:
        if not any(char in item for char in string.ascii_letters):
            item = float(item.replace(',', '.'))
        formatted.append(item)

    return formatted


def get_thermal(session, logger):
    """
    Requests thermal generation data then parses and sorts by type.  Nuclear is included.
    Returns a dictionary.
    """

    # Need to persist session in order to get ControlID and ReportSession so we can send second request
    # for table data.  Both these variables change on each new request.
    s = session or requests.Session()
    r = s.get(url)
    pat = re.search("ControlID=[^&]*", r.text).group()
    spat = re.search("ReportSession=[^&]*", r.text).group()
    cid = pat.rpartition('=')[2]
    rs = spat.rpartition('=')[2]
    full_table = []

    # 'En Reserva' plants are not generating and can be ignored.
    # The table has an extra column on 'Costo Operativo' page which must be removed to find power generated correctly.

    pagenumber = 1
    reserves = False

    while not reserves:
        t = s.get(turl, params={'ControlID': cid, 'ReportSession': rs,
                                'PageNumber': '{}'.format(pagenumber)})
        text_only = webparser(t)
        if 'Estado' in text_only:
            for item in text_only:
                if len(item) == 1 and item in string.ascii_letters:
                    text_only.remove(item)
        if 'En Reserva' in text_only:
            reserves = True
            continue
        full_table.append(text_only)
        pagenumber += 1

    data = list(itertools.chain.from_iterable(full_table))
    formatted_data = dataformat(data)
    mapped_data = [power_plant_type.get(x, x) for x in formatted_data]

    for item in mapped_data:
        try:
            # avoids including titles and headings
            if all((item.isupper(), not item.isalpha(), ' ' not in item)):
                logger.warning(
                    '{} is missing from the AR plant mapping!'.format(item),
                    extra={'key': 'AR'})
        except AttributeError:
            # not a string....
            continue

    find_totals = [i + 1 for i, x in enumerate(mapped_data) if x == 'Totales ']
    thermal_generation = sum([mapped_data[i] for i in find_totals])

    find_nuclear = [i + 2 for i, x in enumerate(mapped_data) if x == 'nuclear']
    nuclear_generation = sum([mapped_data[i] for i in find_nuclear])
    find_oil = [i + 2 for i, x in enumerate(mapped_data) if x == 'oil']
    oil_generation = sum([mapped_data[i] for i in find_oil])
    find_coal = [i + 2 for i, x in enumerate(mapped_data) if x == 'coal']
    coal_generation = sum([mapped_data[i] for i in find_coal])
    find_biomass = [i + 2 for i, x in enumerate(mapped_data) if x == 'biomass']
    biomass_generation = sum([mapped_data[i] for i in find_biomass])
    find_gas = [i + 2 for i, x in enumerate(mapped_data) if x == 'gas']
    gas_generation = sum([mapped_data[i] for i in find_gas])

    unknown_generation = (thermal_generation - nuclear_generation - gas_generation
                          - oil_generation - coal_generation - biomass_generation)

    if unknown_generation < 0.0:
        unknown_generation = 0.0

    return {'gas': gas_generation,
            'nuclear': nuclear_generation,
            'coal': coal_generation,
            'unknown': unknown_generation,
            'oil': oil_generation,
            'biomass': biomass_generation
            }


def get_hydro(session=None):
    """Requests hydro generation data then parses, returns a dictionary."""

    s = session or requests.Session()
    r = s.get(hurl)
    pat = re.search("ControlID=[^&]*", r.text).group()
    spat = re.search("ReportSession=[^&]*", r.text).group()
    cid = pat.rpartition('=')[2]
    rs = spat.rpartition('=')[2]
    full_table = []

    pagenumber = 1
    reserves = False

    while not reserves:
        t = s.get(thurl, params={'ControlID': cid, 'ReportSession': rs,
                                 'PageNumber': '{}'.format(pagenumber)})
        text_only = webparser(t)
        if 'En Reserva' in text_only:
            reserves = True
            continue
        full_table.append(text_only)
        pagenumber += 1

    data = list(itertools.chain.from_iterable(full_table))
    formatted_data = dataformat(data)
    find_hydro = [i + 1 for i, x in enumerate(formatted_data) if x == 'Totales ']
    total_hydro_generation = sum([formatted_data[i] for i in find_hydro])

    return {'hydro': total_hydro_generation}


def fetch_production(zone_key='AR', session=None, target_datetime=None, logger=None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    target_datetime: if we want to parser for a specific time and not latest
    logger: where to log useful information
    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
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
    if target_datetime is not None:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    gdt = get_datetime(session=None)
    thermal = get_thermal(session, logger)
    hydro = get_hydro(session=None)
    production_mix = {
        'zoneKey': zone_key,
        'datetime': gdt['datetime'],
        'production': {
            'biomass': thermal.get('biomass', 0.0),
            'coal': thermal.get('coal', 0.0),
            'gas': thermal.get('gas', 0.0),
            'hydro': hydro.get('hydro', 0.0),
            'nuclear': thermal.get('nuclear', 0.0),
            'oil': thermal.get('oil', 0.0),
            'solar': None,
            'wind': None,
            'geothermal': 0.0,
            'unknown': thermal.get('unknown', 0.0)
        },
        'storage': {
            'hydro': None,
        },
        'source': 'portalweb.cammesa.com'
    }

    return production_mix


def direction_finder(direction, exchange):
    """
    Uses the 'src' attribute of an "img" tag to find the
    direction of flow. In the data source small arrow images
    are used to show flow direction.
    """

    if direction == "/uflujpot.nsf/f90.gif":
        # flow from Argentina
        return 1
    elif direction == "/uflujpot.nsf/f270.gif":
        # flow to Argentina
        return -1
    else:
        raise ValueError('Flow direction for {} cannot be determined, got {}'.format(exchange, direction))


def tie_finder(exchange_url, exchange, session):
    """
    Finds tie data using div tag style attribute.
    Returns a float.
    """

    req = session.get(exchange_url)
    soup = BeautifulSoup(req.text, 'html.parser')

    tie = soup.find("div", style = tie_mapping[exchange])
    flow = float(tie.text)
    direction_tag = tie.find_next("img")
    direction = direction_finder(direction_tag['src'], exchange)

    netflow = flow*direction

    return netflow


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    """Requests the last known power exchange (in MW) between two zones

    Arguments:
    zone_key1, zone_key2: specifies which exchange to get
    session: requests session passed in order to re-use an existing session,
      not used here due to difficulty providing it to pandas
    target_datetime: the datetime for which we want production data. If not provided, we should
      default it to now. The provided target_datetime is timezone-aware in UTC.
    logger: an instance of a `logging.Logger`; all raised exceptions are also logged automatically

    Return:
    A list of dictionaries in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    where net flow is from DK into NO
    """

    # Only hourly data is available.
    if target_datetime:
        lookup_time = arrow.get(target_datetime).floor('hour').format('DD/MM/YYYY HH:mm')
    else:
        current_time = arrow.now('UTC-3')
        if current_time.minute < 30:
            # Data for current hour seems to be available after 30mins.
            current_time = current_time.shift(hours=-1)
        lookup_time = current_time.floor('hour').format('DD/MM/YYYY HH:mm')

    sortedcodes = '->'.join(sorted([zone_key1, zone_key2]))

    if sortedcodes == 'AR->CL-SING':
        base_url = 'http://www.cammesa.com/uflujpot.nsf/FlujoW?OpenAgent&Unifilar de NOA&'
    else:
        base_url = 'http://www.cammesa.com/uflujpot.nsf/FlujoW?OpenAgent&Tensiones y Flujos de Potencia&'

    exchange_url = base_url + lookup_time

    s = session or requests.Session()

    if sortedcodes == 'AR->UY':
        first_tie = tie_finder(exchange_url, 'UY_1', s)
        second_tie = tie_finder(exchange_url, 'UY_2', s)
        flow = first_tie + second_tie
    elif sortedcodes == 'AR->PY':
        flow = tie_finder(exchange_url, 'PY', s)
    elif sortedcodes == 'AR->CL-SING':
        flow = tie_finder(exchange_url, 'CL-SING', s)
    else:
        raise NotImplementedError('This exchange is not currently implemented')

    exchange = {
      'sortedZoneKeys': sortedcodes,
      'datetime': arrow.now('UTC-3').datetime,
      'netFlow': flow,
      'source': 'cammesa.com'
    }

    return exchange


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_price() ->')
    print(fetch_price())
    print('fetch_exchange(AR, PY) ->')
    print(fetch_exchange('AR', 'PY'))
    print('fetch_exchange(AR, UY) ->')
    print(fetch_exchange('AR', 'UY'))
    print('fetch_exchange(AR, CL-SING) ->')
    print(fetch_exchange('AR', 'CL-SING'))
