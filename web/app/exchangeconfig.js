var exports = module.exports = {};

exports.addExchangesConfiguration = function(exchanges) {
    // AL
    exchanges['AL->GR'] = {
        lonlat: [20.689872, 40.198219],
        rotation: 135
    };
    exchanges['AL->ME'] = {
      lonlat: [19.500384, 42.428871],
      rotation: -55
    };
    exchanges['AL->RS'] = {
        lonlat: [20.486292, 42.323472],
        rotation: 40
    };
    // AT
    exchanges['AT->CH'] = {
        lonlat: [9.597882, 47.079455],
        rotation: -90
    };
    exchanges['AT->CZ'] = {
        lonlat: [15.486554, 48.909846],
        rotation: 0
    };
    exchanges['AT->DE'] = {
        lonlat: [12.679547, 47.696804],
        rotation: -30
    };
    exchanges['AT->HU'] = {
        lonlat: [16.605363, 47.444264],
        rotation: 120
    };
    exchanges['AT->IT'] = {
        lonlat: [12.344464, 46.741723],
        rotation: -140
    };
    exchanges['AT->SI'] = {
        lonlat: [15.014142, 46.613582],
        rotation: 180
    };
    // BA
    exchanges['BA->ME'] = {
      lonlat: [18.665423, 43.042137],
      rotation: 120
    };
    exchanges['BA->RS'] = {
        lonlat: [19.127873, 44.377951],
        rotation: 90
    };
    // BE
    exchanges['BE->FR-ACA'] = {
        lonlat: [5.3, 49.6],
        rotation: -170
    };
    exchanges['BE->FR-NPP'] = {
        lonlat: [3.3, 50.5],
        rotation: -125
    };
    exchanges['BE->NL'] = {
        lonlat: [5.026873, 51.425174],
        rotation: 0
    };
    // BG
    exchanges['BG->GR'] = {
        lonlat: [24.1, 41.558088],
        rotation: 180
    };
    exchanges['BG->MK'] = {
        lonlat: [22.912615, 41.867840],
        rotation: -90
    };
    exchanges['BG->RO'] = {
        lonlat: [25.609385, 43.674878],
        rotation: 0
    };
    exchanges['BG->RS'] = {
        lonlat: [22.978533, 43.131375],
        rotation: -90
    };
    exchanges['BG->TR'] = {
        lonlat: [26.898640, 42.002181],
        rotation: 135
    };
    //
    exchanges['BY->LT'] = {
        lonlat: [25.756061, 54.789457],
        rotation: -90
    };
    // CH
    exchanges['CH->DE'] = {
        lonlat: [8.806354, 47.667048],
        rotation: 0
    };
    exchanges['CH->FR-ACA'] = {
        lonlat: [7.4, 47.46],
        rotation: -15
    };
    exchanges['CH->FR-ARA'] = {
        lonlat: [6.8, 46.2],
        rotation: -120
    };
    exchanges['CH->FR-BFC'] = {
        lonlat: [6.78, 47.1],
        rotation: -45
    };
    exchanges['CH->IT'] = {
        lonlat: [9.047334, 46.113596],
        rotation: 180
    };
    // CZ
    exchanges['CZ->SK'] = {
        lonlat: [18.100645, 49.089498],
        rotation: 135
    };
    exchanges['CZ->PL'] = {
        lonlat: [16.496641, 50.269487],
        rotation: 45
    };
    exchanges['CZ->DE'] = {
        lonlat: [12.321836, 50.227335],
        rotation: -60
    };
    // DE
    exchanges['DE->DK'] = {
        lonlat: [9.3, 54.9],
        rotation: 0
    };
    exchanges['DE->FR'] = {
        lonlat: [8.048297, 48.931337],
        rotation: -110
    };
    exchanges['DE->NL'] = {
        lonlat: [6.916521, 52.159037],
        rotation: -90
    };
    exchanges['DE->PL'] = {
        lonlat: [14.585163, 52.410625],
        rotation: 90
    };
    exchanges['DE->SE'] = {
        lonlat: [13.552264, 54.925814],
        rotation: 0
    };
    // ES
    exchanges['ES->FR-ALP'] = {
        lonlat: [-1.07, 42.9],
        rotation: 10
    };
    exchanges['ES->FR-LRM'] = {
        lonlat: [1.67, 42.5],
        rotation: 20
    };
    exchanges['ES->PT'] = {
        lonlat: [-7, 40.0],
        rotation: -90
    };
    // DK
    exchanges['DK->NO'] = {
        lonlat: [8.8, 57.7],
        rotation: -25
    };
    exchanges['DK->SE'] = {
        lonlat: [11.556268, 56.857802],
        rotation: 70
    };
    // EE
    exchanges['EE->FI'] = {
        lonlat: [25.690143, 59.923241],
        rotation: -35
    };
    exchanges['EE->LV'] = {
        lonlat: [26.041706, 57.810982],
        rotation: 180
    };
    exchanges['EE->RU'] = {
        lonlat: [27.468803, 58.545189],
        rotation: 90
    }
    // FI
    exchanges['FI->NO'] = {
        lonlat: [25.351580, 68.862684],
        rotation: -30
    };
    exchanges['FI->RU'] = {
        lonlat: [29.733112, 65.422768],
        rotation: 90
    };
    exchanges['FI->SE'] = {
        lonlat: [20.979206, 63.441789],
        rotation: -50
    };
    // FR
    exchanges['FR-NPP->GB'] = {
        lonlat: [1.6, 50.8],
        rotation: -25
    };
    exchanges['FR-ACA->FR-NPP'] = {
        lonlat: [3.98, 49.4],
        rotation: -40
    };
    exchanges['FR-ACA->FR-IDF'] = {
        lonlat: [3.46, 48.63],
        rotation: -90
    };
    exchanges['FR-ACA->FR-BFC'] = {
        lonlat: [5.25, 47.5],
        rotation: -170
    };
    exchanges['FR-ALP->FR-ARA'] = {
        lonlat: [2.48, 45.8],
        rotation: 100
    };
    exchanges['FR-ALP->FR-CEN'] = {
        lonlat: [1, 46.5],
        rotation: 30
    };
    exchanges['FR-ALP->FR-LRM'] = {
        lonlat: [1, 44.4],
        rotation: 120
    };
    exchanges['FR-ALP->FR-PLO'] = {
        lonlat: [-0.65, 46.7],
        rotation: -24
    };
    exchanges['FR-ARA->FR-BFC'] = {
        lonlat: [4.87, 46.41],
        rotation: 15
    };
    exchanges['FR-ARA->FR-CEN'] = {
        lonlat: [2.7, 46.7],
        rotation: -45
    };
    exchanges['FR-ARA->FR-LRM'] = {
        lonlat: [3.67, 44.83],
        rotation: -140
    };
    exchanges['FR-ARA->IT'] = {
        lonlat: [7.11, 45.4],
        rotation: 105
    };
    exchanges['FR-BFC->FR-CEN'] = {
        lonlat: [2.94, 47.5],
        rotation: -90
    };
    exchanges['FR-BFC->FR-IDF'] = {
        lonlat: [3.17, 48.36],
        rotation: -20
    };
    exchanges['FR-BRE->FR-CEN'] = {
        lonlat: [1.05, 48.7],
        rotation: -15
    };
    exchanges['FR-BRE->FR-IDF'] = {
        lonlat: [1.64, 49.1],
        rotation: -45
    };
    exchanges['FR-BRE->FR-NOR'] = {
        lonlat: [-1.47, 48.52],
        rotation: 45
    };
    exchanges['FR-BRE->FR-PLO'] = {
        lonlat: [-1.6, 47.7],
        rotation: 120
    };
    exchanges['FR-CEN->FR-IDF'] = {
        lonlat: [2.17, 48.3],
        rotation: 10
    };
    exchanges['FR-CEN->FR-PLO'] = {
        lonlat: [0.5, 47.6],
        rotation: -75
    };
    exchanges['FR-IDF->FR-NPP'] = {
        lonlat: [2.62, 49.07],
        rotation: 5
    };
    exchanges['FR-LRM->FR-PAC'] = {
        lonlat: [4.75, 43.9],
        rotation: -90
    };
    exchanges['FR-NOR->FR-NPP'] = {
        lonlat: [1.7, 49.66],
        rotation: 70
    };
    exchanges['FR-NOR->FR-PLO'] = {
        lonlat: [-0.2, 48.5],
        rotation: -170
    };
    exchanges['FR-PAC->IT'] = {
        lonlat: [6.9, 44.4],
        rotation: 70
    };
    // GB
    exchanges['GB->IE'] = {
        lonlat: [-5.7, 53],
        rotation: -80
    };
    exchanges['GB->NL'] = {
        lonlat: [3.3, 52.4],
        rotation: 90
    };
    exchanges['GB->GB-NIR'] = {
        lonlat: [-5.428149, 54.878260],
        rotation: -110
    }
    // GR
    exchanges['GR->IT'] = {
        lonlat: [18.759248, 38.902132],
        rotation: -90
    };
    exchanges['GR->MK'] = {
        lonlat: [22.011736, 41.160374],
        rotation: 0
    };
    exchanges['GR->TR'] = {
        lonlat: [26.316812, 41.12620],
        rotation: 90
    };
    // HR
    exchanges['HR->HU'] = {
        lonlat: [17.407365, 45.967775],
        rotation: 30
    };
    exchanges['HR->RS'] = {
      lonlat: [19.021212, 45.354302],
      rotation: 90
    };
    // HU
    exchanges['HU->SK'] = {
        lonlat: [19.615617, 48.204006],
        rotation: 0
    };
    exchanges['HU->UA'] = {
        lonlat: [22.526994, 48.240603],
        rotation: 35
    };
    exchanges['HU->RO'] = {
        lonlat: [21.8074107, 47.1141229],
        rotation: 110
    };
    exchanges['HU->RS'] = {
        lonlat: [19.494768, 46.112673],
        rotation: 180
    };
    // IT
    exchanges['IT->SI'] = {
        lonlat: [13.596393, 46.105418],
        rotation: 90
    };
    // LT
    exchanges['LT->PL'] = {
        lonlat: [23.308307, 54.247411],
        rotation: 180
    };
    exchanges['LT->LV'] = {
        lonlat: [24.373981, 56.287428],
        rotation: 0
    };
    exchanges['LT->RU-KGD'] = {
        lonlat: [21.963913, 55.080726],
        rotation: -180
    };
    exchanges['LT->SE'] = {
        lonlat: [18.847674, 55.910978],
        rotation: -90
    };
    // LV
    exchanges['LV->RU'] = {
        lonlat: [27.733600, 56.874360],
        rotation: 45
    };
    // ME
    exchanges['ME->RS'] = {
      lonlat: [19.566302, 43.242543],
      rotation: 40
    };
    // MD
    exchanges['MD->RO'] = {
        lonlat: [28.009764, 47.003312],
        rotation: -120
    };
    // MK
    exchanges['MK->RS'] = {
        lonlat: [22.039250, 42.317020],
        rotation: 0
    }
    // NL
    exchanges['NL->NO'] = {
        lonlat: [5.795449, 55.859727],
        rotation: 0
    };
    // NO
    exchanges['NO->SE'] = {
        lonlat: [12.308438, 62.195230],
        rotation: 90
    };
    // PL
    exchanges['PL->SE'] = {
        lonlat: [15.969256, 55.215172],
        rotation: -20
    };
    exchanges['PL->SK'] = {
        lonlat: [20.614102, 49.359467],
        rotation: 180
    };
    exchanges['PL->UA'] = {
        lonlat: [24.097224, 50.664587],
        rotation: 90
    }
    // RO
    exchanges['RO->UA'] = {
        lonlat: [24.821959, 47.768595],
        rotation: 0
    };
    exchanges['RO->RS'] = {
        lonlat: [21.469049, 44.947107],
        rotation: -140
    };
    // UA
    exchanges['SK->UA'] = {
        lonlat: [22.384512, 48.820578],
        rotation: 90
    };
    // ** Canada
    exchanges['CA-AB->CA-BC'] = {
        lonlat: [-119.811359, 53.797027],
        rotation: -90
    };
    exchanges['CA-AB->CA-SK'] = {
        lonlat: [-109.986644, 54.883208],
        rotation: 90
    };
    exchanges['CA-AB->US'] = {
        lonlat: [-111.920238, 49.016577],
        rotation: 180
    };
    exchanges['CA-BC->US'] = {
        lonlat: [-119.300532, 49.044392],
        rotation: 180
    };
    exchanges['CA-MB->CA-ON'] = {
        lonlat: [-95.177354, 52.802819],
        rotation: 90
    };
    exchanges['CA-ON->CA-QC'] = {
        lonlat: [-79.494485, 48.798268],
        rotation: 90
    };
    exchanges['CA-ON->US'] = {
        lonlat: [-92.722024, 48.566155],
        rotation: 180
    };
    exchanges['CA-NB->CA-NS'] = {
        lonlat: [-65.7552, 45.0425],
        rotation: 90
    };
    exchanges['CA-NB->CA-PE'] = {
        lonlat: [-64.5739, 46.7349],
        rotation: 90
    };
    exchanges['CA-NB->CA-QC'] = {
        lonlat: [-67.2344, 47.8871],
        rotation: -45
    };
    exchanges['CA-NB->US'] = {
        lonlat: [-67.7771, 46.1390],
        rotation: -90
    };
    // ** Oceania
    exchanges['AUS-NSW->AUS-QLD'] = {
        lonlat: [146.503228, -29.054874],
        rotation: 0
    }
    exchanges['AUS-NSW->AUS-VIC'] = {
        lonlat: [145.308829, -35.850801],
        rotation: 180
    }
    exchanges['AUS-SA->AUS-VIC'] = {
        lonlat: [140.965561, -35.784766],
        rotation: 90
    }
    exchanges['AUS-TAS->AUS-VIC'] = {
        lonlat: [146.096047, -39.836207],
        rotation: 0
    }
    exchanges['NZ-NZN->NZ-NZS'] = {
        lonlat: [174.424066, -41.140732],
        rotation: 90
    };
}
