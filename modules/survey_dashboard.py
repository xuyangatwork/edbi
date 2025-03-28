import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, time
import snowflake.connector
import math

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

# # Establish Snowflake connection
conn = create_connection()

def create_date_filter():
    col1, col2 = st.columns(2)

    # Define default dates as datetime.date objects
    default_min_date = datetime.strptime('2024-09-20', '%Y-%m-%d').date()
    default_max_date = datetime.strptime('2025-03-18', '%Y-%m-%d').date()
    default_min_date_datetime_obj = datetime.combine(default_min_date, time.min)
    default_max_date_datetime_obj = datetime.combine(default_max_date, time.max)
    
    # Initialize session state variables if they are not already set
    if 'min_date' not in st.session_state:
        st.session_state['min_date'] = datetime.combine(default_min_date, time.min)
    if 'max_date' not in st.session_state:
        st.session_state['max_date'] = datetime.combine(default_max_date, time.max)
    
    with col1:
        start_date = st.date_input(
            "From Date",
            value=default_min_date_datetime_obj,
            min_value=default_min_date_datetime_obj,
            max_value=default_max_date
        )
    
    with col2:
        end_date = st.date_input(
            "To Date",
            value=default_max_date_datetime_obj,
            min_value=default_min_date_datetime_obj,
            # max_value=default_max_date
        )
    
    # Update session state with selected dates
    st.session_state['min_date'] = start_date
    st.session_state['max_date'] = end_date

    # # Convert to datetime for further processing if needed
    # start_datetime = datetime.combine(start_date, datetime.min.time())
    # end_datetime = datetime.combine(end_date, datetime.max.time())

    return default_min_date, default_max_date

def render_chart_1(data):
    """
    Render charts based on the provided DataFrame.

    Parameters:
    - data (DataFrame): The DataFrame containing the necessary data for visualization.
    """

    required_cols = {'SCHOOLNAME', 'SURVEYDATETIME', 'QUESTIONID', 'ANSWER'}
    if not required_cols.issubset(data.columns):
        st.error("Input data must contain SCHOOLNAME, SURVEYDATETIME, QUESTIONID, and ANSWER columns.")
        return

    # Extract subject & confidence data
    subjects_df = data[data['QUESTIONID'] == 'Q1'][['SCHOOLNAME', 'SURVEYDATETIME', 'ANSWER']]
    scores_df = data[data['QUESTIONID'] == 'Q7'][['SCHOOLNAME', 'SURVEYDATETIME', 'ANSWER']]

    subjects_df = subjects_df.rename(columns={'ANSWER': 'subject'})
    scores_df = scores_df.rename(columns={'ANSWER': 'confidence'})

    # Merge and clean
    merged_df = pd.merge(subjects_df, scores_df, on=['SCHOOLNAME', 'SURVEYDATETIME'])
    merged_df['confidence'] = pd.to_numeric(merged_df['confidence'], errors='coerce')
    merged_df = merged_df.dropna(subset=['confidence'])
    merged_df = merged_df.rename(columns={'SCHOOLNAME': 'school'})

    # Map subjects into grouped categories
    subject_group_map = {
        'English': 'Lang',
        'Chinese': 'Lang',
        'Malay': 'Lang',
        'Tamil': 'Lang',
        'Mathematics': 'Math',
        'Science': 'Sci',
        'Social Studies': 'Social Sci',
        'Music': 'Arts',
        'Art': 'Arts',
        'Physical Education': 'PE',
        'Design & Technology': 'Tech',
        'ICT': 'Tech',
        # Add other mappings as needed
    }

    merged_df['subject_group'] = merged_df['subject'].map(subject_group_map)
    merged_df = merged_df.dropna(subset=['subject_group'])  # Remove unmapped

    # Limit to 15 schools (alphabetically by default)
    top_schools = merged_df['school'].drop_duplicates().sort_values().head(15)
    filtered_df = merged_df[merged_df['school'].isin(top_schools)]

    # Pivot for heatmap
    heatmap_data = filtered_df.pivot_table(
        index="school", 
        columns="subject_group", 
        values="confidence", 
        aggfunc="mean"
    ).reindex(columns=['Lang', 'Math', 'Sci', 'Social Sci', 'Arts', 'PE', 'Tech'])  # Consistent column order

    # Draw heatmap
    st.header("📊 Product Usage Confidence: Subject Analysis")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(heatmap_data, annot=True, cmap="Blues", linewidths=0.5, ax=ax)
    st.pyplot(fig)

