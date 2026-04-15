from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from datetime import datetime, timedelta

class YouTubeService:
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            self.youtube = build("youtube", "v3", developerKey=api_key)
            self.is_valid = True
        except Exception as e:
            self.is_valid = False
            self.error = str(e)

    def get_outperforming_videos(self, query, max_results=50, days_ago=30):
        if not self.is_valid:
            return None, "YouTube service is not initialized correctly."

        try:
            # 1. Search for videos
            published_after = (datetime.utcnow() - timedelta(days=days_ago)).isoformat() + "Z"
            
            search_response = self.youtube.search().list(
                q=query,
                part="id,snippet",
                maxResults=max_results,
                type="video",
                relevanceLanguage="en",
                publishedAfter=published_after,
                order="viewCount"
            ).execute()

            video_ids = []
            channel_ids = set()
            videos_data = {}

            for item in search_response.get("items", []):
                vid = item["id"]["videoId"]
                cid = item["snippet"]["channelId"]
                video_ids.append(vid)
                channel_ids.add(cid)
                videos_data[vid] = {
                    "video_id": vid,
                    "title": item["snippet"]["title"],
                    "channel_id": cid,
                    "channel_name": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
                }

            if not video_ids:
                return pd.DataFrame(), None

            # 2. Get Video Statistics
            video_stats_response = self.youtube.videos().list(
                part="statistics",
                id=",".join(video_ids)
            ).execute()

            for item in video_stats_response.get("items", []):
                vid = item["id"]
                stats = item["statistics"]
                videos_data[vid]["views"] = int(stats.get("viewCount", 0))
                videos_data[vid]["likes"] = int(stats.get("likeCount", 0))
                videos_data[vid]["comments"] = int(stats.get("commentCount", 0))

            # 3. Get Channel Statistics (To calculate Outlier Score)
            channel_ids_list = list(channel_ids)
            channels_data = {}
            
            # Batch channel requests up to 50 at a time
            for i in range(0, len(channel_ids_list), 50):
                batch_ids = channel_ids_list[i:i+50]
                channel_stats_response = self.youtube.channels().list(
                    part="statistics",
                    id=",".join(batch_ids)
                ).execute()

                for item in channel_stats_response.get("items", []):
                    cid = item["id"]
                    stats = item["statistics"]
                    # If subscriber count is hidden, it's not returned or it's 0.
                    subs = int(stats.get("subscriberCount", 0))
                    # Avoid division by zero by setting a minimum baseline.
                    channels_data[cid] = subs if subs > 0 else 1

            # 4. Integrate Data and Calculate Outlier Score
            final_data = []
            for vid, data in videos_data.items():
                subs = channels_data.get(data["channel_id"], 1)
                views = data.get("views", 0)
                outlier_score = views / subs if subs > 0 else 0
                
                data["subscribers"] = subs
                data["outlier_score"] = round(outlier_score, 2)
                data["url"] = f"https://www.youtube.com/watch?v={vid}"
                final_data.append(data)

            df = pd.DataFrame(final_data)
            df = df.sort_values(by="outlier_score", ascending=False)
            
            return df, None

        except HttpError as e:
            return None, f"YouTube API Error: {e.reason}"
        except Exception as e:
            return None, str(e)
