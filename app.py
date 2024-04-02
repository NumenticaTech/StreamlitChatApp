import streamlit as st
import requests
import json
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


MAX_RETRY = 5
MAX_RETRY_FOR_SESSION = 5
BACK_OFF_FACTOR = 0.1
ERROR_CODES = [504]
API = 'https://3gu4uqkxbg.execute-api.ap-south-1.amazonaws.com/default/csv_chat'
API_KEY = st.secrets["APIKEY"]


def output_parser(responses):
    try:
        res = ""
        table_item = None
        if "benefits" in responses:
            if isinstance(responses['benefits'], list):
                res = res + "  \n"+responses['benefits'][0]
        if "plans" in responses:
            if isinstance(responses['plans'], list):
                df = pd.DataFrame(responses['plans'][0]).reset_index(drop=True)
                if 'Plan Name' in df.columns and 'Cost(OMR)' in df.columns:
                    table_item = df[['Plan Name', 'Cost(OMR)']]
                    table_item.index = table_item.index + 1
        return res, table_item
    except Exception as e:
        print(e)
        return None, None


def requests_retry_session():
    session = requests.Session()
    retry = Retry(total=MAX_RETRY, backoff_factor=BACK_OFF_FACTOR, status_forcelist=ERROR_CODES,
                  allowed_methods=frozenset({'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PUT', 'TRACE', 'POST'}))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def call_openai_api(input_text):
    try:
        payload = json.dumps({
            "query": input_text,
            "compulory_columns": [
                "Plan Name",
                "Cost(OMR)"
            ]
        })
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': API_KEY
        }
        session = requests_retry_session()
        responses = session.post(url=API, headers=headers, data=payload)
        responses = responses.json()
        print(responses)
        result, table = output_parser(responses)
        if result:
            return result, table
        return None,None
    except Exception as e:
        print(str(e))
        return None,None


st.title("Chat Bot")


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Please write your query here"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        output, table = call_openai_api(prompt)
        if output:
            st.write(output)
            st.session_state.messages.append({"role": "assistant", "content": output})
            if table is not None:
                st.table(table)
                st.session_state.messages.append({"role": "assistant", "content": output})
        else:
            st.error("An error occurred,Please try again!")
    # st.session_state.messages.append({"role": "assistant", "content": output})