def extract_minutes(answer):
    try:
        if pd.isna(answer):
            return None
        answer = answer.strip().lower()
        if "min" in answer:
            return int(answer.split()[0])
    except:
        return None
    return None

def tag_before_after(group):
    median_time = group["SURVEYDATETIME"].median()
    group["tag"] = group["SURVEYDATETIME"].apply(lambda x: "before" if x <= median_time else "after")
    return group

def preprocess_lesson_time_data(raw_data):
    # Filter Q4 and extract numeric time
    df = raw_data[raw_data["QUESTIONID"] == "Q4"].copy()
    df["time_minutes"] = df["ANSWER"].apply(extract_minutes)
    df = df.dropna(subset=["time_minutes"])

    # Parse datetime
    df["SURVEYDATETIME"] = pd.to_datetime(df["SURVEYDATETIME"])

    # Tag before/after using median split
    tagged = df.groupby("SCHOOLNAME").apply(tag_before_after)
    tagged = tagged.reset_index(drop=True)

    # Aggregate to get avg time per tag
    summary = tagged.groupby(["SCHOOLNAME", "tag"])["time_minutes"].mean().reset_index()
    pivot = summary.pivot(index="SCHOOLNAME", columns="tag", values="time_minutes").reset_index()
    pivot.columns.name = None

    # Rename for compatibility
    pivot = pivot.rename(columns={
        "SCHOOLNAME": "school",
        "before": "time_before",
        "after": "time_after"
    })

    return pivot.dropna(subset=["time_before", "time_after"])

def render_chart_2(data):
    st.header("⏱ Lesson Planning Time Saved with EduPlan AI")

    # Step 1: Keep only valid "NN min" entries from Q4
    filtered_data = data[data["QUESTIONID"] == "Q4"].copy()
    filtered_data["ANSWER"] = filtered_data["ANSWER"].str.strip().str.lower()
    valid_rows = filtered_data["ANSWER"].str.match(r"^\d+\s*min$")
    filtered_data = filtered_data[valid_rows].copy()
    filtered_data["time_minutes"] = filtered_data["ANSWER"].str.extract(r"(\d+)").astype(float)

    # Parse survey datetime
    filtered_data["SURVEYDATETIME"] = pd.to_datetime(filtered_data["SURVEYDATETIME"])

    # Split into "before" and "after" using median per school
    def tag_before_after(group):
        median_time = group["SURVEYDATETIME"].median()
        group["tag"] = group["SURVEYDATETIME"].apply(lambda x: "before" if x <= median_time else "after")
        return group

    tagged_data = filtered_data.groupby("SCHOOLNAME").apply(tag_before_after).reset_index(drop=True)

    # Calculate average before/after per school
    avg_time = tagged_data.groupby(["SCHOOLNAME", "tag"])["time_minutes"].mean().reset_index()
    pivot = avg_time.pivot(index="SCHOOLNAME", columns="tag", values="time_minutes").reset_index()
    pivot = pivot.rename(columns={"before": "time_before", "after": "time_after", "SCHOOLNAME": "school"})
    pivot = pivot.dropna(subset=["time_before", "time_after"])

    # Calculate % saved
    pivot["savings"] = ((pivot["time_before"] - pivot["time_after"]) / pivot["time_before"] * 100).round(2)

    # Limit to first 15 schools alphabetically
    pivot = pivot.sort_values("school").head(15)

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))  # Wider figure to reduce overlap
    bars = ax.bar(pivot["school"], pivot["savings"])

    ax.set_xlabel("School")
    ax.set_ylabel("Time Saved (%)")
    ax.set_title("Average Lesson Planning Time Saved with EduPlan AI (First 15 Schools A–Z)")
    ax.set_ylim(0, pivot["savings"].max() * 1.25)  # Extra padding at top
    ax.set_xticklabels(pivot["school"], rotation=45, ha='right')

    # Annotate bars above, staggered to avoid overlap
    for i, (bar, value) in enumerate(zip(bars, pivot["savings"])):
        offset = 2 + (i % 2) * 3  # alternate offset to reduce clutter
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + offset, f"{value:.1f}%", ha='center', fontsize=9)

    st.pyplot(fig)

