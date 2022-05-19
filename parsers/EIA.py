#!/usr/bin/env python3
"""
Parser for U.S. Energy Information Administration, https://www.eia.gov/ .

Aggregates and standardizes data from most of the US ISOs,
and exposes them via a unified API.

Requires an API key, set in the EIA_KEY environment variable. Get one here:
https://www.eia.gov/opendata/register.php
"""
import datetime

import requests
from dateutil import parser, tz

from parsers.lib.config import refetch_frequency

from .ENTSOE import merge_production_outputs
from .lib.validation import validate

# Reverse exchanges need to be multiplied by -1, since they are reported in the opposite direction
REVERSE_EXCHANGES = [
    "US-CA->MX-BC",
    "MX-BC->US-CAL-CISO",
    "CA-SK->US-CENT-SWPP",
    "CA-MB->US-MIDW-MISO",
    "CA-ON->US-MIDW-MISO",
    "CA-QC->US-NE-ISNE",
    "CA-NB->US-NE-ISNE",
    "CA-BC->US-NW-BPAT",
    "CA-AB->US-NW-NWMT",
    "CA-QC->US-NY-NYIS",
    "CA-ON->US-NY-NYIS",
    "MX-NE->US-TEX-ERCO",
    "MX-NO->US-TEX-ERCO",
    "US-SW-PNM->US-SW-SRP",  # For some reason EBA.SRP-PNM.ID.H exists in EIA, but PNM-SRP does not. Probably because it is unidirectional
]

NEGATIVE_PRODUCTION_THRESHOLDS_TYPE = {
    "default": -10,
    "coal": -50,
    "gas": -20,
    "solar": -100,
    "wind": -20,
    "unknown": -50,
}


