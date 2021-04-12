const fs = require('fs');

// https://stackoverflow.com/a/15030117/3218806
function flatten(arr) {
  return arr.reduce(function (flat, toFlatten) {
    return flat.concat(Array.isArray(toFlatten) ? flatten(toFlatten) : toFlatten);
  }, []);
}

function readNDJSON(path) {
  return fs.readFileSync(path, 'utf8').split('\n')
    .filter(d => d !== '')
    .map(JSON.parse);
}

const countryGeos = readNDJSON('./build/tmp_countries.json');
const stateGeos = readNDJSON('./build/tmp_states.json');
const thirdpartyGeos = readNDJSON('./build/tmp_thirdparty.json').concat([
    require('./third_party_maps/DK-DK2-without-BHM.json'),
    require('./third_party_maps/NO-NO1.json'),
    require('./third_party_maps/NO-NO2.json'),
    require('./third_party_maps/NO-NO3.json'),
    require('./third_party_maps/NO-NO4.json'),
    require('./third_party_maps/NO-NO5.json'),
    require('./third_party_maps/SE-SE1.json'),
    require('./third_party_maps/SE-SE2.json'),
    require('./third_party_maps/SE-SE3.json'),
    require('./third_party_maps/SE-SE4.json'),
    require('./third_party_maps/sct-no-islands.json'),
    JSON.parse(fs.readFileSync('./third_party_maps/JP-CB.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/JP-HR.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/JP-KN.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/JP-KY.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/JP-ON.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/JP-TK.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/ES-IB-FO.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/ES-IB-IZ.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/ES-IB-MA.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/ES-IB-ME.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/AUS-TAS.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/AUS-TAS-KI.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/AUS-TAS-FI.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/AUS-TAS-CBI.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/NZ-NZS.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/NZ-NZST.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/AUS-WA-RI.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/US-HI-HA.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/US-HI-MA.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/US-HI-KA.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/US-HI-KH.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/US-HI-LA.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/US-HI-MO.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/US-HI-NI.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/US-HI-OA.geojson')),
    JSON.parse(fs.readFileSync('./third_party_maps/CL-SEN.geojson')),
  ]);

const USSimplifiedGeos = [JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CAL-BANC.geojson'))].concat([//Balancing Authority Of Northern California
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CAL-CISO.geojson')), //California Independent System Operator
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CAL-IID.geojson')), //Imperial Irrigation District
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CAL-LDWP.geojson')), //Los Angeles Department Of Water And Power
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CAL-TIDC.geojson')), //Turlock Irrigation District
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CAR-CPLE.geojson')), //Duke Energy Progress East
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CAR-CPLW.geojson')), //Duke Energy Progress West
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CAR-DUK.geojson')), //Duke Energy Carolinas
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CAR-SC.geojson')), //South Carolina Public Service Authority
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CAR-SCEG.geojson')), //South Carolina Electric & Gas Company
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CAR-YAD.geojson')), //Alcoa Power Generating, Inc. - Yadkin Division
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CENT-SPA.geojson')), //Southwestern Power Administration
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-CENT-SWPP.geojson')), //Southwest Power Pool
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-FLA-FMPP.geojson')), //Florida Municipal Power Pool
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-FLA-FPC.geojson')), //Duke Energy Florida Inc
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-FLA-FPL.geojson')), //Florida Power & Light Company
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-FLA-GVL.geojson')), //Gainesville Regional Utilities
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-FLA-HST.geojson')), //City Of Homestead
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-FLA-JEA.geojson')), //Jea
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-FLA-NSB.geojson')), //New Smyrna Beach, Utilities Commission Of
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-FLA-SEC.geojson')), //Seminole Electric Cooperative
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-FLA-TAL.geojson')), //City Of Tallahassee
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-FLA-TEC.geojson')), //Tampa Electric Company
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-MIDA-OVEC.geojson')), //Ohio Valley Electric Corporation
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-MIDA-PJM.geojson')), //Pjm Interconnection, Llc
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-MIDW-AECI.geojson')), //Associated Electric Cooperative, Inc.
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-MIDW-EEI.geojson')), //Electric Energy, Inc.
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-MIDW-LGEE.geojson')), //Louisville Gas And Electric Company And Kentucky Utilities
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-MIDW-MISO.geojson')), //Midcontinent Independent Transmission System Operator, Inc..
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NE-ISNE.geojson')), //Iso New England Inc.
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-AVA.geojson')), //Avista Corporation
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-BPAT.geojson')), //Bonneville Power Administration
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-CHPD.geojson')), //Public Utility District No. 1 Of Chelan County
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-DOPD.geojson')), //Pud No. 1 Of Douglas County
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-GCPD.geojson')), //Public Utility District No. 2 Of Grant County, Washington
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-GRID.geojson')), //Gridforce Energy Management, Llc
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-GWA.geojson')), //Naturener Power Watch, Llc (Gwa)
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-IPCO.geojson')), //Idaho Power Company
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-NEVP.geojson')), //Nevada Power Company
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-NWMT.geojson')), //Northwestern Energy (Nwmt)
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-PACE.geojson')), //Pacificorp - East
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-PACW.geojson')), //Pacificorp - West
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-PGE.geojson')), //Portland General Electric Company
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-PSCO.geojson')), //Public Service Company Of Colorado
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-PSEI.geojson')), //Puget Sound Energy
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-SCL.geojson')), //Seattle City Light
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-TPWR.geojson')), //City Of Tacoma, Department Of Public Utilities, Light Division
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-WACM.geojson')), //Western Area Power Administration - Rocky Mountain Region
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-WAUW.geojson')), //Western Area Power Administration Ugp West
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NW-WWA.geojson')), //Naturener Wind Watch, Llc
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-NY-NYIS.geojson')), //New York Independent System Operator
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SE-AEC.geojson')), //Powersouth Energy Cooperative
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SE-SEPA.geojson')), //Southeastern Power Administration
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SE-SOCO.geojson')), //Southern Company Services, Inc. - Trans
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SW-AZPS.geojson')), //Arizona Public Service Company
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SW-DEAA.geojson')), //Arlington Valley, Llc - Avba
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SW-EPE.geojson')), //El Paso Electric Company
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SW-GRIF.geojson')), //Griffith Energy, Llc
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SW-GRMA.geojson')), //Gila River Power, Llc
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SW-HGMA.geojson')), //New Harquahala Generating Company, Llc - Hgba
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SW-PNM.geojson')), //Public Service Company Of New Mexico
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SW-SRP.geojson')), //Salt River Project
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SW-TEPC.geojson')), //Tucson Electric Power Company
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-SW-WALC.geojson')), //Western Area Power Administration - Desert Southwest Region
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-TEN-TVA.geojson')), //Tennessee Valley Authority
    JSON.parse(fs.readFileSync('./third_party_maps/US_simplified/US-TEX-ERCO.geojson')), //Electric Reliability Council Of Texas, Inc.
  ]);

const USOriginalGeos = [JSON.parse(fs.readFileSync('./third_party_maps/US/US-CAL-BANC.geojson'))].concat([//Balancing Authority Of Northern California
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CAL-CISO.geojson')), //California Independent System Operator
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CAL-IID.geojson')), //Imperial Irrigation District
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CAL-LDWP.geojson')), //Los Angeles Department Of Water And Power
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CAL-TIDC.geojson')), //Turlock Irrigation District
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CAR-CPLE.geojson')), //Duke Energy Progress East
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CAR-CPLW.geojson')), //Duke Energy Progress West
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CAR-DUK.geojson')), //Duke Energy Carolinas
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CAR-SC.geojson')), //South Carolina Public Service Authority
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CAR-SCEG.geojson')), //South Carolina Electric & Gas Company
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CAR-YAD.geojson')), //Alcoa Power Generating, Inc. - Yadkin Division
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CENT-SPA.geojson')), //Southwestern Power Administration
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-CENT-SWPP.geojson')), //Southwest Power Pool
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-FLA-FMPP.geojson')), //Florida Municipal Power Pool
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-FLA-FPC.geojson')), //Duke Energy Florida Inc
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-FLA-FPL.geojson')), //Florida Power & Light Company
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-FLA-GVL.geojson')), //Gainesville Regional Utilities
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-FLA-HST.geojson')), //City Of Homestead
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-FLA-JEA.geojson')), //Jea
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-FLA-NSB.geojson')), //New Smyrna Beach, Utilities Commission Of
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-FLA-SEC.geojson')), //Seminole Electric Cooperative
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-FLA-TAL.geojson')), //City Of Tallahassee
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-FLA-TEC.geojson')), //Tampa Electric Company
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-MIDA-OVEC.geojson')), //Ohio Valley Electric Corporation
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-MIDA-PJM.geojson')), //Pjm Interconnection, Llc
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-MIDW-AECI.geojson')), //Associated Electric Cooperative, Inc.
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-MIDW-EEI.geojson')), //Electric Energy, Inc.
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-MIDW-LGEE.geojson')), //Louisville Gas And Electric Company And Kentucky Utilities
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-MIDW-MISO.geojson')), //Midcontinent Independent Transmission System Operator, Inc..
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NE-ISNE.geojson')), //Iso New England Inc.
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-AVA.geojson')), //Avista Corporation
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-BPAT.geojson')), //Bonneville Power Administration
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-CHPD.geojson')), //Public Utility District No. 1 Of Chelan County
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-DOPD.geojson')), //Pud No. 1 Of Douglas County
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-GCPD.geojson')), //Public Utility District No. 2 Of Grant County, Washington
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-GRID.geojson')), //Gridforce Energy Management, Llc
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-GWA.geojson')), //Naturener Power Watch, Llc (Gwa)
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-IPCO.geojson')), //Idaho Power Company
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-NEVP.geojson')), //Nevada Power Company
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-NWMT.geojson')), //Northwestern Energy (Nwmt)
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-PACE.geojson')), //Pacificorp - East
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-PACW.geojson')), //Pacificorp - West
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-PGE.geojson')), //Portland General Electric Company
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-PSCO.geojson')), //Public Service Company Of Colorado
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-PSEI.geojson')), //Puget Sound Energy
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-SCL.geojson')), //Seattle City Light
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-TPWR.geojson')), //City Of Tacoma, Department Of Public Utilities, Light Division
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-WACM.geojson')), //Western Area Power Administration - Rocky Mountain Region
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-WAUW.geojson')), //Western Area Power Administration Ugp West
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NW-WWA.geojson')), //Naturener Wind Watch, Llc
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-NY-NYIS.geojson')), //New York Independent System Operator
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SE-AEC.geojson')), //Powersouth Energy Cooperative
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SE-SEPA.geojson')), //Southeastern Power Administration
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SE-SOCO.geojson')), //Southern Company Services, Inc. - Trans
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SW-AZPS.geojson')), //Arizona Public Service Company
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SW-DEAA.geojson')), //Arlington Valley, Llc - Avba
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SW-EPE.geojson')), //El Paso Electric Company
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SW-GRIF.geojson')), //Griffith Energy, Llc
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SW-GRMA.geojson')), //Gila River Power, Llc
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SW-HGMA.geojson')), //New Harquahala Generating Company, Llc - Hgba
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SW-PNM.geojson')), //Public Service Company Of New Mexico
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SW-SRP.geojson')), //Salt River Project
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SW-TEPC.geojson')), //Tucson Electric Power Company
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-SW-WALC.geojson')), //Western Area Power Administration - Desert Southwest Region
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-TEN-TVA.geojson')), //Tennessee Valley Authority
    JSON.parse(fs.readFileSync('./third_party_maps/US/US-TEX-ERCO.geojson')), //Electric Reliability Council Of Texas, Inc.
  ]);

