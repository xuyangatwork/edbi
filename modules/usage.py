import streamlit as st
import plotly.express as px
from streamlit_folium import folium_static
import folium
import ssl
from geopy.geocoders import Nominatim
from geopy.geocoders import OpenCage
import openai
from datetime import datetime
from modules.analysis import getData_Search, getData_Map, getData_Bot, get_global_filter


zone_data = {"East": "1", "West": "2", "North": "3", "South": "4"}

# Initialize geocoder
geolocator = Nominatim(user_agent="edbi_moe_sls_app")

def geo_test(schoolName):
    # Disable SSL verification for testing purposes (not recommended for production)
    ssl._create_default_https_context = ssl._create_unverified_context
    
    geolocator = OpenCage(api_key=st.secrets["OPENCAGE_API_KEY"])
    location = geolocator.geocode(f"{schoolName}, Singapore", timeout=10)  # Postal code for Singapore
    #st.write(location)
    
    return location.latitude, location.longitude

def show_mapview():
    
    get_global_filter()

    zone_name = st.selectbox("Zone", list(zone_data.keys()))

    start_date, end_date = create_date_filter()
    
    df_map = getData_Map(start_date, end_date, zone_data[zone_name])
    #st.dataframe(df_map)

    mean_total_usage = df_map["TOTAL_USAGE"].mean()

    if df_map.empty:
        st.warning("No data available to display on the map.")
        return

    # Create the map
    m = folium.Map(location=[1.3521, 103.8198], zoom_start=12, tiles="CartoDB positron")  # Singapore's coordinates

    # Add markers for each school
    for _, row in df_map.iterrows():
        # Geocode postal code to latitude and longitude
        latitude, longitude = geo_test(row['SCHOOLNAME'])

        if latitude and longitude:  # Proceed if valid coordinates found
            popup_text = f"""
            <b>{row['SCHOOLNAME']}</b><br>
            📊 Total Usage: {row['TOTAL_USAGE']}<br>
            👩‍🏫 Unique Users: {row['UNIQUE_USERS']}
            """
            
            # Set marker color based on mean_total_usage
            if row['TOTAL_USAGE'] > 0.75 * mean_total_usage:
                color = '#22c55e'  # green
                radius = 7
            elif row['TOTAL_USAGE'] > 0.40 * mean_total_usage:
                color = '#f5b03b'  # amber
                radius = 5
            else:
                color = '#f05454'  # red
                radius = 3
            
            # Add marker
            folium.CircleMarker(
                location=[latitude, longitude],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                tooltip=popup_text
            ).add_to(m)

    # Display the map in Streamlit
    folium_static(m, width=1000, height=400)
        
    st.caption("Map data © OpenStreetMap contributors")

