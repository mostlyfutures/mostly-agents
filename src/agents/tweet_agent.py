"""
🐦 Moon Dev's Tweet Generator
Built with love by Moon Dev 🚀

This agent takes text input and generates tweets based on the content.
"""

# Model override settings
# Set to "0" to use config.py's AI_MODEL setting
# Available models:
# - "deepseek-chat" (DeepSeek's V3 model - fast & efficient)
# - "deepseek-reasoner" (DeepSeek's R1 reasoning model)
# - "0" (Use config.py's AI_MODEL setting)
MODEL_OVERRIDE = "deepseek-chat"  # Set to "0" to disable override
DEEPSEEK_BASE_URL = "https://api.deepseek.com"  # Base URL for DeepSeek API

# Text Processing Settings
MAX_CHUNK_SIZE = 10000  # Maximum characters per chunk
TWEETS_PER_CHUNK = 3   # Number of tweets to generate per chunk
USE_TEXT_FILE = True   # Whether to use og_tweet_text.txt by default
# if the above is true, then the below is the file to use
OG_TWEET_FILE = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/tweets/og_tweet_text.txt"

import os
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import openai
import anthropic
import traceback
import math
from termcolor import colored, cprint
import sys

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# AI Settings - Override config.py if set
from src import config

# Only set these if you want to override config.py settings
AI_MODEL = False  # Set to model name to override config.AI_MODEL
AI_TEMPERATURE = 0  # Set > 0 to override config.AI_TEMPERATURE
AI_MAX_TOKENS = 150  # Set > 0 to override config.AI_MAX_TOKENS

# Tweet Generation Prompt
TWEET_PROMPT = """Here is a chunk of transcript or text. Please generate three tweets for that text.
Use the below manifest to understand how to speak in the tweet.
Don't use emojis or any corny stuff!
Don't number the tweets - just separate them with blank lines.

Text to analyze:
{text}

Manifest:
- casual, conversational tone with technical depth
- lowercase writing style (no capitalization except for acronyms like AI, API, USD)
- use emojis strategically (🚀 🌙 💰 🤖 ⚡ 🎯) but not excessively
- focus on ai agents, trading, crypto, and futurism
- include tech jargon but explain complex concepts simply
- short declarative sentences that pack insights
- emphasize experimental/educational nature of ideas
- always be kind and supportive to the community
- use "we" and "you" to be inclusive
- mention discord community engagement when relevant
- no numbered lists in tweets
- hashtags only when natural (lowercase: #ai #trading #crypto)
- maximum 280 characters per tweet
- separate tweets with blank lines

EACH TWEET MUST BE A COMPLETE TAKE AND BE INTERESTING
"""

# Color settings for terminal output
TWEET_COLORS = [
    {'text': 'white', 'bg': 'on_green'},
    {'text': 'white', 'bg': 'on_blue'},
    {'text': 'white', 'bg': 'on_red'}
]