def render_chart_3(data):
    # 3. Word Frequency Bar Chart: Top Feedback Keywords
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

def show_feedbackAnalysis():
    # Filters
        zone_name = st.selectbox("Zone", list(zone_data.keys()))

        start_date, end_date = create_date_filter()
                
        if st.button("Search"):
            df_search_plot_1 = getData_Search(start_date, end_date, zone_data[zone_name], ['Q1','Q7'])
            df_search_plot_2 = getData_Search(start_date, end_date, zone_data[zone_name], ['Q4'])
            df_search_plot_3 = getData_Search(start_date, end_date, zone_data[zone_name], ['Q8'])
            if not (df_search_plot_1.empty and df_search_plot_2.empty and df_search_plot_3.empty):
                render_chart_1(df_search_plot_1)
                render_chart_2(df_search_plot_2)
                render_chart_3(df_search_plot_3)
            else:
                st.error("No data found, please re-select the filter.")


def getData_Search(start_date, end_date, selected_zone=None, question_ids=None):

    if isinstance(start_date, datetime):
        start_date = start_date.strftime('%Y-%m-%d')
    if isinstance(end_date, datetime):
        end_date = end_date.strftime('%Y-%m-%d')

    # Query to retrieve schools, optionally filtered by zone
    query = """
        SELECT 
            sa.SCHOOLCODE,
            ds.SCHOOLNAME,
            sa.SURVEYDATETIME,
            sa.QUESTIONID,
            sa.ANSWER
        FROM 
            GOLD.SURVEY_ANALYSIS AS sa
        JOIN 
            SILVER.DIM_SCHOOL AS ds ON sa.SCHOOLCODE = ds.SCHOOLCODE
        WHERE
            sa.SURVEYDATETIME BETWEEN %s AND %s
    """
    params = [start_date, end_date]

    # Apply zone filter if selected_zone is provided
    if selected_zone:
        query += " AND ds.ZONECODE = %s"
        params.append(selected_zone)

    # Apply question ID filter if question_ids are provided
    if question_ids:
        # Create a string of placeholders for the IN clause
        placeholders = ', '.join(['%s'] * len(question_ids))
        query += f" AND sa.QUESTIONID IN ({placeholders})"
        params.extend(question_ids)

    print(query)
    # Execute the query with parameters
    df_search = pd.read_sql(query, conn, params=params)

    print('-'*50)
    print(df_search)
    print('-'*50)

    return df_search


# -- QUESTIONID	QNTEXT
# -- Q1	Subjects and Level Taught
# -- Q2	Design Tech Enabled Lessons Frequency
# -- Q3	Average Time to Plan Tech Enabled Lesson
# -- Q4	Time Saved By Tool
# -- Q5	Resonated Persona
# -- Q6	Knowledge of E-Pedagogy Rating
# -- Q7	Confidence in E-Pedagogy Rating
# -- Q8	Challenges in Tech Enabled Lessons



# -- QUESTIONID	QNTEXT	ANSWER	SCHOOLCODE	SURVEYDATETIME
# -- Q8	Challenges in Tech Enabled Lessons	Inadequate training on new digital resources limits effective integration into lessons Furthermore, Balancing traditional teaching methods with modern tech-enabled approaches is a persistent challenge	1072	2025-03-01 22:44:25.900 -0800