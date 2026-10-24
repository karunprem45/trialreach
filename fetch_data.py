"""Download all TrialReach datasets into data/ (see docs/03-data-sources.md).

Run once:  python fetch_data.py
The app then reads data/ and works offline.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

try:
    import truststore

    truststore.inject_into_ssl()  # fixes Mac SSL errors
except ImportError:
    pass

DATA = Path("data")
TIMEOUT = 60
RETRIES = 3
PAGE = 1000

ARCGIS = "https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL"
PLACES_URL = "https://data.cdc.gov/resource/swc5-untb.json"
TRIALS_URL = "https://clinicaltrials.gov/api/v2/studies"

# measure id -> ClinicalTrials.gov search term
TRIAL_TERMS = {
    "DIABETES": "diabetes",
    "OBESITY": "obesity",
    "DEPRESSION": "depression",
    "BPHIGH": "hypertension",
    "CHD": "coronary artery disease",
    "COPD": "COPD",
    "CASTHMA": "asthma",
    "STROKE": "stroke",
    "CANCER": "cancer",
}


def get_json(url, params):
    """GET with timeout and retries. Returns parsed JSON."""
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            # ArcGIS reports some errors with HTTP 200
            if isinstance(data, dict) and "error" in data:
                raise RuntimeError(data["error"])
            return data
        except (requests.RequestException, ValueError, RuntimeError) as e:
            if attempt == RETRIES:
                raise RuntimeError(f"Failed after {RETRIES} tries: {url} ({e})") from e
            print(f"  retry {attempt}/{RETRIES - 1} after error: {e}")
            time.sleep(2 * attempt)


def arcgis_query(layer, **params):
    """Fetch every feature of an ArcGIS layer, paging 1000 rows at a time."""
    url = f"{ARCGIS}/{layer}/query"
    base = {"where": "1=1", "outSR": 4326, "f": "json", "resultRecordCount": PAGE}
    base.update(params)
    features, offset = [], 0
    while True:
        data = get_json(url, {**base, "resultOffset": offset})
        page = data.get("features", [])
        features.extend(page)
        if len(page) < PAGE and not data.get("exceededTransferLimit"):
            return features
        offset += len(page)


def save(name, obj):
    DATA.mkdir(exist_ok=True)
    path = DATA / name
    path.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
    print(f"  saved {path} ({path.stat().st_size / 1024:.0f} KB)")


def check(label, got, expected):
    note = "" if got == expected else f"  <-- expected {expected}"
    print(f"  {label}: {got}{note}")


# 1. Town shapes
def fetch_town_shapes():
    data = get_json(f"{ARCGIS}/Census2020_Towns/MapServer/2/query", {
        "where": "1=1", "outFields": "TOWN20,COUNTY20", "returnGeometry": "true",
        "outSR": 4326, "maxAllowableOffset": 0.003, "geometryPrecision": 4,
        "f": "geojson",
    })
    check("towns", len(data.get("features", [])), 351)
    save("towns.geojson", data)


# 2. Town attributes
def fetch_town_attributes():
    feats = arcgis_query(
        "Census2020_Towns/MapServer/2",
        outFields="TOWN20,COUNTY20,POP2020,INTPTLAT20,INTPTLON20",
        returnGeometry="false",
    )
    towns = []
    for f in feats:
        a = f["attributes"]
        a["INTPTLAT20"] = float(a["INTPTLAT20"])  # strings like "+42.36"
        a["INTPTLON20"] = float(a["INTPTLON20"])
        towns.append(a)
    check("towns", len(towns), 351)
    save("towns.json", towns)


# 3. CDC PLACES
def fetch_places():
    measures = ",".join(f"'{m}'" for m in TRIAL_TERMS)
    rows = get_json(PLACES_URL, {
        "$select": "year,locationname,measureid,measure,data_value,"
                   "low_confidence_limit,high_confidence_limit,totalpopulation",
        "$where": "stateabbr='MA' AND data_value_type='Crude prevalence' "
                  f"AND measureid in({measures})",
        "$limit": 5000,
    })
    check("rows", len(rows), 126)
    save("cdc_places.json", rows)


# 4. ClinicalTrials.gov
def slim_study(study):
    """Keep only needed fields, and only Massachusetts sites with coordinates."""
    p = study.get("protocolSection", {})
    ident = p.get("identificationModule", {})
    sites = []
    for loc in p.get("contactsLocationsModule", {}).get("locations", []):
        geo = loc.get("geoPoint")
        if loc.get("state") == "Massachusetts" and geo:
            sites.append({
                "facility": loc.get("facility", ""),
                "city": loc.get("city", ""),
                "lat": geo["lat"],
                "lon": geo["lon"],
            })
    return {
        "nct": ident.get("nctId"),
        "title": ident.get("briefTitle", ""),
        "conditions": p.get("conditionsModule", {}).get("conditions", []),
        "phases": p.get("designModule", {}).get("phases", []),
        "sites": sites,
    }


def fetch_trials_for(term):
    params = {
        "query.locn": "Massachusetts",
        "query.cond": term,
        "filter.overallStatus": "RECRUITING",
        "pageSize": PAGE,
        "fields": "NCTId,BriefTitle,Condition,Phase,LocationFacility,"
                  "LocationCity,LocationState,LocationGeoPoint",
    }
    studies = {}  # keyed by NCT id so repeats collapse
    while True:
        data = get_json(TRIALS_URL, params)
        for s in data.get("studies", []):
            slim = slim_study(s)
            if slim["nct"] and slim["sites"]:
                studies[slim["nct"]] = slim
        token = data.get("nextPageToken")
        if not token:
            return list(studies.values())
        params["pageToken"] = token


def fetch_trials():
    out = {}
    for measure, term in TRIAL_TERMS.items():
        out[measure] = fetch_trials_for(term)
        print(f"  {measure}: {len(out[measure])} trials")
    save("trials.json", out)


# 5. Hospitals
def fetch_hospitals():
    feats = arcgis_query(
        "Hospitals/MapServer/0",
        outFields="FACILITY_NAME,FACILITY_TYPE,MUNICIPALITY,COUNTY,ICU,MED_SURG,PEDIATRIC",
        returnGeometry="true",
    )
    hospitals = []
    for f in feats:
        h = f["attributes"]
        for bed in ("ICU", "MED_SURG", "PEDIATRIC"):
            h[bed] = h.get(bed) or 0  # null beds -> 0
        geo = f.get("geometry") or {}
        h["lat"] = geo.get("y")
        h["lon"] = geo.get("x")
        hospitals.append(h)
    check("hospitals", len(hospitals), 103)
    save("hospitals.json", hospitals)


# 6. Environmental-justice block groups
def fetch_ej():
    feats = arcgis_query(
        "EJ2020/MapServer/0",
        where="EJ='Yes'",
        outFields="MUNICIPALITY,TOTAL_POP,PCT_MINORITY,LIMENGHHPCT,BG_MHHI,EJ_CRIT_DESC",
        returnGeometry="false",
    )
    rows = [f["attributes"] for f in feats]
    check("block groups", len(rows), 2604)
    save("ej.json", rows)


STEPS = [
    ("Town shapes", fetch_town_shapes),
    ("Town attributes", fetch_town_attributes),
    ("CDC PLACES", fetch_places),
    ("ClinicalTrials.gov", fetch_trials),
    ("Hospitals", fetch_hospitals),
    ("Environmental-justice block groups", fetch_ej),
]


def main():
    for i, (name, step) in enumerate(STEPS, 1):
        print(f"{i}/{len(STEPS)} {name}")
        try:
            step()
        except Exception as e:  # report which dataset failed, then stop
            print(f"FAILED: {name}: {e}")
            sys.exit(1)
    DATA.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    (DATA / "fetched_at.txt").write_text(stamp, encoding="utf-8")
    print(f"Done. Fetched at {stamp}")


if __name__ == "__main__":
    main()