def show_detailedAnalysis():
    
        get_global_filter()

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
            #st.dataframe(df_search)

            if not df_search.empty:
                # get Usage Data
                df_usage_sorted = df_search.sort_values(by='TOTAL_USAGE', ascending=False)
                # Get top 5 rows
                top_5_usage = df_usage_sorted.head(3)
                # Get bottom 5 rows
                bottom_5_usage = df_usage_sorted.tail(3)

                # get Adoption Data
                df_adoption_sorted = df_search.sort_values(by='UNIQUE_USERS', ascending=False)
                # Get top 5 rows
                top_5_adoption = df_adoption_sorted.head(3)
                # Get bottom 5 rows
                bottom_5_adoption = df_adoption_sorted.tail(3)

                #st.dataframe(top_5_adoption)
                #st.dataframe(bottom_5_adoption)

                avg_usage_per_tchr = round(df_search['TOTAL_USAGE'].sum()/df_search['UNIQUE_USERS'].sum(),1)

                # Cluster info
                st.markdown(f"""
                    <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; 
                                padding: 0.75rem; border-radius: 1rem; border: 2px solid #e5e7eb; 
                                margin-bottom: 1rem; transition: background-color 0.2s;
                                hover:background-color: #3b82f6;'>
                        <div style='text-align: center; margin: 1rem'>
                            <p style='font-size: 2.175rem; font-weight: bold;'>Cluster: {zone_name}{cluster} </p>
                            <p style='font-size: 1.875rem; color: #3b82f6;'>Average Product Usage per Teacher: {avg_usage_per_tchr}</p>
                            <p style='font-size: 0.975rem; color: #666666;'> from {datetime.date(start_date)} to {datetime.date(end_date)} across {df_search['SCHOOLNAME'].nunique()} Schools, {df_search['UNIQUE_USERS'].sum()} Teachers </p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Top and bottom performers
                col1, col2 = st.columns(2)
                
                # Top
                with col1:
                    st.markdown("#### Highest Usage Rate")
                    
                    for index, school in top_5_usage.iterrows():
                        #st.dataframe(school)
                        color = "#22c55e" #if school["is_highest"] else "#60a5fa"
                        st.markdown(f"""
                        <div style='display: flex; align-items: center; justify-content: space-between; 
                                    padding: 0.75rem; border-radius: 0.5rem; border: 1px solid #e5e7eb; 
                                    margin-bottom: 1rem; transition: background-color 0.2s;
                                    hover:background-color: rgba(243, 244, 246, 0.5);'>
                            <div style='display: flex; align-items: center;'>
                                <div style='width: 2rem; height: 2rem; display: flex; align-items: center; 
                                        justify-content: center; border-radius: 9999px; color: white; 
                                        font-weight: 500; background-color: {color};'>
                                    {index+1}
                                </div>
                                <span style='margin-left: 0.75rem; font-weight: 500;'>{school["SCHOOLNAME"]}</span>
                            </div>
                            <span style='color: {color}; font-size: 2.5 rem; font-weight: 300;'>{school["TOTAL_USAGE"]}</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Bottom
                with col2:
                    st.markdown("#### Lowest Usage Rate")
                    
                    for index, school in bottom_5_usage.iterrows():
                        color = "#f05454" #if school["is_lowest"] else "#f87171"
                        st.markdown(f"""
                        <div style='display: flex; align-items: center; justify-content: space-between; 
                                    padding: 0.75rem; border-radius: 0.5rem; border: 1px solid #e5e7eb; 
                                    margin-bottom: 1rem; transition: background-color 0.2s;
                                    hover:background-color: rgba(243, 244, 246, 0.5);'>
                            <div style='display: flex; align-items: center;'>
                                <div style='width: 2rem; height: 2rem; display: flex; align-items: center; 
                                        justify-content: center; border-radius: 9999px; color: white; 
                                        font-weight: 500; background-color: {color};'>
                                    {index+1}
                                </div>
                                <span style='margin-left: 0.75rem; font-weight: 500;'>{school["SCHOOLNAME"]}</span>
                            </div>
                            <span style='color: {color}; font-size: 2.5 rem; font-weight: 300;'>{school["TOTAL_USAGE"]}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                # Bar chart
                st.markdown("")
                st.markdown("#### Adoption Rate by Schools")
                
                fig = px.bar(
                    df_adoption_sorted,
                    x='SCHOOLNAME',
                    y='UNIQUE_USERS',
                    color_discrete_sequence=['#5A8EED'],
                    labels={'SCHOOLNAME': '', 'UNIQUE_USERS': 'Total Users'},
                    text='UNIQUE_USERS',
                    height=500
                )
                # Update trace to show the text outside the bars
                fig.update_traces(texttemplate='%{text}', textposition='outside')
                
                st.plotly_chart(fig, use_container_width=True)
            
            else:
                st.error("No data found, please re-select the filter.")


def show_chatbot():
    # API key input - for demonstration purposes
        with st.sidebar.expander("OpenAI API Settings"):
            api_key = st.text_input("Enter your OpenAI API Key", type="password")
            model = st.selectbox("Select model", ["gpt-4o-mini", "gpt-4o"], index=0)
            st.caption("Note: Your API key is not stored and will be cleared when you refresh the page.")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Hello! I'm your analytics assistant. How can I help you today? You can ask me questions like 'Generate a report for North East zone's adoption trends' or 'What are the top performing schools in Cluster N1?'"
            }]
        
        # Get Data
        df_bot = getData_Bot()

        # Convert DataFrame to JSON
        df_bot_json = df_bot.to_json(orient="records")


        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a question about adoption rates, trends, or request a report..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                if not api_key:
                    bot_response = "Please enter your OpenAI API key in the sidebar to enable AI-powered responses."
                else:
                    with st.spinner("Generating response..."):
                        bot_response = get_openai_response(prompt, api_key, model, df_bot_json)
                
                st.write(bot_response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": bot_response})



# Function to create date filter UI
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

# Function to get system prompt
def load_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# Function to get OpenAI response
def get_openai_response(prompt, api_key, model, df_bot_json):
          
    # Prepare prompt with context
    context = f"""
        You are an AI assistant for a Singapore Ministry of Education (MOE) analytics dashboard. 
        Your purpose is to analyse school usage and adoption rates across Singapore and provide insights based on the data '{df_bot_json}'.
        Please note "East Zone": 1, "West Zone": 2, "North Zone": 3, "South Zone": 4
        """

    try:
        client = openai.OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=10000
        )
        #st.write(completion.usage)
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error getting response: {str(e)}"

