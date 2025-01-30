#!/bin/env python3
import sys
import os
import time
import tempfile
import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
from htmlTemplates import css, bot_template, user_template

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.naive_rag import ProcessPDF


def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)

def display_messages():
    #st.subheader("Chat")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message(msg, is_user=is_user, key=str(i))
    st.session_state["thinking_spinner"] = st.empty()

def process_input():
    if (
        st.session_state["user_input"]
        and len(st.session_state["user_input"].strip()) > 0
    ):
        user_text = st.session_state["user_input"].strip()
        with st.session_state["thinking_spinner"], st.spinner("Thinking"):
            agent_text = st.session_state["assistant"].ask(user_text)

        st.session_state["messages"].append((user_text, True))
        st.session_state["messages"].append((agent_text, False))

def read_and_save_file():
    st.session_state["assistant"].clear()
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""

    for file in st.session_state["file_uploader"]:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        with st.session_state["ingestion_spinner"], st.spinner(
            f"Ingesting {file.name}"
        ):
            t0 = time.time()
            st.session_state["assistant"].ingest(file_path)
            t1 = time.time()

        st.session_state["messages"].append(
            (
                f"Ingested {file.name} in {t1 - t0:.2f} seconds",
                False,
            )
        )
        os.remove(file_path)


def main():
    load_dotenv()
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["assistant"] = ProcessPDF()

    st.set_page_config(page_title="Chat with 7P Docs",
                       page_icon=":books:")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with multiple PDFs :books:")
    #user_question = st.text_input("Ask a question about your documents:")
    st.text_input("Ask a question about your documents:", key="user_input")

    if st.button("Enter"):
        process_input()

    st.session_state["ingestion_spinner"] = st.empty()

    display_messages()

    with st.sidebar:
        st.subheader("Your documents")
        #pdf_docs = st.file_uploader(
        #    "Upload your PDFs here and click on 'Process'", accept_multiple_files=True)
        
        st.file_uploader(
        "Upload your PDFs here and click on 'Process'",
        type=["pdf"],
        key="file_uploader",
        on_change=read_and_save_file,
        label_visibility="collapsed",
        accept_multiple_files=True,
    )
        #if st.button("Process"):
        #    with st.spinner("Processing"):
                


if __name__ == '__main__':
    main()