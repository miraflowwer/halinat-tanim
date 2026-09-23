# TANIM Data Sources

These sources inform TANIM data structure, names, geography, and broad context. They do not provide the synthetic agricultural values in the demo dataset.

## Philippine Standard Geographic Code

- Source name: Philippine Standard Geographic Code (PSGC), Second Quarter 2026
- Institution: Philippine Statistics Authority (PSA)
- Resource: PSGC as of 30 June 2026, publication datafile and national and provincial summary
- Use in TANIM: official geographic names, PSGC codes, hierarchy, and supported Luzon coverage
- Retrieval date: 2026-09-24
- URL: [PSGC summary and downloads](https://psa.gov.ph/classification/psgc/summary)
- License: CC BY 4.0, as stated by PSA for website content unless otherwise noted
- Transformation: TANIM keeps Regions, Provinces, and Municipalities or Cities in Luzon. It omits barangays. The registry has 8 regions, 38 provinces, and 771 municipalities or cities. NCR units link directly to NCR because PSGC has no provinces in NCR.

The geographic names and codes were loaded from the public PSGC Cloud API as a structured convenience copy. The PSA Second Quarter 2026 summary and release notes were checked for current totals and relevant coverage updates. PSGC Cloud is a third-party service and is not operated by PSA. PSA remains the source of authority.

- Source name: PSGC Cloud API v2
- Institution: PSGC Cloud, third-party service
- Resource: regions, provinces, and cities-municipalities endpoints
- Use in TANIM: structured extraction of PSGC names, codes, and parent names
- Retrieval date: 2026-09-24
- URLs: [regions](https://psgc.cloud/api/v2/regions), [provinces](https://psgc.cloud/api/v2/provinces), [cities and municipalities](https://psgc.cloud/api/v2/cities-municipalities)
- License: no separate license claim is made for the API copy
- Transformation: filtered to Luzon and to City or Municipality records. The PSA summary was used to cross-check aggregate coverage counts. Barangays, sub-municipalities, and special geographic area rows are not included.

## Crop and price context

- Source name: Commercial Crops: Farmgate Prices, by Month, Region and Province
- Institution: Philippine Statistics Authority (PSA)
- Resource: OpenSTAT table 2M4AFN08
- Use in TANIM: crop and price data concepts, reporting frequency, and available geographic levels
- Retrieval date: 2026-09-24
- URL: [PSA OpenSTAT metadata](https://openstat.psa.gov.ph/Metadata/2M4AFN08)
- License: PSA website content is CC BY 4.0 unless otherwise noted
- Transformation: used as a reference for the shape of crop price history. TANIM values are synthetic and are not PSA observations or farmgate estimates.

- Source name: Price Monitoring
- Institution: Department of Agriculture (DA)
- Resource: Weekly Average Retail Prices and Daily Retail Price Range
- Use in TANIM: marketed crop coverage and broad retail price context
- Retrieval date: 2026-09-24
- URL: [DA Price Monitoring](https://www.da.gov.ph/price-monitoring/)
- License: no specific data license was stated on the page
- Transformation: used for crop coverage and broad retail market context. Demo price baselines are manually set and are not statistically calibrated to the published prices. TANIM does not copy those prices into the synthetic series.

- Source name: Plants of the World Online
- Institution: Royal Botanic Gardens, Kew
- Resource: botanical names and plant taxonomy database
- Use in TANIM: scientific names in the crop registry
- Retrieval date: 2026-09-24
- URL: [Plants of the World Online](https://powo.science.kew.org/)
- License: see Kew's terms for database use
- Transformation: consulted as a reference when reviewing selected scientific names. This does not mean every registry name was checked against POWO. TANIM does not use the database to generate agricultural measurements.

## Synthetic data rule

All generated prices, reference areas, planned areas, supply ratios, and soil suitability labels use `data_kind = synthetic_demo`. PSA, DA, Kew, and PSGC Cloud did not publish those generated values. Read the method and unit notes in each generated dataset's `metadata.json`.