EXCHANGES = {
    # Exchanges to non-US BAs
    "MX-BC->US-CAL-CISO": "EBA.CISO-CFE.ID.H",  # Unable to verify if MX-BC is correct
    "CA-SK->US-CENT-SWPP": "EBA.SWPP-SPC.ID.H",
    "CA-MB->US-MIDW-MISO": "EBA.MISO-MHEB.ID.H",
    "CA-ON->US-MIDW-MISO": "EBA.MISO-IESO.ID.H",
    "CA-QC->US-NE-ISNE": "EBA.ISNE-HQT.ID.H",
    "CA-NB->US-NE-ISNE": "EBA.ISNE-NBSO.ID.H",
    "CA-BC->US-NW-BPAT": "EBA.BPAT-BCHA.ID.H",
    "CA-AB->US-NW-NWMT": "EBA.NWMT-AESO.ID.H",
    "CA-QC->US-NY-NYIS": "EBA.NYIS-HQT.ID.H",
    "CA-ON->US-NY-NYIS": "EBA.NYIS-IESO.ID.H",
    "MX-NE->US-TEX-ERCO": "EBA.ERCO-CEN.ID.H",  # Unable to verify if MX-NE is correct
    "MX-NO->US-TEX-ERCO": "EBA.ERCO-CFE.ID.H",  # Unable to verify if MX-NO is correct
    # Exchanges to other US balancing authorities
    "US-CAL-BANC->US-NW-BPAT": "EBA.BANC-BPAT.ID.H",
    "US-CAL-BANC->US-CAL-CISO": "EBA.BANC-CISO.ID.H",
    "US-CAL-BANC->US-CAL-TIDC": "EBA.BANC-TIDC.ID.H",
    "US-CAL-CISO->US-SW-AZPS": "EBA.CISO-AZPS.ID.H",
    "US-CAL-CISO->US-NW-BPAT": "EBA.CISO-BPAT.ID.H",
    "US-CAL-CISO->US-CAL-IID": "EBA.CISO-IID.ID.H",
    "US-CAL-CISO->US-CAL-LDWP": "EBA.CISO-LDWP.ID.H",
    "US-CAL-CISO->US-NW-NEVP": "EBA.CISO-NEVP.ID.H",
    "US-CAL-CISO->US-NW-PACW": "EBA.CISO-PACW.ID.H",
    "US-CAL-CISO->US-SW-SRP": "EBA.CISO-SRP.ID.H",
    "US-CAL-CISO->US-CAL-TIDC": "EBA.CISO-TIDC.ID.H",
    "US-CAL-CISO->US-SW-WALC": "EBA.CISO-WALC.ID.H",
    "US-CAL-IID->US-SW-AZPS": "EBA.IID-AZPS.ID.H",
    "US-CAL-IID->US-SW-WALC": "EBA.IID-WALC.ID.H",
    "US-CAL-LDWP->US-SW-AZPS": "EBA.LDWP-AZPS.ID.H",
    "US-CAL-LDWP->US-NW-BPAT": "EBA.LDWP-BPAT.ID.H",
    "US-CAL-LDWP->US-NW-NEVP": "EBA.LDWP-NEVP.ID.H",
    "US-CAL-LDWP->US-NW-PACE": "EBA.LDWP-PACE.ID.H",
    "US-CAL-LDWP->US-SW-WALC": "EBA.LDWP-WALC.ID.H",
    "US-CAR-CPLE->US-CAR-YAD": "EBA.CPLE-YAD.ID.H",
    "US-CAR-CPLE->US-CAR-DUK": "EBA.CPLE-DUK.ID.H",
    "US-CAR-CPLE->US-MIDA-PJM": "EBA.CPLE-PJM.ID.H",
    "US-CAR-CPLE->US-CAR-SCEG": "EBA.CPLE-SCEG.ID.H",
    "US-CAR-CPLE->US-CAR-SC": "EBA.CPLE-SC.ID.H",
    "US-CAR-CPLW->US-CAR-DUK": "EBA.CPLW-DUK.ID.H",
    "US-CAR-CPLW->US-MIDA-PJM": "EBA.CPLW-PJM.ID.H",
    "US-CAR-CPLW->US-TEN-TVA": "EBA.CPLW-TVA.ID.H",
    "US-CAR-DUK->US-CAR-YAD": "EBA.DUK-YAD.ID.H",
    "US-CAR-DUK->US-MIDA-PJM": "EBA.DUK-PJM.ID.H",
    "US-CAR-DUK->US-CAR-SCEG": "EBA.DUK-SCEG.ID.H",
    "US-CAR-DUK->US-CAR-SC": "EBA.DUK-SC.ID.H",
    "US-CAR-DUK->US-SE-SEPA": "EBA.DUK-SEPA.ID.H",
    "US-CAR-DUK->US-SE-SOCO": "EBA.DUK-SOCO.ID.H",
    "US-CAR-DUK->US-TEN-TVA": "EBA.DUK-TVA.ID.H",
    "US-CAR-SC->US-CAR-SCEG": "EBA.SC-SCEG.ID.H",
    "US-CAR-SC->US-SE-SEPA": "EBA.SC-SEPA.ID.H",
    "US-CAR-SC->US-SE-SOCO": "EBA.SC-SOCO.ID.H",
    "US-CAR-SCEG->US-SE-SEPA": "EBA.SCEG-SEPA.ID.H",
    "US-CAR-SCEG->US-SE-SOCO": "EBA.SCEG-SOCO.ID.H",
    "US-CENT-SPA->US-MIDW-AECI": "EBA.SPA-AECI.ID.H",
    "US-CENT-SPA->US-MIDW-MISO": "EBA.SPA-MISO.ID.H",
    "US-CENT-SPA->US-CENT-SWPP": "EBA.SPA-SWPP.ID.H",
    "US-CENT-SWPP->US-MIDW-AECI": "EBA.SWPP-AECI.ID.H",
    "US-CENT-SWPP->US-SW-EPE": "EBA.SWPP-EPE.ID.H",
    "US-CENT-SWPP->US-TEX-ERCO": "EBA.SWPP-ERCO.ID.H",
    "US-CENT-SWPP->US-MIDW-MISO": "EBA.SWPP-MISO.ID.H",
    "US-CENT-SWPP->US-NW-PSCO": "EBA.SWPP-PSCO.ID.H",
    "US-CENT-SWPP->US-SW-PNM": "EBA.SWPP-PNM.ID.H",
    "US-CENT-SWPP->US-NW-WACM": "EBA.SWPP-WACM.ID.H",
    "US-CENT-SWPP->US-NW-WAUW": "EBA.SWPP-WAUW.ID.H",
    "US-FLA-FMPP->US-FLA-FPC": "EBA.FMPP-FPC.ID.H",
    "US-FLA-FMPP->US-FLA-FPL": "EBA.FMPP-FPL.ID.H",
    "US-FLA-FMPP->US-FLA-JEA": "EBA.FMPP-JEA.ID.H",
    "US-FLA-FMPP->US-FLA-TEC": "EBA.FMPP-TEC.ID.H",
    "US-FLA-FPC->US-FLA-TAL": "EBA.FPC-TAL.ID.H",
    "US-FLA-FPC->US-FLA-FPL": "EBA.FPC-FPL.ID.H",
    "US-FLA-FPC->US-FLA-GVL": "EBA.FPC-GVL.ID.H",
    "US-FLA-FPC->US-FLA-SEC": "EBA.FPC-SEC.ID.H",
    "US-FLA-FPC->US-SE-SOCO": "EBA.FPC-SOCO.ID.H",
    "US-FLA-FPC->US-FLA-TEC": "EBA.FPC-TEC.ID.H",
    "US-FLA-FPC->US-FLA-NSB": "EBA.FPC-NSB.ID.H",
    "US-FLA-FPL->US-FLA-HST": "EBA.FPL-HST.ID.H",
    "US-FLA-FPL->US-FLA-GVL": "EBA.FPL-GVL.ID.H",
    "US-FLA-FPL->US-FLA-JEA": "EBA.FPL-JEA.ID.H",
    "US-FLA-FPL->US-FLA-SEC": "EBA.FPL-SEC.ID.H",
    "US-FLA-FPL->US-SE-SOCO": "EBA.FPL-SOCO.ID.H",
    "US-FLA-FPL->US-FLA-TEC": "EBA.FPL-TEC.ID.H",
    "US-FLA-FPL->US-FLA-NSB": "EBA.FPL-NSB.ID.H",
    "US-FLA-JEA->US-FLA-SEC": "EBA.JEA-SEC.ID.H",
    "US-FLA-SEC->US-FLA-TEC": "EBA.SEC-TEC.ID.H",
    "US-FLA-TAL->US-SE-SOCO": "EBA.TAL-SOCO.ID.H",
    "US-MIDA-PJM->US-MIDW-LGEE": "EBA.PJM-LGEE.ID.H",
    "US-MIDA-PJM->US-MIDW-MISO": "EBA.PJM-MISO.ID.H",
    "US-MIDA-PJM->US-NY-NYIS": "EBA.PJM-NYIS.ID.H",
    "US-MIDA-PJM->US-TEN-TVA": "EBA.PJM-TVA.ID.H",
    "US-MIDW-AECI->US-MIDW-MISO": "EBA.AECI-MISO.ID.H",
    "US-MIDW-AECI->US-TEN-TVA": "EBA.AECI-TVA.ID.H",
    "US-MIDW-GLHB->US-MIDW-LGEE": "EBA.GLHB-LGEE.ID.H",
    "US-MIDW-GLHB->US-MIDW-MISO": "EBA.GLHB-MISO.ID.H",
    "US-MIDW-GLHB->US-TEN-TVA": "EBA.EEI-TVA.ID.H",
    "US-MIDW-LGEE->US-MIDW-MISO": "EBA.LGEE-MISO.ID.H",
    "US-MIDW-LGEE->US-TEN-TVA": "EBA.LGEE-TVA.ID.H",
    "US-MIDW-MISO->US-SE-AEC": "EBA.MISO-AEC.ID.H",
    "US-MIDW-MISO->US-SE-SOCO": "EBA.MISO-SOCO.ID.H",
    "US-MIDW-MISO->US-TEN-TVA": "EBA.MISO-TVA.ID.H",
    "US-NE-ISNE->US-NY-NYIS": "EBA.ISNE-NYIS.ID.H",
    "US-NW-AVA->US-NW-BPAT": "EBA.AVA-BPAT.ID.H",
    "US-NW-AVA->US-NW-IPCO": "EBA.AVA-IPCO.ID.H",
    "US-NW-AVA->US-NW-NWMT": "EBA.AVA-NWMT.ID.H",
    "US-NW-AVA->US-NW-PACW": "EBA.AVA-PACW.ID.H",
    "US-NW-AVA->US-NW-CHPD": "EBA.AVA-CHPD.ID.H",
    "US-NW-AVA->US-NW-GCPD": "EBA.AVA-GCPD.ID.H",
    "US-NW-BPAT->US-NW-TPWR": "EBA.BPAT-TPWR.ID.H",
    "US-NW-BPAT->US-NW-GRID": "EBA.BPAT-GRID.ID.H",
    "US-NW-BPAT->US-NW-IPCO": "EBA.BPAT-IPCO.ID.H",
    "US-NW-BPAT->US-NW-NEVP": "EBA.BPAT-NEVP.ID.H",
    "US-NW-BPAT->US-NW-NWMT": "EBA.BPAT-NWMT.ID.H",
    "US-NW-BPAT->US-NW-DOPD": "EBA.BPAT-DOPD.ID.H",
    "US-NW-BPAT->US-NW-PACW": "EBA.BPAT-PACW.ID.H",
    "US-NW-BPAT->US-NW-PGE": "EBA.BPAT-PGE.ID.H",
    "US-NW-BPAT->US-NW-CHPD": "EBA.BPAT-CHPD.ID.H",
    "US-NW-BPAT->US-NW-GCPD": "EBA.BPAT-GCPD.ID.H",
    "US-NW-BPAT->US-NW-PSEI": "EBA.BPAT-PSEI.ID.H",
    "US-NW-BPAT->US-NW-SCL": "EBA.BPAT-SCL.ID.H",
    "US-NW-CHPD->US-NW-DOPD": "EBA.CHPD-DOPD.ID.H",
    "US-NW-CHPD->US-NW-PSEI": "EBA.CHPD-PSEI.ID.H",
    "US-NW-GCPD->US-NW-PACW": "EBA.GCPD-PACW.ID.H",
    "US-NW-GCPD->US-NW-PSEI": "EBA.GCPD-PSEI.ID.H",
    "US-NW-GWA->US-NW-NWMT": "EBA.GWA-NWMT.ID.H",
    "US-NW-IPCO->US-NW-NEVP": "EBA.IPCO-NEVP.ID.H",
    "US-NW-IPCO->US-NW-NWMT": "EBA.IPCO-NWMT.ID.H",
    "US-NW-IPCO->US-NW-PACE": "EBA.IPCO-PACE.ID.H",
    "US-NW-IPCO->US-NW-PACW": "EBA.IPCO-PACW.ID.H",
    "US-NW-NEVP->US-NW-PACE": "EBA.NEVP-PACE.ID.H",
    "US-NW-NEVP->US-SW-WALC": "EBA.NEVP-WALC.ID.H",
    "US-NW-NWMT->US-NW-WWA": "EBA.NWMT-WWA.ID.H",
    "US-NW-NWMT->US-NW-PACE": "EBA.NWMT-PACE.ID.H",
    "US-NW-NWMT->US-NW-WAUW": "EBA.NWMT-WAUW.ID.H",
    "US-NW-PACE->US-SW-AZPS": "EBA.PACE-AZPS.ID.H",
    "US-NW-PACE->US-NW-PACW": "EBA.PACE-PACW.ID.H",
    "US-NW-PACE->US-NW-WACM": "EBA.PACE-WACM.ID.H",
    "US-NW-PACW->US-NW-PGE": "EBA.PACW-PGE.ID.H",
    "US-NW-PSCO->US-SW-PNM": "EBA.PSCO-PNM.ID.H",
    "US-NW-PSCO->US-NW-WACM": "EBA.PSCO-WACM.ID.H",
    "US-NW-PSEI->US-NW-TPWR": "EBA.PSEI-TPWR.ID.H",
    "US-NW-PSEI->US-NW-SCL": "EBA.PSEI-SCL.ID.H",
    "US-NW-WACM->US-SW-AZPS": "EBA.WACM-AZPS.ID.H",
    "US-NW-WACM->US-SW-PNM": "EBA.WACM-PNM.ID.H",
    "US-NW-WACM->US-SW-WALC": "EBA.WACM-WALC.ID.H",
    "US-NW-WACM->US-NW-WAUW": "EBA.WACM-WAUW.ID.H",
    "US-SE-AEC->US-SE-SOCO": "EBA.AEC-SOCO.ID.H",
    "US-SE-SEPA->US-SE-SOCO": "EBA.SEPA-SOCO.ID.H",
    "US-SE-SOCO->US-TEN-TVA": "EBA.SOCO-TVA.ID.H",
    "US-SW-AZPS->US-SW-GRMA": "EBA.AZPS-GRMA.ID.H",
    "US-SW-AZPS->US-SW-PNM": "EBA.AZPS-PNM.ID.H",
    "US-SW-AZPS->US-SW-SRP": "EBA.AZPS-SRP.ID.H",
    "US-SW-AZPS->US-SW-TEPC": "EBA.AZPS-TEPC.ID.H",
    "US-SW-AZPS->US-SW-WALC": "EBA.AZPS-WALC.ID.H",
    "US-SW-EPE->US-SW-PNM": "EBA.EPE-PNM.ID.H",
    "US-SW-EPE->US-SW-TEPC": "EBA.EPE-TEPC.ID.H",
    "US-SW-GRIF->US-SW-WALC": "EBA.GRIF-WALC.ID.H",
    "US-SW-HGMA->US-SW-SRP": "EBA.HGMA-SRP.ID.H",
    "US-SW-PNM->US-SW-TEPC": "EBA.PNM-TEPC.ID.H",
    "US-SW-PNM->US-SW-SRP": "EBA.SRP-PNM.ID.H",
    "US-SW-SRP->US-SW-TEPC": "EBA.SRP-TEPC.ID.H",
    "US-SW-SRP->US-SW-WALC": "EBA.SRP-WALC.ID.H",
    "US-SW-TEPC->US-SW-WALC": "EBA.TEPC-WALC.ID.H",
}

