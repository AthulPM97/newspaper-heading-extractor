from pymongo import MongoClient
import streamlit as st

uri = st.secrets["mongo"]["uri"]

# Connect to cluster
client = MongoClient(uri)