function geomerge() {
  // Convert both into multipolygon
  const geos = Array.prototype.slice.call(arguments).filter(d => d != null);
  geos.forEach((geo) => {
    if (geo.geometry.type === 'Polygon') {
      geo.geometry = {
        type: 'MultiPolygon',
        coordinates: [geo.geometry.coordinates],
      };
    } else if (geo.geometry.type !== 'MultiPolygon') {
      throw new Error(`Unexpected geometry type '${geo.geometry.type}'`);
    }
  });
  // Merge both
  return {
    type: 'Feature',
    geometry: {
      type: 'MultiPolygon',
      coordinates: Array.prototype.concat(...geos.map(d => d.geometry.coordinates)),
    },
    properties: {},
  };
}

const zoneDefinitions = [
  // Map between "zones" iso_a2 and adm0_a3 in order to support XX, GB etc..
  // Note that the definition of "zones" is very vague here..
  // Specific case of Kosovo and Serbia: considered as a whole as long as they will be reported together in ENTSO-E.
  // Add moreDetails:true to use a smaller threshold for simplifying a zone thus the zone will have more details. More details also means bigger world.json so use with small zones.
  { zoneName:'XX', type:'country', id:'CYN'},

  // List of all zones
  { zoneName: 'AE', type: 'country', id: 'ARE'},
  { zoneName: 'AF', type: 'country', id: 'AFG'},
  { zoneName: 'AL', type: 'country', id: 'ALB'},
  { zoneName: 'AS', type: 'country', id: 'ASM'},
  { zoneName: 'AD', type: 'country', id: 'AND'},
  { zoneName: 'AO', type: 'country', id: 'AGO'},
  { zoneName: 'AG', type: 'country', id: 'ATG'},
  { zoneName: 'AI', type: 'country', id: 'AIA'},
  { zoneName: 'AN', type: 'country', id: 'ANT'},
  { zoneName: 'AR', type: 'country', id: 'ARG'},
  // { zoneName: 'AQ', type: 'country', id: 'AT},
  { zoneName: 'AM', type: 'country', id: 'ARM'},
  { zoneName: 'AT', type: 'country', id: 'AUT'},
  { zoneName: 'AUS-NSW', type: 'states', countryId: 'AUS', states: ['AU.NS', 'AU.AC']},
  { zoneName: 'AUS-NT', countryId: 'AUS', stateId: 'AU.NT', type: 'state' },
  // { zoneName: 'AU', type: 'country', id: 'AUS'},
  // { zoneName: 'AUS-ACT', countryId: 'AUS', stateId: 'AU.AC', type: 'state' },
  { zoneName: 'AUS-QLD', countryId: 'AUS', stateId: 'AU.QL', type: 'state' },
  { zoneName: 'AUS-SA', countryId: 'AUS', stateId: 'AU.SA', type: 'state' },
  // { zoneName: 'AUS-TAS', countryId: 'AUS', stateId: 'AU.TS', type: 'state' },
  { zoneName: 'AUS-TAS', type: 'subZone', id: 'AUS-TAS'},
  { zoneName: 'AUS-TAS-KI', type: 'subZone', id: 'AUS-TAS-KI'},
  { zoneName: 'AUS-TAS-FI', type: 'subZone', id: 'AUS-TAS-FI'},
  { zoneName: 'AUS-TAS-CBI', type: 'subZone', id: 'AUS-TAS-CBI'},
  { zoneName: 'AUS-VIC', countryId: 'AUS', stateId: 'AU.VI', type: 'state' },
  { zoneName: 'AUS-WA', countryId: 'AUS', stateId: 'AU.WA', type: 'state' },
  { zoneName: 'AUS-WA-RI', type: 'subZone', id: 'AUS-WA-RI', moreDetails: true},
  { zoneName: 'AW', type: 'country', id: 'ABW', moreDetails: true},
  { zoneName: 'AX', type: 'country', id: 'ALA'},
  { zoneName: 'AZ', type: 'administrations', administrations: ['AZE-1684', 'AZE-1676', 'AZE-1687', 'AZE-1678', 'AZE-1677', 'AZE-2419', 'AZE-2415', 'AZE-5567', 'AZE-2420', 'AZE-2423', 'AZE-2421', 'AZE-2418', 'AZE-1723', 'AZE-1731', 'AZE-1730', 'AZE-1729', 'AZE-1725', 'AZE-1727', 'AZE-1726', 'AZE-1724', 'AZE-1686', 'AZE-1704', 'AZE-1698', 'AZE-1700', 'AZE-1720', 'AZE-1709', 'AZE-1702', 'AZE-1697', 'AZE-1695', 'AZE-1701', 'AZE-1712', 'AZE-1719', 'AZE-1717', 'AZE-1689', 'AZE-1715', 'AZE-1710', 'AZE-1707', 'AZE-1708', 'AZE-5562', 'AZE-2422', 'AZE-1681', 'AZE-1694', 'AZE-1690', 'AZE-1680', 'AZE-1706', 'AZE-1721', 'AZE-1714', 'AZE-5563', 'AZE-1713', 'AZE-1696', 'AZE-1685', 'AZE-1693', 'AZE-1716', 'AZE-1728', 'AZE-1718', 'AZE-1711', 'AZE-1705', 'AZE-1688', 'AZE-1679', 'AZE-1683', 'AZE-1703', 'AZE-1692', 'AZE-1722', 'AZE-5566', 'AZE-5561', 'AZE-5564']},
  //{ zoneName: 'BA', type: 'country', id: 'BIH'},
  { zoneName: 'BA', type: 'administrations', administrations: [
      'BIH-4801', 'BIH-4802', 'BIH-2225', 'BIH-2224', 'BIH-2226', 'BIH-2227', 'BIH-2228', 'BIH-4807',
      'BIH-4808', 'BIH-4805', 'BIH-4806', 'BIH-2890', 'BIH-2891', 'BIH-2889', 'BIH-2887',
      'BIH-4804', 'BIH-3153', 'BIH-4803']},
  { zoneName: 'BB', type: 'country', id: 'BRB'},
  { zoneName: 'BD', type: 'country', id: 'BGD'},
  { zoneName: 'BE', type: 'country', id: 'BEL'},
  { zoneName: 'BH', type: 'country', id: 'BHR'},
  { zoneName: 'BJ', type: 'country', id: 'BEN'},
  { zoneName: 'BL', type: 'country', id: 'BLM'},
  { zoneName: 'BO', type: 'country', id: 'BOL'},
  { zoneName: 'BM', type: 'country', id: 'BMU'},
  //{ zoneName: 'BR', type: 'country', id: 'BRA'},
  { zoneName: 'BR-CS', type: 'states', countryId: 'BRA', states: ['BR.', 'BR.AC', 'BR.GO', 'BR.SP', 'BR.DF', 'BR.MS', 'BR.MG', 'BR.MT', 'BR.ES', 'BR.RJ', 'BR.RO']},
  { zoneName: 'BR-N', type: 'states', countryId: 'BRA', states: ['BR.AM', 'BR.PA', 'BR.TO', 'BR.RR', 'BR.AP']},
  { zoneName: 'BR-NE', type: 'states', countryId: 'BRA', states: ['BR.PE', 'BR.MA', 'BR.CE', 'BR.PI', 'BR.AL', 'BR.BA', 'BR.PB', 'BR.RN', 'BR.SE']},
  { zoneName: 'BR-S', type: 'states', countryId: 'BRA', states: ['BR.RS', 'BR.SC', 'BR.PR']},
  { zoneName: 'BS', type: 'country', id: 'BHS'},
  { zoneName: 'BT', type: 'country', id: 'BTN'},
  { zoneName: 'BV', type: 'country', id: 'BVT'},
  { zoneName: 'BW', type: 'country', id: 'BWA'},
  { zoneName: 'BY', type: 'country', id: 'BLR'},
  { zoneName: 'BZ', type: 'country', id: 'BLZ'},
  { zoneName: 'BN', type: 'country', id: 'BRN'},
  { zoneName: 'BG', type: 'country', id: 'BGR'},
  { zoneName: 'BF', type: 'country', id: 'BFA'},
  { zoneName: 'BI', type: 'country', id: 'BDI'},
  { zoneName: 'CA-AB', countryId: 'CAN', stateId: 'CA.AB', type: 'state' },
  // { zoneName: 'CA', type: 'country', id: 'CAN'},
  { zoneName: 'CA-BC', countryId: 'CAN', stateId: 'CA.BC', type: 'state' },
  { zoneName: 'CA-MB', countryId: 'CAN', stateId: 'CA.MB', type: 'state' },
  { zoneName: 'CA-NB', countryId: 'CAN', stateId: 'CA.NB', type: 'state' },
  // since 2002, ISO 3166-2 is "CA-NL", code_hasc in naturalearth is "CA.NF"
  { zoneName: 'CA-NL', countryId: 'CAN', stateId: 'CA.NF', type: 'state' },
  { zoneName: 'CA-NS', countryId: 'CAN', stateId: 'CA.NS', type: 'state' },
  { zoneName: 'CA-ON', countryId: 'CAN', stateId: 'CA.ON', type: 'state' },
  { zoneName: 'CA-PE', countryId: 'CAN', stateId: 'CA.PE', type: 'state' },
  { zoneName: 'CA-QC', countryId: 'CAN', stateId: 'CA.QC', type: 'state' },
  { zoneName: 'CA-SK', countryId: 'CAN', stateId: 'CA.SK', type: 'state' },
  { zoneName: 'CA-NT', countryId: 'CAN', stateId: 'CA.NT', type: 'state' },
  { zoneName: 'CA-NU', countryId: 'CAN', stateId: 'CA.NU', type: 'state' },
  { zoneName: 'CA-YT', countryId: 'CAN', stateId: 'CA.YT', type: 'state' },
  { zoneName: 'CC', type: 'country', id: 'CCK'},
  { zoneName: 'CF', type: 'country', id: 'CAF'},
  { zoneName: 'CG', type: 'country', id: 'COG'},
  { zoneName: 'CH', type: 'country', id: 'CHE'},
  { zoneName: 'CI', type: 'country', id: 'CIV'},
  //{ zoneName: 'CL-SING', type: 'states', countryId: 'CHL', states: ['CL.AP', 'CL.TA', 'CL.AN']},
  //{ zoneName: 'CL', type: 'country', id: 'CHL'},
  { zoneName: 'CL-SEN', type: 'subunits', subunits: ['CL-SEN']},
  { zoneName: 'CL-SEM', countryId: 'CHL', stateId: 'CL.MA', type: 'state' },
  { zoneName: 'CL-SEA', countryId: 'CHL', stateId: 'CL.AI', type: 'state' },
  { zoneName: 'CL-CHP', type: 'subunits', subunits: ['CHP']},
  { zoneName: 'CM', type: 'country', id: 'CMR'},
  { zoneName: 'CN', type: 'country', id: 'CHN'},
  { zoneName: 'CO', type: 'country', id: 'COL'},
  { zoneName: 'CV', type: 'country', id: 'CPV'},
  { zoneName: 'CX', type: 'country', id: 'CXR'},
  { zoneName: 'CD', type: 'country', id: 'COD'},
  { zoneName: 'CK', type: 'country', id: 'COK'},
  { zoneName: 'CR', type: 'country', id: 'CRI'},
  { zoneName: 'CU', type: 'country', id: 'CUB'},
  { zoneName: 'CY', type: 'country', id: 'CYP'},
  { zoneName: 'CZ', type: 'country', id: 'CZE'},
  { zoneName: 'DE', type: 'country', id: 'DEU'},
  { zoneName: 'DJ', type: 'country', id: 'DJI'},
  // { zoneName: 'DK', type: 'subunits', subunits: ['DNK']},
  { zoneName: 'DK-DK1', type: 'states', countryId: 'DNK', states: ['DK.MJ', 'DK.ND', 'DK.SD'] },
  { zoneName: 'DK-DK2', type: 'subZone', id: 'DK-DK2' },
  { zoneName: 'DK-BHM', type: 'subunits', subunits: ['DNB']},
  { zoneName: 'DM', type: 'country', id: 'DMA'},
  { zoneName: 'DO', type: 'country', id: 'DOM'},
  { zoneName: 'DZ', type: 'country', id: 'DZA'},
  { zoneName: 'EC', type: 'country', id: 'ECU'},
  { zoneName: 'EE', type: 'country', id: 'EST'},
  { zoneName: 'EG', type: 'country', id: 'EGY'},
  { zoneName: 'EH', type: 'country', id: 'ESH'},
  { zoneName: 'ER', type: 'country', id: 'ERI'},
  { zoneName: 'ES', type: 'subunits', subunits: ['ESX', 'SEC', 'SEM']}, //Spain Peninsula
  // spain canaries islands
  { zoneName: 'ES-CN-LP', type: 'country', id: 'La Palma'},
  { zoneName: 'ES-CN-HI', type: 'country', id: 'Hierro'},
  { zoneName: 'ES-CN-IG', type: 'country', id: 'Isla de la Gomera'},
  { zoneName: 'ES-CN-TE', type: 'country', id: 'Tenerife'},
  { zoneName: 'ES-CN-GC', type: 'country', id: 'Gran Canaria'},
  { zoneName: 'ES-CN-FVLZ', type: 'countries', countries: ['Fuerteventura', 'Lanzarote']},
  // { zoneName: 'ES-IB', type: 'subunits', subunits: ['ESI']}, //Spain Balearic islands
  { zoneName: 'ES-IB-FO', type: 'subZone', id: 'ES-IB-FO', moreDetails: true},
  { zoneName: 'ES-IB-IZ', type: 'subZone', id: 'ES-IB-IZ'},
  { zoneName: 'ES-IB-MA', type: 'subZone', id: 'ES-IB-MA'},
  { zoneName: 'ES-IB-ME', type: 'subZone', id: 'ES-IB-ME'},
  { zoneName: 'ET', type: 'country', id: 'ETH'},
  { zoneName: 'FI', type: 'country', id: 'FIN'},
  { zoneName: 'FJ', type: 'country', id: 'FJI'},
  { zoneName: 'FK', type: 'country', id: 'FLK'},
  { zoneName: 'FM', type: 'country', id: 'FSM'},
  // { zoneName: 'FR', type: 'country', id: 'FRA'},
  { zoneName: 'FO', type: 'country', id: 'FRO'},
  { zoneName: 'FR', type: 'subunits', subunits: ['FXX']},
  { zoneName: 'FR-COR', type: 'subunits', subunits: ['FXC']},
  { zoneName: 'GA', type: 'country', id: 'GAB'},
  // see https://github.com/tmrowco/electricitymap-contrib/pull/1615 for how SCT-no-islands is generated
  { zoneName: 'GB', type: 'subunits', subunits: ['SCT-no-islands', 'ENG', 'WLS']},
  { zoneName: 'GB-NIR', type: 'subunits', subunits: ['NIR']},
  { zoneName: 'GB-ORK', type: 'administrations', administrations: ['GBR-2744']},
  { zoneName: 'GB-SHI', type: 'administrations', administrations: ['GBR-2747']},
  { zoneName: 'GD', type: 'country', id: 'GRD'},
  { zoneName: 'GE', type: 'country', id: 'GEO'},
  { zoneName: 'GF', type: 'country', id: 'GUF'},
  { zoneName: 'GG', type: 'country', id: 'GGY'},
  { zoneName: 'GH', type: 'country', id: 'GHA'},
  { zoneName: 'GI', type: 'country', id: 'GIB'},
  { zoneName: 'GL', type: 'country', id: 'GRL'},
  { zoneName: 'GM', type: 'country', id: 'GMB'},
  { zoneName: 'GN', type: 'country', id: 'GIN'},
  { zoneName: 'GP', type: 'country', id: 'GLP'},
  { zoneName: 'GQ', type: 'country', id: 'GNQ'},
  // { zoneName: 'GR', type: 'country', id: 'GRC'},
  { zoneName: 'GR', type: 'states', countryId: 'GRC', states: ['GR.AT', 'GR.EP', 'GR.GC','GR.GW',
      'GR.II', 'GR.MA', 'GR.MC', 'GR.MT', 'GR.MW', 'GR.PP', 'GR.TS']},
  { zoneName: 'GR-IS', type: 'states', countryId: 'GRC', states: ['GR.AN', 'GR.AS', 'GR.CR']},
  { zoneName: 'GS', type: 'country', id: 'SGS' },
  { zoneName: 'GT', type: 'country', id: 'GTM' },
  { zoneName: 'GU', type: 'country', id: 'GUM' },
  { zoneName: 'GW', type: 'country', id: 'GNB' },
  { zoneName: 'GY', type: 'country', id: 'GUY' },
  { zoneName: 'HK', type: 'country', id: 'HKG' },
  { zoneName: 'HM', type: 'country', id: 'HMD' },
  { zoneName: 'HN', type: 'country', id: 'HND' },
  { zoneName: 'HT', type: 'country', id: 'HTI' },
  { zoneName: 'HU', type: 'country', id: 'HUN' },
  { zoneName: 'HR', type: 'country', id: 'HRV' },
  { zoneName: 'ID', type: 'country', id: 'IDN' },
  { zoneName: 'IE', type: 'country', id: 'IRL' },
  { zoneName: 'IL', type: 'country', id: 'ISR' },
  { zoneName: 'IM', type: 'country', id: 'IMN' },
  // TODO: Use iso_3166_2 field instead
  { zoneName: 'IN-AN', countryId: 'IND', stateId: 'IN.AN', useMaybe: true, type: 'state' },
  { zoneName: 'IN-AP', countryId: 'IND', stateId: 'IN.AD', useMaybe: true, type: 'state' },
  { zoneName: 'IN-AR', countryId: 'IND', stateId: 'IN.AR', useMaybe: true, type: 'state' },
  { zoneName: 'IN-AS', countryId: 'IND', stateId: 'IN.AS', useMaybe: true, type: 'state' },
  { zoneName: 'IN-BR', countryId: 'IND', stateId: 'IN.BR', useMaybe: true, type: 'state' },
  { zoneName: 'IN-CT', countryId: 'IND', stateId: 'IN.CT', useMaybe: true, type: 'state' },
  { zoneName: 'IN-CH', countryId: 'IND', stateId: 'IN.CH', useMaybe: true, type: 'state' },
  { zoneName: 'IN-DD', countryId: 'IND', stateId: 'IN.DD', useMaybe: true, type: 'state' },
  { zoneName: 'IN-DN', countryId: 'IND', stateId: 'IN.DN', useMaybe: true, type: 'state' },
  { zoneName: 'IN-DL', countryId: 'IND', stateId: 'IN.DL', useMaybe: true, type: 'state' },
  { zoneName: 'IN-GA', countryId: 'IND', stateId: 'IN.GA', useMaybe: true, type: 'state' },
  // For some reason IN.GJ is not a code_hasc in database, use FIPS code instead.
  // { zoneName: 'IN-GJ', countryId: 'IND', stateId: 'IN.GJ', useMaybe: true, type: 'state' },
  { zoneName: 'IN-GJ', type: 'fips', fips:['IND', 'IN32']},
  { zoneName: 'IN-HR', countryId: 'IND', stateId: 'IN.HR', useMaybe: true, type: 'state' },
  { zoneName: 'IN-HP', countryId: 'IND', stateId: 'IN.HP', useMaybe: true, type: 'state' },
  { zoneName: 'IN-JK', countryId: 'IND', stateId: 'IN.JK', useMaybe: true, type: 'state' },
  { zoneName: 'IN-JH', countryId: 'IND', stateId: 'IN.JH', useMaybe: true, type: 'state' },
  { zoneName: 'IN-KA', countryId: 'IND', stateId: 'IN.KA', useMaybe: true, type: 'state' },
  { zoneName: 'IN-KL', countryId: 'IND', stateId: 'IN.KL', useMaybe: true, type: 'state' },
  { zoneName: 'IN-LD', countryId: 'IND', stateId: 'IN.LD', useMaybe: true, type: 'state' },
  { zoneName: 'IN-MP', countryId: 'IND', stateId: 'IN.MP', useMaybe: false, type: 'state' },
  { zoneName: 'IN-MH', countryId: 'IND', stateId: 'IN.MH', useMaybe: true, type: 'state' },
  { zoneName: 'IN-MN', countryId: 'IND', stateId: 'IN.MN', useMaybe: true, type: 'state' },
  { zoneName: 'IN-ML', countryId: 'IND', stateId: 'IN.ML', useMaybe: true, type: 'state' },
  { zoneName: 'IN-MZ', countryId: 'IND', stateId: 'IN.MZ', useMaybe: true, type: 'state' },
  { zoneName: 'IN-NL', countryId: 'IND', stateId: 'IN.NL', useMaybe: true, type: 'state' },
  { zoneName: 'IN-OR', countryId: 'IND', stateId: 'IN.OR', useMaybe: true, type: 'state' },
  { zoneName: 'IN-PB', countryId: 'IND', stateId: 'IN.PB', useMaybe: true, type: 'state' },
  { zoneName: 'IN-PY', countryId: 'IND', stateId: 'IN.PY', useMaybe: true, type: 'state' },
  { zoneName: 'IN-RJ', countryId: 'IND', stateId: 'IN.RJ', useMaybe: true, type: 'state' },
  { zoneName: 'IN-SK', countryId: 'IND', stateId: 'IN.SK', useMaybe: true, type: 'state' },
  { zoneName: 'IN-TN', countryId: 'IND', stateId: 'IN.TN', useMaybe: true, type: 'state' },
  { zoneName: 'IN-TG', countryId: 'IND', stateId: 'IN.TG', useMaybe: true, type: 'state' },
  { zoneName: 'IN-TR', countryId: 'IND', stateId: 'IN.TR', useMaybe: true, type: 'state' },
  { zoneName: 'IN-UT', countryId: 'IND', stateId: 'IN.UT', useMaybe: true, type: 'state' },
  { zoneName: 'IN-UP', countryId: 'IND', stateId: 'IN.UP', useMaybe: true, type: 'state' },
  { zoneName: 'IN-WB', countryId: 'IND', stateId: 'IN.WB', useMaybe: true, type: 'state' },
  { zoneName: 'IO', type: 'country', id: 'IOT'},
  { zoneName: 'IQ', type: 'subunits', subunits: ['IRR']},
  { zoneName: 'IQ-KUR', type: 'subunits', subunits: ['IRK']},
  { zoneName: 'IR', type: 'country', id: 'IRN'},
  { zoneName: 'IS', type: 'country', id: 'ISL'},
  // { zoneName: 'IT', type: 'country', id: 'ITA'},
  { zoneName: 'IT-CNO', type: 'region_cod', region_cod: ['IT-57', 'IT-52', 'IT-55'] },
  { zoneName: 'IT-CSO', type: 'region_cod', region_cod: ['IT-65', 'IT-72', 'IT-62'] },
  { zoneName: 'IT-NO', type: 'region_cod',
    region_cod: ['IT-45', 'IT-36', 'IT-42', 'IT-25', 'IT-21', 'IT-32', 'IT-23', 'IT-34'],
  },
  { zoneName: 'IT-SAR', type: 'region_cod', region_cod: ['IT-88'] },
  { zoneName: 'IT-SIC', type: 'region_cod', region_cod: ['IT-82'] },
  { zoneName: 'IT-SO', type: 'region_cod', region_cod: ['IT-75', 'IT-77', 'IT-78', 'IT-67'] },
  { zoneName: 'JE', type: 'country', id: 'JEY'},
  { zoneName: 'JM', type: 'country', id: 'JAM'},
  //{ zoneName: 'JP', type: 'country', id: 'JPN'},
  { zoneName: 'JP-CB', type: 'subZone', id: 'JP-CB' },
  { zoneName: 'JP-CG', type: 'administrations', administrations: [
    'JPN-1824', 'JPN-1826', 'JPN-1825', 'JPN-1822', 'JPN-1821'] },
  { zoneName: 'JP-HKD', type: 'administrations', administrations: ['JPN-1847'] },
  { zoneName: 'JP-HR', type: 'subZone', id: 'JP-HR' },
  { zoneName: 'JP-KN', type: 'subZone', id: 'JP-KN' },
  { zoneName: 'JP-KY', type: 'subZone', id: 'JP-KY' },
  { zoneName: 'JP-ON', type: 'subZone', id: 'JP-ON' },
  { zoneName: 'JP-SK', type: 'administrations', administrations: [
    'JPN-1836', 'JPN-1833', 'JPN-1832', 'JPN-1834'] },
  { zoneName: 'JP-TH', type: 'administrations', administrations: [
    'JPN-1867', 'JPN-1868', 'JPN-1862', 'JPN-1863', 'JPN-1865', 'JPN-1866', 'JPN-1864'] },
  { zoneName: 'JP-TK', type: 'subZone', id: 'JP-TK' },
  { zoneName: 'JO', type: 'country', id: 'JOR'},
  { zoneName: 'KE', type: 'country', id: 'KEN'},
  { zoneName: 'KG', type: 'country', id: 'KGZ'},
  { zoneName: 'KH', type: 'country', id: 'KHM'},
  { zoneName: 'KI', type: 'country', id: 'KIR'},
  { zoneName: 'KM', type: 'country', id: 'COM'},
  { zoneName: 'KN', type: 'country', id: 'KNA'},
  { zoneName: 'KP', type: 'country', id: 'PRK'},
  { zoneName: 'KR', type: 'country', id: 'KOR'},
  { zoneName: 'KW', type: 'country', id: 'KWT'},
  { zoneName: 'KY', type: 'country', id: 'CYM'},
  { zoneName: 'KZ', type: 'countries', countries: ['KAZ', 'KAB']},
  { zoneName: 'LA', type: 'country', id: 'LAO'},
  { zoneName: 'LB', type: 'country', id: 'LBN'},
  { zoneName: 'LC', type: 'country', id: 'LCA'},
  { zoneName: 'LK', type: 'country', id: 'LKA'},
  { zoneName: 'LI', type: 'country', id: 'LIE'},
  { zoneName: 'LR', type: 'country', id: 'LBR'},
  { zoneName: 'LS', type: 'country', id: 'LSO'},
  { zoneName: 'LT', type: 'country', id: 'LTU'},
  { zoneName: 'LU', type: 'country', id: 'LUX'},
  { zoneName: 'LV', type: 'country', id: 'LVA'},
  { zoneName: 'LY', type: 'country', id: 'LBY'},
  { zoneName: 'MA', type: 'country', id: 'MAR'},
  { zoneName: 'ME', type: 'country', id: 'MNE'},
  { zoneName: 'MF', type: 'country', id: 'MAF'},
  { zoneName: 'MC', type: 'country', id: 'MCO'},
  { zoneName: 'MD', type: 'country', id: 'MDA'},
  { zoneName: 'MG', type: 'country', id: 'MDG'},
  { zoneName: 'MH', type: 'country', id: 'MHL'},
  { zoneName: 'MK', type: 'country', id: 'MKD'},
  { zoneName: 'ML', type: 'country', id: 'MLI'},
  { zoneName: 'MM', type: 'country', id: 'MMR'},
  { zoneName: 'MN', type: 'country', id: 'MNG'},
  { zoneName: 'MO', type: 'country', id: 'MAC'},
  { zoneName: 'MP', type: 'country', id: 'MNP'},
  { zoneName: 'MV', type: 'country', id: 'MDV'},
  { zoneName: 'MT', type: 'country', id: 'MLT'},
  { zoneName: 'MQ', type: 'country', id: 'MTQ'},
  { zoneName: 'MR', type: 'country', id: 'MRT'},
  { zoneName: 'MS', type: 'country', id: 'MSR'},
  { zoneName: 'MU', type: 'country', id: 'MUS'},
  // { zoneName: 'MX', type: 'country', id: 'MEX'},
  // { zoneName: 'MX', type: 'administrations', administrations: [
  //   'MEX-2714', 'MEX-2716', 'MEX-2713', 'MEX-2715',
  //   'MEX-2734', 'MEX-2721', 'MEX-2719', 'MEX-2717', 'MEX-2728', 'MEX-2728', 'MEX-2733','MEX-2730',
  //   'MEX-2724', 'MEX-2726', 'MEX-2731', 'MEX-2718', 'MEX-2720', 'MEX-2727', 'MEX-2732', 'MEX-2724',
  //   'MEX-2729', 'MEX-2723', 'MEX-2735', 'MEX-2725', 'MEX-2722', 'MEX-2737', 'MEX-2736']},
  { zoneName: 'MX-BC', type: 'administrations', administrations: ['MEX-2706', 'MEX-2707']},
  { zoneName: 'MX-CE', type: 'administrations', administrations: ['MEX-2724', 'MEX-2726', 'MEX-2727', 'MEX-2732']},
  { zoneName: 'MX-NW', type: 'administrations', administrations: ['MEX-2711', 'MEX-2712']},
  { zoneName: 'MX-NO', type: 'administrations', administrations: ['MEX-2708', 'MEX-2709', 'MEX-2710']},
  { zoneName: 'MX-NE', type: 'administrations', administrations: ['MEX-2714', 'MEX-2716']},
  { zoneName: 'MX-OC', type: 'administrations', administrations: ['MEX-2713', 'MEX-2715', 'MEX-2717', 'MEX-2718', 'MEX-2719', 'MEX-2720', 'MEX-2721', 'MEX-2728', 'MEX-2730', 'MEX-2731', 'MEX-2733']},
  { zoneName: 'MX-OR', type: 'administrations', administrations: ['MEX-2723', 'MEX-2725', 'MEX-2729', 'MEX-2734', 'MEX-2735']},
  { zoneName: 'MX-PN', type: 'administrations', administrations: ['MEX-2722', 'MEX-2736', 'MEX-2737']},
  // { zoneName: 'MY', type: 'country', id: 'MYS'},
  { zoneName: 'MW', type: 'country', id: 'MWI'},
  { zoneName: 'MY-EM', type: 'administrations', administrations: ['MYS-1186', 'MYS-1187']},
  { zoneName: 'MY-WM', type: 'administrations', administrations: [
      'MYS-1141', 'MYS-1140', 'MYS-1139', 'MYS-1137', 'MYS-1144', 'MYS-1149', 'MYS-1147', 'MYS-1148',
      'MYS-4831', 'MYS-4832', 'MYS-1146', 'MYS-1145', 'MYS-1143']},
  { zoneName: 'MZ', type: 'country', id: 'MOZ'},
  { zoneName: 'NA', type: 'country', id: 'NAM'},
  { zoneName: 'NC', type: 'country', id: 'NCL'},
  { zoneName: 'NE', type: 'country', id: 'NER'},
  { zoneName: 'NF', type: 'country', id: 'NFK'},
  { zoneName: 'NG', type: 'country', id: 'NGA'},
  { zoneName: 'NI', type: 'country', id: 'NIC'},
  { zoneName: 'NKR', type: 'administrations', administrations: ['AZE-1691', 'AZE-1699', 'AZE-1682', 'AZE-1735', 'AZE-1736', 'AZE-1737', 'AZE-5565', 'AZE-1738', 'AZE-4838', 'AZE-1739', 'AZE-1734', 'AZE-1740']},
  { zoneName: 'NL', type: 'country', id: 'NLD'},
  // { zoneName: 'NO', type: 'country', id: 'NOR'},
  { zoneName: 'NO-NO1', type: 'subZone', id: 'NO-NO1' },
  { zoneName: 'NO-NO2', type: 'subZone', id: 'NO-NO2' },
  { zoneName: 'NO-NO3', type: 'subZone', id: 'NO-NO3' },
  { zoneName: 'NO-NO4', type: 'subZone', id: 'NO-NO4' },
  { zoneName: 'NO-NO5', type: 'subZone', id: 'NO-NO5' },
  { zoneName: 'NP', type: 'country', id: 'NPL'},
  { zoneName: 'NU', type: 'country', id: 'NIU'},
  { zoneName: 'NR', type: 'country', id: 'NRU'},
  // { zoneName: 'NZ', type: 'country', id: 'NZL'},
  { zoneName: 'NZ-NZA', type: 'subunits', subunits: ['NZA']},
  { zoneName: 'NZ-NZC', type: 'subunits', subunits: ['NZC']},
  { zoneName: 'NZ-NZN', type: 'subunits', subunits: ['NZN']},
  { zoneName: 'NZ-NZS', type: 'subunits', subunits: ['NZS-without-nzst']},
  { zoneName: 'NZ-NZST', type: 'subunits', subunits: ['NZST']},
  { zoneName: 'OM', type: 'country', id: 'OMN'},
  { zoneName: 'PA', type: 'country', id: 'PAN'},
  { zoneName: 'PE', type: 'country', id: 'PER'},
  { zoneName: 'PF', type: 'country', id: 'PYF'},
  { zoneName: 'PG', type: 'country', id: 'PNG'},
  { zoneName: 'PM', type: 'country', id: 'SPM'},
  { zoneName: 'PK', type: 'country', id: 'PAK'},
  { zoneName: 'PH', type: 'country', id: 'PHL'},
  { zoneName: 'PL', type: 'country', id: 'POL'},
  { zoneName: 'PN', type: 'country', id: 'PCN'},
  { zoneName: 'PR', type: 'country', id: 'PRI'}, // Puerto Rico Electric Power Authority
  { zoneName: 'PS', type: 'country', id: 'PSX'},
  { zoneName: 'PT', type: 'subunits', subunits: ['PRX']}, // Portugal Mainland,
  { zoneName: 'PT-MA', type: 'subunits', subunits: ['PMD']}, // Madeira Island,
  { zoneName: 'PT-AC', type: 'subunits', subunits: ['PAZ']}, // Azores Islands,
  { zoneName: 'PW', type: 'country', id: 'PLW'},
  { zoneName: 'PY', type: 'country', id: 'PRY'},
  { zoneName: 'QA', type: 'country', id: 'QAT'},
  { zoneName: 'RE', type: 'country', id: 'REU'},
  { zoneName: 'RO', type: 'country', id: 'ROU'},
  { zoneName: 'RS', type: 'country', id: 'SRB'},
  //{ zoneName: 'RU', type: 'administrations', administrations: [
  //  'RUS-2280', 'RUS-2416', 'RUS-3200', 'RUS-2356', 'RUS-2359', 'RUS-2343', 'RUS-2377', 'RUS-2397',
  //  'RUS-2366', 'RUS-2391', 'RUS-2167', 'RUS-2603', 'RUS-2401', 'RUS-2360', 'RUS-2602', 'RUS-2385',
  //  'RUS-2365', 'RUS-2375', 'RUS-2358', 'RUS-2334', 'RUS-2403', 'RUS-2305', 'RUS-2368', 'RUS-2388',
  //  'RUS-2605', 'RUS-2357', 'RUS-2361', 'RUS-2342', 'RUS-2373', 'RUS-2371', 'RUS-2610', 'RUS-2379',
  //  'RUS-2400', 'RUS-2303', 'RUS-2390', 'RUS-2382', 'RUS-2304', 'RUS-2389', 'RUS-2336', 'RUS-2386',
  //  'RUS-2376', 'RUS-2394', 'RUS-2395', 'RUS-2363', 'RUS-2398', 'RUS-2380', 'RUS-2370', 'RUS-2417',
  //  'RUS-2372', 'RUS-2392', 'RUS-2378', 'RUS-2402', 'RUS-2333', 'RUS-2362', 'RUS-2399',
  //  'RUS-2387', 'RUS-2396', 'RUS-2337', 'RUS-2367', 'RUS-2606', 'RUS-2364', 'RUS-2306',
  //  'RUS-2374', 'RUS-2353', 'RUS-2355', 'RUS-2384', 'RUS-2393', 'RUS-2335', 'RUS-2369', 'RUS-2279']},
  { zoneName: 'RU-1', type: 'administrations', administrations: [
    'RUS-2280', 'RUS-2416', 'RUS-3200', 'RUS-2356', 'RUS-2359', 'RUS-2343', 'RUS-2377', 'RUS-2366',
    'RUS-2391', 'RUS-2360', 'RUS-2385', 'RUS-2365', 'RUS-2375', 'RUS-2358', 'RUS-2334', 'RUS-2305',
    'RUS-2368', 'RUS-2388', 'RUS-2357', 'RUS-2361', 'RUS-2342', 'RUS-2373', 'RUS-2371', 'RUS-2379',
    'RUS-2303', 'RUS-2390', 'RUS-2382', 'RUS-2304', 'RUS-2389', 'RUS-2336', 'RUS-2386', 'RUS-2376',
    'RUS-2394', 'RUS-2395', 'RUS-2363', 'RUS-2398', 'RUS-2380', 'RUS-2370', 'RUS-2417', 'RUS-2372',
    'RUS-2392', 'RUS-2378', 'RUS-2333', 'RUS-2362', 'RUS-2387', 'RUS-2396', 'RUS-2337', 'RUS-2367',
    'RUS-2364', 'RUS-2306', 'RUS-2374', 'RUS-2353', 'RUS-2355', 'RUS-2384', 'RUS-2393', 'RUS-2335',
    'RUS-2369', 'RUS-2279']},
  { zoneName: 'RU-2', type: 'administrations', administrations: [
    'RUS-2400', 'RUS-2606', 'RUS-2605', 'RUS-2610', 'RUS-2397', 'RUS-2403',
    'RUS-2399', 'RUS-2603', 'RUS-2167', 'RUS-2401', 'RUS-2602', 'RUS-2402']},
  { zoneName: 'RU-EU', type: 'administrations', administrations: ['RUS-2354', 'RUS-2383', 'RUS-2381']},
  { zoneName: 'RU-AS', type: 'administrations', administrations: ['RUS-2321', 'RUS-2609', 'RUS-2611', 'RUS-2612', 'RUS-2613', 'RUS-2614', 'RUS-2615', 'RUS-2616', 'RUS-3468']},
  { zoneName: 'RU-KGD', type: 'administrations', administrations: ['RUS-2324']},
  { zoneName: 'RW', type: 'country', id: 'RWA'},
  { zoneName: 'SA', type: 'country', id: 'SAU'},
  { zoneName: 'SB', type: 'country', id: 'SLB'},
  { zoneName: 'SC', type: 'country', id: 'SYC'},
  { zoneName: 'SD', type: 'country', id: 'SDN'},
  { zoneName: 'SE', type: 'country', id: 'SWE'},
  // { zoneName: 'SE-SE1', type: 'subZone', id: 'SE-SE1' },
  // { zoneName: 'SE-SE2', type: 'subZone', id: 'SE-SE2' },
  // { zoneName: 'SE-SE3', type: 'subZone', id: 'SE-SE3' },
  // { zoneName: 'SE-SE4', type: 'subZone', id: 'SE-SE4' },
  { zoneName: 'SG', type: 'country', id: 'SGP'},
  { zoneName: 'SH', type: 'country', id: 'SHN'},
  { zoneName: 'SI', type: 'country', id: 'SVN'},
  { zoneName: 'SJ', type: 'country', id: 'SJM'},
  { zoneName: 'SK', type: 'country', id: 'SVK'},
  { zoneName: 'SL', type: 'country', id: 'SLE'},
  { zoneName: 'SM', type: 'country', id: 'SMR'},
  { zoneName: 'SN', type: 'country', id: 'SEN'},
  { zoneName: 'SO', type: 'countries', countries: ['SOL', 'SOM']},
  { zoneName: 'SR', type: 'country', id: 'SUR'},
  { zoneName: 'SS', type: 'country', id: 'SSD'},
  { zoneName: 'ST', type: 'country', id: 'STP'},
  { zoneName: 'SV', type: 'country', id: 'SLV'},
  { zoneName: 'SY', type: 'country', id: 'SYR'},
  { zoneName: 'SZ', type: 'country', id: 'SWZ'},
  { zoneName: 'TC', type: 'country', id: 'TCA'},
  { zoneName: 'TD', type: 'country', id: 'TCD'},
  { zoneName: 'TF', type: 'country', id: 'ATF'},
  { zoneName: 'TG', type: 'country', id: 'TGO'},
  { zoneName: 'TH', type: 'country', id: 'THA'},
  { zoneName: 'TJ', type: 'country', id: 'TJK'},
  { zoneName: 'TK', type: 'country', id: 'TKL'},
  { zoneName: 'TL', type: 'country', id: 'TLS'},
  { zoneName: 'TO', type: 'country', id: 'TON'},
  { zoneName: 'TM', type: 'country', id: 'TKM'},
  { zoneName: 'TN', type: 'country', id: 'TUN'},
  { zoneName: 'TR', type: 'country', id: 'TUR'},
  { zoneName: 'TT', type: 'country', id: 'TTO'},
  { zoneName: 'TV', type: 'country', id: 'TUV'},
  { zoneName: 'TW', type: 'country', id: 'TWN'},
  { zoneName: 'TZ', type: 'country', id: 'TZA'},
  { zoneName: 'UA', type: 'country', id: 'UKR'},
  // Crimea
  { zoneName: 'UA-CR', type: 'administrations', administrations: ['RUS-283', 'RUS-5482']},
  { zoneName: 'UG', type: 'country', id: 'UGA'},
  { zoneName: 'UM', type: 'country', id: 'UMI'},
  { zoneName: 'US-AK', countryId: 'USA', stateId: 'US.AK', type: 'state' }, //Alaska
  { zoneName: 'US-CAL-BANC', type: 'subZone', countryId: 'USA', id: 'US-CAL-BANC' }, //Balancing Authority Of Northern California
  { zoneName: 'US-CAL-CISO', type: 'subZone', countryId: 'USA', id: 'US-CAL-CISO' }, //California Independent System Operator
  { zoneName: 'US-CAL-IID', type: 'subZone', countryId: 'USA', id: 'US-CAL-IID' }, //Imperial Irrigation District
  { zoneName: 'US-CAL-LDWP', type: 'subZone', countryId: 'USA', id: 'US-CAL-LDWP' }, //Los Angeles Department Of Water And Power
  { zoneName: 'US-CAL-TIDC', type: 'subZone', countryId: 'USA', id: 'US-CAL-TIDC' }, //Turlock Irrigation District
  { zoneName: 'US-CAR-CPLE', type: 'subZone', countryId: 'USA', id: 'US-CAR-CPLE' }, //Duke Energy Progress East
  { zoneName: 'US-CAR-CPLW', type: 'subZone', countryId: 'USA', id: 'US-CAR-CPLW' }, //Duke Energy Progress West
  { zoneName: 'US-CAR-DUK', type: 'subZone', countryId: 'USA', id: 'US-CAR-DUK' }, //Duke Energy Carolinas
  { zoneName: 'US-CAR-SC', type: 'subZone', countryId: 'USA', id: 'US-CAR-SC' }, //South Carolina Public Service Authority
  { zoneName: 'US-CAR-SCEG', type: 'subZone', countryId: 'USA', id: 'US-CAR-SCEG' }, //South Carolina Electric & Gas Company
  { zoneName: 'US-CAR-YAD', type: 'subZone', countryId: 'USA', id: 'US-CAR-YAD' }, //Alcoa Power Generating, Inc. - Yadkin Division
  { zoneName: 'US-CENT-SPA', type: 'subZone', countryId: 'USA', id: 'US-CENT-SPA' }, //Southwestern Power Administration
  { zoneName: 'US-CENT-SWPP', type: 'subZone', countryId: 'USA', id: 'US-CENT-SWPP' }, //Southwest Power Pool
  { zoneName: 'US-FLA-FMPP', type: 'subZone', countryId: 'USA', id: 'US-FLA-FMPP' }, //Florida Municipal Power Pool
  { zoneName: 'US-FLA-FPC', type: 'subZone', countryId: 'USA', id: 'US-FLA-FPC' }, //Duke Energy Florida Inc
  { zoneName: 'US-FLA-FPL', type: 'subZone', countryId: 'USA', id: 'US-FLA-FPL' }, //Florida Power & Light Company
  { zoneName: 'US-FLA-GVL', type: 'subZone', countryId: 'USA', id: 'US-FLA-GVL' }, //Gainesville Regional Utilities
  { zoneName: 'US-FLA-HST', type: 'subZone', countryId: 'USA', id: 'US-FLA-HST' }, //City Of Homestead
  { zoneName: 'US-FLA-JEA', type: 'subZone', countryId: 'USA', id: 'US-FLA-JEA' }, //Jea
  { zoneName: 'US-FLA-NSB', type: 'subZone', countryId: 'USA', id: 'US-FLA-NSB' }, //New Smyrna Beach, Utilities Commission Of
  { zoneName: 'US-FLA-SEC', type: 'subZone', countryId: 'USA', id: 'US-FLA-SEC' }, //Seminole Electric Cooperative
  { zoneName: 'US-FLA-TAL', type: 'subZone', countryId: 'USA', id: 'US-FLA-TAL' }, //City Of Tallahassee
  { zoneName: 'US-FLA-TEC', type: 'subZone', countryId: 'USA', id: 'US-FLA-TEC' }, //Tampa Electric Company
  { zoneName: 'US-HI-HA', type: 'subZone', id: 'US-HI-HA'}, //Hawaii
  { zoneName: 'US-HI-KA', type: 'subZone', id: 'US-HI-KA'},
  { zoneName: 'US-HI-KH', type: 'subZone', id: 'US-HI-KH', moreDetails: true},
  { zoneName: 'US-HI-LA', type: 'subZone', id: 'US-HI-LA'},
  { zoneName: 'US-HI-MA', type: 'subZone', id: 'US-HI-MA'},
  { zoneName: 'US-HI-MO', type: 'subZone', id: 'US-HI-MO'},
  { zoneName: 'US-HI-NI', type: 'subZone', id: 'US-HI-NI'},
  { zoneName: 'US-HI-OA', type: 'subZone', id: 'US-HI-OA'},
  { zoneName: 'US-MIDA-OVEC', type: 'subZone', countryId: 'USA', id: 'US-MIDA-OVEC' }, //Ohio Valley Electric Corporation
  { zoneName: 'US-MIDA-PJM', type: 'subZone', countryId: 'USA', id: 'US-MIDA-PJM' }, //Pjm Interconnection, Llc
  { zoneName: 'US-MIDW-AECI', type: 'subZone', countryId: 'USA', id: 'US-MIDW-AECI' }, //Associated Electric Cooperative, Inc.
  { zoneName: 'US-MIDW-EEI', type: 'subZone', countryId: 'USA', id: 'US-MIDW-EEI' }, //Electric Energy, Inc.
  { zoneName: 'US-MIDW-LGEE', type: 'subZone', countryId: 'USA', id: 'US-MIDW-LGEE' }, //Louisville Gas And Electric Company And Kentucky Utilities
  { zoneName: 'US-MIDW-MISO', type: 'subZone', countryId: 'USA', id: 'US-MIDW-MISO' }, //Midcontinent Independent Transmission System Operator, Inc..
  { zoneName: 'US-NE-ISNE', type: 'subZone', countryId: 'USA', id: 'US-NE-ISNE' }, //Iso New England Inc.
  { zoneName: 'US-NW-AVA', type: 'subZone', countryId: 'USA', id: 'US-NW-AVA' }, //Avista Corporation
  { zoneName: 'US-NW-BPAT', type: 'subZone', countryId: 'USA', id: 'US-NW-BPAT' }, //Bonneville Power Administration
  { zoneName: 'US-NW-CHPD', type: 'subZone', countryId: 'USA', id: 'US-NW-CHPD' }, //Public Utility District No. 1 Of Chelan County
  { zoneName: 'US-NW-DOPD', type: 'subZone', countryId: 'USA', id: 'US-NW-DOPD' }, //Pud No. 1 Of Douglas County
  { zoneName: 'US-NW-GCPD', type: 'subZone', countryId: 'USA', id: 'US-NW-GCPD' }, //Public Utility District No. 2 Of Grant County, Washington
  { zoneName: 'US-NW-GRID', type: 'subZone', countryId: 'USA', id: 'US-NW-GRID' }, //Gridforce Energy Management, Llc
  { zoneName: 'US-NW-GWA', type: 'subZone', countryId: 'USA', id: 'US-NW-GWA' }, //Naturener Power Watch, Llc (Gwa)
  { zoneName: 'US-NW-IPCO', type: 'subZone', countryId: 'USA', id: 'US-NW-IPCO' }, //Idaho Power Company
  { zoneName: 'US-NW-NEVP', type: 'subZone', countryId: 'USA', id: 'US-NW-NEVP' }, //Nevada Power Company
  { zoneName: 'US-NW-NWMT', type: 'subZone', countryId: 'USA', id: 'US-NW-NWMT' }, //Northwestern Energy (Nwmt)
  { zoneName: 'US-NW-PACE', type: 'subZone', countryId: 'USA', id: 'US-NW-PACE' }, //Pacificorp - East
  { zoneName: 'US-NW-PACW', type: 'subZone', countryId: 'USA', id: 'US-NW-PACW' }, //Pacificorp - West
  { zoneName: 'US-NW-PGE', type: 'subZone', countryId: 'USA', id: 'US-NW-PGE' }, //Portland General Electric Company
  { zoneName: 'US-NW-PSCO', type: 'subZone', countryId: 'USA', id: 'US-NW-PSCO' }, //Public Service Company Of Colorado
  { zoneName: 'US-NW-PSEI', type: 'subZone', countryId: 'USA', id: 'US-NW-PSEI' }, //Puget Sound Energy
  { zoneName: 'US-NW-SCL', type: 'subZone', countryId: 'USA', id: 'US-NW-SCL' }, //Seattle City Light
  { zoneName: 'US-NW-TPWR', type: 'subZone', countryId: 'USA', id: 'US-NW-TPWR' }, //City Of Tacoma, Department Of Public Utilities, Light Division
  { zoneName: 'US-NW-WACM', type: 'subZone', countryId: 'USA', id: 'US-NW-WACM' }, //Western Area Power Administration - Rocky Mountain Region
  { zoneName: 'US-NW-WAUW', type: 'subZone', countryId: 'USA', id: 'US-NW-WAUW' }, //Western Area Power Administration Ugp West
  { zoneName: 'US-NW-WWA', type: 'subZone', countryId: 'USA', id: 'US-NW-WWA' }, //Naturener Wind Watch, Llc
  { zoneName: 'US-NY-NYIS', type: 'subZone', countryId: 'USA', id: 'US-NY-NYIS' }, //New York Independent System Operator
  { zoneName: 'US-SE-AEC', type: 'subZone', countryId: 'USA', id: 'US-SE-AEC' }, //Powersouth Energy Cooperative
  { zoneName: 'US-SE-SEPA', type: 'subZone', countryId: 'USA', id: 'US-SE-SEPA' }, //Southeastern Power Administration
  { zoneName: 'US-SE-SOCO', type: 'subZone', countryId: 'USA', id: 'US-SE-SOCO' }, //Southern Company Services, Inc. - Trans
  { zoneName: 'US-SW-AZPS', type: 'subZone', countryId: 'USA', id: 'US-SW-AZPS' }, //Arizona Public Service Company
  { zoneName: 'US-SW-DEAA', type: 'subZone', countryId: 'USA', id: 'US-SW-DEAA' }, //Arlington Valley, Llc - Avba
  { zoneName: 'US-SW-EPE', type: 'subZone', countryId: 'USA', id: 'US-SW-EPE' }, //El Paso Electric Company
  { zoneName: 'US-SW-GRIF', type: 'subZone', countryId: 'USA', id: 'US-SW-GRIF' }, //Griffith Energy, Llc
  { zoneName: 'US-SW-GRMA', type: 'subZone', countryId: 'USA', id: 'US-SW-GRMA' }, //Gila River Power, Llc
  { zoneName: 'US-SW-HGMA', type: 'subZone', countryId: 'USA', id: 'US-SW-HGMA' }, //New Harquahala Generating Company, Llc - Hgba
  { zoneName: 'US-SW-PNM', type: 'subZone', countryId: 'USA', id: 'US-SW-PNM' }, //Public Service Company Of New Mexico
  { zoneName: 'US-SW-SRP', type: 'subZone', countryId: 'USA', id: 'US-SW-SRP' }, //Salt River Project
  { zoneName: 'US-SW-TEPC', type: 'subZone', countryId: 'USA', id: 'US-SW-TEPC' }, //Tucson Electric Power Company
  { zoneName: 'US-SW-WALC', type: 'subZone', countryId: 'USA', id: 'US-SW-WALC' }, //Western Area Power Administration - Desert Southwest Region
  { zoneName: 'US-TEN-TVA', type: 'subZone', countryId: 'USA', id: 'US-TEN-TVA' }, //Tennessee Valley Authority
  { zoneName: 'US-TEX-ERCO', type: 'subZone', countryId: 'USA', id: 'US-TEX-ERCO' }, //Electric Reliability Council Of Texas, Inc.
  { zoneName: 'VC', type: 'country', id: 'VCT'},
  { zoneName: 'UY', type: 'country', id: 'URY'},
  { zoneName: 'UZ', type: 'country', id: 'UZB'},
  { zoneName: 'VA', type: 'country', id: 'VAT'},
  { zoneName: 'VE', type: 'country', id: 'VEN'},
  { zoneName: 'VG', type: 'country', id: 'VGB'},
  { zoneName: 'VI', type: 'country', id: 'VIR'},
  { zoneName: 'VN', type: 'country', id: 'VNM'},
  { zoneName: 'VU', type: 'country', id: 'VUT'},
  { zoneName: 'WF', type: 'country', id: 'WLF'},
  { zoneName: 'WS', type: 'country', id: 'WSM'},
  { zoneName: 'XK', type: 'country', id: 'KOS'},
  { zoneName: 'YE', type: 'country', id: 'YEM'},
  { zoneName: 'YT', type: 'country', id: 'MYT'},
  { zoneName: 'ZA', type: 'country', id: 'ZAF'},
  { zoneName: 'ZM', type: 'country', id: 'ZMB'},
  { zoneName: 'ZW', type: 'country', id: 'ZWE'},
];


