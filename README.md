# Treatment Review Collector

An AI-powered system for collecting and analyzing reliable medical treatment reviews that match specific clinical trial criteria.

## 🎯 Problem Statement

When researching medical treatments, especially those from older clinical trials (e.g., from 2015), it's challenging to find genuine, reliable reviews from people who actually underwent similar therapy protocols. This system addresses the Linear issue **DAV-5** by:

1. **Defining reliable reviews**: Reviews from real people who underwent therapy matching clinical trial parameters
2. **Filtering AI-generated content**: Using multiple detection methods to identify fake/AI-generated reviews
3. **Matching clinical criteria**: Ensuring reviews align with specific trial protocols and timelines

## 🔧 Features

### Core Capabilities
- **Multi-source Review Collection**: Crawls medical forums, patient communities, and review sites
- **AI Content Detection**: Identifies AI-generated or suspicious reviews using pattern matching and linguistic analysis
- **Clinical Trial Matching**: Matches reviews against specific trial criteria (therapy type, duration, dosage, side effects)
- **Source Credibility Assessment**: Evaluates review source reliability and user authenticity
- **Temporal Relevance**: Prioritizes reviews from relevant time periods relative to clinical trials

### Technical Features
- **Comprehensive Reliability Scoring**: Multi-factor scoring system (0-1 scale)
- **Configurable Thresholds**: Adjustable reliability criteria
- **Multiple Output Formats**: JSON, CSV, database storage
- **Rate-Limited Crawling**: Respectful web scraping with configurable delays
- **CLI Interface**: Easy-to-use command-line tools

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Davz33/treatment-review-collector.git
cd treatment-review-collector

# Install dependencies
pip install -r requirements.txt

# Optional: Install advanced AI detection models
pip install torch transformers sentence-transformers
```

### Basic Usage

```bash
# Collect reliable reviews for a specific therapy
python main.py collect \
  --therapy-name "Cognitive Behavioral Therapy" \
  --condition "chronic pain" \
  --trial-year 2015 \
  --duration-weeks 12 \
  --max-reviews 100 \
  --threshold 0.6

# Analyze existing reviews from a file
python main.py analyze reviews.json \
  --therapy-name "CBT" \
  --condition "chronic pain" \
  --trial-year 2015

# Test a single review
python main.py test-review "I tried CBT for 12 weeks in 2016 for chronic pain. Initially felt more anxious but by week 8 saw real improvements..."

# Search for related clinical trials
python main.py search-trials --therapy-name "Cognitive Behavioral Therapy" --condition "chronic pain"
```

## 📊 How It Works

### 1. Reliability Detection Framework

The system uses a multi-factor approach to assess review reliability:

```python
# Example: Creating clinical trial criteria
trial_criteria = ClinicalTrialCriteria(
    therapy_name="Cognitive Behavioral Therapy",
    year=2015,
    duration_weeks=12,
    condition_treated="chronic pain",
    side_effects_mentioned=["initial anxiety", "fatigue"]
)

# Initialize detector
detector = ReliableReviewDetector(trial_criteria)

# Analyze a review
is_reliable, score = detector.is_reliable_review(review_text, metadata)
```

### 2. Scoring Components

| Component | Weight | Description |
|-----------|--------|-------------|
| **Authenticity** | 35% | Human vs AI-generated content detection |
| **Clinical Match** | 30% | Alignment with trial parameters |
| **Source Credibility** | 20% | Platform and user reliability |
| **Temporal Relevance** | 15% | Time proximity to clinical trial |

### 3. AI Detection Methods

- **Pattern Matching**: Detects common AI phrases and structures
- **Linguistic Analysis**: Identifies repetitive or overly structured content
- **Medical Disclaimer Detection**: Flags generic medical advice patterns
- **Advanced Models** (optional): Transformer-based AI detection

### 4. Clinical Matching Criteria

- Therapy name and type mention
- Treatment duration alignment
- Dosage and frequency information
- Known side effects from trial data
- Medical terminology usage
- Condition-specific keywords

## 🏗️ Architecture

```
treatment-review-collector/
├── reliable_review_detector.py    # Core reliability detection logic
├── review_crawler.py              # Web crawling and data collection
├── config.py                      # Configuration and settings
├── main.py                        # CLI interface
├── requirements.txt               # Python dependencies
├── data/                          # Collected review data
├── logs/                          # Application logs
└── models/                        # AI detection models (optional)
```

## ⚙️ Configuration

### Environment Variables

```bash
# Crawler settings
export CRAWLER_DELAY=1.0
export CRAWLER_MAX_RETRIES=3
export RELIABILITY_THRESHOLD=0.6

# API keys (optional)
export REDDIT_CLIENT_ID="your_reddit_client_id"
export REDDIT_CLIENT_SECRET="your_reddit_secret"
export GOOGLE_API_KEY="your_google_api_key"
export OPENAI_API_KEY="your_openai_key"

