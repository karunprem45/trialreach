"""TrialReach: page router. Pages live in page_*.py; shared helpers in ui.py."""
import streamlit as st

import ui

st.set_page_config(page_title="TrialReach", layout="wide")
st.markdown(ui.css(), unsafe_allow_html=True)

pages = [
    st.Page("page_story.py", title="Story", default=True),
    st.Page("page_explore.py", title="Explore"),
    st.Page("page_scout.py", title="Site Scout"),
]
nav = st.navigation(pages, position="top")

st.markdown('<p class="brand">TrialReach</p>'
            '<p class="tagline">Finding the research deserts of Massachusetts.</p>',
            unsafe_allow_html=True)
with st.container(key="page-" + nav.title.lower().replace(" ", "-")):
    nav.run()
ui.footer(ui.load_data())