class TweetAgent:
    """Moon Dev's Tweet Generator 🐦"""
    
    def __init__(self):
        """Initialize the Tweet Agent"""
        # Set AI parameters - use config values unless overridden
        self.ai_model = MODEL_OVERRIDE if MODEL_OVERRIDE != "0" else config.AI_MODEL
        self.ai_temperature = AI_TEMPERATURE if AI_TEMPERATURE > 0 else config.AI_TEMPERATURE
        self.ai_max_tokens = AI_MAX_TOKENS if AI_MAX_TOKENS > 0 else config.AI_MAX_TOKENS
        
        print(f"🤖 Using AI Model: {self.ai_model}")
        if AI_MODEL or AI_TEMPERATURE > 0 or AI_MAX_TOKENS > 0:
            print("⚠️ Note: Using some override settings instead of config.py defaults")
            if AI_MODEL:
                print(f"  - Model: {AI_MODEL}")
            if AI_TEMPERATURE > 0:
                print(f"  - Temperature: {AI_TEMPERATURE}")
            if AI_MAX_TOKENS > 0:
                print(f"  - Max Tokens: {AI_MAX_TOKENS}")
        
        load_dotenv()
        
        # Get API keys
        openai_key = os.getenv("OPENAI_KEY")
        anthropic_key = os.getenv("ANTHROPIC_KEY")
        
        if not openai_key:
            raise ValueError("🚨 OPENAI_KEY not found in environment variables!")
        if not anthropic_key:
            raise ValueError("🚨 ANTHROPIC_KEY not found in environment variables!")
            
        openai.api_key = openai_key
        self.client = anthropic.Anthropic(api_key=anthropic_key)

        # Initialize DeepSeek client if needed
        if "deepseek" in self.ai_model.lower():
            deepseek_key = os.getenv("DEEPSEEK_KEY")
            if deepseek_key:
                self.deepseek_client = openai.OpenAI(
                    api_key=deepseek_key,
                    base_url=DEEPSEEK_BASE_URL
                )
            else:
                self.deepseek_client = None
                print("⚠️ DEEPSEEK_KEY not found - DeepSeek model will not be available")
        else:
            self.deepseek_client = None
        
        # Initialize Twitter API client (optional - only if credentials are provided)
        self.twitter_client = None
        try:
            twitter_api_key = os.getenv("TWITTER_API_KEY") or config.TWITTER_API_KEY
            twitter_api_secret = os.getenv("TWITTER_API_SECRET") or config.TWITTER_API_SECRET
            twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN") or config.TWITTER_ACCESS_TOKEN
            twitter_access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET") or config.TWITTER_ACCESS_TOKEN_SECRET
            
            if twitter_api_key and twitter_api_secret and twitter_access_token and twitter_access_token_secret:
                import tweepy
                # Twitter API v2 authentication
                self.twitter_client = tweepy.Client(
                    consumer_key=twitter_api_key,
                    consumer_secret=twitter_api_secret,
                    access_token=twitter_access_token,
                    access_token_secret=twitter_access_token_secret
                )
                print("✅ Twitter API client initialized successfully")
            else:
                print("ℹ️ Twitter API credentials not found - tweets will only be saved to file")
        except ImportError:
            print("⚠️ tweepy not installed - run: pip install tweepy")
            self.twitter_client = None
        except Exception as e:
            print(f"⚠️ Error initializing Twitter client: {str(e)}")
            self.twitter_client = None
        
        # Create tweets directory if it doesn't exist
        self.tweets_dir = Path("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/tweets")
        self.tweets_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = self.tweets_dir / f"generated_tweets_{timestamp}.txt"
        
    def _chunk_text(self, text):
        """Split text into chunks of MAX_CHUNK_SIZE characters"""
        return [text[i:i + MAX_CHUNK_SIZE] 
                for i in range(0, len(text), MAX_CHUNK_SIZE)]
    
    def _get_input_text(self, text=None):
        """Get input text from either file or direct input"""
        if USE_TEXT_FILE:
            try:
                with open(OG_TWEET_FILE, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"❌ Error reading text file: {str(e)}")
                print("⚠️ Falling back to direct text input if provided")
                
        return text
    
    def _print_colored_tweet(self, tweet, color_idx):
        """Print tweet with color based on its position"""
        color_settings = TWEET_COLORS[color_idx % len(TWEET_COLORS)]
        cprint(tweet, color_settings['text'], color_settings['bg'])
        print()  # Add spacing between tweets
    
    def generate_tweets(self, text=None):
        """Generate tweets from text input or file"""
        try:
            # Get input text
            input_text = self._get_input_text(text)
            
            if not input_text:
                print("❌ No input text provided and couldn't read from file")
                return None
            
            # Calculate and display text stats
            total_chars = len(input_text)
            total_chunks = math.ceil(total_chars / MAX_CHUNK_SIZE)
            total_tweets = total_chunks * TWEETS_PER_CHUNK
            
            print(f"\n📊 Text Analysis:")
            print(f"Total characters: {total_chars:,}")
            print(f"Chunk size: {MAX_CHUNK_SIZE:,}")
            print(f"Number of chunks: {total_chunks:,}")
            print(f"Tweets per chunk: {TWEETS_PER_CHUNK}")
            print(f"Total tweets to generate: {total_tweets:,}")
            print("=" * 50)
            
            # Split text into chunks if needed
            chunks = self._chunk_text(input_text)
            all_tweets = []
            
            for i, chunk in enumerate(chunks, 1):
                print(f"\n🔄 Processing chunk {i}/{total_chunks} ({len(chunk):,} characters)")
                
                # Prepare the context
                context = TWEET_PROMPT.format(text=chunk)
                
                # Use either DeepSeek or Claude based on model setting
                if "deepseek" in self.ai_model.lower():
                    if not self.deepseek_client:
                        raise ValueError("🚨 DeepSeek client not initialized - check DEEPSEEK_KEY")
                        
                    # Make DeepSeek API call
                    response = self.deepseek_client.chat.completions.create(
                        model=self.ai_model,
                        messages=[
                            {"role": "system", "content": TWEET_PROMPT},
                            {"role": "user", "content": context}
                        ],
                        max_tokens=self.ai_max_tokens,
                        temperature=self.ai_temperature,
                        stream=False
                    )
                    response_text = response.choices[0].message.content.strip()
                else:
                    # Get tweets using Claude
                    message = self.client.messages.create(
                        model=self.ai_model,
                        max_tokens=self.ai_max_tokens,
                        temperature=self.ai_temperature,
                        messages=[{
                            "role": "user",
                            "content": context
                        }]
                    )
                    # Handle both string and list responses
                    if isinstance(message.content, list):
                        response_text = message.content[0].text if message.content else ""
                    else:
                        response_text = message.content
                
                # Parse tweets from response and remove any numbering
                chunk_tweets = []
                for line in response_text.split('\n'):
                    line = line.strip()
                    if line:
                        # Remove any leading numbers (1., 2., etc.)
                        cleaned_line = line.lstrip('0123456789. ')
                        if cleaned_line:
                            chunk_tweets.append(cleaned_line)
                
                # Print tweets with colors to terminal
                print("\n🐦 Generated tweets for this chunk:")
                for idx, tweet in enumerate(chunk_tweets):
                    self._print_colored_tweet(tweet, idx)
                
                all_tweets.extend(chunk_tweets)
                
                # Write tweets to file with paragraph spacing (clean format)
                with open(self.output_file, 'a') as f:
                    for tweet in chunk_tweets:
                        f.write(f"{tweet}\n\n")  # Double newline for paragraph spacing
                
                # Small delay between chunks to avoid rate limits
                if i < total_chunks:
                    time.sleep(1)
            
            return all_tweets
            
        except Exception as e:
            print(f"❌ Error generating tweets: {str(e)}")
            traceback.print_exc()
            return None
    
    def post_tweet(self, tweet_text):
        """
        Post a tweet to Twitter using the API
        
        Args:
            tweet_text (str): The text content to tweet (max 280 characters)
            
        Returns:
            bool: True if posted successfully, False otherwise
        """
        if not self.twitter_client:
            print("⚠️ Twitter client not initialized - skipping posting")
            return False
        
        try:
            # Validate tweet length
            if len(tweet_text) > 280:
                print(f"⚠️ Tweet too long ({len(tweet_text)} chars), truncating to 280...")
                tweet_text = tweet_text[:277] + "..."
            
            # Post the tweet
            response = self.twitter_client.create_tweet(text=tweet_text)
            
            if response and response.data:
                tweet_id = response.data.get('id', 'unknown')
                print(f"✅ Tweet posted successfully! ID: {tweet_id}")
                return True
            else:
                print("⚠️ Tweet posted but no response data received")
                return False
                
        except Exception as e:
            print(f"❌ Error posting tweet: {str(e)}")
            # Don't crash the agent, just log the error and continue
            return False

