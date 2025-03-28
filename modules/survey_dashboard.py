import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import snowflake.connector

zone_data = {"East": "1", "West": "2", "North": "3", "South": "4"}

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

def create_date_filter():
    #today = datetime.now()
    col1, col2 = st.columns(2)
    min_date = st.session_state.get('min_date')
    max_date = st.session_state.get('max_date')

        # Ensure min_date and max_date are datetime.date objects
    if isinstance(min_date, str):
        min_date = datetime.strptime(min_date, "%Y-%m-%d").date()
    elif isinstance(min_date, datetime):
        min_date = min_date.date()

    if isinstance(max_date, str):
        max_date = datetime.strptime(max_date, "%Y-%m-%d").date()
    elif isinstance(max_date, datetime):
        max_date = max_date.date()

    # Set default values within the valid range
    default_start_date = min_date
    default_end_date = max_date
    
    with col1:
        start_date = st.date_input(
            "From Date",
            value=default_start_date,
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        end_date = st.date_input(
            "To Date",
            value=default_end_date,
            min_value=min_date,
            max_value=max_date
        )
    
    # Convert to datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    return start_datetime, end_datetime

def render_charts(data):
    """
    Render charts based on the provided DataFrame.

    Parameters:
    - data (DataFrame): The DataFrame containing the necessary data for visualization.
    """

    # Ensure the DataFrame is not empty
    if data.empty:
        st.warning("No data available to display charts.")
        return

    # 1. Heatmap: Product Usage Confidence by Subject and School
    st.header("📊 Product Usage Confidence: Subject Analysis")
    if 'school' in data.columns and 'subject' in data.columns and 'confidence' in data.columns:
        heatmap_data = data.pivot_table(index="school", columns="subject", values="confidence", aggfunc="mean")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(heatmap_data, annot=True, cmap="Blues", ax=ax)
        st.pyplot(fig)
    else:
        st.error("Required columns for heatmap are missing in the data.")

    # 2. Word Frequency Bar Chart: Top Feedback Keywords
    st.header("💬 Feedback from using EduPlan AI Product")
    if 'feedback' in data.columns:
        feedback_text = " ".join(data["feedback"].dropna().astype(str).tolist()).lower()
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(feedback_text)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
    else:
        st.error("Feedback column is missing in the data.")

    # 3. Bar Chart: Lesson Planning Time Before vs. After EduPlan AI
    st.header("⏱ Lesson Planning Time: Before vs. After EduPlan AI")
    if 'school' in data.columns and 'time_before' in data.columns and 'time_after' in data.columns:
        lesson_data = data.groupby("school")[["time_before", "time_after"]].mean().reset_index()
        lesson_data["savings"] = ((lesson_data["time_before"] - lesson_data["time_after"]) / lesson_data["time_before"] * 100).round(2)

        fig, ax = plt.subplots(figsize=(10, 6))
        bar_width = 0.35
        index = range(len(lesson_data))

        bar1 = ax.bar(index, lesson_data["time_before"], bar_width, label="Before EduPlan AI")
        bar2 = ax.bar([i + bar_width for i in index], lesson_data["time_after"], bar_width, label="After EduPlan AI")

        ax.set_xlabel('School')
        ax.set_ylabel('Average Planning Time (mins)')
        ax.set_title('Lesson Planning Time by School')
        ax.set_xticks([i + bar_width / 2 for i in index])
        ax.set_xticklabels(lesson_data["school"], rotation=45)
        ax.legend()

        # Annotate savings percentage
        for i, txt in enumerate(lesson_data["savings"]):
            ax.text(i + bar_width, lesson_data["time_after"].iloc[i] + 2, f"Saved: {txt}%", ha='center')

        st.pyplot(fig)
    else:
        st.error("Required columns for lesson planning time comparison are missing in the data.")

def show_feedbackAnalysis():
    # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            zone_name = st.selectbox("Zone", list(zone_data.keys()))
        with col2:
            cluster = st.selectbox("Cluster", st.session_state.df_clusters)
        with col3:
            type = st.selectbox("School Type", st.session_state.df_types)
        
        start_date, end_date = create_date_filter()
        
        if st.button("Search"):
            df_search = getData_Search(start_date, end_date, zone_data[zone_name], cluster, type)
            print('168', df_search)
            st.markdown(df_search)
            if not df_search.empty:
                render_charts(df_search)
            else:
                st.error("No data found, please re-select the filter.")


def getData_Search(start_date, end_date, selected_zone=None, selected_cluster=None, selected_type=None):
    # Base query for filtering schools from SILVER.DIM_SCHOOL
    school_query = """
        SELECT SCHOOLCODE, SCHOOLNAME
        FROM SILVER.DIM_SCHOOL
        WHERE 1=1
    """
    
    # Apply filters based on provided criteria
    if selected_zone:
        school_query += f" AND ZONECODE = '{selected_zone}'"
    if selected_cluster:
        school_query += f" AND CLUSTERCODE = '{selected_cluster}'"
    if selected_type:
        school_query += f" AND TYPE = '{selected_type}'"

    # Main query to retrieve survey data for the filtered schools
    query = f"""
        SELECT 
            sa.SCHOOLCODE,
            ds.SCHOOLNAME,
            sa.SURVEYDATETIME,
            sa.*
        FROM 
            GOLD.SURVEY_ANALYSIS AS sa
        JOIN 
            ({school_query}) AS ds ON sa.SCHOOLCODE = ds.SCHOOLCODE
        WHERE
            DATE(sa.SURVEYDATETIME) BETWEEN '{start_date}' AND '{end_date}'
    """
    print("="*50)
    print(query)
    print("="*50)

    df_search = pd.read_sql(query, conn)

    return df_search