# Tweet Agent 🐦

An autonomous AI agent that continuously generates and posts tweets in a customized personality-driven style.

## What It Does
- 🤖 Generates tweets using AI (DeepSeek, Claude, or GPT)
- 🔄 Runs continuously with configurable intervals
- 🐦 Auto-posts to Twitter via API v2 (optional)
- 💾 Saves all generated tweets to file
- 🎯 Uses customizable personality manifest
- ⚡ Handles errors gracefully and continues running

## Features

### Personality-Driven Writing
The agent uses a detailed personality manifest to ensure consistent voice:
- Casual, lowercase style (Moon Dev's voice)
- Strategic emoji use (🚀 🌙 💰 🤖 ⚡ 🎯)
- Tech jargon with simple explanations
- Community-focused language
- Focus on AI agents, trading, crypto, futurism

### Autonomous Operation
- Runs in continuous loop (default: 15 minutes per cycle)
- Automatic tweet generation and posting
- Keyboard interrupt support (Ctrl+C for graceful shutdown)
- Error recovery without crashing

### Safe Mode
Works without Twitter API credentials - just saves tweets to file for review before manual posting.

## Quick Start

### 1. Basic Usage (No Twitter API - Safe Mode)
```bash
python src/agents/tweet_agent.py
```

This will:
- Generate tweets every 15 minutes
- Save to `src/data/tweets/generated_tweets_TIMESTAMP.txt`
- NOT post to Twitter (requires API credentials)

### 2. With Twitter Auto-Posting

**Step 1: Get Twitter API Credentials**
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create a new app (or use existing)
3. Generate API keys and access tokens
4. Make sure you have "Read and Write" permissions

**Step 2: Add Credentials to `.env`**
```bash
# Twitter API v2 credentials
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

**Step 3: Run the Agent**
```bash
python src/agents/tweet_agent.py
```

The agent will now automatically post generated tweets to your Twitter account!

## Configuration

All settings are in `src/config.py`:

```python
# Tweet Agent Settings
TWEET_INTERVAL_SECONDS = 900  # 15 minutes between cycles
TWEET_POST_DELAY_SECONDS = 10  # Delay between posting individual tweets

# Twitter API Credentials (or use .env)
TWITTER_API_KEY = ""
TWITTER_API_SECRET = ""
TWITTER_ACCESS_TOKEN = ""
TWITTER_ACCESS_TOKEN_SECRET = ""
```

### Customizing the Interval

To change how often tweets are generated, edit `src/config.py`:

```python
TWEET_INTERVAL_SECONDS = 1800  # 30 minutes
# TWEET_INTERVAL_SECONDS = 3600  # 1 hour
# TWEET_INTERVAL_SECONDS = 14400  # 4 hours
```

## Customizing the Personality

The personality manifest is in `src/agents/tweet_agent.py` (lines 49-68):

```python
TWEET_PROMPT = """...

Manifest:
- casual, conversational tone with technical depth
- lowercase writing style (no capitalization except for acronyms)
- use emojis strategically (🚀 🌙 💰 🤖 ⚡ 🎯)
- focus on ai agents, trading, crypto, and futurism
...
```

Edit this manifest to change the agent's writing style!

## Advanced Usage

### Custom Text Input

By default, the agent uses example text. To provide your own content:

**Option 1: Direct text (edit the script)**
```python
test_text = """Your custom content here"""
```

**Option 2: Text file**
1. Set `USE_TEXT_FILE = True` in `tweet_agent.py`
2. Create file: `src/data/tweets/og_tweet_text.txt`
3. Add your source content to that file

The agent will chunk long text and generate tweets from each chunk.

### Tweet Generation Settings

In `src/agents/tweet_agent.py`:

```python
MAX_CHUNK_SIZE = 10000  # Maximum characters per chunk
TWEETS_PER_CHUNK = 3   # Number of tweets to generate per chunk
```

### AI Model Selection

```python
# In tweet_agent.py (line 14)
MODEL_OVERRIDE = "deepseek-chat"  # or "0" to use config.AI_MODEL
```

Available models:
- `"deepseek-chat"` - Fast & efficient (default)
- `"deepseek-reasoner"` - DeepSeek's reasoning model
- `"claude-3-haiku-20240307"` - Fast Claude
- `"claude-3-sonnet-20240229"` - Balanced Claude
- `"0"` - Use `config.AI_MODEL` setting

## Output

### File Output
All tweets are saved to timestamped files:
```
src/data/tweets/generated_tweets_20250115_143022.txt
```

Format:
```
first tweet content here

second tweet content here

third tweet content here
```

### Console Output
The agent provides detailed logging:
```
🔄 Starting new tweet generation cycle at 2025-01-15 14:30:22
📊 Text Analysis:
Total characters: 256
...
✅ Generated 3 tweets successfully
📤 Posting tweet 1/3:
✅ Tweet posted successfully! ID: 1234567890
😴 Next run at: 2025-01-15 14:45:22
```

## Safety Features

### Tweet Validation
- ✅ Automatic length validation (280 char limit)
- ✅ Truncation with ellipsis if too long
- ✅ Character count displayed before posting

### Error Handling
- ✅ API errors don't crash the agent
- ✅ Rate limit protection via delays
- ✅ Network failures logged and retried
- ✅ Graceful shutdown on Ctrl+C

### Rate Limit Protection
- Default 10-second delay between posts
- Configurable via `TWEET_POST_DELAY_SECONDS`
- Respects Twitter's API rate limits

## Troubleshooting

### "Twitter API credentials not found"
- Add credentials to `.env` file
- Agent will run in safe mode (file-only output)

### "tweepy not installed"
- Run: `pip install tweepy`
- Or: `pip install -r requirements.txt`

### "DeepSeek client not initialized"
- Add `DEEPSEEK_KEY` to `.env`
- Or set `MODEL_OVERRIDE = "0"` and use Claude/GPT

### Tweets not posting
1. Check Twitter API credentials are correct
2. Verify app has "Read and Write" permissions
3. Check console for error messages
4. Ensure tweets are under 280 characters

## Best Practices

1. **Start in Safe Mode**: Run without Twitter API first to review generated tweets
2. **Test with Short Intervals**: Use `TWEET_INTERVAL_SECONDS = 60` for testing
3. **Monitor the Output**: Watch the first few cycles to ensure quality
4. **Customize the Personality**: Edit the manifest to match your voice
5. **Use Good Source Content**: Better input = better tweets

## Example Workflow

```bash
# 1. Test tweet generation (no posting)
python src/agents/tweet_agent.py
# Review output in src/data/tweets/

# 2. Add Twitter credentials to .env
# 3. Test with short interval
# Edit config.py: TWEET_INTERVAL_SECONDS = 120

# 4. Run with auto-posting
python src/agents/tweet_agent.py

# 5. Monitor first few cycles
# 6. Increase interval for production
# Edit config.py: TWEET_INTERVAL_SECONDS = 3600

# 7. Run long-term
nohup python src/agents/tweet_agent.py &
```

## Integration with Other Agents

The tweet agent can work with other agents in the ecosystem:

- **Chat Agent**: Generate tweets from stream insights
- **Research Agent**: Tweet about new trading strategies
- **Sentiment Agent**: Tweet market sentiment analysis
- **RBI Agent**: Share backtest results

## Disclaimer

⚠️ **Use Responsibly**
- Review generated content before auto-posting
- Ensure compliance with Twitter's Terms of Service
- Don't spam or post misleading information
- This is an experimental tool for educational purposes

---

*Built with love by Moon Dev 🌙 - Part of the Moon Dev AI Agents ecosystem*