function hascMatch(properties, hasc) {
  return (
    properties.code_hasc === hasc ||
    (properties.hasc_maybe && properties.hasc_maybe.split('|').indexOf(hasc) !== -1)
  );
}

function equals(obj, prop, val) {
  return obj && prop in obj && obj[prop] === val;
}

function getCountry(countryId, geos) {
  return geomerge(...geos.filter(d => equals(d, 'id', countryId)));
}
function getByPropertiesId(zoneId, geos) {
  return geomerge(...geos.filter(d => equals(d.properties, 'id', zoneId)));
}
function getSubUnit(subid, geos) {
  return geomerge(...geos.filter(d => equals(d.properties, 'subid', subid)));
}
function getState(countryId, geos, code_hasc, use_maybe=false) {
  return geomerge(...geos.filter(d =>
    equals(d, 'id', countryId) && 'code_hasc' in d.properties &&
    (use_maybe && hascMatch(d.properties, code_hasc) || d.properties.code_hasc === code_hasc)));
}
function getStateByFips(countryId, geos, fips) {
  return geomerge(...geos.filter(d =>
    equals(d, 'id', countryId) && equals(d.properties, 'fips', fips)));
}
function getStateByAdm1(adm1_code, geos) {
  return geomerge(...geos.filter(d => equals(d.properties, 'adm1_code', adm1_code)));
}
function getByRegionCod(region_cod, geos) {
  return geomerge(...geos.filter(d => equals(d.properties, 'region_cod', region_cod)));
}
function getCounty(county_name, geos) {
  return geomerge(...geos.filter(d => equals(d.properties, 'COUNTYNAME', county_name)));
}
function getStates(countryId, geos, code_hascs, use_maybe) {
  return geomerge(...code_hascs.map(d => getState(countryId, geos, d, use_maybe)));
}
function getStatesByAdm1(adm1_codes, geos) {
  return geomerge(...adm1_codes.map(d => getStateByAdm1(d, geos)));
}
function getCountries(countryIds, geos) {
  return geomerge(...countryIds.map(d => getCountry(d, geos)));
}
function getSubUnits(ids, geos) {
  return geomerge(...ids.map(d => getSubUnit(d, geos)));
}
function getCounties(names, geos) {
  return geomerge(...names.map(d => getCounty(d, geos)));
}

