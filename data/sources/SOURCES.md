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

- Source name: Price Monitoring report, 25 February 2026
- Source ID: `DA-AMAS-PM-2026-02-25`
- Institution: Department of Agriculture (DA)
- Resource: Weekly Average Retail Prices and Daily Retail Price Range
- Use in TANIM: cross-checks commodity coverage, including White Potato, Chayote, Celery, and Baguio Beans
- Retrieval date: 2026-09-24
- URL: [DA Price Monitoring, 25 February 2026](https://www.da.gov.ph/wp-content/uploads/2026/02/Price-Monitoring-February-25-2026.pdf)
- License: no specific data license was stated in the report
- Transformation: used to identify relevant commodity names and coverage. The report's prices are not copied into generated TANIM values.

- Source name: 2022 Crops Production in Quezon
- Source ID: `PSA-QUEZON-CRPS-2022`
- Institution: Philippine Statistics Authority (PSA), CALABARZON
- Resource: Statistical Release No. 2025-172
- Use in TANIM: cross-checks a broad local crop list, including vegetables, root crops, fruits, and industrial crops
- Retrieval date: 2026-09-24
- URL: [PSA 2022 Crops Production in Quezon](https://rsso04a.psa.gov.ph/sites/default/files/attachment-dir/Region04A-56_SR%20No.%202025-172_2022%20Crops%20Production%20in%20Quezon.pdf)
- License: PSA website content is CC BY 4.0 unless otherwise noted
- Transformation: used as a crop coverage and naming reference. The report's production values are not copied into generated TANIM data. Its Quezon coverage does not imply that each listed crop is produced in every TANIM geography.

- Source name: 2025 Vegetable and Root Crops Situation in Quezon
- Source ID: `PSA-QUEZON-VRC-2025`
- Institution: Philippine Statistics Authority (PSA), CALABARZON
- Resource: Statistical Release No. 2026-100
- Use in TANIM: cross-checks current vegetable and root crop names, including Kangkong, Radish, Habitchuelas, Chayote, and Patola
- Retrieval date: 2026-09-24
- URL: [PSA 2025 Vegetable and Root Crops Situation in Quezon](https://rsso04a.psa.gov.ph/sites/default/files/attachment-dir/Region04A-56_SR%20No.%202026-100_2025%20Vegetable%20and%20Root%20Crops%20Situation%20in%20Quezon.pdf)
- License: PSA website content is CC BY 4.0 unless otherwise noted
- Transformation: used as a crop coverage and naming reference. The report's production values are not copied into generated TANIM data.

- Source name: 2010-2025 Strawberry Situationer: Province of Benguet
- Source ID: `PSA-BENGUET-STRAWBERRY-2010-2025`
- Institution: Philippine Statistics Authority (PSA), Cordillera Administrative Region
- Resource: Special Release SSR 2026-49, released 30 June 2026
- Use in TANIM: confirms strawberry as a significant Benguet fruit crop
- Retrieval date: 2026-09-24
- URL: [PSA Benguet strawberry situationer](https://rssocar.psa.gov.ph/content/2010-2025-strawberry-situationer-province-benguet)
- License: PSA website content is CC BY 4.0 unless otherwise noted
- Transformation: used to add strawberry to the crop registry. Its production values are not copied into TANIM data.

- Source name: 2025 First Quarter Other Crops Production Situation in Benguet
- Source ID: `PSA-BENGUET-CRPS-2025-Q1`
- Institution: Philippine Statistics Authority (PSA), Cordillera Administrative Region
- Resource: first quarter 2025 crop production report
- Use in TANIM: confirms strawberry, lemon, and Chinese cabbage crop coverage in Benguet
- Retrieval date: 2026-09-24
- URL: [PSA Benguet first quarter crop report](https://rssocar.psa.gov.ph/content/2025-first-quarter-other-crops-production-situation-benguet)
- License: PSA website content is CC BY 4.0 unless otherwise noted
- Transformation: used to review crop names and registry coverage. Its production values are not copied into TANIM data.

- Source name: Situation of Selected High Value Crops of Benguet, January-June 2025
- Source ID: `PSA-BENGUET-HV-2025-H1`
- Institution: Philippine Statistics Authority (PSA), Cordillera Administrative Region
- Resource: first semester 2025 high value vegetable report
- Use in TANIM: confirms Chinese cabbage and sweet peas as marketed Benguet crops
- Retrieval date: 2026-09-24
- URL: [PSA Benguet high value crops report](https://rssocar.psa.gov.ph/content/situation-selected-high-value-crops-benguet-january-june-2025)
- License: PSA website content is CC BY 4.0 unless otherwise noted
- Transformation: used for crop coverage and naming. Its production values are not copied into TANIM data.

- Source name: Plants of the World Online
- Institution: Royal Botanic Gardens, Kew
- Resource: botanical names and plant taxonomy database
- Use in TANIM: scientific names in the crop registry
- Retrieval date: 2026-09-24
- URL: [Plants of the World Online](https://powo.science.kew.org/)
- License: see Kew's terms for database use
- Transformation: consulted as a reference when reviewing selected scientific names. This does not mean every registry name was checked against POWO. TANIM does not use the database to generate agricultural measurements.

## Synthetic data rule

All generated prices, reference areas, planned areas, supply ratios, and soil suitability labels use `data_kind = synthetic_demo`. PSA, DA, Kew, and PSGC Cloud did not publish those generated values. NCCAG and BSWM suitability layers are not used to create the generated suitability rows. Read the method and unit notes in each generated dataset's `metadata.json`.

## TANIM crop scope inventory

`data/registry/crop_scope_inventory.csv` records the food-crop coverage decisions for Luzon under the [product crop scope](../../requirements/PRODUCT_REQUIREMENTS.md). It is cross-checked against DA price monitoring and PSA crop reports from Quezon and Benguet. The inventory records aliases, source context, and explicit category exclusions. The latest review added Strawberry, Lemon, Chinese cabbage, and Sweet peas after checking the Benguet reports. A newly identified relevant crop must be added with all required TANIM datasets and a deliberate English and Tagalog profile before it is supported.

These sources support coverage review and naming context. They do not publish the generated profile, area, supply, or suitability values. Crops reported for Quezon are not assumed to be grown in every supported Luzon municipality. Rice, corn, plantation crops, livestock, fisheries, ornamentals, and beverage or industrial crops outside the current MVP categories are listed as explicit exclusions with reasons.

## Suitability source category

- Source name: National Color-Coded Agricultural Guide (NCCAG) Map 2.0
- Source ID: `DA-NCCAG-2023` (documentation only, not used by the generated suitability data)
- Institution: Department of Agriculture (DA)
- Resource: updated color-coded agricultural map article
- Use in TANIM: conceptual reference for the type of crop and location suitability guidance that may inform future product work
- Retrieval date: 2026-09-24
- URL: [DA NCCAG Map 2.0 announcement](https://www.da.gov.ph/da-launches-updated-color-coded-agri-map-to-help-farmers-address-climate-vulnerability-and-boost-yield-income/)
- License: no specific data license was stated on the article
- Transformation: no NCCAG or Bureau of Soils and Water Management location-level suitability layer was selected or used for this dataset. Generated suitability rows are TANIM synthetic demo context and cite the TANIM method identifier only.

## Local supply map geometry

- Source name: geoBoundaries Open Philippines ADM1
- Boundary ID: `PHL-ADM1-36201628`
- Boundary year: 2020
- Source agencies in metadata: National Mapping and Resource Information Authority (NAMRIA), Philippine Statistics Authority (PSA), and OCHA Philippines
- Resource: [geoBoundaries PHL ADM1 metadata](https://www.geoboundaries.org/api/current/gbOpen/PHL/ADM1/)
- Geometry: [pre-simplified GeoJSON](https://github.com/wmgeolab/geoBoundaries/raw/41af8f1/releaseData/gbOpen/PHL/ADM1/geoBoundaries-PHL-ADM1_simplified.geojson)
- Source license in metadata: CC BY 3.0 IGO. geoBoundaries also states that its generated `gbOpen` files are CC BY 4.0. Keep both notices and check the individual source license before reuse outside TANIM.
- Use in TANIM: local display boundaries for the eight Luzon regions in the current product scope
- Transformation: selected the eight Luzon region features from the source's already simplified GeoJSON, removed other regions, and added TANIM geography IDs and canonical region names. No boundaries were drawn or edited.
- Usage status: redistributed in `data/geometry/luzon-regions.geojson` with source attribution. This layer is a local demo display aid, not an official legal map.

## TANIM synthetic method identifiers

The generated rows use method identifiers when an external source did not directly shape a value:

- `TANIM-SYNTH-CROP-PROFILE-V1` supplies deliberate English and Tagalog crop profile text for each active crop.
- `TANIM-SYNTH-REFERENCE-AREA-V1` supplies synthetic reference area values.
- `TANIM-SYNTH-CURRENT-SUPPLY-V1` supplies the September 2026 current map context.
- `TANIM-SYNTH-FUTURE-SUPPLY-CONTEXT-V1` supplies future planning context rows.
- `TANIM-SYNTH-SOIL-BASELINE-V1` supplies the synthetic suitability baseline.

These identifiers mean that a documented method informed the model. They never mean that TANIM published or observed the generated number in an external source.
