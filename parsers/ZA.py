from collections import OrderedDict
from datetime import datetime
from logging import Logger, getLogger
from pprint import PrettyPrinter
from typing import List, Optional

from arrow import get, now
from requests import Response, Session, post

pp = PrettyPrinter(indent=4)

TIMEZONE = "Africa/Johannesburg"

curr_month = now().format("MM")
PRODUCTION_URL = f"https://www.eskom.co.za/dataportal/wp-content/uploads/2022/{curr_month}/Station_Build_Up.csv"
POWER_BI_URL = "https://wabi-south-africa-north-a-primary-api.analysis.windows.net/public/reports/querydata"


def get_power_bi_values():
    data = {
        "version": "1.0.0",
        "queries": [
            {
                "Query": {
                    "Commands": [
                        {
                            "SemanticQueryDataShapeCommand": {
                                "Query": {
                                    "Version": 2,
                                    "From": [
                                        {
                                            "Name": "q",
                                            "Entity": "Station_Build_Up",
                                            "Type": 0,
                                        }
                                    ],
                                    "Select": [
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "q"}
                                                },
                                                "Property": "Date_Time_Hour_Beginning",
                                            },
                                            "Name": "Query1.Date_Time_Hour_Beginning",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Nuclear_Generation",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Nuclear_Generation)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "International_Imports",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.International_Imports)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Eskom_OCGT_Generation",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Eskom_OCGT_Generation)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Eskom_Gas_Generation",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Eskom_Gas_Generation)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Dispatchable_IPP_OCGT",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Dispatchable_IPP_OCGT)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Hydro_Water_Generation",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Hydro_Water_Generation)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Pumped_Water_Generation",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Pumped_Water_Generation)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "IOS_Excl_ILS_and_MLR",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.IOS_Excl_ILS_and_MLR)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "ILS_Usage",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.ILS_Usage)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Manual_Load_Reduction_MLR",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Manual_Load_Reduction_MLR)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Wind",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Wind)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "PV",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.PV)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "CSP",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.CSP)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Other_RE",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Other_RE)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Eskom_Gas_SCO_Pumping",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Eskom_Gas_SCO_Pumping)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Eskom_OCGT_SCO_Pumping",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Eskom_OCGT_SCO_Pumping)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Hydro_Water_SCO_Pumping",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Hydro_Water_SCO_Pumping)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Pumped_Water_SCO_Pumping",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Pumped_Water_SCO_Pumping)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "Thermal_Gen_Excl_Pumping_and_SCO",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.Thermal_Gen_Excl_Pumping_and_SCO)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "                   Eskom_OCGT_SCO_Pumping",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.                   Eskom_OCGT_SCO_Pumping)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "                  Eskom_Gas_SCO_Pumping",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.                  Eskom_Gas_SCO_Pumping)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "                 Hydro_Water_SCO_Pumping",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.                 Hydro_Water_SCO_Pumping)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "                Pumped_Water_SCO_Pumping",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.                Pumped_Water_SCO_Pumping)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "               Thermal_Generation",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.               Thermal_Generation)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "              Nuclear_Generation",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.              Nuclear_Generation)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "             International_Imports",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.             International_Imports)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "            Eskom_OCGT_Generation",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.            Eskom_OCGT_Generation)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "           Eskom_Gas_Generation",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.           Eskom_Gas_Generation)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "          Dispatchable_IPP_OCGT",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.          Dispatchable_IPP_OCGT)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "         Hydro_Water_Generation",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.         Hydro_Water_Generation)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "        Pumped_Water_Generation",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.        Pumped_Water_Generation)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "       IOS_Excl_ILS_and_MLR",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.       IOS_Excl_ILS_and_MLR)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "      ILS_Usage",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.      ILS_Usage)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "     Manual_Load_Reduction_MLR",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.     Manual_Load_Reduction_MLR)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "    Wind",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.    Wind)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "   PV",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.   PV)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": "  CSP",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up.  CSP)",
                                        },
                                        {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": "q"}
                                                        },
                                                        "Property": " Other_RE",
                                                    }
                                                },
                                                "Function": 0,
                                            },
                                            "Name": "Sum(Station_Build_Up. Other_RE)",
                                        },
                                    ],
                                },
                                "Binding": {
                                    "Primary": {
                                        "Groupings": [
                                            {
                                                "Projections": [
                                                    0,
                                                    1,
                                                    2,
                                                    3,
                                                    4,
                                                    5,
                                                    6,
                                                    7,
                                                    8,
                                                    9,
                                                    10,
                                                    11,
                                                    12,
                                                    13,
                                                    14,
                                                    15,
                                                    16,
                                                    17,
                                                    18,
                                                    19,
                                                    20,
                                                    21,
                                                    22,
                                                    23,
                                                    24,
                                                    25,
                                                    26,
                                                    27,
                                                    28,
                                                    29,
                                                    30,
                                                    31,
                                                    32,
                                                    33,
                                                    34,
                                                    35,
                                                    36,
                                                    37,
                                                    38,
                                                ]
                                            }
                                        ]
                                    },
                                    "DataReduction": {
                                        "DataVolume": 4,
                                        "Primary": {"Sample": {}},
                                    },
                                    "SuppressedJoinPredicates": [
                                        20,
                                        21,
                                        22,
                                        23,
                                        24,
                                        25,
                                        26,
                                        27,
                                        28,
                                        29,
                                        30,
                                        31,
                                        32,
                                        33,
                                        34,
                                        35,
                                        36,
                                        37,
                                        38,
                                    ],
                                    "Version": 1,
                                },
                                "ExecutionMetricsKind": 1,
                            }
                        }
                    ]
                },
                "CacheKey": '{"Commands":[{"SemanticQueryDataShapeCommand":{"Query":{"Version":2,"From":[{"Name":"q","Entity":"Station_Build_Up","Type":0}],"Select":[{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Date_Time_Hour_Beginning"},"Name":"Query1.Date_Time_Hour_Beginning"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Nuclear_Generation"}},"Function":0},"Name":"Sum(Station_Build_Up.Nuclear_Generation)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"International_Imports"}},"Function":0},"Name":"Sum(Station_Build_Up.International_Imports)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Eskom_OCGT_Generation"}},"Function":0},"Name":"Sum(Station_Build_Up.Eskom_OCGT_Generation)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Eskom_Gas_Generation"}},"Function":0},"Name":"Sum(Station_Build_Up.Eskom_Gas_Generation)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Dispatchable_IPP_OCGT"}},"Function":0},"Name":"Sum(Station_Build_Up.Dispatchable_IPP_OCGT)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Hydro_Water_Generation"}},"Function":0},"Name":"Sum(Station_Build_Up.Hydro_Water_Generation)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Pumped_Water_Generation"}},"Function":0},"Name":"Sum(Station_Build_Up.Pumped_Water_Generation)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"IOS_Excl_ILS_and_MLR"}},"Function":0},"Name":"Sum(Station_Build_Up.IOS_Excl_ILS_and_MLR)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"ILS_Usage"}},"Function":0},"Name":"Sum(Station_Build_Up.ILS_Usage)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Manual_Load_Reduction_MLR"}},"Function":0},"Name":"Sum(Station_Build_Up.Manual_Load_Reduction_MLR)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Wind"}},"Function":0},"Name":"Sum(Station_Build_Up.Wind)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"PV"}},"Function":0},"Name":"Sum(Station_Build_Up.PV)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"CSP"}},"Function":0},"Name":"Sum(Station_Build_Up.CSP)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Other_RE"}},"Function":0},"Name":"Sum(Station_Build_Up.Other_RE)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Eskom_Gas_SCO_Pumping"}},"Function":0},"Name":"Sum(Station_Build_Up.Eskom_Gas_SCO_Pumping)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Eskom_OCGT_SCO_Pumping"}},"Function":0},"Name":"Sum(Station_Build_Up.Eskom_OCGT_SCO_Pumping)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Hydro_Water_SCO_Pumping"}},"Function":0},"Name":"Sum(Station_Build_Up.Hydro_Water_SCO_Pumping)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Pumped_Water_SCO_Pumping"}},"Function":0},"Name":"Sum(Station_Build_Up.Pumped_Water_SCO_Pumping)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"Thermal_Gen_Excl_Pumping_and_SCO"}},"Function":0},"Name":"Sum(Station_Build_Up.Thermal_Gen_Excl_Pumping_and_SCO)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"                   Eskom_OCGT_SCO_Pumping"}},"Function":0},"Name":"Sum(Station_Build_Up.                   Eskom_OCGT_SCO_Pumping)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"                  Eskom_Gas_SCO_Pumping"}},"Function":0},"Name":"Sum(Station_Build_Up.                  Eskom_Gas_SCO_Pumping)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"                 Hydro_Water_SCO_Pumping"}},"Function":0},"Name":"Sum(Station_Build_Up.                 Hydro_Water_SCO_Pumping)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"                Pumped_Water_SCO_Pumping"}},"Function":0},"Name":"Sum(Station_Build_Up.                Pumped_Water_SCO_Pumping)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"               Thermal_Generation"}},"Function":0},"Name":"Sum(Station_Build_Up.               Thermal_Generation)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"              Nuclear_Generation"}},"Function":0},"Name":"Sum(Station_Build_Up.              Nuclear_Generation)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"             International_Imports"}},"Function":0},"Name":"Sum(Station_Build_Up.             International_Imports)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"            Eskom_OCGT_Generation"}},"Function":0},"Name":"Sum(Station_Build_Up.            Eskom_OCGT_Generation)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"           Eskom_Gas_Generation"}},"Function":0},"Name":"Sum(Station_Build_Up.           Eskom_Gas_Generation)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"          Dispatchable_IPP_OCGT"}},"Function":0},"Name":"Sum(Station_Build_Up.          Dispatchable_IPP_OCGT)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"         Hydro_Water_Generation"}},"Function":0},"Name":"Sum(Station_Build_Up.         Hydro_Water_Generation)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"        Pumped_Water_Generation"}},"Function":0},"Name":"Sum(Station_Build_Up.        Pumped_Water_Generation)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"       IOS_Excl_ILS_and_MLR"}},"Function":0},"Name":"Sum(Station_Build_Up.       IOS_Excl_ILS_and_MLR)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"      ILS_Usage"}},"Function":0},"Name":"Sum(Station_Build_Up.      ILS_Usage)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"     Manual_Load_Reduction_MLR"}},"Function":0},"Name":"Sum(Station_Build_Up.     Manual_Load_Reduction_MLR)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"    Wind"}},"Function":0},"Name":"Sum(Station_Build_Up.    Wind)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"   PV"}},"Function":0},"Name":"Sum(Station_Build_Up.   PV)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":"  CSP"}},"Function":0},"Name":"Sum(Station_Build_Up.  CSP)"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"q"}},"Property":" Other_RE"}},"Function":0},"Name":"Sum(Station_Build_Up. Other_RE)"}]},"Binding":{"Primary":{"Groupings":[{"Projections":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38]}]},"DataReduction":{"DataVolume":4,"Primary":{"Sample":{}}},"SuppressedJoinPredicates":[20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38],"Version":1},"ExecutionMetricsKind":1}}]}',
                "QueryId": "",
                "ApplicationContext": {
                    "DatasetId": "41f7dfd2-71c9-4ad5-af19-cedd75514048",
                    "Sources": [
                        {
                            "ReportId": "0d29e969-2444-4ce9-9e52-e3cc936474ca",
                            "VisualId": "5a8d6dfdd561dd6a71a3",
                        }
                    ],
                },
            }
        ],
        "cancelQueries": [],
        "modelId": 165350,
    }
    params = {"synchronous": "true"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Activity-ID": "c3f74581-8bcd-cca5-7062-2cb380a00e8a",
        "Request-ID": "18281c9a-2be5-ac40-418a-a22b288943a7",
        "X-PowerBI-ResourceKey": "e4768909-4cc1-4164-a53a-4a5cab19ad76",
        "Content-Type": "application/json; charset=utf-8",
    }

    response = post(
        url=POWER_BI_URL,
        json=data,
        params=params,
        headers=headers,
    )

    data = response.json()

    only_power_values = data["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0][
        "DM0"
    ]

    cleaned_power_bi_values = []

    for i, value in enumerate(only_power_values):
        cleaned_power_bi_values.append(value["C"])

    assert len(cleaned_power_bi_values) > 0

    return cleaned_power_bi_values


