# Parsers

A parser is a file or script that is responsible for fetching data for a particular zone or set of zones and/or exchanges.

Parsers are built using public URLs that has data available at hourly or better granularity. For a full list of technical requirements regarding data sources check out our wiki page: [Technical requirements for data sources][wiki data source req]

If you want to **create a new parser** you can check out the specific parser function documentation in the [examples folder](/parsers/examples/) or take a look at one of our existing parsers.
Note: Not all of our existing parsers have been updated with the latest syntax and might be functional but outdated.

## Different kinds of parsers

Right now we support the following parsers:

### Live parsers:

- #### Production parsers:
  These parsers are our primary source of data and parse aggregated production data from our sources.
- #### Consumption parsers:
  Like the production parsers these parse aggregated data but instead of parsing what a zone produces they parse the zones electricity consumption.
- #### Price parsers:
  Price parsers parse electricity cost before any potential taxes or transmission fees and should return the price at hourly or better resolution even if the _Market Time Unit_ or MTU, is longer.
- #### Production Per Unit parsers:
  These parsers parse the production of individual production units or power plants for a zone.
- #### Exchange parsers:
  These parsers parse the net flow, exchange, of electricity between two zones.

### Forecast parsers:

- #### Generation Forecast parser:
  Parse the forecasted total generation for a zone.
- #### Generation Per Mode Forecast parser:
  Similar to the generation forecast parser but parse forecasted generation per production mode.
- #### Consumption Forecast parser:
  Parse the forecasted consumption for a zone.
- #### Exchange Forecast parser:
  Parse the forecasted net flow, exchange, between two zones.

# Archived parsers

Parsers that are no longer used or have been broken for a long time reside in the [/archived](/parsers/archived/) folder.

[wiki data source req]: https://github.com/electricitymaps/electricitymaps-contrib/wiki/Technical-requirements-for-parser-data
