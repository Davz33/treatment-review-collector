# Troubleshooting Guide

## 🚨 Common Issues and Solutions

### Issue: 403 Forbidden Errors During Web Crawling

**Problem:** You see errors like:
```
ERROR:review_crawler:Request failed for https://www.drugs.com/comments/cognitive-behavioral-therapy/: 403 Client Error: Forbidden
```

**Why this happens:**
- Many medical websites block automated requests to prevent scraping
- Anti-bot protection systems detect and block programmatic access
- Rate limiting and IP-based restrictions

**Solutions:**

#### 1. **Install Required Dependencies First**
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install requests beautifulsoup4 lxml click

# Or install system-wide (if allowed)
pip install --break-system-packages requests beautifulsoup4 lxml click
```

#### 2. **Use Alternative Data Sources**
The system is designed with multiple fallback sources:

```bash
# The system automatically tries these sources in order:
# 1. PubMed (academic patient studies) - Most reliable
# 2. Healthline community - More accessible
# 3. ClinicalTrials.gov - Trial context
# 4. Drugs.com - Often blocked but attempted
```

#### 3. **Configure Better Web Scraping**
Add these to your environment:
```bash
export CRAWLER_DELAY=2.0  # Slower requests
export CRAWLER_MAX_RETRIES=5  # More retries
```

#### 4. **Use API Access (Recommended for Production)**

**Reddit API (PRAW):**
```bash
pip install praw
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USER_AGENT="your_app_name"
```

**Google Custom Search API:**
```bash
export GOOGLE_API_KEY="your_api_key"
export GOOGLE_SEARCH_ENGINE_ID="your_engine_id"
```

#### 5. **Try Different Therapy Name Formats**
The system tries multiple URL patterns:
```bash
# These are all attempted automatically:
# - "cognitive-behavioral-therapy"
# - "cognitive_behavioral_therapy" 
# - "cognitivebehavioraltherapy"
```

#### 6. **Use Proxy or VPN**
For persistent blocking:
```python
# Add to config.py
PROXY_CONFIG = {
    'http': 'http://proxy-server:port',
    'https': 'https://proxy-server:port'
}
```

### Issue: No Reviews Found

**Problem:** System returns 0 reviews collected.

**Solutions:**

#### 1. **Check Network Connectivity**
```bash
# Test basic connectivity
curl -I https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
```

#### 2. **Try More Specific Terms**
```bash
# Instead of generic terms, use specific ones:
python main.py collect \
  --therapy-name "CBT" \  # Try abbreviations
  --condition "fibromyalgia" \  # Try specific conditions
  --trial-year 2015
```

#### 3. **Use Academic Sources**
```bash
# Focus on PubMed and clinical sources
python main.py collect \
  --therapy-name "mindfulness based stress reduction" \
  --condition "anxiety" \
  --trial-year 2018 \
  --max-reviews 20
```

### Issue: All Reviews Marked as Unreliable

**Problem:** Reliability threshold too high.

**Solutions:**

#### 1. **Lower the Threshold**
```bash
python main.py collect \
  --threshold 0.4 \  # Lower from default 0.6
  --include-unreliable \  # See all results
  --therapy-name "your-therapy"
```

#### 2. **Check Scoring Components**
```bash
# Test individual review
python main.py test-review "Your review text here" \
  --therapy-name "CBT" \
  --condition "pain"
```

## 🔧 Advanced Configuration

### Custom Source Priority
Edit `config.py`:
```python
# Prioritize accessible sources
PLATFORM_CONFIGS = {
    "pubmed": {"priority": 1, "rate_limit": 3},
    "healthline": {"priority": 2, "rate_limit": 10},
    "drugs.com": {"priority": 3, "rate_limit": 30}  # Often blocked
}
```

### Enhanced Anti-Detection
```python
# In review_crawler.py
ENHANCED_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}
```

## 🎯 Production Recommendations

### 1. **Use Official APIs**
- **Reddit API (PRAW)**: For medical subreddits
- **PubMed E-utilities**: For academic literature
- **ClinicalTrials.gov API**: For trial data

### 2. **Implement Caching**
```python
# Add Redis caching
pip install redis
export USE_REDIS_CACHE=true
export REDIS_HOST=localhost
```

### 3. **Set Up Monitoring**
```python
# Log successful vs failed requests
import logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
```

### 4. **Use Selenium for Dynamic Content**
```bash
pip install selenium
# For sites requiring JavaScript
```

## 📊 Testing Without Web Dependencies

If you want to test the core functionality without web crawling:

```bash
# Test the reliability detection system
python3 test_without_deps.py

# Test individual review analysis
python3 main.py test-review "I tried CBT for 12 weeks for chronic pain. Initially felt more anxious but improved by week 8."
```

## 🆘 Getting Help

### Debug Mode
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python main.py collect --therapy-name "CBT" --condition "pain" --trial-year 2015
```

### Check System Status
```bash
python main.py config-info  # Show current configuration
```

### Report Issues
When reporting issues, include:
1. Full error message
2. Command used
3. Operating system
4. Python version: `python3 --version`
5. Installed packages: `pip list`

## 💡 Alternative Approaches

### 1. **Manual Data Import**
```python
# Import reviews from CSV/JSON files
reviews_data = [
    {"text": "Review text", "date": "2016-01-01", "source": "manual"},
    # ... more reviews
]
```

### 2. **Academic Literature Focus**
```bash
# Focus on peer-reviewed sources only
python main.py search-trials --therapy-name "CBT" --condition "pain"
```

### 3. **Crowdsourced Collection**
- Set up forms for patients to submit reviews
- Verify submissions manually
- Import into the reliability system

The system is designed to be robust and work even when some sources fail. The core reliability detection will work regardless of data source!