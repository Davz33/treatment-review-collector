"""
Configuration settings for Treatment Review Collector
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CrawlerConfig:
    """Configuration for web crawler"""
    delay_between_requests: float = 1.0
    max_retries: int = 3
    timeout: int = 10
    user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    # Rate limiting
    requests_per_minute: int = 30
    requests_per_hour: int = 1000
    
    # Source-specific settings
    enable_drugs_com: bool = True
    enable_reddit: bool = True
    enable_patient_forums: bool = True
    enable_clinical_trials: bool = True

@dataclass
class ReliabilityConfig:
    """Configuration for reliability detection"""
    # Scoring thresholds
    reliability_threshold: float = 0.6
    authenticity_threshold: float = 0.3
    clinical_match_threshold: float = 0.1
    
    # Scoring weights
    authenticity_weight: float = 0.35
    clinical_match_weight: float = 0.30
    source_credibility_weight: float = 0.20
    temporal_relevance_weight: float = 0.15
    
    # AI detection settings
    enable_advanced_ai_detection: bool = False  # Requires transformer models
    ai_detection_model: str = "roberta-base-openai-detector"
    
    # Text analysis
    min_review_length: int = 20
    max_review_length: int = 2000
    language_detection: bool = True

@dataclass
class DatabaseConfig:
    """Database configuration"""
    use_database: bool = False
    database_url: str = "sqlite:///reviews.db"
    
    # Redis cache (optional)
    use_redis_cache: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    cache_ttl: int = 3600  # 1 hour

@dataclass
class APIConfig:
    """API keys and endpoints"""
    # Reddit API (optional)
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: Optional[str] = None
    
    # Google Custom Search API (optional)
    google_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    
    # OpenAI API (for advanced AI detection)
    openai_api_key: Optional[str] = None
    
    # Hugging Face (for transformer models)
    huggingface_api_key: Optional[str] = None

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.crawler = CrawlerConfig()
        self.reliability = ReliabilityConfig()
        self.database = DatabaseConfig()
        self.api = APIConfig()
        
        # Load from environment variables
        self._load_from_env()
        
        # Paths
        self.project_root = Path(__file__).parent
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        self.models_dir = self.project_root / "models"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Crawler config
        self.crawler.delay_between_requests = float(os.getenv("CRAWLER_DELAY", "1.0"))
        self.crawler.max_retries = int(os.getenv("CRAWLER_MAX_RETRIES", "3"))
        self.crawler.timeout = int(os.getenv("CRAWLER_TIMEOUT", "10"))
        
        # Reliability config
        self.reliability.reliability_threshold = float(os.getenv("RELIABILITY_THRESHOLD", "0.6"))
        self.reliability.enable_advanced_ai_detection = os.getenv("ENABLE_ADVANCED_AI_DETECTION", "false").lower() == "true"
        
        # Database config
        self.database.use_database = os.getenv("USE_DATABASE", "false").lower() == "true"
        self.database.database_url = os.getenv("DATABASE_URL", "sqlite:///reviews.db")
        self.database.use_redis_cache = os.getenv("USE_REDIS_CACHE", "false").lower() == "true"
        self.database.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.database.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        
        # API config
        self.api.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.api.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.api.reddit_user_agent = os.getenv("REDDIT_USER_AGENT")
        self.api.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.api.google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.api.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.api.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")

# Global configuration instance
config = Config()

# Predefined platform configurations
PLATFORM_CONFIGS = {
    "drugs.com": {
        "base_url": "https://www.drugs.com",
        "review_endpoint": "/comments/{drug_name}/",
        "selectors": {
            "review_container": ".review",
            "review_text": ".review-content",
            "date": ".review-date",
            "user": ".review-author",
            "rating": ".rating-score"
        },
        "rate_limit": 30,  # requests per minute
        "requires_js": False
    },
    
    "patientslikeme.com": {
        "base_url": "https://www.patientslikeme.com",
        "review_endpoint": "/treatments/{treatment_name}/reviews",
        "selectors": {
            "review_container": ".experience-item",
            "review_text": ".experience-text",
            "date": ".experience-date",
            "user": ".experience-author"
        },
        "rate_limit": 20,
        "requires_js": True  # May require JavaScript rendering
    },
    
    "reddit.com": {
        "base_url": "https://www.reddit.com",
        "api_endpoint": "https://www.reddit.com/r/{subreddit}/search.json",
        "selectors": {
            "review_container": "[data-testid='comment']",
            "review_text": ".RichTextJSON-root",
            "date": "time",
            "user": "[data-testid='comment_author_link']"
        },
        "rate_limit": 60,  # Reddit API limit
        "requires_api": True
    },
    
    "webmd.com": {
        "base_url": "https://www.webmd.com",
        "review_endpoint": "/drugs/drugreview-{drug_id}",
        "selectors": {
            "review_container": ".review-item",
            "review_text": ".review-description",
            "date": ".review-date",
            "user": ".review-author"
        },
        "rate_limit": 25,
        "requires_js": False
    }
}

# Medical terminology and keywords for different conditions
MEDICAL_KEYWORDS = {
    "chronic_pain": [
        "chronic pain", "pain management", "fibromyalgia", "arthritis",
        "back pain", "joint pain", "neuropathic pain", "migraine"
    ],
    
    "depression": [
        "depression", "major depressive disorder", "MDD", "antidepressant",
        "mood disorder", "mental health", "anxiety", "bipolar"
    ],
    
    "diabetes": [
        "diabetes", "type 1 diabetes", "type 2 diabetes", "blood sugar",
        "glucose", "insulin", "diabetic", "A1C", "hemoglobin"
    ],
    
    "hypertension": [
        "high blood pressure", "hypertension", "blood pressure",
        "systolic", "diastolic", "ACE inhibitor", "beta blocker"
    ]
}

# Trusted medical sources for credibility scoring
TRUSTED_MEDICAL_SOURCES = [
    "mayoclinic.org",
    "webmd.com", 
    "drugs.com",
    "patientslikeme.com",
    "healthgrades.com",
    "medscape.com",
    "nih.gov",
    "ncbi.nlm.nih.gov",
    "clinicaltrials.gov",
    "fda.gov",
    "who.int"
]

# Suspicious patterns that might indicate fake reviews
SUSPICIOUS_PATTERNS = {
    "generic_medical_advice": [
        "consult your doctor",
        "speak with your healthcare provider", 
        "this is not medical advice",
        "individual results may vary",
        "always follow your doctor's instructions"
    ],
    
    "ai_generated_phrases": [
        "i hope this helps",
        "it's important to note",
        "from my perspective",
        "that being said",
        "on the other hand",
        "in conclusion",
        "to summarize"
    ],
    
    "overly_promotional": [
        "amazing results",
        "miracle cure", 
        "life-changing",
        "incredible improvement",
        "highly recommend to everyone",
        "best treatment ever"
    ]
}