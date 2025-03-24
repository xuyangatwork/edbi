import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_folium import folium_static
import folium
import openai
from datetime import datetime, timedelta

# Sample data for demonstration
@st.cache_data
def load_sample_data():
    # School data
    schools_data = pd.DataFrame({
        'id': range(1, 10),
        'name': [
            'Fu Hua Secondary', 'Greenview Secondary', 'East View Secondary',
            'Compassvale Secondary', 'Punggol Secondary', 'Sengkang Secondary',
            'Rivervale Secondary', 'Edgefield Secondary', 'North Vista Secondary'
        ],
        'x': [38, 42, 48, 30, 36, 33, 28, 25, 22],  # Map coordinates
        'y': [40, 45, 47, 48, 53, 47, 42, 45, 48],  # Map coordinates
        'type': ['high', 'high', 'high', 'medium', 'medium', 'medium', 'low', 'low', 'low'],
        'rate': [67, 71, 63, 42, 38, 45, 24, 18, 21],
        'teachers': [62, 58, 75, 68, 82, 59, 71, 66, 77]
    })
    
    # Bar chart data
    school_usage_data = pd.DataFrame({
        'name': [f'School {chr(65+i)}' for i in range(13)],
        'value': [328449, 223844, 206966, 201413, 114880, 107532, 91705, 78479, 46624, 27119, 16476, 12486, 3024],
        'fill': ['#5A8EED'] * 13
    })
    
    return schools_data, school_usage_data

schools_data, school_usage_data = load_sample_data()