const getDataForZone = (zone, geos, mergeStates) => {
  /* for a specifi zone, defined by an Object having at least `zoneName` and
   * `type` as properties, call the corresponding function to get the data */
  if (zone.type === 'country'){
    return getCountry(zone.id, geos)
  }
  else if (zone.type === 'states'){
    if (mergeStates){
      return getStates(zone.countryId, geos, zone.states);
    }
    else{
      return ['multipleStates', zone.states.map(state => getState(zone.countryId, geos, state))];
    }
  }
  else if (zone.type === 'state'){
    return getState(zone.countryId, geos, zone.stateId, zone.useMaybe);
  }
  else if (zone.type === 'administrations'){
    return getStatesByAdm1(zone.administrations, geos);
  }
  else if (zone.type === 'subunits'){
    return getSubUnits(zone.subunits, geos);
  }
  else if (zone.type === 'countries'){
    return getCountries(zone.countries, geos);
  }
  else if (zone.type === 'fips'){
    return getStateByFips(zone.fips[0], geos, zone.fips[1]);
  }
  else if (zone.type === 'subZone') {
    return getByPropertiesId(zone.id, geos);
  }
  else if (zone.type === 'region_cod') {
    if (typeof zone.region_cod === 'object') {
      // assume array
      return geomerge(...zone.region_cod.map(d => getByRegionCod(d, geos)));
    } else {
      return getByRegionCod(zone.region_cod, geos);
    }
  }
  else if (zone.type === 'county') {
    return getCounties(zone.counties, geos);
  }
  else{
    console.warn(`unknown type "${zone.type}" for zone`, zone.zoneName);
  }
};