if __name__ == "__main__":
    try:
        agent = TweetAgent()
        
        # Example usage with direct text
        test_text = """Bitcoin showing strong momentum with increasing volume. 
        Price action suggests accumulation phase might be complete. 
        Key resistance at $69,000 with support holding at $65,000."""
        
        print(f"\n🌙 Moon Dev's Tweet Agent starting (interval: {config.TWEET_INTERVAL_SECONDS}s)...")
        
        while True:
            try:
                print(f"\n{'='*60}")
                print(f"🔄 Starting new tweet generation cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}")
                
                # If USE_TEXT_FILE is True, it will use the file instead of test_text
                tweets = agent.generate_tweets(test_text)
                
                if tweets:
                    print(f"\n✅ Generated {len(tweets)} tweets successfully")
                    print(f"📁 Tweets saved to: {agent.output_file}")
                    
                    # Post tweets to Twitter if client is initialized
                    if agent.twitter_client:
                        print(f"\n🐦 Posting {len(tweets)} tweets to Twitter...")
                        posted_count = 0
                        
                        for idx, tweet in enumerate(tweets, 1):
                            print(f"\n📤 Posting tweet {idx}/{len(tweets)}:")
                            print(f"   {tweet[:100]}{'...' if len(tweet) > 100 else ''}")
                            
                            success = agent.post_tweet(tweet)
                            if success:
                                posted_count += 1
                            
                            # Delay between posts to avoid rate limits
                            if idx < len(tweets):
                                time.sleep(config.TWEET_POST_DELAY_SECONDS)
                        
                        print(f"\n✅ Posted {posted_count}/{len(tweets)} tweets successfully")
                    else:
                        print("\nℹ️ Twitter posting disabled (no API credentials)")
                
                # Calculate next run time
                next_run = datetime.now() + pd.Timedelta(seconds=config.TWEET_INTERVAL_SECONDS)
                print(f"\n😴 Generation complete. Sleeping for {config.TWEET_INTERVAL_SECONDS} seconds...")
                print(f"⏰ Next run at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}\n")
                
                time.sleep(config.TWEET_INTERVAL_SECONDS)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"\n❌ Error in tweet generation cycle: {str(e)}")
                traceback.print_exc()
                print(f"\n⏳ Waiting 60 seconds before retrying...")
                time.sleep(60)  # Wait before retrying on error
                
    except KeyboardInterrupt:
        print("\n\n👋 Moon Dev's Tweet Agent shutting down gracefully...")
        print("🌙 Thanks for using the Tweet Agent! 🚀")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
