#!/usr/bin/env python3
"""Parser for U.S. Energy Information Administration, https://www.eia.gov/ .

Aggregates and standardizes data from most of the US ISOs,
and exposes them via a unified API.

Requires an API key, set in the EIA_KEY environment variable. Get one here:
https://www.eia.gov/opendata/register.php
"""
import datetime
import os

import arrow
from dateutil import parser, tz
os.environ.setdefault('EIA_KEY', 'eia_key')
from eiapy import Series
import requests

from .lib.validation import validate
from .ENTSOE import merge_production_outputs

EXCHANGES = {

#Old exchanges with old zones, to be updated/removed once clients have had time to switch
    'MX-BC->US-CA': 'EBA.CISO-CFE.ID.H',
    'US-BPA->US-IPC': 'EBA.BPAT-IPCO.ID.H',
    'US-SPP->US-TX': 'SWPP.ID.H-EBA.ERCO',
    'US-MISO->US-PJM': 'EBA.MISO-PJM.ID.H',
    'US-MISO->US-SPP': 'EBA.MISO-SWPP.ID.H',
    'US-NEISO->US-NY': 'EBA.ISNE-NYIS.ID.H',
    'US-NY->US-PJM': 'EBA.NYIS-PJM.ID.H',

#Exchanges to non-US BAs
    'US-CAL-CISO->MX-BC': 'EBA.CISO-CFE.ID.H' #Unable to verify if MX-BC is correct
    'US-CENT-SWPP->CA-SK': 'EBA.SWPP-SPC.ID.H'
    'US-MIDW-MISO->CA-MB': 'EBA.MISO-MHEB.ID.H'
    'US-MIDW-MISO->CA-ON': 'EBA.MISO-IESO.ID.H'
    'US-NE-ISNE->CA-QC': 'EBA.ISNE-HQT.ID.H'
    'US-NE-ISNE->CA-NB': 'EBA.ISNE-NBSO.ID.H'
    'US-NW-BPAT->CA-BC': 'EBA.BPAT-BCHA.ID.H'
    'US-NW-NWMT->CA-AB': 'EBA.NWMT-AESO.ID.H'
    'US-NY-NYIS->CA-QC': 'EBA.NYIS-HQT.ID.H'
    'US-NY-NYIS->CA-ON': 'EBA.NYIS-IESO.ID.H'
    'US-TEX-ERCO->MX-NE': 'EBA.ERCO-CEN.ID.H' #Unable to verify if MX-NE is correct
    'US-TEX-ERCO->MX-NO': 'EBA.ERCO-CFE.ID.H' #Unable to verify if MX-NO is correct

#Exchanges to other US balancing authorities
    'US-CAL-BANC->US-NW-BPAT': 'EBA.BANC-BPAT.ID.H'
    'US-CAL-BANC->US-CAL-CISO': 'EBA.BANC-CISO.ID.H'
    'US-CAL-BANC->US-CAL-TIDC': 'EBA.BANC-TIDC.ID.H'
    'US-CAL-CISO->US-SW-AZPS': 'EBA.CISO-AZPS.ID.H'
    'US-CAL-CISO->US-CAL-BANC': 'EBA.CISO-BANC.ID.H'
    'US-CAL-CISO->US-NW-BPAT': 'EBA.CISO-BPAT.ID.H'
    'US-CAL-CISO->US-CAL-IID': 'EBA.CISO-IID.ID.H'
    'US-CAL-CISO->US-CAL-LDWP': 'EBA.CISO-LDWP.ID.H'
    'US-CAL-CISO->US-NW-NEVP': 'EBA.CISO-NEVP.ID.H'
    'US-CAL-CISO->US-NW-PACW': 'EBA.CISO-PACW.ID.H'
    'US-CAL-CISO->US-SW-SRP': 'EBA.CISO-SRP.ID.H'
    'US-CAL-CISO->US-CAL-TIDC': 'EBA.CISO-TIDC.ID.H'
    'US-CAL-CISO->US-SW-WALC': 'EBA.CISO-WALC.ID.H'
    'US-CAL-IID->US-SW-AZPS': 'EBA.IID-AZPS.ID.H'
    'US-CAL-IID->US-CAL-CISO': 'EBA.IID-CISO.ID.H'
    'US-CAL-IID->US-SW-WALC': 'EBA.IID-WALC.ID.H'
    'US-CAL-LDWP->US-SW-AZPS': 'EBA.LDWP-AZPS.ID.H'
    'US-CAL-LDWP->US-NW-BPAT': 'EBA.LDWP-BPAT.ID.H'
    'US-CAL-LDWP->US-CAL-CISO': 'EBA.LDWP-CISO.ID.H'
    'US-CAL-LDWP->US-NW-NEVP': 'EBA.LDWP-NEVP.ID.H'
    'US-CAL-LDWP->US-NW-PACE': 'EBA.LDWP-PACE.ID.H'
    'US-CAL-LDWP->US-SW-WALC': 'EBA.LDWP-WALC.ID.H'
    'US-CAL-TIDC->US-CAL-BANC': 'EBA.TIDC-BANC.ID.H'
    'US-CAL-TIDC->US-CAL-CISO': 'EBA.TIDC-CISO.ID.H'
    'US-CAR-CPLE->US-CAR-YAD': 'EBA.CPLE-YAD.ID.H'
    'US-CAR-CPLE->US-CAR-DUK': 'EBA.CPLE-DUK.ID.H'
    'US-CAR-CPLE->US-MIDA-PJM': 'EBA.CPLE-PJM.ID.H'
    'US-CAR-CPLE->US-CAR-SCEG': 'EBA.CPLE-SCEG.ID.H'
    'US-CAR-CPLE->US-CAR-SC': 'EBA.CPLE-SC.ID.H'
    'US-CAR-CPLW->US-CAR-DUK': 'EBA.CPLW-DUK.ID.H'
    'US-CAR-CPLW->US-MIDA-PJM': 'EBA.CPLW-PJM.ID.H'
    'US-CAR-CPLW->US-TEN-TVA': 'EBA.CPLW-TVA.ID.H'
    'US-CAR-DUK->US-CAR-YAD': 'EBA.DUK-YAD.ID.H'
    'US-CAR-DUK->US-CAR-CPLE': 'EBA.DUK-CPLE.ID.H'
    'US-CAR-DUK->US-CAR-CPLW': 'EBA.DUK-CPLW.ID.H'
    'US-CAR-DUK->US-MIDA-PJM': 'EBA.DUK-PJM.ID.H'
    'US-CAR-DUK->US-CAR-SCEG': 'EBA.DUK-SCEG.ID.H'
    'US-CAR-DUK->US-CAR-SC': 'EBA.DUK-SC.ID.H'
    'US-CAR-DUK->US-SE-SEPA': 'EBA.DUK-SEPA.ID.H'
    'US-CAR-DUK->US-SE-SOCO': 'EBA.DUK-SOCO.ID.H'
    'US-CAR-DUK->US-TEN-TVA': 'EBA.DUK-TVA.ID.H'
    'US-CAR-SC->US-CAR-DUK': 'EBA.SC-DUK.ID.H'
    'US-CAR-SC->US-CAR-CPLE': 'EBA.SC-CPLE.ID.H'
    'US-CAR-SC->US-CAR-SCEG': 'EBA.SC-SCEG.ID.H'
    'US-CAR-SC->US-SE-SEPA': 'EBA.SC-SEPA.ID.H'
    'US-CAR-SC->US-SE-SOCO': 'EBA.SC-SOCO.ID.H'
    'US-CAR-SCEG->US-CAR-DUK': 'EBA.SCEG-DUK.ID.H'
    'US-CAR-SCEG->US-CAR-CPLE': 'EBA.SCEG-CPLE.ID.H'
    'US-CAR-SCEG->US-CAR-SC': 'EBA.SCEG-SC.ID.H'
    'US-CAR-SCEG->US-SE-SEPA': 'EBA.SCEG-SEPA.ID.H'
    'US-CAR-SCEG->US-SE-SOCO': 'EBA.SCEG-SOCO.ID.H'
    'US-CAR-YAD->US-CAR-DUK': 'EBA.YAD-DUK.ID.H'
    'US-CAR-YAD->US-CAR-CPLE': 'EBA.YAD-CPLE.ID.H'
    'US-CENT-SPA->US-MIDW-AECI': 'EBA.SPA-AECI.ID.H'
    'US-CENT-SPA->US-MIDW-MISO': 'EBA.SPA-MISO.ID.H'
    'US-CENT-SPA->US-CENT-SWPP': 'EBA.SPA-SWPP.ID.H'
    'US-CENT-SWPP->US-MIDW-AECI': 'EBA.SWPP-AECI.ID.H'
    'US-CENT-SWPP->US-SW-EPE': 'EBA.SWPP-EPE.ID.H'
    'US-CENT-SWPP->US-TEX-ERCO': 'EBA.SWPP-ERCO.ID.H'
    'US-CENT-SWPP->US-MIDW-MISO': 'EBA.SWPP-MISO.ID.H'
    'US-CENT-SWPP->US-NW-PSCO': 'EBA.SWPP-PSCO.ID.H'
    'US-CENT-SWPP->US-SW-PNM': 'EBA.SWPP-PNM.ID.H'
    'US-CENT-SWPP->US-CENT-SPA': 'EBA.SWPP-SPA.ID.H'
    'US-CENT-SWPP->US-NW-WACM': 'EBA.SWPP-WACM.ID.H'
    'US-CENT-SWPP->US-NW-WAUW': 'EBA.SWPP-WAUW.ID.H'
    'US-FLA-FMPP->US-FLA-FPC': 'EBA.FMPP-FPC.ID.H'
    'US-FLA-FMPP->US-FLA-FPL': 'EBA.FMPP-FPL.ID.H'
    'US-FLA-FMPP->US-FLA-JEA': 'EBA.FMPP-JEA.ID.H'
    'US-FLA-FMPP->US-FLA-TEC': 'EBA.FMPP-TEC.ID.H'
    'US-FLA-FPC->US-FLA-TAL': 'EBA.FPC-TAL.ID.H'
    'US-FLA-FPC->US-FLA-FMPP': 'EBA.FPC-FMPP.ID.H'
    'US-FLA-FPC->US-FLA-FPL': 'EBA.FPC-FPL.ID.H'
    'US-FLA-FPC->US-FLA-GVL': 'EBA.FPC-GVL.ID.H'
    'US-FLA-FPC->US-FLA-SEC': 'EBA.FPC-SEC.ID.H'
    'US-FLA-FPC->US-SE-SOCO': 'EBA.FPC-SOCO.ID.H'
    'US-FLA-FPC->US-FLA-TEC': 'EBA.FPC-TEC.ID.H'
    'US-FLA-FPC->US-FLA-NSB': 'EBA.FPC-NSB.ID.H'
    'US-FLA-FPL->US-FLA-HST': 'EBA.FPL-HST.ID.H'
    'US-FLA-FPL->US-FLA-FPC': 'EBA.FPL-FPC.ID.H'
    'US-FLA-FPL->US-FLA-FMPP': 'EBA.FPL-FMPP.ID.H'
    'US-FLA-FPL->US-FLA-GVL': 'EBA.FPL-GVL.ID.H'
    'US-FLA-FPL->US-FLA-JEA': 'EBA.FPL-JEA.ID.H'
    'US-FLA-FPL->US-FLA-SEC': 'EBA.FPL-SEC.ID.H'
    'US-FLA-FPL->US-SE-SOCO': 'EBA.FPL-SOCO.ID.H'
    'US-FLA-FPL->US-FLA-TEC': 'EBA.FPL-TEC.ID.H'
    'US-FLA-FPL->US-FLA-NSB': 'EBA.FPL-NSB.ID.H'
    'US-FLA-GVL->US-FLA-FPC': 'EBA.GVL-FPC.ID.H'
    'US-FLA-GVL->US-FLA-FPL': 'EBA.GVL-FPL.ID.H'
    'US-FLA-HST->US-FLA-FPL': 'EBA.HST-FPL.ID.H'
    'US-FLA-JEA->US-FLA-FMPP': 'EBA.JEA-FMPP.ID.H'
    'US-FLA-JEA->US-FLA-FPL': 'EBA.JEA-FPL.ID.H'
    'US-FLA-JEA->US-FLA-SEC': 'EBA.JEA-SEC.ID.H'
    'US-FLA-NSB->US-FLA-FPC': 'EBA.NSB-FPC.ID.H'
    'US-FLA-NSB->US-FLA-FPL': 'EBA.NSB-FPL.ID.H'
    'US-FLA-SEC->US-FLA-FPC': 'EBA.SEC-FPC.ID.H'
    'US-FLA-SEC->US-FLA-FPL': 'EBA.SEC-FPL.ID.H'
    'US-FLA-SEC->US-FLA-JEA': 'EBA.SEC-JEA.ID.H'
    'US-FLA-SEC->US-FLA-TEC': 'EBA.SEC-TEC.ID.H'
    'US-FLA-TAL->US-FLA-FPC': 'EBA.TAL-FPC.ID.H'
    'US-FLA-TAL->US-SE-SOCO': 'EBA.TAL-SOCO.ID.H'
    'US-FLA-TEC->US-FLA-FPC': 'EBA.TEC-FPC.ID.H'
    'US-FLA-TEC->US-FLA-FMPP': 'EBA.TEC-FMPP.ID.H'
    'US-FLA-TEC->US-FLA-FPL': 'EBA.TEC-FPL.ID.H'
    'US-FLA-TEC->US-FLA-SEC': 'EBA.TEC-SEC.ID.H'
    'US-MIDA-OVEC->US-MIDW-LGEE': 'EBA.OVEC-LGEE.ID.H'
    'US-MIDA-OVEC->US-MIDA-PJM': 'EBA.OVEC-PJM.ID.H'
    'US-MIDA-PJM->US-CAR-DUK': 'EBA.PJM-DUK.ID.H'
    'US-MIDA-PJM->US-CAR-CPLE': 'EBA.PJM-CPLE.ID.H'
    'US-MIDA-PJM->US-CAR-CPLW': 'EBA.PJM-CPLW.ID.H'
    'US-MIDA-PJM->US-MIDW-LGEE': 'EBA.PJM-LGEE.ID.H'
    'US-MIDA-PJM->US-MIDW-MISO': 'EBA.PJM-MISO.ID.H'
    'US-MIDA-PJM->US-NY-NYIS': 'EBA.PJM-NYIS.ID.H'
    'US-MIDA-PJM->US-MIDA-OVEC': 'EBA.PJM-OVEC.ID.H'
    'US-MIDA-PJM->US-TEN-TVA': 'EBA.PJM-TVA.ID.H'
    'US-MIDW-AECI->US-MIDW-MISO': 'EBA.AECI-MISO.ID.H'
    'US-MIDW-AECI->US-CENT-SWPP': 'EBA.AECI-SWPP.ID.H'
    'US-MIDW-AECI->US-CENT-SPA': 'EBA.AECI-SPA.ID.H'
    'US-MIDW-AECI->US-TEN-TVA': 'EBA.AECI-TVA.ID.H'
    'US-MIDW-EEI->US-MIDW-LGEE': 'EBA.EEI-LGEE.ID.H'
    'US-MIDW-EEI->US-MIDW-MISO': 'EBA.EEI-MISO.ID.H'
    'US-MIDW-EEI->US-TEN-TVA': 'EBA.EEI-TVA.ID.H'
    'US-MIDW-LGEE->US-MIDW-EEI': 'EBA.LGEE-EEI.ID.H'
    'US-MIDW-LGEE->US-MIDW-MISO': 'EBA.LGEE-MISO.ID.H'
    'US-MIDW-LGEE->US-MIDA-OVEC': 'EBA.LGEE-OVEC.ID.H'
    'US-MIDW-LGEE->US-MIDA-PJM': 'EBA.LGEE-PJM.ID.H'
    'US-MIDW-LGEE->US-TEN-TVA': 'EBA.LGEE-TVA.ID.H'
    'US-MIDW-MISO->US-MIDW-AECI': 'EBA.MISO-AECI.ID.H'
    'US-MIDW-MISO->US-MIDW-EEI': 'EBA.MISO-EEI.ID.H'
    'US-MIDW-MISO->US-MIDW-LGEE': 'EBA.MISO-LGEE.ID.H'
    'US-MIDW-MISO->US-MIDA-PJM': 'EBA.MISO-PJM.ID.H'
    'US-MIDW-MISO->US-SE-AEC': 'EBA.MISO-AEC.ID.H'
    'US-MIDW-MISO->US-SE-SOCO': 'EBA.MISO-SOCO.ID.H'
    'US-MIDW-MISO->US-CENT-SWPP': 'EBA.MISO-SWPP.ID.H'
    'US-MIDW-MISO->US-CENT-SPA': 'EBA.MISO-SPA.ID.H'
    'US-MIDW-MISO->US-TEN-TVA': 'EBA.MISO-TVA.ID.H'
    'US-NE-ISNE->US-NY-NYIS': 'EBA.ISNE-NYIS.ID.H'
    'US-NW-AVA->US-NW-BPAT': 'EBA.AVA-BPAT.ID.H'
    'US-NW-AVA->US-NW-IPCO': 'EBA.AVA-IPCO.ID.H'
    'US-NW-AVA->US-NW-NWMT': 'EBA.AVA-NWMT.ID.H'
    'US-NW-AVA->US-NW-PACW': 'EBA.AVA-PACW.ID.H'
    'US-NW-AVA->US-NW-CHPD': 'EBA.AVA-CHPD.ID.H'
    'US-NW-AVA->US-NW-GCPD': 'EBA.AVA-GCPD.ID.H'
    'US-NW-AVRN->US-NW-BPAT': 'EBA.AVRN-BPAT.ID.H'
    'US-NW-AVRN->US-NW-PACW': 'EBA.AVRN-PACW.ID.H'
    'US-NW-BPAT->US-NW-AVRN': 'EBA.BPAT-AVRN.ID.H'
    'US-NW-BPAT->US-NW-AVA': 'EBA.BPAT-AVA.ID.H'
    'US-NW-BPAT->US-CAL-BANC': 'EBA.BPAT-BANC.ID.H'
    'US-NW-BPAT->US-CAL-CISO': 'EBA.BPAT-CISO.ID.H'
    'US-NW-BPAT->US-NW-TPWR': 'EBA.BPAT-TPWR.ID.H'
    'US-NW-BPAT->US-NW-GRID': 'EBA.BPAT-GRID.ID.H'
    'US-NW-BPAT->US-NW-IPCO': 'EBA.BPAT-IPCO.ID.H'
    'US-NW-BPAT->US-CAL-LDWP': 'EBA.BPAT-LDWP.ID.H'
    'US-NW-BPAT->US-NW-NEVP': 'EBA.BPAT-NEVP.ID.H'
    'US-NW-BPAT->US-NW-NWMT': 'EBA.BPAT-NWMT.ID.H'
    'US-NW-BPAT->US-NW-DOPD': 'EBA.BPAT-DOPD.ID.H'
    'US-NW-BPAT->US-NW-PACW': 'EBA.BPAT-PACW.ID.H'
    'US-NW-BPAT->US-NW-PGE': 'EBA.BPAT-PGE.ID.H'
    'US-NW-BPAT->US-NW-CHPD': 'EBA.BPAT-CHPD.ID.H'
    'US-NW-BPAT->US-NW-GCPD': 'EBA.BPAT-GCPD.ID.H'
    'US-NW-BPAT->US-NW-PSEI': 'EBA.BPAT-PSEI.ID.H'
    'US-NW-BPAT->US-NW-SCL': 'EBA.BPAT-SCL.ID.H'
    'US-NW-CHPD->US-NW-AVA': 'EBA.CHPD-AVA.ID.H'
    'US-NW-CHPD->US-NW-BPAT': 'EBA.CHPD-BPAT.ID.H'
    'US-NW-CHPD->US-NW-DOPD': 'EBA.CHPD-DOPD.ID.H'
    'US-NW-CHPD->US-NW-PSEI': 'EBA.CHPD-PSEI.ID.H'
    'US-NW-DOPD->US-NW-BPAT': 'EBA.DOPD-BPAT.ID.H'
    'US-NW-DOPD->US-NW-CHPD': 'EBA.DOPD-CHPD.ID.H'
    'US-NW-GCPD->US-NW-AVA': 'EBA.GCPD-AVA.ID.H'
    'US-NW-GCPD->US-NW-BPAT': 'EBA.GCPD-BPAT.ID.H'
    'US-NW-GCPD->US-NW-PACW': 'EBA.GCPD-PACW.ID.H'
    'US-NW-GCPD->US-NW-PSEI': 'EBA.GCPD-PSEI.ID.H'
    'US-NW-GRID->US-NW-BPAT': 'EBA.GRID-BPAT.ID.H'
    'US-NW-GWA->US-NW-NWMT': 'EBA.GWA-NWMT.ID.H'
    'US-NW-IPCO->US-NW-AVA': 'EBA.IPCO-AVA.ID.H'
    'US-NW-IPCO->US-NW-BPAT': 'EBA.IPCO-BPAT.ID.H'
    'US-NW-IPCO->US-NW-NEVP': 'EBA.IPCO-NEVP.ID.H'
    'US-NW-IPCO->US-NW-NWMT': 'EBA.IPCO-NWMT.ID.H'
    'US-NW-IPCO->US-NW-PACE': 'EBA.IPCO-PACE.ID.H'
    'US-NW-IPCO->US-NW-PACW': 'EBA.IPCO-PACW.ID.H'
    'US-NW-NEVP->US-NW-BPAT': 'EBA.NEVP-BPAT.ID.H'
    'US-NW-NEVP->US-CAL-CISO': 'EBA.NEVP-CISO.ID.H'
    'US-NW-NEVP->US-NW-IPCO': 'EBA.NEVP-IPCO.ID.H'
    'US-NW-NEVP->US-CAL-LDWP': 'EBA.NEVP-LDWP.ID.H'
    'US-NW-NEVP->US-NW-PACE': 'EBA.NEVP-PACE.ID.H'
    'US-NW-NEVP->US-SW-WALC': 'EBA.NEVP-WALC.ID.H'
    'US-NW-NWMT->US-NW-AVA': 'EBA.NWMT-AVA.ID.H'
    'US-NW-NWMT->US-NW-BPAT': 'EBA.NWMT-BPAT.ID.H'
    'US-NW-NWMT->US-NW-IPCO': 'EBA.NWMT-IPCO.ID.H'
    'US-NW-NWMT->US-NW-GWA': 'EBA.NWMT-GWA.ID.H'
    'US-NW-NWMT->US-NW-WWA': 'EBA.NWMT-WWA.ID.H'
    'US-NW-NWMT->US-NW-PACE': 'EBA.NWMT-PACE.ID.H'
    'US-NW-NWMT->US-NW-WAUW': 'EBA.NWMT-WAUW.ID.H'
    'US-NW-PACE->US-SW-AZPS': 'EBA.PACE-AZPS.ID.H'
    'US-NW-PACE->US-NW-IPCO': 'EBA.PACE-IPCO.ID.H'
    'US-NW-PACE->US-CAL-LDWP': 'EBA.PACE-LDWP.ID.H'
    'US-NW-PACE->US-NW-NEVP': 'EBA.PACE-NEVP.ID.H'
    'US-NW-PACE->US-NW-NWMT': 'EBA.PACE-NWMT.ID.H'
    'US-NW-PACE->US-NW-PACW': 'EBA.PACE-PACW.ID.H'
    'US-NW-PACE->US-NW-WACM': 'EBA.PACE-WACM.ID.H'
    'US-NW-PACW->US-NW-AVRN': 'EBA.PACW-AVRN.ID.H'
    'US-NW-PACW->US-NW-AVA': 'EBA.PACW-AVA.ID.H'
    'US-NW-PACW->US-NW-BPAT': 'EBA.PACW-BPAT.ID.H'
    'US-NW-PACW->US-CAL-CISO': 'EBA.PACW-CISO.ID.H'
    'US-NW-PACW->US-NW-IPCO': 'EBA.PACW-IPCO.ID.H'
    'US-NW-PACW->US-NW-PACE': 'EBA.PACW-PACE.ID.H'
    'US-NW-PACW->US-NW-PGE': 'EBA.PACW-PGE.ID.H'
    'US-NW-PACW->US-NW-GCPD': 'EBA.PACW-GCPD.ID.H'
    'US-NW-PGE->US-NW-BPAT': 'EBA.PGE-BPAT.ID.H'
    'US-NW-PGE->US-NW-PACW': 'EBA.PGE-PACW.ID.H'
    'US-NW-PSCO->US-SW-PNM': 'EBA.PSCO-PNM.ID.H'
    'US-NW-PSCO->US-CENT-SWPP': 'EBA.PSCO-SWPP.ID.H'
    'US-NW-PSCO->US-NW-WACM': 'EBA.PSCO-WACM.ID.H'
    'US-NW-PSEI->US-NW-BPAT': 'EBA.PSEI-BPAT.ID.H'
    'US-NW-PSEI->US-NW-TPWR': 'EBA.PSEI-TPWR.ID.H'
    'US-NW-PSEI->US-NW-CHPD': 'EBA.PSEI-CHPD.ID.H'
    'US-NW-PSEI->US-NW-GCPD': 'EBA.PSEI-GCPD.ID.H'
    'US-NW-PSEI->US-NW-SCL': 'EBA.PSEI-SCL.ID.H'
    'US-NW-SCL->US-NW-BPAT': 'EBA.SCL-BPAT.ID.H'
    'US-NW-SCL->US-NW-PSEI': 'EBA.SCL-PSEI.ID.H'
    'US-NW-TPWR->US-NW-BPAT': 'EBA.TPWR-BPAT.ID.H'
    'US-NW-TPWR->US-NW-PSEI': 'EBA.TPWR-PSEI.ID.H'
    'US-NW-WACM->US-SW-AZPS': 'EBA.WACM-AZPS.ID.H'
    'US-NW-WACM->US-NW-PACE': 'EBA.WACM-PACE.ID.H'
    'US-NW-WACM->US-NW-PSCO': 'EBA.WACM-PSCO.ID.H'
    'US-NW-WACM->US-SW-PNM': 'EBA.WACM-PNM.ID.H'
    'US-NW-WACM->US-CENT-SWPP': 'EBA.WACM-SWPP.ID.H'
    'US-NW-WACM->US-SW-WALC': 'EBA.WACM-WALC.ID.H'
    'US-NW-WACM->US-NW-WAUW': 'EBA.WACM-WAUW.ID.H'
    'US-NW-WAUW->US-NW-NWMT': 'EBA.WAUW-NWMT.ID.H'
    'US-NW-WAUW->US-CENT-SWPP': 'EBA.WAUW-SWPP.ID.H'
    'US-NW-WAUW->US-NW-WACM': 'EBA.WAUW-WACM.ID.H'
    'US-NW-WWA->US-NW-NWMT': 'EBA.WWA-NWMT.ID.H'
    'US-NY-NYIS->US-NE-ISNE': 'EBA.NYIS-ISNE.ID.H'
    'US-NY-NYIS->US-MIDA-PJM': 'EBA.NYIS-PJM.ID.H'
    'US-SE-AEC->US-MIDW-MISO': 'EBA.AEC-MISO.ID.H'
    'US-SE-AEC->US-SE-SOCO': 'EBA.AEC-SOCO.ID.H'
    'US-SE-SEPA->US-CAR-DUK': 'EBA.SEPA-DUK.ID.H'
    'US-SE-SEPA->US-CAR-SCEG': 'EBA.SEPA-SCEG.ID.H'
    'US-SE-SEPA->US-CAR-SC': 'EBA.SEPA-SC.ID.H'
    'US-SE-SEPA->US-SE-SOCO': 'EBA.SEPA-SOCO.ID.H'
    'US-SE-SOCO->US-FLA-TAL': 'EBA.SOCO-TAL.ID.H'
    'US-SE-SOCO->US-CAR-DUK': 'EBA.SOCO-DUK.ID.H'
    'US-SE-SOCO->US-FLA-FPC': 'EBA.SOCO-FPC.ID.H'
    'US-SE-SOCO->US-FLA-FPL': 'EBA.SOCO-FPL.ID.H'
    'US-SE-SOCO->US-MIDW-MISO': 'EBA.SOCO-MISO.ID.H'
    'US-SE-SOCO->US-SE-AEC': 'EBA.SOCO-AEC.ID.H'
    'US-SE-SOCO->US-CAR-SCEG': 'EBA.SOCO-SCEG.ID.H'
    'US-SE-SOCO->US-CAR-SC': 'EBA.SOCO-SC.ID.H'
    'US-SE-SOCO->US-SE-SEPA': 'EBA.SOCO-SEPA.ID.H'
    'US-SE-SOCO->US-TEN-TVA': 'EBA.SOCO-TVA.ID.H'
    'US-SW-AZPS->US-CAL-CISO': 'EBA.AZPS-CISO.ID.H'
    'US-SW-AZPS->US-SW-GRMA': 'EBA.AZPS-GRMA.ID.H'
    'US-SW-AZPS->US-CAL-IID': 'EBA.AZPS-IID.ID.H'
    'US-SW-AZPS->US-CAL-LDWP': 'EBA.AZPS-LDWP.ID.H'
    'US-SW-AZPS->US-NW-PACE': 'EBA.AZPS-PACE.ID.H'
    'US-SW-AZPS->US-SW-PNM': 'EBA.AZPS-PNM.ID.H'
    'US-SW-AZPS->US-SW-SRP': 'EBA.AZPS-SRP.ID.H'
    'US-SW-AZPS->US-SW-TEPC': 'EBA.AZPS-TEPC.ID.H'
    'US-SW-AZPS->US-SW-WALC': 'EBA.AZPS-WALC.ID.H'
    'US-SW-AZPS->US-NW-WACM': 'EBA.AZPS-WACM.ID.H'
    'US-SW-DEAA->US-SW-SRP': 'EBA.DEAA-SRP.ID.H'
    'US-SW-EPE->US-SW-PNM': 'EBA.EPE-PNM.ID.H'
    'US-SW-EPE->US-CENT-SWPP': 'EBA.EPE-SWPP.ID.H'
    'US-SW-EPE->US-SW-TEPC': 'EBA.EPE-TEPC.ID.H'
    'US-SW-GRIF->US-SW-WALC': 'EBA.GRIF-WALC.ID.H'
    'US-SW-GRMA->US-SW-AZPS': 'EBA.GRMA-AZPS.ID.H'
    'US-SW-HGMA->US-SW-SRP': 'EBA.HGMA-SRP.ID.H'
    'US-SW-PNM->US-SW-AZPS': 'EBA.PNM-AZPS.ID.H'
    'US-SW-PNM->US-SW-EPE': 'EBA.PNM-EPE.ID.H'
    'US-SW-PNM->US-NW-PSCO': 'EBA.PNM-PSCO.ID.H'
    'US-SW-PNM->US-CENT-SWPP': 'EBA.PNM-SWPP.ID.H'
    'US-SW-PNM->US-SW-TEPC': 'EBA.PNM-TEPC.ID.H'
    'US-SW-PNM->US-NW-WACM': 'EBA.PNM-WACM.ID.H'
    'US-SW-SRP->US-SW-AZPS': 'EBA.SRP-AZPS.ID.H'
    'US-SW-SRP->US-SW-DEAA': 'EBA.SRP-DEAA.ID.H'
    'US-SW-SRP->US-CAL-CISO': 'EBA.SRP-CISO.ID.H'
    'US-SW-SRP->US-SW-HGMA': 'EBA.SRP-HGMA.ID.H'
    'US-SW-SRP->US-SW-PNM': 'EBA.SRP-PNM.ID.H'
    'US-SW-SRP->US-SW-TEPC': 'EBA.SRP-TEPC.ID.H'
    'US-SW-SRP->US-SW-WALC': 'EBA.SRP-WALC.ID.H'
    'US-SW-TEPC->US-SW-AZPS': 'EBA.TEPC-AZPS.ID.H'
    'US-SW-TEPC->US-SW-EPE': 'EBA.TEPC-EPE.ID.H'
    'US-SW-TEPC->US-SW-PNM': 'EBA.TEPC-PNM.ID.H'
    'US-SW-TEPC->US-SW-SRP': 'EBA.TEPC-SRP.ID.H'
    'US-SW-TEPC->US-SW-WALC': 'EBA.TEPC-WALC.ID.H'
    'US-SW-WALC->US-SW-AZPS': 'EBA.WALC-AZPS.ID.H'
    'US-SW-WALC->US-CAL-CISO': 'EBA.WALC-CISO.ID.H'
    'US-SW-WALC->US-SW-GRIF': 'EBA.WALC-GRIF.ID.H'
    'US-SW-WALC->US-CAL-IID': 'EBA.WALC-IID.ID.H'
    'US-SW-WALC->US-CAL-LDWP': 'EBA.WALC-LDWP.ID.H'
    'US-SW-WALC->US-NW-NEVP': 'EBA.WALC-NEVP.ID.H'
    'US-SW-WALC->US-SW-SRP': 'EBA.WALC-SRP.ID.H'
    'US-SW-WALC->US-SW-TEPC': 'EBA.WALC-TEPC.ID.H'
    'US-SW-WALC->US-NW-WACM': 'EBA.WALC-WACM.ID.H'
    'US-TEN-TVA->US-MIDW-AECI': 'EBA.TVA-AECI.ID.H'
    'US-TEN-TVA->US-CAR-DUK': 'EBA.TVA-DUK.ID.H'
    'US-TEN-TVA->US-CAR-CPLW': 'EBA.TVA-CPLW.ID.H'
    'US-TEN-TVA->US-MIDW-EEI': 'EBA.TVA-EEI.ID.H'
    'US-TEN-TVA->US-MIDW-LGEE': 'EBA.TVA-LGEE.ID.H'
    'US-TEN-TVA->US-MIDW-MISO': 'EBA.TVA-MISO.ID.H'
    'US-TEN-TVA->US-MIDA-PJM': 'EBA.TVA-PJM.ID.H'
    'US-TEN-TVA->US-SE-SOCO': 'EBA.TVA-SOCO.ID.H'
    'US-TEX-ERCO->US-CENT-SWPP': 'EBA.ERCO-SWPP.ID.H'
}