const toListOfFeatures = (zones) => {
  /* transform a list of (zoneName, properties) to the right geoJSON format */
  return zones.filter(d => d[1] != null).map((d) => {
    const [k, v] = d;
    let zoneName = k;
    v.id = zoneName;
    v.properties = {
      zoneName: zoneName,
    };
    return v;
  });
};

//Adds the zones from topo2 to topo1
function mergeTopoJsonSingleZone(topo1, topo2) {
  let srcArcsLength = topo1.arcs.length;
  // Copy Zones from topo2 to topo1
  Object.keys(topo2.objects).forEach(zoneName=>{
    topo1.objects[zoneName]=topo2.objects[zoneName];
    // Relocate arc into zone by adding srcArcsLength
    topo1.objects[zoneName].arcs.forEach(arcList1=>{
      arcList1.forEach(arcList2=>{
        for(i=0; i<arcList2.length; i++) {
          arcList2[i]+=srcArcsLength;
        }
      });
    });
  });

  // Add arcs from topo2
  topo2.arcs.forEach(arc=> {
    topo1.arcs.push(arc);
  });
}

// create zones from definitions, avoid zones having moreDetails==true
function getZones(zoneDefinitions, geos) {
  let zones = {};
  zoneDefinitions.forEach(zone => {
    if (zone.zoneName in zones)
      throw ('Warning: ' + zone.zoneName + ' has duplicated entries. Each zoneName must be present ' +
        'only once in zoneDefinitions');
    // Avoid zone with moreDetails
    if ( !('moreDetails' in zone) || !zone.moreDetails) {
      zones[zone.zoneName] = getDataForZone(zone, geos, true);
    }
  });
  return zones
}

