# Real-Time Twitter Sentiment Analysis

This repository contains two Python scripts that fetch recent tweets containing a specified brand name using Tweepy (Twitter API v2) and perform sentiment analysis using TextBlob. The processed data is prepared for visualization and analysis in Power BI, and both scripts can be run in the VS Code Terminal. The v2 script includes a DEBUG mode switch for flexible integration with Power BI and for development.

---

## Features

- Real-time extraction of tweets using the Twitter API v2.
- Text cleaning and sentiment scoring (polarity and subjectivity).
- Categorization of sentiment into Positive, Neutral, and Negative.
- Engagement metrics calculation (likes, retweets, replies, quotes).
- Time-based feature extraction for detailed analysis.
- Ready-to-load data format for Power BI dashboards.
- Two script versions (v1 and v2), allowing fallback if one encounters issues.
- v2: DEBUG mode flag for flexible output:  
  - `DEBUG = True`: VS Code mode (prints processed output, saves CSV, verbose logging).  
  - `DEBUG = False`: Power BI mode (silent, outputs only CSV).

---

## Important Notes on API Usage


**TWITTER API CREDENTIALS - Get these from (`developer.twitter.com`)**

This project uses the free tier of Twitter's (X) API, which has strict rate limits, including:
- Maximum of 100 tweets per run (recommended to keep under this limit).
- Limited number of API requests allowed per 15-minute window and per day.
- Rate limiting may cause delays or require waiting if the quota is exceeded.

**If you plan to use this script with real Twitter data:**
- Stay within the free tier limits—keep requests under 100 tweets per run.
- Consider upgrading to a paid tier for higher limits and larger data access.
- Adjust configuration parameters (`MAX_TWEETS`) as needed to avoid rate limits.
- During development, mock or cache outputs to minimize live API calls.

---

## Getting Started

1. Clone this repository.
2. Add your Twitter API credentials in the scripts.
3. (Optional) Use the included demo dataset for initial testing to avoid API limits.
4. Choose which script to run:  
   - `tweepy_scrapper_v1.py` for compatibility and fallback.  
   - `tweepy_scrapper_v2.py` with DEBUG mode for Power BI or development.
5. Set the `DEBUG` flag in v2 as required.
6. Run the script to generate a CSV output for Power BI.
7. Import the CSV into Power BI to visualize sentiment trends.

---

## Usage

Modify these parameters in the script(s):

- `BRAND_NAME = "Tesla"`       # Brand to track  
- `MAX_TWEETS = 100`           # Number of tweets per run (between 10 and 100 for free API)  
- `DAYS_BACK = 7`              # Days back for historical tweets (must be ≤ 7 for free API)  
- In v2: `DEBUG = True` (VS Code mode) or `False` (Power BI mode)

---

## Script Selection and Dashboard

- Use `tweepy_scrapper_v1.py` for maximum compatibility and as a fallback if API or data structure changes occur.
- Use `tweepy_scrapper_v2.py` for advanced use with the `DEBUG` mode flag, allowing seamless integration in Power BI pipelines and enhanced development logging in VS Code.

---

## Dashboard
<img width="1116" height="629" alt="Screenshot 2025-10-25 013508" src="https://github.com/user-attachments/assets/934eedeb-c7c6-46c9-b1ad-59bc87c70f43" />




