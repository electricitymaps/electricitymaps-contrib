from enum import Enum


class ParserDataType(Enum):
    CONSUMPTION = "consumption"
    CONSUMPTION_FORECAST = "consumptionForecast"
    DAYAHEAD_LOCATIONAL_MARGINAL_PRICE = "dayaheadLocationalMarginalPrice"
    EXCHANGE_FORECAST = "exchangeForecast"
    EXCHANGE = "exchange"
    GENERATION_FORECAST = "generationForecast"
    PRICE = "price"
    PRODUCTION = "production"
    PRODUCTION_PER_MODE_FORECAST = "productionPerModeForecast"
    REALTIME_LOCATIONAL_MARGINAL_PRICE = "realtimeLocationalMarginalPrice"
    # TODO: Double check if we should keep them here?
    PRODUCTION_CAPACITY = "productionCapacity"

    def __str__(self) -> str:
        return self.value


ALL_DATA_TYPES = [dt.value for dt in ParserDataType]
EXCHANGE_DATA_TYPES = [ParserDataType.EXCHANGE, ParserDataType.EXCHANGE_FORECAST]
LMP_DATA_TYPES = [
    ParserDataType.REALTIME_LOCATIONAL_MARGINAL_PRICE,
    ParserDataType.DAYAHEAD_LOCATIONAL_MARGINAL_PRICE,
]
