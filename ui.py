"""Shared UI helpers for all pages. Display only; scoring lives in deserts.py."""
import html

import streamlit as st

import deserts as ds

INK, MUTED, BG, CARD, ACCENT = "#1F1A17", "#6B625C", "#FFFAF3", "#F3E9DC", "#C2502E"
GRAY = "#CFC6BD"
BOSTON = "SUFFOLK"  # "Boston" on screen means Suffolk County
BOSTON_NOTE = "Boston here means Suffolk County (Boston, Chelsea, Revere and Winthrop)."

SOURCES = ("[ClinicalTrials.gov](https://clinicaltrials.gov) · "
           "[CDC PLACES](https://www.cdc.gov/places) · "
           "[MassGIS](https://www.mass.gov/orgs/massgis-bureau-of-geographic-information)")

# Plain words for text that comes from deserts.py or scout.py (their logic stays as is).
PLAIN = {"environmental-justice neighborhoods": "neighborhoods that need extra outreach",
         "prevalence": "share of adults"}

CSS = f"""
<style>
.block-container, [data-testid="stMainBlockContainer"] {{
  max-width: 1000px; padding: 1.5rem 1.25rem 4rem;}}
.brand {{font-family: "Source Serif 4", Georgia, serif; font-size: 1.5rem; font-weight: 600;
        color: {INK}; margin: 0;}}
.tagline {{color: {MUTED}; margin: 0 0 1rem; font-size: .95rem;}}

/* story sections */
.num {{color: {ACCENT}; font-weight: 600; letter-spacing: .14em; font-size: .85rem; margin: 0;}}
[data-testid="stMarkdownContainer"] h2.headline {{
  font-family: "Source Serif 4", Georgia, serif; color: {INK}; font-weight: 600;
  font-size: clamp(1.7rem, 5vw, 2.6rem) !important; line-height: 1.15 !important;
  margin: .4rem 0 .9rem !important; padding: 0 !important;}}
h2.headline em {{font-style: normal; color: {ACCENT};}}
.lede {{color: {MUTED}; font-size: 1.1rem; line-height: 1.55; max-width: 38rem; margin: 0 0 1rem;}}
[class*="st-key-story-"] {{padding: 2.75rem 0; animation: fadeUp .8s ease-out both;}}
.st-key-story-2 {{animation-delay: .05s;}} .st-key-story-3 {{animation-delay: .1s;}}
.st-key-story-4 {{animation-delay: .15s;}} .st-key-story-5 {{animation-delay: .2s;}}
@keyframes fadeUp {{from {{opacity: 0; transform: translateY(12px);}}
                   to {{opacity: 1; transform: none;}}}}
@media (prefers-reduced-motion: reduce) {{
  [class*="st-key-story-"] {{animation: none !important;}}}}

/* cards: a grid that wraps into one column on phones */
.cards {{display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem; margin: 1rem 0;}}
.card {{background: {CARD}; border-radius: 12px; padding: 1.1rem 1.25rem;}}
.card .big {{font-family: "Source Serif 4", Georgia, serif; font-size: 2.1rem;
            font-weight: 600; color: {ACCENT}; line-height: 1.1;}}
.card .title {{font-weight: 600; margin-top: .35rem;}}
.card .small {{color: {MUTED}; font-size: .95rem;}}

/* page links as buttons */
[data-testid="stPageLink"] a {{justify-content: center; border-radius: 999px;
  padding: .7rem 1.4rem; border: 2px solid {ACCENT}; text-decoration: none;}}
.st-key-cta-primary [data-testid="stPageLink"] a {{background: {ACCENT};}}
.st-key-cta-primary [data-testid="stPageLink"] a * {{color: #FFFFFF !important; font-weight: 600;}}
.st-key-cta-secondary [data-testid="stPageLink"] a * {{color: {ACCENT} !important; font-weight: 600;}}

[data-testid="stMetric"] {{background: #FFFFFF; border-radius: 12px;}}
@media (max-width: 640px) {{
  .block-container, [data-testid="stMainBlockContainer"] {{padding: 1rem .9rem 3rem;}}
  [class*="st-key-story-"] {{padding: 1.75rem 0;}}
}}
</style>
"""


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
