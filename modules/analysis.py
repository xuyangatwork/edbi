# modules/analysis.py

import streamlit as st
import snowflake.connector

@st.cache_resource
def create_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )

def show_analysis():
    st.title('Analysis Page')

    # Establish Snowflake connection
    conn = create_connection()
    st.success("Connected to Snowflake!")

    # Example query
    query = "SELECT * FROM ANALYSIS_SESSION LIMIT 10"
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()

    # Display data
    for row in rows:
        st.write(row)
