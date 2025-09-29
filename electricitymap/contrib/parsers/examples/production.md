# Production Parser

## Arguments

`zone_key`

> Type: `str` - Native Python string object. <br/>
> Description: <br/>
> Passed to the parser as a unique identifier for each zone.

---

`session`

> Type: `request.Session` - A Request Session object. <br/>
> Description: <br/>
> Passed to the parser in order to reuse an existing connection. Should default to `request.Session()`.

---

`target_datetime`

> Type: Datetime | None - Native python datetime or None. <br/>
> Description: <br/>
> Passed to the parser if the backend request to fetch data from a specific datetime. Should default to `None`.

---

`logger`

> Type: logging.Logger - Native python logging object. <br/>
> Description: <br/>
> Passed to the parser by the backend to enable public logging. Should default to `logging.getLogger(__name__)`.

## Return value signature

The parser should return a list of ProductionBreakdown objects.

```python
from logging import get_logger
from datetime import datetime, timezone
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList


logger = getLogger(__name__)
production_list = ProductionBreakdownList(logger=logger)
production_list.append(
            zoneKey="AT",
            datetime= datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(
                biomass=10,
                coal=4,
                gas=3,
                hydro=1,
                nuclear=None,
                oil=None,
                solar=10,
                wind=10,
                geothermal=10,
                unknown=10
            ),
            storage=StorageMix(hydro=-10),
            source="someservice.com",
        )
production_list.to_list()
```

Note: If data from a production mode is missing it should be omitted or returned as `None` like the above example, _NOT_ `0`.