function getZonesMoreDetails(zoneDefinitions, geos, zones) {
  // create zonesMoreDetails by getting zone having moreDetails===true
  let zonesMoreDetails = {};
  zoneDefinitions.forEach(zone => {
    // Take only zones having modeDetails
    if (('moreDetails' in zone) && zone.moreDetails) {
    if (zone.zoneName in zonesMoreDetails || zone.zoneName in zones)
        throw ('Warning: ' + zone.zoneName + ' has duplicated entries. Each zoneName must be present ' +
          'only once in zoneDefinitions');
    zonesMoreDetails[zone.zoneName] = getDataForZone(zone, geos, true);
    }
  });
  return zonesMoreDetails
}

function getZoneFeatures(zoneDefinitions, geos) {
  // We do not want to merge states
  // related to PR #455 in the backend
  let zoneFeatures = zoneDefinitions.map(
    zone => [zone.zoneName, getDataForZone(zone, geos, false)]);
  // where there are multiple states, we need to inline the values
  let zoneFeaturesInline = [];
  zoneFeatures.forEach((data) => {
    let [name, zoneFeature] = data;
    if (Array.isArray(zoneFeature) && zoneFeature[0] === 'multipleStates'){
      zoneFeature[1].forEach(z => {zoneFeaturesInline.push([name, z])});
    }
    else{
      zoneFeaturesInline.push(data);
    }
  });
  zoneFeatures = toListOfFeatures(zoneFeaturesInline);
  return zoneFeatures
}

