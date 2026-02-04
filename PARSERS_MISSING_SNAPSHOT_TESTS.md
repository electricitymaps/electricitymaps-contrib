# Parsers Missing Snapshot Tests

## Overview

This document tracks parsers that are currently missing snapshot tests. Out of **101 active parsers**, **45 parsers (44.6%)** do not have snapshot tests.

Snapshot tests are important for:
- Ensuring parser output format consistency
- Catching regressions in data structure changes
- Validating parser behavior across updates
- Documenting expected output format

## Summary Statistics

- **Total Active Parsers**: 101
- **Parsers with Snapshot Tests**: 56 (55.4%)
- **Parsers Missing Snapshot Tests**: 45 (44.6%)
  - Without any test file: 44
  - With test file but missing snapshot: 1

## Parsers Missing Snapshot Tests

### Africa (1 parser)
- `NG.py` - Nigeria

### Americas (14 parsers)

#### Canada (6 parsers)
- `CA_BC.py` - British Columbia
- `CA_NB.py` - New Brunswick
- `CA_NS.py` - Nova Scotia
- `CA_QC.py` - Quebec
- `CA_SK.py` - Saskatchewan
- `YUKONENERGY.py` - Yukon

#### Central America & Caribbean (1 parser)
- `BB.py` - Barbados

#### Mexico (1 parser)
- `CENACE.py` - Centro Nacional de Control de Energía

#### South America (6 parsers)
- `PrinceEdwardIsland.py` - Prince Edward Island (Note: This appears to be misnamed/misplaced)
- `US_PREPA.py` - Puerto Rico Electric Power Authority

### Asia (14 parsers)

#### India (6 parsers)
- `IN_DL.py` - Delhi
- `IN_HP.py` - Himachal Pradesh
- `IN_KA.py` - Karnataka
- `IN_MH.py` - Maharashtra
- `IN_PB.py` - Punjab
- `IN_UT.py` - Uttarakhand
- `IN_WE.py` - West (region)

#### Japan (2 parsers)
- `JP_KN.py` - Kansai
- `JP_SK.py` - Shikoku

#### Middle East (3 parsers)
- `GCCIA.py` - Gulf Cooperation Council Interconnection Authority
- `GSO.py` - Gulf States Organization
- `IL.py` - Israel
- `KW.py` - Kuwait

#### Southeast Asia (3 parsers)
- `SEAPA.py` - Southeast Asia Power Alliance
- `SG.py` - Singapore (has test file `test_SG.py` but missing snapshot `.ambr` file)
- `TH.py` - Thailand
- `VN.py` - Vietnam

### Europe (14 parsers)

#### Nordic Countries (2 parsers)
- `AX.py` - Åland Islands
- `NO-NO4_SE.py` - Norway-Sweden interconnection
- `SE.py` - Sweden

#### Western Europe (5 parsers)
- `CH.py` - Switzerland
- `NL.py` - Netherlands

#### Eastern Europe (2 parsers)
- `UA.py` - Ukraine

#### British Isles (2 parsers)
- `ELEXON.py` - UK electricity market operator
- `GB_ORK.py` - Orkney Islands
- `NI.py` - Northern Ireland

#### France (1 parser)
- `ECO2MIX.py` - French grid data
- `FR_O.py` - French overseas territories

### Oceania (0 parsers)
All Oceania parsers have snapshot tests.

### Multi-Region/Utility Parsers (2 parsers)
- `MN.py` - Mongolia
- `NED.py` - Network operator

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
5. **CH** - Switzerland (major EU country)
6. **IL** - Israel (significant grid)
7. **SG** - Singapore (has test but missing snapshot)
8. **TH** - Thailand (major Southeast Asian country)
9. **VN** - Vietnam (major Southeast Asian country)
10. **UA** - Ukraine (European grid)

### Medium Priority (Regional Coverage)
Important for regional grid coverage:

1. Indian regional parsers (IN_HP, IN_KA, IN_MH, IN_PB, IN_UT, IN_WE)
2. Canadian provinces (CA_NB, CA_NS, CA_SK)
3. Japanese regions (JP_KN, JP_SK)
4. UK regions (ELEXON, GB_ORK, NI)

### Lower Priority (Specialized/Small Coverage)
Less critical but should still have tests:

1. Utility parsers (ajenti, eSett, email_grid_alerts, occtonet)
2. Small island grids (AX, BB)
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
**Total Parsers Analyzed**: 101  
**Coverage**: 55.4% (56/101 parsers have snapshot tests)
