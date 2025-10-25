# Real-Time Twitter Sentiment Analysis for Power BI and VS Code

import pandas as pd
from datetime import datetime, timedelta
import re
from textblob import TextBlob
import warnings
warnings.filterwarnings('ignore')

# ========================================================================
# CONFIGURATION
# ========================================================================

DEBUG = True   # True = VS Code mode (prints + saves CSV)
               # False = Power BI mode (silent, no prints)

API_KEY = "Your_API_Key_Here"
API_SECRET = "Your_API_Secret_Here"
ACCESS_TOKEN = "Your_Access_Token_Here"
ACCESS_TOKEN_SECRET = "Your_Access_Token_Secret_Here"
BEARER_TOKEN = "Your_Bearer_Token_Here"  # For API v2

BRAND_NAME = "Brand_Name_Here"  # Change this to any brand you want to track
SEARCH_QUERY = f"{BRAND_NAME} -is:retweet lang:en"
MAX_TWEETS = 100  # Number of tweets to fetch per refresh (Must be between 10 and 100 for free API)
DAYS_BACK = 7  # How many days of historical tweets to fetch (Must be <= 7 for free API)
USE_API_V2 = True # Set to True to use Twitter API v2, False for v1.1

# ========================================================================
# SENTIMENT HELPERS
# ========================================================================

def log(msg):
    """Conditional print for debug mode"""
    if DEBUG:
        print(msg)

def clean_tweet(tweet):
    tweet = re.sub(r'http\S+|www.\S+', '', tweet)
    tweet = re.sub(r'@\w+', '', tweet)
    tweet = re.sub(r'#(\w+)', r'\1', tweet)
    tweet = re.sub(r'\s+', ' ', tweet).strip()
    return tweet

def get_sentiment_score(text):
    try:
        return TextBlob(text).sentiment.polarity
    except:
        return 0.0

def get_sentiment_subjectivity(text):
    try:
        return TextBlob(text).sentiment.subjectivity
    except:
        return 0.0

def categorize_sentiment(score):
    if score > 0.1:
        return "Positive"
    elif score < -0.1:
        return "Negative"
    else:
        return "Neutral"

# ========================================================================
# TWITTER FETCHING
# ========================================================================

def fetch_tweets_with_tweepy():
    import tweepy
    tweets_data = []

    try:
        if USE_API_V2:
            log("Using Twitter API v2...")
            client = tweepy.Client(
                bearer_token=BEARER_TOKEN,
                consumer_key=API_KEY,
                consumer_secret=API_SECRET,
                access_token=ACCESS_TOKEN,
                access_token_secret=ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True
            )

            start_time = datetime.utcnow() - timedelta(days=DAYS_BACK)
            response = client.search_recent_tweets(
                query=SEARCH_QUERY,
                max_results=min(MAX_TWEETS, 100),
                tweet_fields=['created_at', 'public_metrics', 'lang', 'author_id'],
                user_fields=['username', 'name', 'verified', 'public_metrics'],
                expansions=['author_id'],
                start_time=start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            )

            if response.data:
                users = {u.id: u for u in response.includes['users']}
                for tweet in response.data:
                    user = users.get(tweet.author_id)
                    tweets_data.append({
                        'tweet_id': str(tweet.id),
                        'created_at': tweet.created_at,
                        'username': user.username if user else 'unknown',
                        'user_display_name': user.name if user else 'unknown',
                        'text': tweet.text,
                        'retweet_count': tweet.public_metrics['retweet_count'],
                        'reply_count': tweet.public_metrics['reply_count'],
                        'like_count': tweet.public_metrics['like_count'],
                        'quote_count': tweet.public_metrics['quote_count'],
                        'user_followers': user.public_metrics['followers_count'] if user else 0,
                        'user_verified': user.verified if user else False,
                        'language': tweet.lang
                    })
            else:
                log("No tweets found.")
        else:
            log("Using Twitter API v1.1...")
            auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
            auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
            api = tweepy.API(auth, wait_on_rate_limit=True)
            tweets = tweepy.Cursor(
                api.search_tweets,
                q=SEARCH_QUERY,
                lang='en',
                tweet_mode='extended',
                result_type='recent'
            ).items(MAX_TWEETS)

            for tweet in tweets:
                tweets_data.append({
                    'tweet_id': str(tweet.id),
                    'created_at': tweet.created_at,
                    'username': tweet.user.screen_name,
                    'user_display_name': tweet.user.name,
                    'text': tweet.full_text,
                    'retweet_count': tweet.retweet_count,
                    'reply_count': 0,
                    'like_count': tweet.favorite_count,
                    'quote_count': 0,
                    'user_followers': tweet.user.followers_count,
                    'user_verified': tweet.user.verified,
                    'language': tweet.lang
                })

        log(f"Fetched {len(tweets_data)} tweets.")
    except Exception as e:
        log(f"Fetch error: {e}")
        return pd.DataFrame()

    return pd.DataFrame(tweets_data)

# ========================================================================
# MAIN SENTIMENT PIPELINE
# ========================================================================

def process_sentiment_data():
    df = fetch_tweets_with_tweepy()

    if df.empty:
        log("No data fetched.")
        return pd.DataFrame(columns=[
            'tweet_id', 'created_at', 'date', 'hour', 'day_of_week',
            'brand', 'username', 'user_display_name', 'text', 'cleaned_text',
            'sentiment_score', 'sentiment_subjectivity', 'sentiment_category',
            'retweet_count', 'reply_count', 'like_count', 'quote_count',
            'engagement', 'user_followers', 'user_verified', 'language'
        ])

    df['cleaned_text'] = df['text'].apply(clean_tweet)
    df['sentiment_score'] = df['cleaned_text'].apply(get_sentiment_score)
    df['sentiment_subjectivity'] = df['cleaned_text'].apply(get_sentiment_subjectivity)
    df['sentiment_category'] = df['sentiment_score'].apply(categorize_sentiment)
    df['brand'] = BRAND_NAME
    df['engagement'] = df['like_count'] + df['retweet_count'] + df['reply_count'] + df['quote_count']
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['date'] = df['created_at'].dt.date
    df['hour'] = df['created_at'].dt.hour
    df['day_of_week'] = df['created_at'].dt.day_name()

    columns = [
        'tweet_id', 'created_at', 'date', 'hour', 'day_of_week',
        'brand', 'username', 'user_display_name', 'text', 'cleaned_text',
        'sentiment_score', 'sentiment_subjectivity', 'sentiment_category',
        'retweet_count', 'reply_count', 'like_count', 'quote_count',
        'engagement', 'user_followers', 'user_verified', 'language'
    ]

    df = df[columns]

    if DEBUG:
        log(f"\nTotal tweets analyzed: {len(df)}")
        sentiment_counts = df['sentiment_category'].value_counts()
        for cat, count in sentiment_counts.items():
            log(f"{cat}: {count}")
        csv_filename = f"twitter_sentiment_{BRAND_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False)
        log(f"Saved dataset to: {csv_filename}")

    return df

# ========================================================================
# OUTPUT (Power BI reads this variable)
# ========================================================================

dataset = process_sentiment_data()
