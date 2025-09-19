"""
Review Crawler for Medical Treatment Reviews

This module implements web crawling and API integration capabilities
to collect medical treatment reviews from various sources.
"""

import requests
import time
import json
import logging
from typing import Dict, List, Optional, Generator, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import re
import hashlib
from reliable_review_detector import ReviewMetadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReviewData:
    """Raw review data collected from sources"""
    text: str
    metadata: ReviewMetadata
    raw_data: Dict[str, Any]  # Store original data for debugging
    

class ReviewCrawler:
    """
    Web crawler for collecting medical treatment reviews from various sources.
    
    Supports:
    - Patient forums and communities
    - Medical review websites
    - Reddit medical communities
    - Clinical trial databases
    """
    
    def __init__(self, delay_between_requests: float = 1.0):
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Common selectors for different platforms
        self.platform_selectors = {
            'drugs.com': {
                'review_container': '.review',
                'review_text': '.review-content',
                'date': '.review-date',
                'user': '.review-author',
                'rating': '.rating'
            },
            'patientslikeme.com': {
                'review_container': '.experience-item',
                'review_text': '.experience-text',
                'date': '.experience-date',
                'user': '.experience-author'
            },
            'reddit.com': {
                'review_container': '.Comment',
                'review_text': '[data-testid="comment"]',
                'date': 'time',
                'user': '.author'
            },
            'webmd.com': {
                'review_container': '.review-item',
                'review_text': '.review-description',
                'date': '.review-date',
                'user': '.review-author'
            }
        }
    
    def _make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with rate limiting and error handling"""
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _extract_date(self, date_str: str) -> Optional[datetime]:
        """Extract datetime from various date string formats"""
        if not date_str:
            return None
            
        # Common date patterns
        patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',  # Month DD, YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if pattern == patterns[0]:  # MM/DD/YYYY
                        month, day, year = map(int, match.groups())
                        return datetime(year, month, day)
                    elif pattern == patterns[1]:  # YYYY-MM-DD
                        year, month, day = map(int, match.groups())
                        return datetime(year, month, day)
                    elif pattern == patterns[2]:  # DD-MM-YYYY
                        day, month, year = map(int, match.groups())
                        return datetime(year, month, day)
                    elif pattern == patterns[3]:  # Month DD, YYYY
                        month_str, day, year = match.groups()
                        month_map = {
                            'january': 1, 'february': 2, 'march': 3, 'april': 4,
                            'may': 5, 'june': 6, 'july': 7, 'august': 8,
                            'september': 9, 'october': 10, 'november': 11, 'december': 12
                        }
                        month = month_map.get(month_str.lower(), 1)
                        return datetime(int(year), month, int(day))
                except ValueError:
                    continue
        
        # Fallback: try to extract just year
        year_match = re.search(r'\b(20\d{2})\b', date_str)
        if year_match:
            return datetime(int(year_match.group(1)), 1, 1)
        
        return None
    
    def _identify_platform(self, url: str) -> str:
        """Identify platform from URL"""
        domain = urlparse(url).netloc.lower()
        for platform in self.platform_selectors.keys():
            if platform in domain:
                return platform
        return "unknown"
    
    def crawl_drugs_com(self, drug_name: str, max_pages: int = 5) -> Generator[ReviewData, None, None]:
        """Crawl reviews from Drugs.com"""
        base_url = f"https://www.drugs.com/comments/{drug_name.replace(' ', '-').lower()}/"
        
        for page in range(1, max_pages + 1):
            url = f"{base_url}?page={page}" if page > 1 else base_url
            response = self._make_request(url)
            
            if not response:
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            reviews = soup.find_all('div', class_='review')
            
            if not reviews:
                logger.info(f"No more reviews found on page {page}")
                break
            
            for review_elem in reviews:
                try:
                    # Extract review text
                    text_elem = review_elem.find('div', class_='review-content')
                    if not text_elem:
                        continue
                    
                    review_text = text_elem.get_text(strip=True)
                    
                    # Extract metadata
                    date_elem = review_elem.find('span', class_='review-date')
                    date_str = date_elem.get_text(strip=True) if date_elem else ""
                    review_date = self._extract_date(date_str) or datetime.now()
                    
                    user_elem = review_elem.find('span', class_='review-author')
                    user_id = user_elem.get_text(strip=True) if user_elem else "anonymous"
                    
                    # Create metadata
                    metadata = ReviewMetadata(
                        source_url=url,
                        date_posted=review_date,
                        user_id=user_id,
                        platform="drugs.com",
                        review_length=len(review_text),
                        language_detected="en"
                    )
                    
                    yield ReviewData(
                        text=review_text,
                        metadata=metadata,
                        raw_data={
                            'platform': 'drugs.com',
                            'drug_name': drug_name,
                            'page': page
                        }
                    )
                    
                except Exception as e:
                    logger.error(f"Error parsing review: {e}")
                    continue
    
    def crawl_reddit_medical(self, subreddit: str, query: str, max_posts: int = 50) -> Generator[ReviewData, None, None]:
        """
        Crawl medical discussions from Reddit.
        Note: This is a simplified version. For production, use Reddit API (PRAW).
        """
        # This would typically use Reddit API, but here's a web scraping approach
        search_url = f"https://www.reddit.com/r/{subreddit}/search/"
        params = {
            'q': query,
            'restrict_sr': 'on',
            'sort': 'relevance',
            'limit': max_posts
        }
        
        response = self._make_request(search_url, params=params)
        if not response:
            return
        
        # Note: Reddit's HTML structure is complex and changes frequently
        # In production, use Reddit API instead
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # This is a simplified parser - real implementation would be more robust
        posts = soup.find_all('div', {'data-testid': 'post-content'})
        
        for post in posts[:max_posts]:
            try:
                text_elem = post.find('div', {'data-testid': 'post-text'})
                if not text_elem:
                    continue
                
                review_text = text_elem.get_text(strip=True)
                
                # Extract basic metadata
                metadata = ReviewMetadata(
                    source_url=f"https://reddit.com/r/{subreddit}",
                    date_posted=datetime.now(),  # Would extract real date in production
                    platform="reddit.com",
                    review_length=len(review_text),
                    language_detected="en"
                )
                
                yield ReviewData(
                    text=review_text,
                    metadata=metadata,
                    raw_data={
                        'platform': 'reddit',
                        'subreddit': subreddit,
                        'query': query
                    }
                )
                
            except Exception as e:
                logger.error(f"Error parsing Reddit post: {e}")
                continue
    
    def crawl_clinicaltrials_gov(self, therapy_name: str, condition: str) -> Generator[Dict[str, Any], None, None]:
        """
        Crawl clinical trial information from ClinicalTrials.gov
        This provides context for matching reviews to trials.
        """
        api_url = "https://clinicaltrials.gov/api/query/full_studies"
        params = {
            'expr': f'"{therapy_name}" AND "{condition}"',
            'fmt': 'json',
            'max_rnk': 50
        }
        
        response = self._make_request(api_url, params=params)
        if not response:
            return
        
        try:
            data = response.json()
            studies = data.get('FullStudiesResponse', {}).get('FullStudies', [])
            
            for study in studies:
                study_info = study.get('Study', {})
                protocol_section = study_info.get('ProtocolSection', {})
                
                # Extract relevant information
                identification = protocol_section.get('IdentificationModule', {})
                design = protocol_section.get('DesignModule', {})
                eligibility = protocol_section.get('EligibilityModule', {})
                
                yield {
                    'nct_id': identification.get('NCTId'),
                    'title': identification.get('BriefTitle'),
                    'study_type': design.get('StudyType'),
                    'phases': design.get('PhaseList', {}).get('Phase', []),
                    'conditions': protocol_section.get('ConditionsModule', {}).get('ConditionList', {}).get('Condition', []),
                    'interventions': protocol_section.get('ArmsInterventionsModule', {}).get('InterventionList', {}).get('Intervention', []),
                    'eligibility_criteria': eligibility.get('EligibilityCriteria'),
                    'min_age': eligibility.get('MinimumAge'),
                    'max_age': eligibility.get('MaximumAge'),
                    'gender': eligibility.get('Gender')
                }
                
        except Exception as e:
            logger.error(f"Error parsing ClinicalTrials.gov data: {e}")
    
    def crawl_patient_forums(self, forum_urls: List[str], search_terms: List[str]) -> Generator[ReviewData, None, None]:
        """
        Generic crawler for patient forums and medical communities.
        """
        for url in forum_urls:
            platform = self._identify_platform(url)
            selectors = self.platform_selectors.get(platform, {})
            
            response = self._make_request(url)
            if not response:
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find review containers
            review_containers = []
            for selector in [selectors.get('review_container'), '.post', '.comment', '.review']:
                if selector:
                    review_containers = soup.find_all(class_=selector.replace('.', ''))
                    if review_containers:
                        break
            
            for container in review_containers:
                try:
                    # Extract text
                    text_selectors = [selectors.get('review_text'), '.content', '.text', 'p']
                    review_text = ""
                    
                    for selector in text_selectors:
                        if selector:
                            text_elem = container.find(class_=selector.replace('.', ''))
                            if text_elem:
                                review_text = text_elem.get_text(strip=True)
                                break
                    
                    if not review_text or len(review_text) < 20:
                        continue
                    
                    # Check if review contains search terms
                    text_lower = review_text.lower()
                    if not any(term.lower() in text_lower for term in search_terms):
                        continue
                    
                    # Extract date
                    date_elem = container.find(class_=selectors.get('date', 'date'))
                    date_str = date_elem.get_text(strip=True) if date_elem else ""
                    review_date = self._extract_date(date_str) or datetime.now()
                    
                    # Extract user
                    user_elem = container.find(class_=selectors.get('user', 'author'))
                    user_id = user_elem.get_text(strip=True) if user_elem else "anonymous"
                    
                    metadata = ReviewMetadata(
                        source_url=url,
                        date_posted=review_date,
                        user_id=user_id,
                        platform=platform,
                        review_length=len(review_text),
                        language_detected="en"
                    )
                    
                    yield ReviewData(
                        text=review_text,
                        metadata=metadata,
                        raw_data={
                            'platform': platform,
                            'search_terms': search_terms,
                            'url': url
                        }
                    )
                    
                except Exception as e:
                    logger.error(f"Error parsing forum post: {e}")
                    continue
    
    def search_google_for_reviews(self, query: str, max_results: int = 20) -> List[str]:
        """
        Search Google for medical review pages.
        Note: This is a simplified approach. Consider using Google Custom Search API.
        """
        # Construct search query for medical reviews
        search_query = f'"{query}" reviews site:drugs.com OR site:patientslikeme.com OR site:webmd.com'
        
        # In production, you would use Google Custom Search API
        # This is a placeholder for the concept
        urls = []
        
        # Example URLs that might be found (placeholder)
        example_urls = [
            f"https://www.drugs.com/comments/{query.replace(' ', '-').lower()}/",
            f"https://www.patientslikeme.com/treatments/{query.replace(' ', '-').lower()}/reviews",
            f"https://www.webmd.com/drugs/drugreview-{query.replace(' ', '-').lower()}"
        ]
        
        return example_urls[:max_results]


# Integration class for combining crawler with reliability detector
class ReliableReviewCollector:
    """
    High-level class that combines web crawling with reliability detection.
    """
    
    def __init__(self, clinical_trial_criteria, reliability_threshold: float = 0.6):
        from reliable_review_detector import ReliableReviewDetector
        
        self.crawler = ReviewCrawler()
        self.detector = ReliableReviewDetector(clinical_trial_criteria)
        self.threshold = reliability_threshold
        self.collected_reviews = []
    
    def collect_reliable_reviews(self, therapy_name: str, max_reviews: int = 100) -> List[Dict[str, Any]]:
        """
        Collect and filter reliable reviews for a specific therapy.
        """
        reliable_reviews = []
        total_collected = 0
        
        # Search multiple sources
        sources = [
            ('drugs.com', lambda: self.crawler.crawl_drugs_com(therapy_name, max_pages=5)),
            ('reddit', lambda: self.crawler.crawl_reddit_medical('ChronicPain', therapy_name, max_posts=20)),
        ]
        
        for source_name, source_func in sources:
            logger.info(f"Collecting reviews from {source_name}...")
            
            try:
                for review_data in source_func():
                    if total_collected >= max_reviews:
                        break
                    
                    # Check reliability
                    is_reliable, score = self.detector.is_reliable_review(
                        review_data.text, 
                        review_data.metadata, 
                        self.threshold
                    )
                    
                    review_result = {
                        'text': review_data.text,
                        'metadata': review_data.metadata.__dict__,
                        'reliability_score': score.to_dict(),
                        'is_reliable': is_reliable,
                        'source': source_name,
                        'raw_data': review_data.raw_data
                    }
                    
                    if is_reliable:
                        reliable_reviews.append(review_result)
                        logger.info(f"Found reliable review (score: {score.overall_score:.3f})")
                    
                    total_collected += 1
                    
            except Exception as e:
                logger.error(f"Error collecting from {source_name}: {e}")
        
        logger.info(f"Collected {len(reliable_reviews)} reliable reviews out of {total_collected} total")
        return reliable_reviews
    
    def save_results(self, reviews: List[Dict[str, Any]], filename: str):
        """Save collected reviews to JSON file"""
        # Convert datetime objects to strings for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, indent=2, ensure_ascii=False, default=json_serializer)
        
        logger.info(f"Saved {len(reviews)} reviews to {filename}")


# Example usage
if __name__ == "__main__":
    from reliable_review_detector import ClinicalTrialCriteria
    
    # Example: Collect reviews for CBT therapy
    trial_criteria = ClinicalTrialCriteria(
        therapy_name="Cognitive Behavioral Therapy",
        year=2015,
        duration_weeks=12,
        condition_treated="chronic pain",
        side_effects_mentioned=["initial anxiety", "fatigue"]
    )
    
    collector = ReliableReviewCollector(trial_criteria, reliability_threshold=0.6)
    
    # Collect reliable reviews
    reliable_reviews = collector.collect_reliable_reviews("cognitive behavioral therapy", max_reviews=50)
    
    # Save results
    collector.save_results(reliable_reviews, "reliable_cbt_reviews.json")
    
    # Print summary
    print(f"Collected {len(reliable_reviews)} reliable reviews")
    if reliable_reviews:
        avg_score = sum(r['reliability_score']['overall_score'] for r in reliable_reviews) / len(reliable_reviews)
        print(f"Average reliability score: {avg_score:.3f}")