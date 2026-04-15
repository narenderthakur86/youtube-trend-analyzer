import streamlit as st
import pandas as pd
from youtube_service import YouTubeService
from openai_service import OpenAIService

st.set_page_config(page_title="AI Trend Analyzer", page_icon="📈", layout="wide")

st.title("📈 AI Niche Trend Analyzer")
st.write("Find outperforming YouTube videos leveraging the Outlier Score (Views / Subscribers).")

# Sidebar Configuration
st.sidebar.header("Configuration")

# Try to load keys securely from Streamlit secrets, otherwise show the text input boxes
yt_api_key = st.secrets.get("YOUTUBE_API_KEY", "") if "YOUTUBE_API_KEY" in st.secrets else ""
if not yt_api_key:
    yt_api_key = st.sidebar.text_input("YouTube Data v3 API Key (or set in secrets)", type="password")

openai_api_key = st.secrets.get("OPENAI_API_KEY", "") if "OPENAI_API_KEY" in st.secrets else ""
if not openai_api_key:
    openai_api_key = st.sidebar.text_input("OpenAI API Key (or set in secrets)", type="password")

st.sidebar.markdown("---")
st.sidebar.header("Search Parameters")
query = st.sidebar.text_input("Search Keyword / Query", value="Artificial Intelligence Tools")
days_ago = st.sidebar.slider("Look back (Days)", min_value=1, max_value=90, value=14)
max_results = st.sidebar.slider("Videos to Analyze", min_value=10, max_value=100, value=50, step=10)
min_outlier_score = st.sidebar.slider("Min Outlier Score", min_value=0.0, max_value=50.0, value=1.0, step=0.5, help="Videos with more views than this multiple of their subscriber count (e.g., 2.0 = double views than subs).")

if st.sidebar.button("Run Analysis", type="primary"):
    if not yt_api_key or not openai_api_key:
        st.error("Please provide both YouTube and OpenAI API keys in the sidebar.")
    elif not query:
        st.error("Please provide a search keyword.")
    else:
        with st.spinner("Fetching data from YouTube API..."):
            yt_service = YouTubeService(yt_api_key)
            if not yt_service.is_valid:
                st.error(f"Error initializing YouTube service: {yt_service.error}")
                st.stop()
                
            df, error = yt_service.get_outperforming_videos(query=query, max_results=max_results, days_ago=days_ago)

            if error:
                st.error(error)
                st.stop()

            if df is None or df.empty:
                st.warning("No videos found matching the criteria.")
                st.stop()

            # Filter by minimum outlier score
            filtered_df = df[df["outlier_score"] >= min_outlier_score]
            
            if filtered_df.empty:
                st.warning(f"Found {len(df)} videos, but none met the minimum Outlier Score of {min_outlier_score}.")
                st.dataframe(df) # show what was found anyway
                st.stop()

            st.success(f"Successfully processed and sorted videos. {len(filtered_df)} videos meet the Outlier Score threshold.")

        # --- AI Analysis ---
        with st.spinner("Analyzing trends with OpenAI..."):
            openai_service = OpenAIService(openai_api_key)
            if not openai_service.is_valid:
                st.error(f"Error initializing OpenAI service: {openai_service.error}")
            else:
                ai_report = openai_service.analyze_trends(filtered_df)
                st.subheader("🤖 AI Trend Analysis Report")
                st.markdown(ai_report)
                st.markdown("---")

        # --- Data Display ---
        st.subheader("📊 Top Outperforming Videos")
        
        # Displaying videos cleanly
        for idx, row in filtered_df.iterrows():
            col1, col2 = st.columns([1, 6])
            with col1:
                st.image(row["thumbnail"], use_column_width=True)
            with col2:
                st.markdown(f"### [{row['title']}]({row['url']})")
                st.markdown(f"**Channel:** {row['channel_name']} | **Views:** {row['views']:,} | **Subscribers:** {row['subscribers']:,}")
                st.markdown(f"🔥 **Outlier Score:** `{row['outlier_score']}x`")
                st.caption(f"Published on: {row['published_at'][:10]} | Likes: {row['likes']:,} | Comments: {row['comments']:,}")
            st.markdown("---")

        with st.expander("Show Raw Data Table"):
            st.dataframe(filtered_df)