def show_mapview():
# Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            zone = st.selectbox("Zone", ["North East", "North West", "South East", "South West", "Central"])
        with col2:
            cluster = st.selectbox("Cluster", ["Cluster N1", "Cluster N2", "Cluster N3", "Cluster N4"])
        with col3:
            school_type = st.selectbox("School Type", ["Primary", "Secondary", "Junior College", "All"])
        
        start_date, end_date = create_date_filter()

        # Create the map
        st.markdown("#### Singapore Schools Adoption Map")
        
        m = folium.Map(location=[1.3521, 103.8198], zoom_start=12, tiles="CartoDB positron")
        
        # Add markers for schools
        for _, school in schools_data.iterrows():
            # Convert percentage coordinates to actual lat/lng (simplified for demo)
            # This is a rough approximation - in a real app, you'd use actual GPS coordinates
            lat = 1.3521 + (school['y'] - 45) * 0.003
            lng = 103.8198 + (school['x'] - 35) * 0.003
            
            # Set marker color based on adoption type
            if school['type'] == 'high':
                color = '#22c55e'  # green
                radius = 8
            elif school['type'] == 'medium':
                color = '#f59e0b'  # amber
                radius = 7
            else:
                color = '#ef4444'  # red
                radius = 6
            
            # Add marker
            folium.CircleMarker(
                location=[lat, lng],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                tooltip=f"{school['name']}: {school['rate']}% adoption rate, {school['teachers']} teachers"
            ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; background-color: white; 
                    padding: 10px; border: 1px solid #e5e7eb; border-radius: 5px;">
            <p><i class="fa fa-circle" style="color:#22c55e"></i> High Adoption (>60%)</p>
            <p><i class="fa fa-circle" style="color:#f59e0b"></i> Medium Adoption (30-60%)</p>
            <p><i class="fa fa-circle" style="color:#ef4444"></i> Low Adoption (<30%)</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Display the map
        folium_static(m, width=1000, height=500)
        
        st.caption("Map data © OpenStreetMap contributors")
    

def show_detailedAnalysis():
    # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            zone = st.selectbox("Zone", ["North East", "North West", "South East", "South West", "Central"])
        with col2:
            cluster = st.selectbox("Cluster", ["Cluster N1", "Cluster N2", "Cluster N3", "Cluster N4"])
        with col3:
            school_type = st.selectbox("School Type", ["Primary", "Secondary", "Junior College", "All"])
        
        start_date, end_date = create_date_filter()
        

        # Cluster info
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h1 style='font-size: 1.875rem; font-weight: 500;'>Cluster N1</h1>
            <p style='font-size: 1.875rem; font-weight: 500; color: #3b82f6;'>35% Avg Adoption Rate</p>
            <p style='color: #6b7280;'>14 Schools, 1,766 Teachers</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Top and bottom performers
        col1, col2 = st.columns(2)
        
        # Top
        with col1:
            st.markdown("#### Highest Adoption Rate")
            
            top_schools = [
                {"name": "Fu Hua Secondary", "rate": 67, "count": "328,449", "is_highest": True},
                {"name": "Greenview Secondary", "rate": 71, "count": "223,844", "is_highest": False},
                {"name": "East View Secondary", "rate": 63, "count": "206,966", "is_highest": False}
            ]
            
            for school in top_schools:
                color = "#22c55e" if school["is_highest"] else "#60a5fa"
                st.markdown(f"""
                <div style='display: flex; align-items: center; justify-content: space-between; 
                            padding: 0.75rem; border-radius: 0.5rem; border: 1px solid #e5e7eb; 
                            margin-bottom: 0.75rem; transition: background-color 0.2s;
                            hover:background-color: rgba(243, 244, 246, 0.5);'>
                    <div style='display: flex; align-items: center;'>
                        <div style='width: 2.5rem; height: 2.5rem; display: flex; align-items: center; 
                                justify-content: center; border-radius: 9999px; color: white; 
                                font-weight: 500; background-color: {color};'>
                            {school["rate"]}%
                        </div>
                        <span style='margin-left: 0.75rem; font-weight: 500;'>{school["name"]}</span>
                    </div>
                    <span style='color: #6b7280; font-size: 0.875rem;'>{school["count"]}</span>
                </div>
                """, unsafe_allow_html=True)
        
        # Bottom
        with col2:
            st.markdown("#### Lowest Adoption Rate")
            
            bottom_schools = [
                {"name": "Rivervale Secondary", "rate": 24, "count": "27,119", "is_lowest": True},
                {"name": "Edgefield Secondary", "rate": 18, "count": "16,476", "is_lowest": False},
                {"name": "North Vista Secondary", "rate": 21, "count": "3,024", "is_lowest": False}
            ]
            
            for school in bottom_schools:
                color = "#ef4444" if school["is_lowest"] else "#f87171"
                st.markdown(f"""
                <div style='display: flex; align-items: center; justify-content: space-between; 
                            padding: 0.75rem; border-radius: 0.5rem; border: 1px solid #e5e7eb; 
                            margin-bottom: 0.75rem; transition: background-color 0.2s;
                            hover:background-color: rgba(243, 244, 246, 0.5);'>
                    <div style='display: flex; align-items: center;'>
                        <div style='width: 2.5rem; height: 2.5rem; display: flex; align-items: center; 
                                justify-content: center; border-radius: 9999px; color: white; 
                                font-weight: 500; background-color: {color};'>
                            {school["rate"]}%
                        </div>
                        <span style='margin-left: 0.75rem; font-weight: 500;'>{school["name"]}</span>
                    </div>
                    <span style='color: #6b7280; font-size: 0.875rem;'>{school["count"]}</span>
                </div>
                """, unsafe_allow_html=True)
                
        # Bar chart
        st.markdown("#### Adoption Rate by Schools")
        
        fig = px.bar(
            school_usage_data,
            x='name',
            y='value',
            color_discrete_sequence=['#5A8EED'],
            labels={'name': 'School', 'value': 'Usage'},
            height=500
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            margin=dict(l=20, r=20, t=40, b=70),
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                gridcolor='rgba(0,0,0,0.05)'
            ),
            yaxis=dict(
                gridcolor='rgba(0,0,0,0.05)'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption("adoption rate by schools")


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
                        bot_response = get_openai_response(prompt, api_key, model)
                
                st.write(bot_response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": bot_response})



# Function to create date filter UI
def create_date_filter():
    today = datetime.now()
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "From Date",
            today - timedelta(days=30),
            min_value=today - timedelta(days=90),
            max_value=today
        )
    
    with col2:
        end_date = st.date_input(
            "To Date",
            today,
            min_value=today - timedelta(days=90),
            max_value=today
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
def get_openai_response(prompt, api_key, model):
          
    # Prepare prompt with context
    context = """
        You are an AI assistant for a Singapore Ministry of Education (MOE) analytics dashboard. 
        Your purpose is to analyse school adoption rates across Singapore and provide insights.
        The data shows adoption rates for various schools grouped by clusters and zones.
        Top performing schools in Cluster N1 include Greenview Secondary (71%), Fu Hua Secondary (67%), 
        and East View Secondary (63%). The overall adoption rate for the North East zone is about 42%.
        Schools with dedicated IT coordinators show 30% higher adoption rates.
        Respond to questions about adoption rates, trends, or generate reports based on this information.
        Keep your responses concise, factual, and focused on educational technology adoption.
        """

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    date_str = ""

    # Load and display
    context = date_str + load_prompt("prompt.txt")
           
    try:
        client = openai.OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                #{"role": "system", "content": context},
                #{"role": "user", "content": prompt}
                {"role": "system", "content": ""},
                {"role": "user", "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://isomer-user-content.by.gov.sg/34/538442d6-fbd6-4323-9f99-7001a01ba5b6/Support%20for%20Singaporeans.jpg",
                            "detail": "low",
                        },
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://isomer-user-content.by.gov.sg/34/622beb19-ccb1-4ab1-a340-1413b02c7881/B2025%20-%20Support%20for%20You.jpg",
                            "detail": "low",
                        },
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://isomer-user-content.by.gov.sg/34/d53a965d-23b9-420d-b6cd-9c07b62063fe/B2025%20-%20Support%20for%20Families%20and%20Seniors.jpg",
                            "detail": "low",
                        },
                    },
                    {"type": "text", "text": prompt},
                ]}
            ],
            temperature=0.7,
            max_tokens=10000
        )
        print(completion.usage)
        st.write(completion.usage)
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error getting response: {str(e)}"
