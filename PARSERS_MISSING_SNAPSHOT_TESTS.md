# Parsers Missing Snapshot Tests

## Overview

This document tracks parsers that are currently missing snapshot tests. Out of **104 active parsers**, **39 parsers (37.5%)** do not have snapshot tests.

Snapshot tests are important for:
- Ensuring parser output format consistency
- Catching regressions in data structure changes
- Validating parser behavior across updates
- Documenting expected output format

## Summary Statistics

- **Total Active Parsers**: 104
- **Parsers with Snapshot Tests**: 65 (62.5%)
- **Parsers Missing Snapshot Tests**: 39 (37.5%)

## Parsers Missing Snapshot Tests

### Africa (1 parser)
- `NG.py` - Nigeria

### Americas (8 parsers)

#### Canada (6 parsers)
- `CA_BC.py` - British Columbia
- `CA_NB.py` - New Brunswick
- `CA_NS.py` - Nova Scotia
- `CA_QC.py` - Quebec
- `CA_SK.py` - Saskatchewan
- `YUKONENERGY.py` - Yukon

#### Central America & Caribbean (1 parser)
- `BB.py` - Barbados

#### South America (1 parser)
- `US_PREPA.py` - Puerto Rico Electric Power Authority

### Asia (9 parsers)

#### India (4 parsers)
- `IN_DL.py` - Delhi
- `IN_MH.py` - Maharashtra
- `IN_PB.py` - Punjab
- `IN_UT.py` - Uttarakhand
- `IN_WE.py` - West (region)

#### Japan (1 parser)
- `JP_KN.py` - Kansai

#### Middle East (3 parsers)
- `GCCIA.py` - Gulf Cooperation Council Interconnection Authority
- `GSO.py` - Gulf States Organization
- `IL.py` - Israel
- `KW.py` - Kuwait

#### Southeast Asia (2 parsers)
- `SEAPA.py` - Southeast Asia Power Alliance
- `TH.py` - Thailand
- `VN.py` - Vietnam

### Europe (12 parsers)

#### Nordic Countries (3 parsers)
- `AX.py` - Åland Islands
- `NO-NO4_SE.py` - Norway-Sweden interconnection
- `SE.py` - Sweden

#### Western Europe (3 parsers)
- `ECO2MIX.py` - French grid data (RTE)
- `NL.py` - Netherlands
- `PrinceEdwardIsland.py` - Special case parser

#### Eastern Europe (1 parser)
- `UA.py` - Ukraine

#### British Isles (3 parsers)
- `ELEXON.py` - UK electricity market operator
- `GB_ORK.py` - Orkney Islands
- `NI.py` - Northern Ireland

#### Other (2 parsers)
- `BORNHOLM_POWERLAB.py` - Bornholm Island grid
- `NED.py` - Network operator

### Oceania (0 parsers)
All Oceania parsers have snapshot tests.

### Multi-Region/Other (1 parser)
- `MN.py` - Mongolia

### Special/Utility Parsers (4 parsers)
- `ajenti.py` - Ajenti data source
- `eSett.py` - Nordic balance settlement
- `email_grid_alerts.py` - Email-based grid alerts
- `occtonet.py` - Organization for Cross-regional Coordination of Transmission Operators (Japan)

## Priority Recommendations

### High Priority (Active, Widely-Used Regions)
These parsers serve major population centers or important grid operators:

1. **IN_DL** - Delhi, India (major metropolitan area)
2. **CA_QC** - Quebec, Canada (major province)
3. **CA_BC** - British Columbia, Canada (major province)
4. **NL** - Netherlands (major EU country)
5. **IL** - Israel (significant grid)
6. **TH** - Thailand (major Southeast Asian country)
7. **VN** - Vietnam (major Southeast Asian country)
8. **UA** - Ukraine (European grid)

### Medium Priority (Regional Coverage)
Important for regional grid coverage:

1. Indian regional parsers (IN_MH, IN_PB, IN_UT, IN_WE)
2. Canadian provinces (CA_NB, CA_NS, CA_SK)
3. Japanese region (JP_KN)
4. UK regions (ELEXON, GB_ORK, NI)

### Lower Priority (Specialized/Small Coverage)
Less critical but should still have tests:

1. Utility parsers (ajenti, eSett, email_grid_alerts, occtonet)
2. Small island grids (AX, BB, BORNHOLM_POWERLAB)
3. Special interconnections (NO-NO4_SE, PrinceEdwardIsland)
4. Regional organizations (GCCIA, GSO, SEAPA)

## Next Steps

1. **Create snapshot tests** for high-priority parsers first
2. **Establish patterns** for testing different parser types (production, consumption, exchange)
3. **Document testing guidelines** for new parser contributions
4. **Add CI checks** to ensure new parsers include snapshot tests
5. **Gradually add tests** for medium and lower priority parsers

## Testing Guidelines for Contributors

When adding snapshot tests for these parsers:

1. **Mock HTTP responses** - Use `requests_mock` to provide sample API responses
2. **Test each method** - Add tests for all implemented methods (fetch_production, fetch_consumption, fetch_exchange, fetch_price)
3. **Use realistic data** - Mock responses should match actual API response format
4. **Test edge cases** - Include tests for null/missing data, different time zones, etc.
5. **Follow naming convention** - Test file: `test_<PARSER>.py`, Snapshot: `test_<PARSER>.ambr`

### Example Test Structure

```python
def test_parser_production(adapter, session, snapshot):
    session.mount("https://api.example.com", adapter)
    output = parser.fetch_production("ZONE_KEY", session)
    assert output == snapshot
```

## References

- Parser directory: `/electricitymap/contrib/parsers/`
- Test directory: `/electricitymap/contrib/parsers/tests/`
- Snapshot directory: `/electricitymap/contrib/parsers/tests/__snapshots__/`
- Testing framework: pytest + syrupy (snapshot testing)

---

**Last Updated**: 2026-02-04  
**Total Parsers Analyzed**: 104  
**Coverage**: 62.5% (65/104 parsers have snapshot tests)