# based on https://www.eia.gov/beta/electricity/gridmonitor/dashboard/electric_overview/US48/US48
# or https://www.eia.gov/opendata/qb.php?category=3390101
# List includes regions and Balancing Authorities. 
REGIONS = {
    'US-BPA': 'BPAT',
    'US-CA': 'CAL',
    'US-CAR': 'CAR',
    'US-DUK': 'DUK', #Duke Energy Carolinas
    'US-SPP': 'CENT',
    'US-FL': 'FLA',
    'US-PJM': 'MIDA',
    'US-MISO': 'MIDW',
    'US-NEISO': 'NE',
    'US-NEVP': 'NEVP', #Nevada Power Company
    'US-NY': 'NY',
    'US-NW': 'NW',
    'US-SC': 'SC', #South Carolina Public Service Authority
    'US-SE': 'SE',
    'US-SEC': 'SEC',
    'US-SOCO': 'SOCO', #Southern Company Services Inc - Trans
    'US-SWPP': 'SWPP', #Southwest Power Pool
    'US-SVERI': 'SW',
    'US-TN': 'TEN',
    'US-TX': 'TEX',

    'US-CAL-BANC': 'BANC' #Balancing Authority Of Northern California
    'US-CAL-CISO': 'CISO' #California Independent System Operator
    'US-CAL-IID': 'IID' #Imperial Irrigation District
    'US-CAL-LDWP': 'LDWP' #Los Angeles Department Of Water And Power
    'US-CAL-TIDC': 'TIDC' #Turlock Irrigation District
    'US-CAR-CPLE': 'CPLE' #Duke Energy Progress East
    'US-CAR-CPLW': 'CPLW' #Duke Energy Progress West
    'US-CAR-DUK': 'DUK' #Duke Energy Carolinas
    'US-CAR-SC': 'SC' #South Carolina Public Service Authority
    'US-CAR-SCEG': 'SCEG' #South Carolina Electric & Gas Company
    'US-CAR-YAD': 'YAD' #Alcoa Power Generating, Inc. - Yadkin Division
    'US-CENT-SPA': 'SPA' #Southwestern Power Administration
    'US-CENT-SWPP': 'SWPP' #Southwest Power Pool
    'US-FLA-FMPP': 'FMPP' #Florida Municipal Power Pool
    'US-FLA-FPC': 'FPC' #Duke Energy Florida Inc
    'US-FLA-FPL': 'FPL' #Florida Power & Light Company
    'US-FLA-GVL': 'GVL' #Gainesville Regional Utilities
    'US-FLA-HST': 'HST' #City Of Homestead
    'US-FLA-JEA': 'JEA' #Jea
    'US-FLA-NSB': 'NSB' #New Smyrna Beach, Utilities Commission Of
    'US-FLA-SEC': 'SEC' #Seminole Electric Cooperative
    'US-FLA-TAL': 'TAL' #City Of Tallahassee
    'US-FLA-TEC': 'TEC' #Tampa Electric Company
    'US-MIDA-OVEC': 'OVEC' #Ohio Valley Electric Corporation
    'US-MIDA-PJM': 'PJM' #Pjm Interconnection, Llc
    'US-MIDW-AECI': 'AECI' #Associated Electric Cooperative, Inc.
    'US-MIDW-EEI': 'EEI' #Electric Energy, Inc.
    'US-MIDW-LGEE': 'LGEE' #Louisville Gas And Electric Company And Kentucky Utilities
    'US-MIDW-MISO': 'MISO' #Midcontinent Independent Transmission System Operator, Inc..
    'US-NE-ISNE': 'ISNE' #Iso New England Inc.
    'US-NW-AVA': 'AVA' #Avista Corporation
    'US-NW-AVRN': 'AVRN' #Avangrid Renewables Cooperative
    'US-NW-BPAT': 'BPAT' #Bonneville Power Administration
    'US-NW-CHPD': 'CHPD' #Public Utility District No. 1 Of Chelan County
    'US-NW-DOPD': 'DOPD' #Pud No. 1 Of Douglas County
    'US-NW-GCPD': 'GCPD' #Public Utility District No. 2 Of Grant County, Washington
    'US-NW-GRID': 'GRID' #Gridforce Energy Management, Llc
    'US-NW-GWA': 'GWA' #Naturener Power Watch, Llc (Gwa)
    'US-NW-IPCO': 'IPCO' #Idaho Power Company
    'US-NW-NEVP': 'NEVP' #Nevada Power Company
    'US-NW-NWMT': 'NWMT' #Northwestern Energy (Nwmt)
    'US-NW-PACE': 'PACE' #Pacificorp - East
    'US-NW-PACW': 'PACW' #Pacificorp - West
    'US-NW-PGE': 'PGE' #Portland General Electric Company
    'US-NW-PSCO': 'PSCO' #Public Service Company Of Colorado
    'US-NW-PSEI': 'PSEI' #Puget Sound Energy
    'US-NW-SCL': 'SCL' #Seattle City Light
    'US-NW-TPWR': 'TPWR' #City Of Tacoma, Department Of Public Utilities, Light Division
    'US-NW-WACM': 'WACM' #Western Area Power Administration - Rocky Mountain Region
    'US-NW-WAUW': 'WAUW' #Western Area Power Administration Ugp West
    'US-NW-WWA': 'WWA' #Naturener Wind Watch, Llc
    'US-NY-NYIS': 'NYIS' #New York Independent System Operator
    'US-SE-AEC': 'AEC' #Powersouth Energy Cooperative
    'US-SE-SEPA': 'SEPA' #Southeastern Power Administration
    'US-SE-SOCO': 'SOCO' #Southern Company Services, Inc. - Trans
    'US-SW-AZPS': 'AZPS' #Arizona Public Service Company
    'US-SW-DEAA': 'DEAA' #Arlington Valley, Llc - Avba
    'US-SW-EPE': 'EPE' #El Paso Electric Company
    'US-SW-GRIF': 'GRIF' #Griffith Energy, Llc
    'US-SW-GRMA': 'GRMA' #Gila River Power, Llc
    'US-SW-HGMA': 'HGMA' #New Harquahala Generating Company, Llc - Hgba
    'US-SW-PNM': 'PNM' #Public Service Company Of New Mexico
    'US-SW-SRP': 'SRP' #Salt River Project
    'US-SW-TEPC': 'TEPC' #Tucson Electric Power Company
    'US-SW-WALC': 'WALC' #Western Area Power Administration - Desert Southwest Region
    'US-TEN-TVA': 'TVA' #Tennessee Valley Authority
    'US-TEX-ERCO': 'ERCO' #Electric Reliability Council Of Texas, Inc.
}
TYPES = {
    # 'biomass': 'BM',  # not currently supported
    'coal': 'COL',
    'gas': 'NG',
    'hydro': 'WAT',
    'nuclear': 'NUC',
    'oil': 'OIL',
    'unknown': 'OTH',
    'solar': 'SUN',
    'wind': 'WND',
}
PRODUCTION_SERIES = 'EBA.%s-ALL.NG.H'
PRODUCTION_MIX_SERIES = 'EBA.%s-ALL.NG.%s.H'
DEMAND_SERIES = 'EBA.%s-ALL.D.H'
FORECAST_SERIES = 'EBA.%s-ALL.DF.H'


