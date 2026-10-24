"""Pure scoring functions for TrialReach (pandas/numpy only, no Streamlit)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"
REACH_MILES = 25
EARTH_MILES = 3958.8
NO_SITE_MILES = 500.0  # finite stand-in when a disease has no trial sites

CONDITIONS = {
    "DIABETES": "Diabetes",
    "OBESITY": "Obesity",
    "DEPRESSION": "Depression",
    "BPHIGH": "High blood pressure",
    "CHD": "Coronary heart disease",
    "COPD": "COPD",
    "CASTHMA": "Asthma",
    "STROKE": "Stroke",
    "CANCER": "Cancer",
}


# ---------- loading ----------
def _read_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def load_all():
    """Read everything from data/. Raises FileNotFoundError if a file is missing."""
    towns = pd.DataFrame(_read_json("towns.json")).rename(columns={
        "TOWN20": "town", "COUNTY20": "county", "POP2020": "pop",
        "INTPTLAT20": "lat", "INTPTLON20": "lon"})
    towns["town"] = towns["town"].str.upper()
    towns["county"] = towns["county"].str.upper()

    places = pd.DataFrame(_read_json("cdc_places.json")).rename(columns={
        "data_value": "prevalence", "low_confidence_limit": "prev_low",
        "high_confidence_limit": "prev_high"})
    places["county"] = places["locationname"].str.upper()
    for col in ("prevalence", "prev_low", "prev_high", "totalpopulation"):
        places[col] = pd.to_numeric(places[col])

    hospitals = pd.DataFrame(_read_json("hospitals.json"))
    hospitals["COUNTY"] = hospitals["COUNTY"].str.upper()

    ej = pd.DataFrame(_read_json("ej.json"))
    ej["town"] = ej["MUNICIPALITY"].str.upper()
    ej["county"] = ej["town"].map(towns.set_index("town")["county"])
    ej["TOTAL_POP"] = pd.to_numeric(ej["TOTAL_POP"]).fillna(0)
    ej["LIMENGHHPCT"] = pd.to_numeric(ej["LIMENGHHPCT"]).fillna(0)

    return {
        "towns": towns,
        "shapes": _read_json("towns.geojson"),
        "places": places,
        "trials": _read_json("trials.json"),
        "hospitals": hospitals,
        "ej": ej,
        "fetched_at": (DATA / "fetched_at.txt").read_text(encoding="utf-8").strip(),
    }


# ---------- distance ----------
def miles(lat1, lon1, lat2, lon2):
    """Haversine distance in miles. Works on scalars or numpy arrays (broadcasts)."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_MILES * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


# ---------- trial sites and access ----------
SITE_COLS = ["nct", "title", "phase", "facility", "city", "lat", "lon", "county"]


def trial_sites(d, mid):
    """One row per (trial, MA site). County = county of the nearest town center."""
    rows = []
    for t in d["trials"].get(mid, []):
        phase = ", ".join(t.get("phases") or []) or "N/A"
        for s in t["sites"]:
            rows.append((t["nct"], t["title"], phase, s["facility"], s["city"],
                         s["lat"], s["lon"]))
    sites = pd.DataFrame(rows, columns=SITE_COLS[:-1])
    towns = d["towns"]
    if sites.empty:
        sites["county"] = pd.Series(dtype=object)
        return sites
    dist = miles(sites["lat"].to_numpy()[:, None], sites["lon"].to_numpy()[:, None],
                 towns["lat"].to_numpy()[None, :], towns["lon"].to_numpy()[None, :])
    sites["county"] = towns["county"].to_numpy()[dist.argmin(axis=1)]
    return sites