# based on https://www.eia.gov/beta/electricity/gridmonitor/dashboard/electric_overview/US48/US48
# or https://www.eia.gov/opendata/qb.php?category=3390101
# List includes regions and Balancing Authorities.
REGIONS = {
    # New regions - EIA
    "US-CAL-BANC": "BANC",  # Balancing Authority Of Northern California
    "US-CAL-CISO": "CISO",  # California Independent System Operator
    "US-CAL-IID": "IID",  # Imperial Irrigation District
    "US-CAL-LDWP": "LDWP",  # Los Angeles Department Of Water And Power
    "US-CAL-TIDC": "TIDC",  # Turlock Irrigation District
    "US-CAR-CPLE": "CPLE",  # Duke Energy Progress East
    "US-CAR-CPLW": "CPLW",  # Duke Energy Progress West
    "US-CAR-DUK": "DUK",  # Duke Energy Carolinas
    "US-CAR-SC": "SC",  # South Carolina Public Service Authority
    "US-CAR-SCEG": "SCEG",  # South Carolina Electric & Gas Company
    "US-CAR-YAD": "YAD",  # Alcoa Power Generating, Inc. - Yadkin Division
    "US-CENT-SPA": "SPA",  # Southwestern Power Administration
    "US-CENT-SWPP": "SWPP",  # Southwest Power Pool
    "US-FLA-FMPP": "FMPP",  # Florida Municipal Power Pool
    "US-FLA-FPC": "FPC",  # Duke Energy Florida Inc
    "US-FLA-FPL": "FPL",  # Florida Power & Light Company
    "US-FLA-GVL": "GVL",  # Gainesville Regional Utilities
    "US-FLA-HST": "HST",  # City Of Homestead
    "US-FLA-JEA": "JEA",  # Jea
    "US-FLA-NSB": "NSB",  # New Smyrna Beach, Utilities Commission Of
    "US-FLA-SEC": "SEC",  # Seminole Electric Cooperative
    "US-FLA-TAL": "TAL",  # City Of Tallahassee
    "US-FLA-TEC": "TEC",  # Tampa Electric Company
    "US-MIDA-PJM": "PJM",  # Pjm Interconnection, Llc
    "US-MIDW-AECI": "AECI",  # Associated Electric Cooperative, Inc.
    "US-MIDW-GLHB": "GLHB",  # GridLiance
    "US-MIDW-LGEE": "LGEE",  # Louisville Gas And Electric Company And Kentucky Utilities
    "US-MIDW-MISO": "MISO",  # Midcontinent Independent Transmission System Operator, Inc..
    "US-NE-ISNE": "ISNE",  # Iso New England Inc.
    "US-NW-AVA": "AVA",  # Avista Corporation
    "US-NW-BPAT": "BPAT",  # Bonneville Power Administration
    "US-NW-CHPD": "CHPD",  # Public Utility District No. 1 Of Chelan County
    "US-NW-DOPD": "DOPD",  # Pud No. 1 Of Douglas County
    "US-NW-GCPD": "GCPD",  # Public Utility District No. 2 Of Grant County, Washington
    "US-NW-GRID": "GRID",  # Gridforce Energy Management, Llc
    "US-NW-GWA": "GWA",  # Naturener Power Watch, Llc (Gwa)
    "US-NW-IPCO": "IPCO",  # Idaho Power Company
    "US-NW-NEVP": "NEVP",  # Nevada Power Company
    "US-NW-NWMT": "NWMT",  # Northwestern Energy (Nwmt)
    "US-NW-PACE": "PACE",  # Pacificorp - East
    "US-NW-PACW": "PACW",  # Pacificorp - West
    "US-NW-PGE": "PGE",  # Portland General Electric Company
    "US-NW-PSCO": "PSCO",  # Public Service Company Of Colorado
    "US-NW-PSEI": "PSEI",  # Puget Sound Energy
    "US-NW-SCL": "SCL",  # Seattle City Light
    "US-NW-TPWR": "TPWR",  # City Of Tacoma, Department Of Public Utilities, Light Division
    "US-NW-WACM": "WACM",  # Western Area Power Administration - Rocky Mountain Region
    "US-NW-WAUW": "WAUW",  # Western Area Power Administration Ugp West
    "US-NW-WWA": "WWA",  # Naturener Wind Watch, Llc
    "US-NY-NYIS": "NYIS",  # New York Independent System Operator
    "US-SE-AEC": "AEC",  # Powersouth Energy Cooperative
    "US-SE-SEPA": "SEPA",  # Southeastern Power Administration
    "US-SE-SOCO": "SOCO",  # Southern Company Services, Inc. - Trans
    "US-SW-AZPS": "AZPS",  # Arizona Public Service Company
    "US-SW-EPE": "EPE",  # El Paso Electric Company
    "US-SW-GRIF": "GRIF",  # Griffith Energy, Llc
    "US-SW-GRMA": "GRMA",  # Gila River Power, Llc
    "US-SW-HGMA": "HGMA",  # New Harquahala Generating Company, Llc - Hgba
    "US-SW-PNM": "PNM",  # Public Service Company Of New Mexico
    "US-SW-SRP": "SRP",  # Salt River Project
    "US-SW-TEPC": "TEPC",  # Tucson Electric Power Company
    "US-SW-WALC": "WALC",  # Western Area Power Administration - Desert Southwest Region
    "US-TEN-TVA": "TVA",  # Tennessee Valley Authority
    "US-TEX-ERCO": "ERCO",  # Electric Reliability Council Of Texas, Inc.
}
TYPES = {
    # 'biomass': 'BM',  # not currently supported
    "coal": "COL",
    "gas": "NG",
    "hydro": "WAT",
    "nuclear": "NUC",
    "oil": "OIL",
    "unknown": "OTH",
    "solar": "SUN",
    "wind": "WND",
}
PRODUCTION_SERIES = "EBA.%s-ALL.NG.H"
PRODUCTION_MIX_SERIES = "EBA.%s-ALL.NG.%s.H"
DEMAND_SERIES = "EBA.%s-ALL.D.H"
FORECAST_SERIES = "EBA.%s-ALL.DF.H"


