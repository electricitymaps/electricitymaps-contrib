"""Data Center model definitions."""

from pydantic.v1 import BaseModel, validator

from electricitymap.contrib.types import ZoneKey


class StrictBaseModel(BaseModel):
    class Config:
        extra = "forbid"


class DataCenter(BaseModel):
    provider: str
    lonlat: tuple[float, float]
    displayName: str
    region: str
    zoneKey: ZoneKey
    operationalSince: str | None
    operationalUntil: str | None
    status: str | None
    source: str | None

    @property
    def ID(self) -> str:
        return f"{self.provider}-{self.region}"

    @validator("provider", "region", "displayName")
    def string_not_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Value must be a non-empty string")
        return v

    @validator("lonlat")
    def lonlat_valid(cls, v):
        lon, lat = v
        if not (-180 <= lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @validator("zoneKey")
    def zone_key_exists(cls, v):
        # Import here to avoid circular dependency
        from electricitymap.contrib.config import ZONES_CONFIG

        if v not in ZONES_CONFIG:
            raise ValueError(
                f"Data center zone key {v} is not one of the allowed zone keys: {ZONES_CONFIG.keys()}"
            )
        return v


class DataCenters(BaseModel):
    """Container for data centers."""

    data_centers: list[DataCenter]

    class Config:
        extra = "forbid"

    # check that the ID for each data center is unique
    @validator("data_centers")
    def ids_are_unique(cls, v):
        ids = set()
        for data_center in v:
            if data_center.ID in ids:
                raise ValueError(f"Duplicate data center ID found: {data_center.ID}")
            ids.add(data_center.ID)
        return v
