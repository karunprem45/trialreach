"""Shared UI helpers for all pages. Display only; scoring lives in deserts.py."""
import functools
import html
from pathlib import Path

import streamlit as st

import deserts as ds

TEXT, MUTED, BG, CARD, BORDER, ACCENT = "#F5F5F5", "#A1A1AA", "#0B0B0C", "#17171A", "#2A2A2E", "#E5484D"
BAR_GRAY = "#3F3F46"  # neutral bars; only the highlighted one uses ACCENT
BOSTON = "SUFFOLK"  # "Boston" on screen means Suffolk County
BOSTON_NOTE = "Boston here means Suffolk County (Boston, Chelsea, Revere and Winthrop)."

SOURCES = ("[ClinicalTrials.gov](https://clinicaltrials.gov) · "
           "[CDC PLACES](https://www.cdc.gov/places) · "
           "[MassGIS](https://www.mass.gov/orgs/massgis-bureau-of-geographic-information)")

# Plain words for text that comes from deserts.py or scout.py (their logic stays as is).
PLAIN = {"environmental-justice neighborhoods": "neighborhoods that need extra outreach",
         "prevalence": "share of adults"}

# Pop-up style for every Plotly hover label (dark card, red border, white text).
HOVERLABEL = dict(bgcolor=CARD, bordercolor=ACCENT, align="left",
                  font=dict(color=TEXT, size=14))


@functools.cache
def _stylesheet():
    """Palette variables + style.css as one <style> block (blank lines removed for markdown)."""
    root = (f":root {{--bg: {BG}; --card: {CARD}; --border: {BORDER}; --text: {TEXT}; "
            f"--muted: {MUTED}; --accent: {ACCENT}; --ease: cubic-bezier(.2, .8, .2, 1);}}")
    css = (Path(__file__).parent / "style.css").read_text(encoding="utf-8")
    lines = [ln for ln in (root + "\n" + css).splitlines() if ln.strip()]
    return "<style>\n" + "\n".join(lines) + "\n</style>"


def css():
    return _stylesheet()


# ---------- small helpers ----------
def pretty(name):
    return str(name).title()


def county_label(county):
    """Name used in sentences: Suffolk is Boston."""
    return "Boston" if county == BOSTON else f"{pretty(county)} County"


def lower_label(label):
    """Disease name inside a sentence; keep acronyms like COPD."""
    return label if label.isupper() else label.lower()


def plain(text):
    """Swap technical words for plain ones (display only)."""
    for old, new in PLAIN.items():
        text = text.replace(old, new)
    return text


def esc(value):
    return html.escape(str(value))


def em(value):
    """Accent-colored key number or name inside a headline."""
    return f"<em>{esc(value)}</em>"


def cards(items):
    """HTML grid of cards. items = [(big, title, small)]. Single line so markdown keeps it as HTML."""
    out = "".join(
        f'<div class="card"><div class="big">{esc(big)}</div>'
        f'<div class="title">{esc(title)}</div><div class="small">{esc(small)}</div></div>'
        for big, title, small in items)
    return f'<div class="cards">{out}</div>'


def info_card(title_html, stats):
    """One card with a heading (HTML, already escaped) and a row of (label, value) stats."""
    body = "".join(f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>'
                   for k, v in stats)
    return f'<div class="card"><div class="head">{title_html}</div><div class="stats">{body}</div></div>'


def site_points(sites):
    """One row per trial site with a ready hover text: shortened study title, site, city."""
    cols = ["facility", "city", "lat", "lon", "county", "hover"]
    if sites.empty:
        return sites.iloc[0:0].reindex(columns=cols)
    g = (sites.groupby(["facility", "city", "lat", "lon", "county"], dropna=False)
         .agg(title=("title", "first"), n=("nct", "nunique")).reset_index())

    def hover(r):
        title = r["title"] if len(r["title"]) <= 70 else r["title"][:67].rstrip() + "..."
        more = f" (+{r['n'] - 1} more)" if r["n"] > 1 else ""
        city = f"<br>{esc(r['city'])}" if r["city"] else ""
        return f"<b>{esc(title)}</b>{esc(more)}<br>{esc(r['facility'])}{city}"

    g["hover"] = g.apply(hover, axis=1)
    return g[cols]


# ---------- cached data ----------
@st.cache_data
def get_data():
    return ds.load_all()


@st.cache_data
def get_scores(mid):
    return ds.county_scores(get_data(), mid)


@st.cache_data
def get_sim(mid, lat, lon, name):
    """(before, after) tables for one new trial site."""
    return ds.simulate_new_site(get_data(), mid, lat, lon, name)


def load_data():
    """Data dict, or a friendly error and stop."""
    try:
        return get_data()
    except FileNotFoundError:
        st.error("Data files are missing. Run `python fetch_data.py` once, then reload.")
        st.stop()


def disease_picker():
    """Disease selectbox. The choice is kept in session_state so it follows you across pages."""
    # The widget state is dropped when a page does not show it, so the start value comes
    # from "mid". The key keeps the widget identity stable when that start value changes.
    ids = list(ds.CONDITIONS)
    start = ids.index(st.session_state.get("mid", "DIABETES"))
    mid = st.selectbox("Choose a disease", ids, index=start, key="mid_pick",
                       format_func=ds.CONDITIONS.get)
    st.session_state["mid"] = mid
    return mid


# ---------- shared text ----------
def data_caption(d):
    st.caption(f"Data updated {d['fetched_at'][:10]} · Sources: {SOURCES}")


def footer(d):
    st.divider()
    st.caption(
        "Sources: [ClinicalTrials.gov](https://clinicaltrials.gov) (U.S. NLM) · "
        "[CDC PLACES](https://www.cdc.gov/places) 2023 county crude prevalence · "
        "[MassGIS](https://www.mass.gov/orgs/massgis-bureau-of-geographic-information) "
        "(Census 2020 towns, hospitals, EJ 2020 block groups). "
        f"Data downloaded {d['fetched_at']}. "
        "TrialReach scores places, never people. Not medical advice. "
        "Distances are straight-line from town centers. Licensed beds are not live occupancy.")
