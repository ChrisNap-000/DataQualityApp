import pandas as pd
import streamlit as st


def load_data(uploaded_file) -> pd.DataFrame | None:
    try:
        name = uploaded_file.name.lower()
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        elif name.endswith(".xls"):
            df = pd.read_excel(uploaded_file, engine="xlrd")
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            return None

        if df.empty:
            st.warning("The uploaded file is empty.")
            return None

        return df

    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None
