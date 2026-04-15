from openai import OpenAI
import json

class OpenAIService:
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            self.client = OpenAI(api_key=api_key)
            self.is_valid = True
        except Exception as e:
            self.is_valid = False
            self.error = str(e)

    def analyze_trends(self, df):
        if not self.is_valid:
            return "OpenAI API is not valid."
        
        if df.empty:
            return "No data provided to analyze."

        # Take the top 15 outperforming videos to summarize
        top_videos = df.head(15)
        
        # Prepare context payload
        video_context = ""
        for i, row in top_videos.iterrows():
            video_context += f"Title: {row['title']} | Channel: {row['channel_name']} | Outlier Score: {row['outlier_score']} | Views: {row['views']}\n"

        prompt = f"""
You are an expert YouTube strategist in the AI niche. 
I am going to provide you with a list of the recent outperforming videos based on an "Outlier Score" (views relative to channel subscribers).

Analyze these titles and data, and give me a clear, actionable summary of the hottest trends right now. What are these videos doing right? Are there specific topics (like "Local LLMs", "Midjourney updates", "AutoGPT") or specific formats (e.g., "The brutal truth about X", "I built Y in 24 hours") that are hitting hard?

Here is the data:
{video_context}

Provide your analysis in Markdown format using bullet points, bold text for key themes, and keep it extremely actionable for a creator looking for their next viral idea.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using a highly accessible model
                messages=[
                    {"role": "system", "content": "You are a trend analyst expert for YouTube creators."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error during OpenAI Analysis: {str(e)}"