@refetch_frequency(datetime.timedelta(days=1))
def fetch_consumption_forecast(
    zone_key, session=None, target_datetime=None, logger=None
):
    return _fetch_series(
        zone_key,
        FORECAST_SERIES % REGIONS[zone_key],
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )


def fetch_production(zone_key, session=None, target_datetime=None, logger=None):
    return _fetch_series(
        zone_key,
        PRODUCTION_SERIES % REGIONS[zone_key],
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )


@refetch_frequency(datetime.timedelta(days=1))
def fetch_consumption(zone_key, session=None, target_datetime=None, logger=None):
    consumption = _fetch_series(
        zone_key,
        DEMAND_SERIES % REGIONS[zone_key],
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    for point in consumption:
        point["consumption"] = point.pop("value")

    return consumption


@refetch_frequency(datetime.timedelta(days=1))
def fetch_production_mix(zone_key, session=None, target_datetime=None, logger=None):
    mixes = []
    for type, code in TYPES.items():
        series = PRODUCTION_MIX_SERIES % (REGIONS[zone_key], code)
        mix = _fetch_series(
            zone_key,
            series,
            session=session,
            target_datetime=target_datetime,
            logger=logger,
        )

        # EIA does not currently split production from the Virgil Summer C
        # plant across the two owning/ utilizing BAs:
        # US-CAR-SCEG and US-CAR-SC,
        # but attributes it all to US-CAR-SCEG
        # Here we apply a temporary fix for that until EIA properly splits the production
        # This split can be found in the eGRID data,
        # https://www.epa.gov/energy/emissions-generation-resource-integrated-database-egrid
        SC_VIRGIL_OWNERSHIP = 0.3333333
        if zone_key == "US-CAR-SC" and type == "nuclear":
            series = PRODUCTION_MIX_SERIES % (REGIONS["US-CAR-SCEG"], code)
            mix = _fetch_series(
                "US-CAR-SCEG",
                series,
                session=session,
                target_datetime=target_datetime,
                logger=logger,
            )
            for point in mix:
                point.update({"value": point["value"] * SC_VIRGIL_OWNERSHIP})

        if zone_key == "US-CAR-SCEG" and type == "nuclear":
            for point in mix:
                point.update({"value": point["value"] * (1 - SC_VIRGIL_OWNERSHIP)})

        if not mix:
            continue
        for point in mix:
            negative_threshold = NEGATIVE_PRODUCTION_THRESHOLDS_TYPE.get(
                type, NEGATIVE_PRODUCTION_THRESHOLDS_TYPE["default"]
            )

            if (
                type != "hydro"
                and point["value"]
                and 0 > point["value"] >= negative_threshold
            ):
                point["value"] = 0

            if type == "hydro" and point["value"] and point["value"] < 0:
                point.update(
                    {
                        "production": {},  # required by merge_production_outputs()
                        "storage": {type: point.pop("value")},
                    }
                )
            else:
                point.update(
                    {
                        "production": {type: point.pop("value")},
                        "storage": {},  # required by merge_production_outputs()
                    }
                )

            # replace small negative values (>-5) with 0s This is necessary for solar
            point = validate(point, logger=logger, remove_negative=True)
        mixes.append(mix)

    if not mixes:
        logger.warning(f"No production mix data found for {zone_key}")
        return []

    # Some of the returned mixes could be for older timeframes.
    # Fx the latest oil data could be 6 months old.
    # In this case we want to discard the old data as we won't be able to merge it
    timeframes = [sorted(map(lambda x: x["datetime"], mix)) for mix in mixes]
    latest_timeframe = max(timeframes, key=lambda x: x[-1])

    correct_mixes = []
    for mix in mixes:
        correct_mix = []
        for production_in_mix in mix:
            if production_in_mix["datetime"] in latest_timeframe:
                correct_mix.append(production_in_mix)
        if len(correct_mix) > 0:
            correct_mixes.append(correct_mix)

    return merge_production_outputs(correct_mixes, zone_key, merge_source="eia.gov")


@refetch_frequency(datetime.timedelta(days=1))
def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
):
    sortedcodes = "->".join(sorted([zone_key1, zone_key2]))
    exchange = _fetch_series(
        sortedcodes,
        EXCHANGES[sortedcodes],
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    for point in exchange:
        point.update(
            {
                "sortedZoneKeys": point.pop("zoneKey"),
                "netFlow": point.pop("value"),
            }
        )
        if sortedcodes in REVERSE_EXCHANGES:
            point["netFlow"] = -point["netFlow"]

    return exchange


def _fetch_series(zone_key, series_id, session=None, target_datetime=None, logger=None):
    """Fetches and converts a data series."""

    s = session or requests.Session()

    # local import to avoid the exception that happens if EIAPY token is not set
    # even if this module is unused
    from eiapy import Series

    series = Series(series_id=series_id, session=s)

    if target_datetime:
        utc = tz.gettz("UTC")
        # eia currently only accepts utc timestamps in the form YYYYMMDDTHHZ
        end = target_datetime.astimezone(utc).strftime("%Y%m%dT%HZ")
        start = (target_datetime.astimezone(utc) - datetime.timedelta(days=1)).strftime(
            "%Y%m%dT%HZ"
        )
        raw_data = series.get_data(start=start, end=end)
    else:
        # Get the last 24 hours available.
        raw_data = series.last(24)

    eia_error_message = raw_data.get("data", {}).get("error")
    if eia_error_message:
        logger.error(f"EIA error, for series_id [{series_id}]: {eia_error_message}")
        return []

    # UTC timestamp with no offset returned.
    if not raw_data.get("series"):
        # Series doesn't exist. Probably requesting a fuel from a region that
        # doesn't have any capacity for that fuel type.
        return []

    return [
        {
            "zoneKey": zone_key,
            "datetime": parser.parse(datapoint[0]),
            "value": datapoint[1],
            "source": "eia.gov",
        }
        for datapoint in raw_data["series"][0]["data"]
    ]


def main():
    "Main method, never used by the Electricity Map backend, but handy for testing."
    from pprint import pprint

    pprint(fetch_consumption_forecast("US-CAL-BANC"))
    pprint(fetch_production("US-SEC"))
    pprint(fetch_production_mix("US-MIDW-GLHB"))
    pprint(fetch_consumption("US-MIDW-LGEE"))
    pprint(fetch_exchange("US-CAL-BANC", "US-NW-BPAT"))


if __name__ == "__main__":
    main()
