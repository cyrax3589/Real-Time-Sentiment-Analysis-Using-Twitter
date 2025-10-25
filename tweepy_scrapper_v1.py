# Real-Time Twitter Sentiment Analysis for Power BI using Tweepy

import pandas as pd
from datetime import datetime, timedelta
import re
from textblob import TextBlob
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
ACCESS_TOKEN_SECRET = "YOUR_ACCESS_TOKEN_SECRET"
BEARER_TOKEN = "YOUR_BEARER_TOKEN"  # For API v2

# Brand/Product to track
BRAND_NAME = "BRAND_NAME"  # Change this to any brand you want to track
SEARCH_QUERY = f"{BRAND_NAME} -is:retweet lang:en"  # Exclude retweets, English only

# Scraping parameters
MAX_TWEETS = 100  # Number of tweets to fetch per refresh (Must be between 10 and 100 for free API)
DAYS_BACK = 7  # How many days of historical tweets to fetch (Must be <= 7 for free API)

# Use API v2 (recommended) or v1.1
USE_API_V2 = True  # Set to False if using old API v1.1

# ============================================================================
# SENTIMENT ANALYSIS FUNCTIONS
# ============================================================================

def clean_tweet(tweet):
    """Clean tweet text for better sentiment analysis"""
    # Remove URLs
    tweet = re.sub(r'http\S+|www.\S+', '', tweet)
    # Remove mentions
    tweet = re.sub(r'@\w+', '', tweet)
    # Remove hashtags symbol but keep text
    tweet = re.sub(r'#(\w+)', r'\1', tweet)
    # Remove extra whitespace
    tweet = re.sub(r'\s+', ' ', tweet).strip()
    return tweet

def get_sentiment_score(text):
    """Calculate sentiment polarity using TextBlob"""
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except:
        return 0.0

def get_sentiment_subjectivity(text):
    """Calculate sentiment subjectivity using TextBlob"""
    try:
        blob = TextBlob(text)
        return blob.sentiment.subjectivity
    except:
        return 0.0

def categorize_sentiment(score):
    """Categorize sentiment into Positive, Negative, or Neutral"""
    if score > 0.1:
        return "Positive"
    elif score < -0.1:
        return "Negative"
    else:
        return "Neutral"

# ============================================================================
# TWITTER DATA FETCHING WITH TWEEPY
# ============================================================================

def fetch_tweets_with_tweepy():
    """
    Fetch tweets using Tweepy (Twitter API)
    This function runs directly in Power BI!
    """
    
    try:
        import tweepy
    except ImportError:
        print("ERROR: tweepy not installed!")
        print("Install with: pip install tweepy")
        return pd.DataFrame()
    
    # Check if API credentials are set
    if API_KEY == "your_api_key_here" or not API_KEY:
        print("\n" + "="*70)
        print("⚠️  TWITTER API CREDENTIALS NOT SET!")
        print("="*70)
        print("\nPlease add your Twitter API credentials at the top of this script.")
        print("See the setup guide for how to get these keys.")
        print("\nRequired credentials:")
        print("  - API_KEY")
        print("  - API_SECRET")
        print("  - ACCESS_TOKEN")
        print("  - ACCESS_TOKEN_SECRET")
        if USE_API_V2:
            print("  - BEARER_TOKEN (for API v2)")
        print("="*70 + "\n")
        return pd.DataFrame()
    
    tweets_data = []
    
    try:
        print(f"Connecting to Twitter API...")
        print(f"Searching for: {SEARCH_QUERY}")
        print(f"Max tweets: {MAX_TWEETS}")
        
        if USE_API_V2:
            # ===== TWITTER API V2 (RECOMMENDED) =====
            print("Using Twitter API v2...")
            
            client = tweepy.Client(
                bearer_token=BEARER_TOKEN,
                consumer_key=API_KEY,
                consumer_secret=API_SECRET,
                access_token=ACCESS_TOKEN,
                access_token_secret=ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True
            )
            
            # Calculate start_time (tweets from last X days)
            start_time = datetime.utcnow() - timedelta(days=DAYS_BACK)
            start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Search recent tweets
            response = client.search_recent_tweets(
                query=SEARCH_QUERY,
                max_results=min(MAX_TWEETS, 100),  # API limit is 100 per request
                tweet_fields=['created_at', 'public_metrics', 'lang', 'author_id'],
                user_fields=['username', 'name', 'verified', 'public_metrics'],
                expansions=['author_id'],
                start_time=start_time_str
            )
            
            if response.data:
                # Create user lookup dictionary
                users = {user.id: user for user in response.includes['users']}
                
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
                
                print(f"✓ Successfully fetched {len(tweets_data)} tweets using API v2")
            else:
                print("No tweets found matching the search criteria")
        
        else:
            # ===== TWITTER API V1.1 (LEGACY) =====
            print("Using Twitter API v1.1...")
            
            auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
            auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
            api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Search tweets
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
                    'reply_count': 0,  # Not available in v1.1
                    'like_count': tweet.favorite_count,
                    'quote_count': 0,  # Not available in v1.1
                    'user_followers': tweet.user.followers_count,
                    'user_verified': tweet.user.verified,
                    'language': tweet.lang
                })
            
            print(f"✓ Successfully fetched {len(tweets_data)} tweets using API v1.1")
        
        return pd.DataFrame(tweets_data)
        
    except tweepy.TweepyException as e:
        print(f"Twitter API Error: {e}")
        if "429" in str(e):
            print("⚠️  Rate limit exceeded. Please wait 15 minutes and try again.")
        elif "401" in str(e):
            print("⚠️  Authentication failed. Check your API credentials.")
        elif "403" in str(e):
            print("⚠️  Access forbidden. Make sure your app has read permissions.")
        return pd.DataFrame()
    
    except Exception as e:
        print(f"Error fetching tweets: {e}")
        return pd.DataFrame()

