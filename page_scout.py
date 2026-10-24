"""Site Scout page: ask where the next trial site should go. Display only."""
import streamlit as st

import llm
import scout
import ui

SCOUT_EXAMPLES = ["Where should my next diabetes trial site go?",
                  "Which county needs more asthma studies, and where could one open?",
                  "Find the biggest research desert for high blood pressure."]


def scout_step(step):
    """One tool step inside st.status."""
    args = ", ".join(f"{k}={v}" for k, v in step["args"].items())
    st.markdown(f"**{step['tool']}**({args})")
    st.caption(ui.plain(step["summary"]))


def set_scout_question(q):
    st.session_state["scout_q"] = q
    st.session_state["scout_go"] = True


d = ui.load_data()

st.title("Site Scout")
st.caption("Ask where the next trial site should go. Site Scout calls the app's own tools "
           f"(at most {scout.MAX_TOOL_CALLS}) and shows every step.")
st.text_input("Your question", key="scout_q",
              placeholder="Where should my next diabetes trial site go?")
ex = st.columns(len(SCOUT_EXAMPLES))
for col, q in zip(ex, SCOUT_EXAMPLES):
    col.button(q, key=f"ex_{q}", on_click=set_scout_question, args=(q,), use_container_width=True)
if st.button("Run Site Scout", type="primary"):
    st.session_state["scout_go"] = True

question = st.session_state.get("scout_q", "").strip()
just_ran = bool(st.session_state.pop("scout_go", False) and question)
if just_ran:
    with st.status("Site Scout is working...", expanded=True) as status:
        def show(step):
            if step is None:
                st.write("The AI service is unavailable. Switching to offline mode.")
            else:
                scout_step(step)
        wait_box = st.empty()  # filled while the AI service asks us to wait

        def busy(seconds):
            wait_box.info("The free AI service is busy, retrying in a few seconds…")

        with llm.notify_waits(busy):
            res = scout.run_scout(d, question, scores=ui.get_scores, on_step=show)
        wait_box.empty()
        status.update(label=f"Site Scout finished ({res['mode']} mode, {len(res['steps'])} tool calls)",
                      state="complete", expanded=False)
    st.session_state["scout_res"] = (question, res)

saved = st.session_state.get("scout_res")
if saved:
    q, res = saved
    st.caption(f"Question: {q}")
    if not just_ran:
        with st.expander(f"Steps ({len(res['steps'])} tool calls)"):
            for s in res["steps"]:
                scout_step(s)
    with st.container(border=True):
        st.markdown("#### Recommendation")
        if res["mode"] == "offline":
            st.caption("Offline mode: the same tools ran in a fixed order, with no AI model.")
        st.markdown(ui.plain(res["answer"]))
        flyer = next((s["result"] for s in res["steps"]
                      if s["tool"] == "write_outreach_flyer" and "error" not in s["result"]), None)
        if flyer:
            st.markdown(f"**Resident flyer draft ({flyer['language']})**")
            st.markdown(flyer["text"])
    st.caption("Numbers come from ClinicalTrials.gov, CDC PLACES and MassGIS data in this app. "
               "Site Scout scores places, never people. Review any text before you share it.")
else:
    st.info("Type a question or press an example. If no AI key is set, Site Scout runs in offline mode.")
