import streamlit as st
from datetime import datetime
from mongo import client

# --- Database ---
db = client["headlines"]
collection = db["newspaper_data"]

st.title("News Archives")

selected_date = st.date_input("Select a date to view archives:",
                              value=datetime.today(),
                              min_value=datetime(2000, 1, 1),
                              max_value=datetime.today())
selected_paper = st.selectbox("Select paper", options=["Hindu", "Mint"])

# set query according to paper selected
if selected_paper == "Mint":
    query = {
        "timestamp": {
            "$gte": datetime.combine(selected_date, datetime.min.time()),
            "$lt": datetime.combine(selected_date, datetime.max.time())
        },
        "filename": {
            "$regex": selected_paper,
            "$options": "i"
        }
    }
elif selected_paper == "Hindu":
    query = {
        "timestamp": {
            "$gte": datetime.combine(selected_date, datetime.min.time()),
            "$lt": datetime.combine(selected_date, datetime.max.time())
        },
        "$or": [
            {
                "filename": {
                    "$regex": "hindu",
                    "$options": "i"
                }
            },
            {
                "filename": {
                    "$regex": "the hindu",
                    "$options": "i"
                }
            },
            {
                "filename": {
                    "$regex": r"\bth\b",
                    "$options": "i"
                }
            }  # \b for word boundaries
        ]
    }

docs = list(collection.find(query))

if docs:
    for doc in docs:
        for page_num, page_headings in doc["articles"].items():
            if page_headings:
                st.subheader(f"Page {int(page_num) + 1}:")
                for i, heading in enumerate(page_headings, start=1):
                    st.write(f"{i}. {heading}")
else:
    st.write(f"No {selected_paper} newspapers found for selected date")