# Advanced features
export ENABLE_ADVANCED_AI_DETECTION=true
export USE_DATABASE=true
export USE_REDIS_CACHE=true
```

### Supported Platforms

- **Drugs.com**: Drug review pages
- **PatientsLikeMe**: Patient community experiences
- **Reddit**: Medical subreddits (r/ChronicPain, r/depression, etc.)
- **WebMD**: Treatment reviews
- **Clinical Forums**: Generic patient forum support
- **ClinicalTrials.gov**: Trial metadata for context

## 📈 Example Results

### Sample Reliable Review (Score: 0.85)
```
"I started CBT for my chronic pain in 2016 after reading about the study. 
The 12-week program was challenging at first - I felt more anxious initially, 
but by week 8 I noticed real improvements. The techniques for pain management 
really helped me cope better. Some fatigue in the beginning but that went away."

✅ Authenticity: 0.9 (Human-like language)
✅ Clinical Match: 0.8 (Mentions duration, timeline, known side effects)
✅ Source Credibility: 0.7 (Verified platform user)
✅ Temporal Relevance: 0.9 (Posted year after 2015 trial)
```

### Sample Unreliable Review (Score: 0.25)
```
"I hope this helps with your decision about CBT therapy. It's important to note 
that everyone's experience may vary with this treatment. From my perspective, 
the cognitive behavioral therapy approach offers several advantages: 
1. Evidence-based treatment methods 2. Structured approach to pain management..."

❌ Authenticity: 0.1 (AI-generated patterns)
❌ Clinical Match: 0.4 (Generic medical information)
❌ Source Credibility: 0.3 (Suspicious account)
❌ Temporal Relevance: 0.1 (Posted too recently)
```

## 🔍 Advanced Features

### Custom AI Detection Models

```python
# Enable advanced transformer-based detection
config.reliability.enable_advanced_ai_detection = True
config.reliability.ai_detection_model = "roberta-base-openai-detector"
```

### Database Integration

```python
# Enable database storage
config.database.use_database = True
config.database.database_url = "postgresql://user:pass@localhost/reviews"
```

### Custom Clinical Criteria

```python
# Define specific trial parameters
trial_criteria = ClinicalTrialCriteria(
    therapy_name="Mindfulness-Based Stress Reduction",
    year=2018,
    duration_weeks=8,
    dosage="45 minutes daily",
    frequency="5 days per week",
    condition_treated="anxiety disorder",
    inclusion_criteria=["adults 18-65", "GAD diagnosis"],
    exclusion_criteria=["severe depression", "substance abuse"],
    side_effects_mentioned=["initial restlessness", "emotional sensitivity"]
)
```

## 🧪 Testing and Validation

### Run the Example
```bash
python reliable_review_detector.py
```

This will test the system with sample human-written and AI-generated reviews, demonstrating the detection capabilities.

### Custom Testing
```bash
python main.py test-review "Your review text here" \
  --therapy-name "Your Therapy" \
  --condition "Your Condition" \
  --trial-year 2015
```

## 📚 Implementation Ideas & Approaches

### 1. Small Language Model Approach (Your Suggestion)
- **Pros**: Can be trained specifically for medical review detection
- **Cons**: Requires training data and computational resources
- **Implementation**: Use models like DistilBERT fine-tuned on medical vs AI text

### 2. Pattern-Based Detection (Current Implementation)
- **Pros**: Fast, interpretable, no model training required
- **Cons**: May miss sophisticated AI-generated content
- **Implementation**: Rule-based system with medical domain knowledge

### 3. Hybrid Approach (Recommended)
- **Pros**: Combines speed of patterns with accuracy of ML models
- **Cons**: More complex to implement and maintain
- **Implementation**: Pattern matching as first filter, ML models for edge cases

### 4. Off-the-shelf Tools Integration
Available tools for AI detection:
- **GPTZero**: General AI content detection
- **Copyleaks**: Plagiarism and AI detection
- **OpenAI Classifier**: GPT-generated text detection
- **Turnitin**: Academic AI detection

## 🚨 Ethical Considerations

- **Privacy**: No personal health information is stored
- **Rate Limiting**: Respectful crawling to avoid overwhelming servers
- **Terms of Service**: Compliance with platform ToS
- **Medical Disclaimer**: This tool is for research purposes only

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Resources

- [ClinicalTrials.gov API](https://clinicaltrials.gov/api/)
- [Reddit API (PRAW)](https://praw.readthedocs.io/)
- [AI Detection Research](https://arxiv.org/abs/2301.07597)
- [Medical Text Analysis](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7153059/)

---

**Note**: This system is designed for research and educational purposes. Always consult healthcare professionals for medical advice.