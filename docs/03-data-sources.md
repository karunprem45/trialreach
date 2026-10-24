# 03 · Data Sources & Contracts (fetch_data.py)

All endpoints are public, no key needed. Tested live 2026-10-24. Use `requests` with 60 s timeout and
3 retries. Save each output as JSON in `data/`. Write `data/fetched_at.txt` with the time.

ArcGIS base: `https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL`
ArcGIS layers return at most ~1000 rows per call: page with `resultOffset` + `resultRecordCount=1000`
until a page returns < 1000 rows and no `exceededTransferLimit`. Use `outSR=4326`, `f=json`.

## 1. Town shapes → `data/towns.geojson`
`{base}/Census2020_Towns/MapServer/2/query` with `where=1=1, outFields=TOWN20,COUNTY20, returnGeometry=true,
outSR=4326, maxAllowableOffset=0.003, geometryPrecision=4, f=geojson`. Expect **351** features. ~200 KB.

## 2. Town attributes → `data/towns.json`
Same layer, `returnGeometry=false`, fields `TOWN20, COUNTY20, POP2020, INTPTLAT20, INTPTLON20`
(lat/lon are strings like "+42.3678582" → cast to float). Names are UPPERCASE. Expect **351**.

## 3. CDC PLACES → `data/cdc_places.json`
`https://data.cdc.gov/resource/swc5-untb.json` with
`$select=year,locationname,measureid,measure,data_value,low_confidence_limit,high_confidence_limit,totalpopulation`,
`$where=stateabbr='MA' AND data_value_type='Crude prevalence' AND measureid in('DIABETES','OBESITY','DEPRESSION','BPHIGH','CHD','COPD','CASTHMA','STROKE','CANCER')`,
`$limit=5000`. Expect **126** rows (14 counties × 9). Numbers arrive as strings. `locationname` is Title Case → upper() to join.

## 4. ClinicalTrials.gov → `data/trials.json`
`https://clinicaltrials.gov/api/v2/studies` with `query.locn=Massachusetts, query.cond=<term>,
filter.overallStatus=RECRUITING, pageSize=1000, fields=NCTId,BriefTitle,Condition,Phase,LocationFacility,LocationCity,LocationState,LocationGeoPoint`.
Follow `nextPageToken` until absent.

| measure id | label | search term | expected trials |
|---|---|---|---|
| DIABETES | Diabetes | diabetes | ~92 |
| OBESITY | Obesity | obesity | ~55 |
| DEPRESSION | Depression | depression | ~104 |
| BPHIGH | High blood pressure | hypertension | ~53 |
| CHD | Coronary heart disease | coronary artery disease | ~51 |
| COPD | COPD | COPD | ~26 |
| CASTHMA | Asthma | asthma | ~20 |
| STROKE | Stroke | stroke | ~56 |
| CANCER | Cancer | cancer | ~1,170 |

Response path: `studies[].protocolSection` → `identificationModule.nctId/briefTitle`,
`conditionsModule.conditions`, `designModule.phases`, `contactsLocationsModule.locations[]` with
`facility, city, state, geoPoint{lat,lon}`.
**Slim before saving** (raw is 15 MB, slim ~700 KB): keep only `{nct, title, conditions, phases,
sites:[{facility, city, lat, lon}]}` and only locations where `state == "Massachusetts"` and geoPoint exists.
Save as `{measure_id: [slim studies]}`.

## 5. Hospitals → `data/hospitals.json`
`{base}/Hospitals/MapServer/0/query`, `where=1=1`, fields `FACILITY_NAME,FACILITY_TYPE,MUNICIPALITY,COUNTY,ICU,MED_SURG,PEDIATRIC`,
`returnGeometry=true` → store point as `lat`/`lon` (geometry.y / geometry.x). Expect **103** (70 are "Acute Hospital"). Beds may be null → 0.

## 6. Environmental-justice block groups → `data/ej.json`
`{base}/EJ2020/MapServer/0/query`, `where=EJ='Yes'`, fields `MUNICIPALITY,TOTAL_POP,PCT_MINORITY,LIMENGHHPCT,BG_MHHI,EJ_CRIT_DESC`, no geometry, paged.
Expect **2,604**. MUNICIPALITY is Title Case; all names match towns.json after upper().

## Sources to cite in the app footer
ClinicalTrials.gov (U.S. NLM) · CDC PLACES 2023 county crude prevalence · MassGIS (Census 2020 towns, hospitals, EJ 2020 block groups).
