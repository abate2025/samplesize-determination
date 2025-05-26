import streamlit as st

def authenticate_user():
    """Basic authentication for demo purposes"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True
        st.session_state.user = "ess_user"