def fetch_consumption_forecast(zone_key, session=None, target_datetime=None, logger=None):
    return _fetch_series(zone_key, FORECAST_SERIES % REGIONS[zone_key],
                         session=session, target_datetime=target_datetime,
                         logger=logger)


def fetch_production(zone_key, session=None, target_datetime=None, logger=None):
    return _fetch_series(zone_key, PRODUCTION_SERIES % REGIONS[zone_key],
                         session=session, target_datetime=target_datetime,
                         logger=logger)


def fetch_consumption(zone_key, session=None, target_datetime=None, logger=None):
    consumption = _fetch_series(zone_key, DEMAND_SERIES % REGIONS[zone_key],
                                session=session, target_datetime=target_datetime,
                                logger=logger)
    for point in consumption:
        point['consumption'] = point.pop('value')

    return consumption


def fetch_production_mix(zone_key, session=None, target_datetime=None, logger=None):
    mixes = []
    for type, code in TYPES.items():
        series = PRODUCTION_MIX_SERIES % (REGIONS[zone_key], code)
        mix = _fetch_series(zone_key, series, session=session,
                            target_datetime=target_datetime, logger=logger)

        if not mix:
            continue
        for point in mix:
            if type == 'hydro' and point['value'] < 0:
                point.update({
                    'production': {},# required by merge_production_outputs()
                    'storage': {type: point.pop('value')},
                })
            else:
                point.update({
                    'production': {type: point.pop('value')},
                    'storage': {},  # required by merge_production_outputs()
                })

            #replace small negative values (>-5) with 0s This is necessary for solar
            point = validate(point, logger=logger, remove_negative=True)
        mixes.append(mix)

    return merge_production_outputs(mixes, zone_key, merge_source='eia.gov')


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    sortedcodes = '->'.join(sorted([zone_key1, zone_key2]))
    exchange = _fetch_series(sortedcodes, EXCHANGES[sortedcodes], session=session,
                             target_datetime=target_datetime, logger=logger)
    for point in exchange:
        point.update({
            'sortedZoneKeys': point.pop('zoneKey'),
            'netFlow': point.pop('value'),
        })
        if sortedcodes == 'MX-BC->US-CA':
            point['netFlow'] = -point['netFlow']

    return exchange


