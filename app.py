"""Streamlit UI. Run: streamlit run app.py"""
import os

import streamlit as st

from docsqa.pipeline import DocsQA

st.set_page_config(page_title="DocsQA", page_icon="🔍")
st.title("🔍 DocsQA")
st.caption("Ask questions about your documents. Answers cite their sources.")


@st.cache_resource
def load() -> DocsQA:
    return DocsQA.from_index(os.getenv("INDEX_DIR", "index"))


try:
    qa = load()
except FileNotFoundError:
    st.error("No index found. Run `python -m docsqa.ingest` first.")
    st.stop()

question = st.text_input("Your question")
if question:
    with st.spinner("Searching..."):
        result = qa.ask(question)
    st.markdown("### Answer")
    st.write(result["answer"])
    st.caption(f"Generated via: {result['generation']}")

    if result["citations"]:
        st.markdown("### Sources")
        for c in result["citations"]:
            with st.expander(f"[{c['ref']}] {c['source']}"):
                st.write(c["text"])

    t = result["trace"]
    st.markdown("### Trace")
    st.json({"total_ms": t["total_ms"], "timings_ms": t["timings_ms"],
             "tokens": [t["input_tokens"], t["output_tokens"]], "cost_usd": t["cost_usd"]})
