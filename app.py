import os
import re
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from graph import stream_with_status
from utils.log import configure_logging

configure_logging()

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
)

st.title("AI Research Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Enter your research topic..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        status = st.empty()
        output_placeholder = st.empty()
        full_text = ""
        is_research = False

        try:
            for kind, data in stream_with_status(user_input):
                if kind == "status":
                    is_research = True
                    status.markdown(f"*{data}*")
                else:
                    status.empty()
                    full_text += data
                    output_placeholder.markdown(full_text + "▌")
        except Exception as e:
            full_text = f"Something went wrong: {e}"

        output_placeholder.markdown(full_text)

        if is_research and full_text:
            slug = re.sub(r"[\s_-]+", "_", re.sub(r"[^\w\s-]", "", user_input.lower()).strip())[:40]
            st.download_button(
                label="Download Report",
                data=full_text,
                file_name=f"report_{slug}.md",
                mime="text/markdown",
            )

        st.session_state.messages.append({"role": "assistant", "content": full_text})
