# Emission factors sources

The emission factors used by Electricity Maps depends on the specific region.

Our default emission factors come from the [IPCC (2014) Fith Assessment Report](https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf#page=7) report, and are fully described in our [wiki](https://github.com/electricitymaps/electricitymaps-contrib/wiki/Default-emission-factors).

For certain areas and zones (all of Europe and US, along with a few other countries), we have more specific emission factors.
The actual numbers used (as well as a link to the source) can be found in the [config/zones YAML file](https://github.com/electricitymaps/electricitymaps-contrib/tree/master/config/zones) for each specific zone.

For Europe, the methodology for calculating emission factors is detailed in our [wiki page for EU emission factors](https://github.com/electricitymaps/electricitymaps-contrib/wiki/EU-emission-factors). The same applies for [US emission factors](https://github.com/electricitymaps/electricitymaps-contrib/wiki/US-emission-factors).

For Australia, a [reproducible NGER calculation](notebooks/au_emission_factors/README.md)
provides regional fossil-fuel direct emission factors for 2024–25. These use gross
generation and require reconciliation with the production data's generation basis
before deployment. The notebook documents the input data and remaining lifecycle
accounting requirements.