# ============================================================================
# MAIN PROCESSING PIPELINE
# ============================================================================

def process_sentiment_data():
    """Main function to fetch, clean, and analyze tweets"""
    
    print("\n" + "="*70)
    print("TWITTER SENTIMENT ANALYSIS - POWER BI")
    print("="*70)
    print(f"Brand: {BRAND_NAME}")
    print(f"Query: {SEARCH_QUERY}")
    print("="*70 + "\n")
    
    # Fetch tweets
    df = fetch_tweets_with_tweepy()
    
    if df.empty:
        print("\n⚠️  No tweets fetched. Returning empty dataset.")
        print("Check your API credentials and search query.")
        # Return empty dataframe with expected schema
        return pd.DataFrame(columns=[
            'tweet_id', 'created_at', 'date', 'hour', 'day_of_week',
            'brand', 'username', 'user_display_name', 'text', 'cleaned_text',
            'sentiment_score', 'sentiment_subjectivity', 'sentiment_category',
            'retweet_count', 'reply_count', 'like_count', 'quote_count',
            'engagement', 'user_followers', 'user_verified', 'language'
        ])
    
    print(f"\nProcessing {len(df)} tweets...")
    
    # Clean tweet text
    df['cleaned_text'] = df['text'].apply(clean_tweet)
    
    # Calculate sentiment scores
    df['sentiment_score'] = df['cleaned_text'].apply(get_sentiment_score)
    df['sentiment_subjectivity'] = df['cleaned_text'].apply(get_sentiment_subjectivity)
    df['sentiment_category'] = df['sentiment_score'].apply(categorize_sentiment)
    
    # Add brand column
    df['brand'] = BRAND_NAME
    
    # Calculate engagement metric
    df['engagement'] = (df['like_count'] + 
                       df['retweet_count'] + 
                       df['reply_count'] + 
                       df['quote_count'])
    
    # Add time-based features
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['date'] = df['created_at'].dt.date
    df['hour'] = df['created_at'].dt.hour
    df['day_of_week'] = df['created_at'].dt.day_name()
    
    # Select and order columns for Power BI
    output_columns = [
        'tweet_id', 'created_at', 'date', 'hour', 'day_of_week',
        'brand', 'username', 'user_display_name', 'text', 'cleaned_text',
        'sentiment_score', 'sentiment_subjectivity', 'sentiment_category',
        'retweet_count', 'reply_count', 'like_count', 'quote_count',
        'engagement', 'user_followers', 'user_verified', 'language'
    ]
    
    df = df[output_columns]
    
    # Print summary
    print("\n" + "="*70)
    print("SENTIMENT ANALYSIS SUMMARY")
    print("="*70)
    print(f"Total tweets analyzed: {len(df)}")
    print(f"\nSentiment Distribution:")
    sentiment_counts = df['sentiment_category'].value_counts()
    for category, count in sentiment_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {category:8s}: {count:3d} ({percentage:.1f}%)")
    
    print(f"\nAverage sentiment score: {df['sentiment_score'].mean():.3f}")
    print(f"Average engagement: {df['engagement'].mean():.1f}")
    print(f"Total engagement: {df['engagement'].sum():,}")
    print("="*70 + "\n")
    
    return df

# ============================================================================
# POWER BI EXECUTION
# ============================================================================


try:
    dataset = process_sentiment_data()
    print(f"✓ Dataset ready for Power BI with {len(dataset)} rows")
    # Save CSV log 
    csv_filename = f"twitter_sentiment_{BRAND_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    dataset.to_csv(csv_filename, index=False)
    print(f"✓ Saved dataset to CSV file: {csv_filename}")
except Exception as e:
    print(f"✗ Error in main execution: {e}")
    import traceback
    traceback.print_exc()
    # Return empty dataframe with expected schema on error
    dataset = pd.DataFrame(columns=[
        'tweet_id', 'created_at', 'date', 'hour', 'day_of_week',
        'brand', 'username', 'user_display_name', 'text', 'cleaned_text',
        'sentiment_score', 'sentiment_subjectivity', 'sentiment_category',
        'retweet_count', 'reply_count', 'like_count', 'quote_count',
        'engagement', 'user_followers', 'user_verified', 'language'
    ])
