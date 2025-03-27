
import streamlit as st
import streamlit_antd_components as sac
from modules.analysis import getData, get_global_filter
from modules.usage import show_mapview, show_detailedAnalysis, show_chatbot
from modules.feedback import show_feedbackAnalysis


#page = st.sidebar.radio("Navigation", ["Map View", "Analysis", "Chatbot", "Feedback"])

def main():

    # Store each filer DataFrame to session
    if 'df_schools' not in st.session_state:
        st.session_state.df_schools = ""
    if 'df_types' not in st.session_state:
        st.session_state.df_types = ""
    if 'df_zones' not in st.session_state:
        st.session_state.df_zones = ""
    if 'df_clusters' not in st.session_state:
        st.session_state.df_clusters = ""
    if 'df_dates' not in st.session_state:
        st.session_state.df_dates = ""
    if 'min_date' not in st.session_state:
        st.session_state.min_date = ""
    if 'max_date' not in st.session_state:
        st.session_state.max_date = ""

    # Create sidebar
    with st.sidebar: #options for sidebar
        #st.image("moe-logo.svg")

        # Sidebar navigation
        st.sidebar.title("EduPlan Analytics")
        st.sidebar.markdown("---")

        page = sac.menu([
            sac.MenuItem('Map View'),
            sac.MenuItem('Analysis'),
            sac.MenuItem('Chatbot'),
            sac.MenuItem('Feedback'),
            #sac.MenuItem('SnowFlake Connection Test')
            ], index=0, format_func='title', open_all=True)


    # Establish Snowflake connection
    #conn = create_connection()

    # Call the cached function once when the app starts
    get_global_filter()

    # Landing Page
    if page == "Landing":
        st.title("EduPlan")
        st.markdown("Welcome to the landing page")
        
    # Map View Page
    elif page == "Map View":
        
        st.title("Map View")
        st.markdown("Interactive visualization of adoption rates across Singapore schools")

        show_mapview()
          
    # Analysis Page
    elif page == "Analysis":
        
        st.title("Detailed Analysis")
        st.markdown("In-depth analytics on school adoption rates, trends, and performance metrics")
        
        show_detailedAnalysis()

    # Chatbot Page
    elif page == "Chatbot":
        st.title("GenAI Analytics Assistant")
        
        show_chatbot()

    # Feedback Dashboard
    elif page == "Feedback":
        st.title("Feedback Dashboard")
        
        show_feedbackAnalysis()

    # SnowFlake Connection Test
    elif page == "SnowFlake Connection Test":
         
        getData()


    # User information in sidebar footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
        <div style='display: flex; align-items: center;'>
            <div style='width: 32px; height: 32px; border-radius: 50%; background-color: rgba(59, 130, 246, 0.1); 
                display: flex; align-items: center; justify-content: center; margin-right: 10px;
                color: rgb(59, 130, 246); font-weight: 500;'>SG</div>
            <div>
                <p style='font-weight: 500; margin: 0;'>Ministry of Education</p>
                <p style='font-size: 12px; color: #6b7280; margin: 0;'>EduPlan Admin Portal</p>
            </div>
        </div>
    """, unsafe_allow_html=True)




if __name__ == "__main__":
	main()
