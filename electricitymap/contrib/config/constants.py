# Note: web/src/helpers.js contains some of the same information.

EXCHANGE_DATA_TYPES = ["exchange", "exchangeForecast"]

WEATHER_GFS_KEYS = ["wind", "solar", "temperature", "dewpoint", "precipitation"]
WEATHER_DATABASE_KEYS = [
    "wind_x",
    "wind_y",
    "solar",
    "temperature",
    "dewpoint",
    "precipitation",
]
OTHER_FORECAST_KEYS = [
    "price",
    "production",
    "consumption",
]

# Note: this is sorted for plotting purposes
PRODUCTION_MODES = [
    "nuclear",
    "geothermal",
    "biomass",
    "coal",
    "wind",
    "solar",
    "hydro",
    "gas",
    "oil",
    "unknown",
]
FORECASTED_PRODUCTION_MODES = [
    "solar",
    "wind",
]
STORAGE_MODES = [
    "battery",
    "hydro",
]


# TODO(olc): Find a more explicit name for `ENERGIES`
# TODO(olc): This is forecast specific, so it should not be here.
ENERGIES = PRODUCTION_MODES + [f"{s} discharge" for s in STORAGE_MODES]

BATCH_SIZE = 500
PLOT_COLUMNS = {
    "consumptionForecast": {"title": "consumption forecast", "col": "value"},
    "consumption": {"title": "consumption", "col": "consumption"},
    "production": {"title": "production total", "col": "prod_total"},
    "price": {"title": "price", "col": "price"},
    "generationForecast": {"title": "generation forecast", "col": "value"},
    "exchange": {"title": "exchange", "col": "netFlow"},
    "exchangeForecast": {"title": "exchange forecast", "col": "netFlow"},
    "weatherForecast": {"title": "weather forecast", "col": "value"},
}

MODE_COLORS = {
    "wind": "#74cdb9",
    "solar": "#f27406",
    "hydro": "#2772b2",
    "battery charge": "lightgray",
    "hydro charge": "#0052cc",
    "hydro discharge": "#0052cc",
    "battery discharge": "lightgray",
    "biomass": "#166a57",
    "geothermal": "yellow",
    "nuclear": "#AEB800",
    "gas": "#bb2f51",
    "coal": "#ac8c35",
    "oil": "#867d66",
    "unknown": "lightgray",
}

weatherForecastSchemaVersion = 3