def _fetch_series(zone_key, series_id, session=None, target_datetime=None,
                  logger=None):
    """Fetches and converts a data series."""
    key = os.environ['EIA_KEY']
    assert key and key != 'eia_key', key

    s = session or requests.Session()
    series = Series(series_id=series_id, session=s)

    if target_datetime:
        utc = tz.gettz('UTC')
        #eia currently only accepts utc timestamps in the form YYYYMMDDTHHZ
        end = target_datetime.astimezone(utc).strftime('%Y%m%dT%HZ')
        start = (target_datetime.astimezone(utc) - datetime.timedelta(days=1)).strftime('%Y%m%dT%HZ')
        raw_data = series.get_data(start=start, end=end)
    else:
        # Get the last 24 hours available.
        raw_data = series.last(24)

    # UTC timestamp with no offset returned.
    if not raw_data.get('series'):
        # Series doesn't exist. Probably requesting a fuel from a region that
        # doesn't have any capacity for that fuel type.
        return []

    return [{
        'zoneKey': zone_key,
        'datetime': parser.parse(datapoint[0]),
        'value': datapoint[1],
        'source': 'eia.gov',
    } for datapoint in raw_data['series'][0]['data']]


def main():
    "Main method, never used by the Electricity Map backend, but handy for testing."
    from pprint import pprint
    pprint(fetch_consumption_forecast('US-NY'))
    pprint(fetch_production('US-SEC'))
    pprint(fetch_production_mix('US-TN'))
    pprint(fetch_consumption('US-CAR'))
    pprint(fetch_exchange('MX-BC', 'US-CA'))


if __name__ == '__main__':
    main()