def town_access(d, sites):
    """Add nearest_miles and trials_in_reach (distinct NCT ids within REACH_MILES)."""
    towns = d["towns"].copy()
    if sites.empty:
        towns["nearest_miles"] = NO_SITE_MILES
        towns["trials_in_reach"] = 0
        return towns
    dist = miles(towns["lat"].to_numpy()[:, None], towns["lon"].to_numpy()[:, None],
                 sites["lat"].to_numpy()[None, :], sites["lon"].to_numpy()[None, :])
    towns["nearest_miles"] = dist.min(axis=1)
    # count distinct trials per town without Python loops over pairs
    codes, uniques = pd.factorize(sites["nct"])
    n_trials = len(uniques)
    town_idx, site_idx = np.nonzero(dist <= REACH_MILES)
    pairs = np.unique(town_idx * n_trials + codes[site_idx])
    towns["trials_in_reach"] = np.bincount(pairs // n_trials, minlength=len(towns))
    return towns


# ---------- score ----------
def desert_score(affected, trials_in_reach):
    """Pure helper. Returns (people_per_trial, score), one entry per county.
    score = round(100 * ppt / max(ppt)); the worst county scores 100."""
    affected = np.asarray(affected, dtype=float)
    trials = np.asarray(trials_in_reach, dtype=float)
    ppt = affected / (trials + 1)
    top = ppt.max() if ppt.size else 0
    if top <= 0:
        return ppt, np.zeros(ppt.shape, dtype=int)
    return ppt, np.rint(100 * ppt / top).astype(int)


def _weighted_mean(df, col):
    return np.average(df[col], weights=df["pop"]) if df["pop"].sum() > 0 else 0.0


def county_scores(d, mid):
    """Returns (county_df, towns_with_access, sites). county_df: 14 rows, worst first."""
    sites = trial_sites(d, mid)
    df, towns = _score_table(d, mid, sites)
    return df, towns, sites


def _score_table(d, mid, sites):
    """County table and town access for a given set of trial sites."""
    towns = town_access(d, sites)

    agg = towns.groupby("county").apply(
        lambda g: pd.Series({
            "pop": g["pop"].sum(),
            "avg_miles": _weighted_mean(g, "nearest_miles"),
            "trials_in_reach": _weighted_mean(g, "trials_in_reach"),
        }), include_groups=False).reset_index()
    in_county = sites.groupby("county")["nct"].nunique()
    agg["trials_in_county"] = agg["county"].map(in_county).fillna(0).astype(int)

    prev = d["places"][d["places"]["measureid"] == mid][
        ["county", "prevalence", "prev_low", "prev_high", "totalpopulation"]]
    df = agg.merge(prev, on="county")
    df["affected"] = df["prevalence"] / 100 * df["totalpopulation"]
    df["people_per_trial"], df["score"] = desert_score(df["affected"], df["trials_in_reach"])
    df = df.drop(columns="totalpopulation")
    df = df.sort_values("people_per_trial", ascending=False).reset_index(drop=True)
    return df, towns


def simulate_new_site(d, mid, lat, lon, label):
    """Add one hypothetical trial site. Returns (before_df, after_df).
    The after score uses the ORIGINAL max people_per_trial, so both are comparable.
    Both tables get `rank` (1 = worst) and `newly_reached` (residents with no trial
    within REACH_MILES before and one after; 0 in the before table)."""
    before, towns_b, sites = county_scores(d, mid)
    # county of the new site = county of the nearest town center (same rule as trial_sites)
    near = d["towns"].iloc[int(miles(lat, lon, d["towns"]["lat"].to_numpy(),
                                     d["towns"]["lon"].to_numpy()).argmin())]
    new = pd.DataFrame([("SIMULATED", label, "N/A", label, "", lat, lon, near["county"])],
                       columns=SITE_COLS)
    sites_after = new if sites.empty else pd.concat([sites, new], ignore_index=True)
    after, towns_a = _score_table(d, mid, sites_after)

    top = before["people_per_trial"].max()
    after["score"] = (np.rint(100 * after["people_per_trial"] / top).astype(int)
                      if top > 0 else 0)
    newly = towns_a["pop"].where((towns_b["trials_in_reach"] == 0)
                                 & (towns_a["trials_in_reach"] >= 1), 0)
    after["newly_reached"] = after["county"].map(newly.groupby(towns_a["county"]).sum()).fillna(0)
    before["newly_reached"] = 0
    for df in (before, after):
        df["rank"] = df["people_per_trial"].rank(ascending=False, method="first").astype(int)
    return before, after


def state_prevalence(county_df):
    """Population-weighted state prevalence (%) from a county_scores table."""
    return float(np.average(county_df["prevalence"], weights=county_df["pop"]))


# ---------- county detail ----------
def county_center(d, county):
    """Population-weighted center (lat, lon) of a county."""
    t = d["towns"][d["towns"]["county"] == county.upper()]
    return (float(np.average(t["lat"], weights=t["pop"])),
            float(np.average(t["lon"], weights=t["pop"])))


def nearest_trials(d, county, sites, n=8):
    """The n nearest trials (nearest site of each) from the county's center."""
    if sites.empty:
        return pd.DataFrame(columns=["miles", "nct", "title", "phase", "city"])
    lat, lon = county_center(d, county)
    s = sites.copy()
    s["miles"] = miles(lat, lon, s["lat"].to_numpy(), s["lon"].to_numpy())
    s = s.sort_values("miles").drop_duplicates("nct").head(n)
    return s[["miles", "nct", "title", "phase", "city"]].reset_index(drop=True)


def candidate_hospitals(d, county, sites):
    """Acute hospitals in the county with licensed beds and miles to nearest trial site."""
    h = d["hospitals"]
    h = h[(h["COUNTY"] == county.upper()) & (h["FACILITY_TYPE"] == "Acute Hospital")].copy()
    h["beds"] = h["ICU"] + h["MED_SURG"] + h["PEDIATRIC"]
    if sites.empty or h.empty:
        h["nearest_trial_miles"] = np.nan
    else:
        dist = miles(h["lat"].to_numpy(dtype=float)[:, None], h["lon"].to_numpy(dtype=float)[:, None],
                     sites["lat"].to_numpy()[None, :], sites["lon"].to_numpy()[None, :])
        h["nearest_trial_miles"] = dist.min(axis=1)
    return h.sort_values("beds", ascending=False).reset_index(drop=True)


def ej_summary(d, county):
    """(total EJ residents, per-town table sorted by EJ population)."""
    ej = d["ej"][d["ej"]["county"] == county.upper()]
    cols = ["town", "ej_pop", "neighborhoods", "limited_english_pct"]
    if ej.empty:
        return 0, pd.DataFrame(columns=cols)
    rows = []
    for town, g in ej.groupby("town"):
        w = g["TOTAL_POP"]
        pct = np.average(g["LIMENGHHPCT"], weights=w) if w.sum() > 0 else 0.0
        rows.append((town, int(w.sum()), len(g), float(pct)))
    by_town = pd.DataFrame(rows, columns=cols).sort_values("ej_pop", ascending=False)
    return int(ej["TOTAL_POP"].sum()), by_town.reset_index(drop=True)


def outreach_brief(condition, row, state_prev, hospitals, ej_pop, ej_towns):
    """Rule-based markdown recommendation. Also the fallback for the AI brief."""
    county = str(row["county"]).title()
    lines = [
        f"**{county} County** has about {row['prevalence']:.1f}% of adults with "
        f"{condition.lower()} (state average {state_prev:.1f}%). "
        f"That is roughly {row['people_per_trial']:,.0f} adults per nearby recruiting trial "
        f"({row['trials_in_reach']:.1f} trials within {REACH_MILES} miles on average)."
    ]
    if len(hospitals):
        top = hospitals.iloc[0]
        lines.append(
            f"- **Where to open a study:** {top['FACILITY_NAME']} in "
            f"{str(top['MUNICIPALITY']).title()} has the most licensed beds ({int(top['beds'])}).")
    else:
        lines.append("- **Where to open a study:** no acute hospital is listed in this county. "
                     "Look at partners in a neighboring county.")
    if ej_pop > 0 and len(ej_towns):
        t = ej_towns.iloc[0]
        lines.append(
            f"- **Who to reach:** about {ej_pop:,} residents live in environmental-justice "
            f"neighborhoods. Start in {str(t['town']).title()}, where about "
            f"{t['limited_english_pct']:.0f}% of households have limited English.")
    else:
        lines.append("- **Who to reach:** no environmental-justice neighborhoods are listed here.")
    lines.append("- Trial details are on ClinicalTrials.gov. Residents should talk to their "
                 "doctor or the study team.")
    return "\n".join(lines)
