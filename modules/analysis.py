# modules/analysis.py

import streamlit as st
import snowflake.connector
import pandas as pd

@st.cache_resource
def create_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        role=st.secrets["snowflake"]["role"]
    )

# Establish Snowflake connection
conn = create_connection()

# Sample Testing
def getData():

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


# get Search Data
def getData_Search(start_date, end_date, selected_zone, selected_cluster, selected_type):
    
    # Start building the query
    query = f"""
        SELECT 
            schoolName,
            schoolCode,
            COUNT(sessionId) AS total_usage,
            COUNT(DISTINCT teacherId) AS unique_users
        FROM 
            GOLD.ANALYSIS_SESSION
        WHERE
            DATE(timestamp) BETWEEN '{start_date}' AND '{end_date}'
        AND zoneCode = '{selected_zone}' 
    """
    
    # Add cluster condition only if selected_cluster is not 'None'
    if selected_cluster:
        query += f" AND clusterCode = '{selected_cluster}'"
    if selected_type:
        query += f" AND type = '{selected_type}'"

    # Finish query
    query += " GROUP BY schoolName, schoolCode ORDER BY total_usage DESC;"

    #st.write(query)
    # Execute the query and convert the result to a DataFrame
    df_search = pd.read_sql(query, conn)

    return df_search

def getData_Map(start_date, end_date, selected_zone):
    
    # Start building the query
    query = f"""
        SELECT 
            schoolName,
            schoolCode,
            postalCode,
            COUNT(sessionId) AS total_usage,
            COUNT(DISTINCT teacherId) AS unique_users
        FROM GOLD.ANALYSIS_SESSION
        WHERE
            DATE(timestamp) BETWEEN '{start_date}' AND '{end_date}' 
        AND zoneCode = '{selected_zone}' 
        GROUP BY schoolName, schoolCode, postalCode  
        ORDER BY total_usage DESC; 
    """
    #st.write(query)
    df_map = pd.read_sql(query, conn)

    return df_map

@st.cache_data
def get_global_filter():
    
    # Query to get unique school names
    query_schools = """
    SELECT DISTINCT schoolName 
    FROM GOLD.ANALYSIS_SESSION 
    ORDER BY schoolName;
    """
    df_schools = pd.read_sql(query_schools, conn)
    
    # Query to get unique school types
    query_types = """
    SELECT DISTINCT type 
    FROM GOLD.ANALYSIS_SESSION 
    ORDER BY type;
    """
    df_types = pd.read_sql(query_types, conn)
    
    # Query to get unique zone codes
    query_zones = """
    SELECT DISTINCT zoneCode 
    FROM GOLD.ANALYSIS_SESSION 
    ORDER BY zoneCode;
    """
    df_zones = pd.read_sql(query_zones, conn)
    
    # Query to get unique cluster codes
    query_clusters = """
    SELECT DISTINCT clusterCode 
    FROM GOLD.ANALYSIS_SESSION 
    ORDER BY clusterCode;
    """
    df_clusters = pd.read_sql(query_clusters, conn)
    
    # Query to get the date range
    query_dates = """
    SELECT MIN(DATE(timestamp)) AS min_date, MAX(DATE(timestamp)) AS max_date 
    FROM GOLD.ANALYSIS_SESSION;
    """
    df_dates = pd.read_sql(query_dates, conn)
    
    st.session_state.df_schools = df_schools
    st.session_state.df_types = df_types
    st.session_state.df_zones = df_zones
    st.session_state.df_clusters = df_clusters
    st.session_state.df_dates = df_dates
    st.session_state.min_date = df_dates['MIN_DATE'].iloc[0]
    st.session_state.max_date = df_dates['MAX_DATE'].iloc[0]


# get Bot Data
def getData_Bot():
    
    # Start building the query
    query = f"""
        SELECT 
            schoolName,
            schoolCode,
            COUNT(sessionId) AS total_usage,
            COUNT(DISTINCT teacherId) AS unique_users
        FROM 
            GOLD.ANALYSIS_SESSION
        GROUP BY schoolName, schoolCode 
        ORDER BY total_usage DESC;
    """

    #st.write(query)
    # Execute the query and convert the result to a DataFrame
    df_bot = pd.read_sql(query, conn)

    return df_bot