def fetch_production(
    zone_key: str = "ZA",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:

    if target_datetime is not None:
        local_target_datetime = get(target_datetime).to(TIMEZONE)
        local_one_week_ago = now(TIMEZONE).shift(days=-7)

        if local_target_datetime < local_one_week_ago:
            raise NotImplementedError(
                f"No production data is available for {local_target_datetime}."
            )

    r = session or Session()

    res: Response = r.get(PRODUCTION_URL)
    assert res.status_code == 200, (
        "Exception when fetching production for "
        "{}: error when calling url={}".format(zone_key, PRODUCTION_URL)
    )

    csv_data = res.text.split("\r\n")

    power_bi_data = get_power_bi_values()

    merged_csv_bi_data = {}

    for i, row in enumerate(csv_data[1:]):
        date = row.split(",")[0]
        if len(date) > 10:
            date = get(date, "YYYY-MM-DD HH:mm:ss")
            sanitized_csv_data = ",".join(row.split(",")[1:])

            if sanitized_csv_data != ",,,,,,,,,,,,,,,,,,,":
                if date not in merged_csv_bi_data:
                    merged_csv_bi_data[date] = {}
                merged_csv_bi_data[date]["csv"] = sanitized_csv_data
                merged_csv_bi_data[date]["cleansed_csv"] = sanitized_csv_data

    for j, row in enumerate(power_bi_data):
        date = get(row[0])

        if date not in merged_csv_bi_data:
            merged_csv_bi_data[date] = {}

        merged_csv_bi_data[date]["power_bi"] = row[1:]

    merged_csv_bi_data = OrderedDict(sorted(merged_csv_bi_data.items()))

    last_cleansed_csv_len = -1
    cleansed_csv_value_updates = []

    for i, (key, value) in enumerate(merged_csv_bi_data.items()):

        curr_update_dict = {}

        # 1. CLEANING STEP: find all decimal places > 10, round to 3 decimal places and substitute comma with dot
        cleansed_csv_values = value["cleansed_csv"].split(",")
        memo_long_idcs = []
        for j, cleansed_csv_value in enumerate(cleansed_csv_values):
            if len(cleansed_csv_value) > 10:
                zeros = 0
                for k in range(len(cleansed_csv_value)):
                    if cleansed_csv_value[k] == "0":
                        zeros += 1
                    else:
                        break
                x_without_lead_zeros = cleansed_csv_value[zeros:]

                x_without_lead_zeros = round(
                    float(x_without_lead_zeros) / 10 ** len(x_without_lead_zeros), 3
                )
                cleansed_csv_values[j] = "0" * zeros + str(
                    int(x_without_lead_zeros * 1000)
                )

                cleansed_csv_values[j] = cleansed_csv_values[j][
                    : len(cleansed_csv_values[j]) - zeros
                ]

                memo_long_idcs.append(j)

        value["cleansed_csv"] = ",".join(cleansed_csv_values)

        comma_idcs = []
        for j, x in enumerate(value["cleansed_csv"]):
            if x == ",":
                comma_idcs.append(j)

        for memo_long_idx in memo_long_idcs:
            value["cleansed_csv"] = (
                value["cleansed_csv"][: comma_idcs[memo_long_idx - 1]]
                + "."
                + value["cleansed_csv"][comma_idcs[memo_long_idx - 1] + 1 :]
            )

            # Update curr_update_dict from 1. CLEANING STEP
            left_from_period = value["cleansed_csv"][
                : comma_idcs[memo_long_idx - 1]
            ].split(",")[-1]
            right_from_period = value["cleansed_csv"][
                comma_idcs[memo_long_idx - 1] + 1 :
            ].split(",")[0]
            old_updated_value = left_from_period + "," + right_from_period
            new_updated_value = left_from_period + "." + right_from_period
            curr_update_dict[old_updated_value] = new_updated_value

        # 2. CLEANING STEP: go through every value in powerbi list and check for floats. if float, check if value in csv row and replace comma with period
        if "power_bi" in value:
            for pb_value in value["power_bi"]:
                if isinstance(pb_value, float):
                    if str(pb_value).replace(".", ",") in value["cleansed_csv"]:
                        starting_idx = value["cleansed_csv"].index(
                            str(pb_value).replace(".", ",")
                        )
                        comma_idx = value["cleansed_csv"][starting_idx:].index(",")
                        value["cleansed_csv"] = (
                            value["cleansed_csv"][: comma_idx + starting_idx]
                            + "."
                            + value["cleansed_csv"][comma_idx + starting_idx + 1 :]
                        )

                        # Update curr_update_dict from 2. CLEANING STEP
                        left_from_period = value["cleansed_csv"][
                            : comma_idx + starting_idx
                        ].split(",")[-1]
                        right_from_period = value["cleansed_csv"][
                            comma_idx + starting_idx + 1 :
                        ].split(",")[0]
                        old_updated_value = left_from_period + "," + right_from_period
                        new_updated_value = left_from_period + "." + right_from_period
                        curr_update_dict[old_updated_value] = new_updated_value

        curr_cleansed_csv_len = len(value["cleansed_csv"].split(","))

        # 3. CLEANING STEP: if last_cleansed_csv_len != curr_cleansed_csv_len, then an update happened in the last few timestamps and value stayed the same until now. Go through cleansed_csv_value_updates in reverse order and check if there are matches with value['cleansed_csv']. If so, update value['cleansed_csv'] with the value from cleansed_csv_value_updates.

        if last_cleansed_csv_len != curr_cleansed_csv_len:
            for update_i in range(len(cleansed_csv_value_updates) - 1, -1, -1):
                break_outer_loop = False
                for key in cleansed_csv_value_updates[update_i]:
                    if key in value["cleansed_csv"]:
                        value["cleansed_csv"] = value["cleansed_csv"].replace(
                            key, cleansed_csv_value_updates[update_i][key]
                        )
                        # Update curr_update_dict from 3. CLEANING STEP
                        curr_update_dict[key] = cleansed_csv_value_updates[update_i][
                            key
                        ]
                        break_outer_loop = True
                        break
                if break_outer_loop:
                    break

        curr_cleansed_csv_len = len(value["cleansed_csv"].split(","))

        # This is useful if debugging corrupt rows
        # ---------------------------------------
        # if last_cleansed_csv_len != curr_cleansed_csv_len:
        #     print(f"{i}/{len(merged_csv_bi_data)}: {key}")
        #     print(f"last: {last_cleansed_csv_len} curr: {curr_cleansed_csv_len}")
        #     pp.pprint(value)
        #     print("-----------------------------------------------------")

        last_cleansed_csv_len = curr_cleansed_csv_len
        cleansed_csv_value_updates.append(curr_update_dict)

    # Mapping columns to keys
    # Helpful: https://www.eskom.co.za/dataportal/glossary/
    column_mapping = {
        0: "coal",  # Thermal_Gen_Excl_Pumping_and_SCO
        1: "unknown",  # Eskom_OCGT_SCO_Pumping             changed to unknown since negative oil is not possible
        2: "unknown",  # Eskom_Gas_SCO_Pumping              changed to unknown since negative gas is not possible
        3: "hydro",  # Hydro_Water_SCO_Pumping
        4: "hydro",  # Pumped_Water_SCO_Pumping
        5: "unknown",  # Thermal_Generation                 sum of 0, 1, 2, 3, 4. This value is not used.
        6: "nuclear",  # Nuclear_Generation
        7: "unknown",  # International_Imports
        8: "oil",  # Eskom_OCGT_Generation
        9: "gas",  # Eskom_Gas_Generation
        10: "oil",  # Dispatchable_IPP_OCGT
        11: "hydro",  # Hydro_Water_Generation
        12: "hydro",  # Pumped_Water_Generation
        13: "unknown",  # IOS_Excl_ILS_and_MLR              Interruption of Supply. Not used.
        14: "unknown",  # ILS_Usage                         Interruptible Load Shed = companies paid not to consume electricity. Not used.
        15: "unknown",  # Manual_Load_Reduction_MLR         MLS = forced load shedding. Not used.
        16: "wind",  # Wind
        17: "solar",  # PV
        18: "solar",  # CSP
        19: "unknown",  # Other_RE
    }

    all_data = []

    for i, (datetime_key, value) in enumerate(merged_csv_bi_data.items()):

        # The production values (MW) should never be negative. Use None, or omit the key if # a specific production mode is not known.
        # ---
        # storage values can be both positive (when storing energy) or negative (when the
        # storage is discharged).

        data = {
            "zoneKey": zone_key,
            "datetime": datetime_key.datetime,
            "production": {
                "biomass": None,
                "coal": 0.0,
                "gas": 0.0,
                "nuclear": 0.0,
                "oil": 0.0,
                "solar": 0.0,
                "wind": 0.0,
                "geothermal": None,
                "unknown": 0.0,
            },
            "storage": {"hydro": 0.0},
            "source": " https://www.eskom.co.za",
        }

        cleansed_csv_values = value["cleansed_csv"].split(",")

        storage_inversion_idcs = [3, 4, 12]
        production_idcs = [0, 1, 2, 6, 8, 9, 10, 11, 16, 17, 18, 19]

        # Omitted values
        # 5, 7, 13, 14, 15
        # TODO:
        # - 7 (international imports) can be further implemented in exchange function.

        for j, cleansed_csv_value in enumerate(cleansed_csv_values):
            if j in storage_inversion_idcs:
                data["storage"][column_mapping[j]] = round(
                    data["storage"][column_mapping[j]] + float(cleansed_csv_value) * -1,
                    2,
                )
            elif j in production_idcs:
                data["production"][column_mapping[j]] = round(
                    data["production"][column_mapping[j]] + float(cleansed_csv_value),
                    2,
                )

        all_data.append(data)

    return all_data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    pp.pprint(fetch_production())