const webGeos = countryGeos.concat(stateGeos, thirdpartyGeos, USSimplifiedGeos);
const backendGeos = countryGeos.concat(stateGeos, thirdpartyGeos, USSimplifiedGeos); //should be changed back to USOriginalGeos

const webZones = getZones(zoneDefinitions, webGeos);
const backendZones = getZones(zoneDefinitions, backendGeos);

const zonesMoreDetails = getZonesMoreDetails(zoneDefinitions, webGeos, webZones);
const zoneFeatures = getZoneFeatures(zoneDefinitions, backendGeos)

// Write unsimplified list of geojson, without state merges
// including overlapping US zones
const zonegeometriesFolder = 'public/dist'
if (!fs.existsSync(zonegeometriesFolder)){
  fs.mkdirSync(zonegeometriesFolder);
}
fs.writeFileSync(`${zonegeometriesFolder}/zonegeometries.json`, zoneFeatures.map(JSON.stringify).join('\n'));

// Convert to TopoJSON
const topojson = require('topojson');
let topo = topojson.topology(webZones);

// merge contiguous Florida counties in US-FL and US-SEC so that we only see the
// outer region boundary line(s), not the interior county boundary lines.
// Example: https://bl.ocks.org/mbostock/5416405
// Background: https://github.com/tmrowco/electricitymap-contrib/issues/1713#issuecomment-517704023
//topo.objects['US-FL'] = topojson.mergeArcs(topo, [topo.objects['US-FL']]);
//topo.objects['US-SEC'] = topojson.mergeArcs(topo, [topo.objects['US-SEC']]);

// Simplify all countries
topo = topojson.presimplify(topo);
topo = topojson.simplify(topo, 0.01);
topo = topojson.filter(topo, topojson.filterWeight(topo, 0.009));

// Simplify to 0.001 zonesMoreDetails zones
topoMoreDetails = topojson.topology(zonesMoreDetails);
topoMoreDetails = topojson.presimplify(topoMoreDetails);
topoMoreDetails = topojson.simplify(topoMoreDetails, 0.001);

// Merge topoMoreDetails into topo
mergeTopoJsonSingleZone(topo, topoMoreDetails);

topo = topojson.quantize(topo, 1e5);
fs.writeFileSync('src/world.json', JSON.stringify(topo));
