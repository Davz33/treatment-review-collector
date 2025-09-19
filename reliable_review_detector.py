"""
Reliable Review Detector for Medical Treatment Reviews

This module defines criteria and implements detection mechanisms to identify
"real/reliable reviews" for medical treatments, specifically to match reviews
to clinical trial parameters and filter out AI-generated or fake content.
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import statistics
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ClinicalTrialCriteria:
    """Defines the criteria from a clinical trial for matching reviews"""
    therapy_name: str
    year: int
    duration_weeks: Optional[int] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    condition_treated: Optional[str] = None
    inclusion_criteria: List[str] = None
    exclusion_criteria: List[str] = None
    side_effects_mentioned: List[str] = None
    
    def __post_init__(self):
        if self.inclusion_criteria is None:
            self.inclusion_criteria = []
        if self.exclusion_criteria is None:
            self.exclusion_criteria = []
        if self.side_effects_mentioned is None:
            self.side_effects_mentioned = []


@dataclass
class ReviewMetadata:
    """Metadata associated with a review"""
    source_url: str
    date_posted: datetime
    user_id: Optional[str] = None
    user_history_length: int = 0
    platform: Optional[str] = None
    verified_user: bool = False
    review_length: int = 0
    language_detected: str = "unknown"


@dataclass
class ReliabilityScore:
    """Comprehensive reliability scoring for a review"""
    authenticity_score: float  # 0-1, higher = more likely human-written
    clinical_match_score: float  # 0-1, higher = better match to trial criteria
    source_credibility: float  # 0-1, higher = more credible source
    temporal_relevance: float  # 0-1, higher = more temporally relevant
    overall_score: float  # 0-1, weighted combination of above
    flags: List[str]  # Any red flags identified
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ReliableReviewDetector:
    """
    Main class for detecting reliable medical treatment reviews.
    
    Combines multiple approaches:
    1. AI-generated content detection
    2. Clinical trial criteria matching
    3. Source credibility assessment
    4. Temporal relevance analysis
    """
    
    def __init__(self, clinical_trial: ClinicalTrialCriteria):
        self.clinical_trial = clinical_trial
        self.ai_detection_patterns = self._load_ai_detection_patterns()
        self.medical_terminology = self._load_medical_terminology()
        
    def _load_ai_detection_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that commonly indicate AI-generated content"""
        return {
            "generic_phrases": [
                "i hope this helps",
                "it's important to note",
                "please consult with",
                "everyone's experience may vary",
                "results may differ",
                "in my experience",
                "from my perspective",
                "it's worth mentioning",
                "on the other hand",
                "that being said"
            ],
            "overly_structured": [
                r"\d+\.\s+\w+",  # Numbered lists
                r"firstly|secondly|thirdly|finally",
                r"in conclusion",
                r"to summarize",
                r"pros:.*cons:",
                r"advantages:.*disadvantages:"
            ],
            "medical_disclaimers": [
                "this is not medical advice",
                "consult your doctor",
                "speak with your healthcare provider",
                "always follow your doctor's instructions",
                "individual results may vary"
            ]
        }
    
    def _load_medical_terminology(self) -> Dict[str, List[str]]:
        """Load medical terminology relevant to the clinical trial"""
        return {
            "treatment_terms": [
                self.clinical_trial.therapy_name.lower(),
                self.clinical_trial.condition_treated.lower() if self.clinical_trial.condition_treated else "",
            ],
            "dosage_terms": [
                "mg", "ml", "dose", "dosage", "twice daily", "once daily",
                "morning", "evening", "with meals", "before meals"
            ],
            "side_effect_terms": [
                "side effect", "adverse reaction", "nausea", "headache",
                "fatigue", "dizziness", "rash", "stomach upset"
            ],
            "outcome_terms": [
                "improvement", "better", "worse", "no change", "effective",
                "ineffective", "helped", "didn't help", "relief", "pain"
            ]
        }
    
    def detect_ai_generated_content(self, review_text: str) -> Tuple[float, List[str]]:
        """
        Detect if content is likely AI-generated.
        
        Returns:
            Tuple of (authenticity_score, flags)
            authenticity_score: 0-1 where 1 = likely human, 0 = likely AI
        """
        flags = []
        text_lower = review_text.lower()
        
        # Check for generic AI phrases
        generic_count = sum(1 for phrase in self.ai_detection_patterns["generic_phrases"] 
                          if phrase in text_lower)
        if generic_count >= 2:
            flags.append(f"Contains {generic_count} generic AI phrases")
        
        # Check for overly structured content
        structure_matches = sum(1 for pattern in self.ai_detection_patterns["overly_structured"]
                              if re.search(pattern, text_lower))
        if structure_matches >= 2:
            flags.append("Overly structured content")
        
        # Check for medical disclaimers (common in AI responses)
        disclaimer_count = sum(1 for disclaimer in self.ai_detection_patterns["medical_disclaimers"]
                             if disclaimer in text_lower)
        if disclaimer_count >= 1:
            flags.append("Contains medical disclaimers")
        
        # Check for repetitive patterns
        sentences = re.split(r'[.!?]+', review_text)
        if len(sentences) > 3:
            sentence_lengths = [len(s.strip().split()) for s in sentences if s.strip()]
            if sentence_lengths and statistics.stdev(sentence_lengths) < 2:
                flags.append("Repetitive sentence structure")
        
        # Calculate authenticity score (inverse of AI likelihood)
        ai_indicators = len(flags)
        authenticity_score = max(0, 1 - (ai_indicators * 0.25))
        
        return authenticity_score, flags
    
    def match_clinical_criteria(self, review_text: str, metadata: ReviewMetadata) -> Tuple[float, List[str]]:
        """
        Match review content against clinical trial criteria.
        
        Returns:
            Tuple of (match_score, matching_elements)
        """
        text_lower = review_text.lower()
        matching_elements = []
        score_components = []
        
        # Check therapy name mention
        if self.clinical_trial.therapy_name.lower() in text_lower:
            matching_elements.append("Therapy name mentioned")
            score_components.append(0.3)
        
        # Check condition mention
        if (self.clinical_trial.condition_treated and 
            self.clinical_trial.condition_treated.lower() in text_lower):
            matching_elements.append("Condition mentioned")
            score_components.append(0.2)
        
        # Check duration mention
        if self.clinical_trial.duration_weeks:
            duration_patterns = [
                f"{self.clinical_trial.duration_weeks} week",
                f"{self.clinical_trial.duration_weeks} month",
                "for \\d+ weeks?",
                "for \\d+ months?"
            ]
            for pattern in duration_patterns:
                if re.search(pattern, text_lower):
                    matching_elements.append("Treatment duration mentioned")
                    score_components.append(0.2)
                    break
        
        # Check dosage/frequency patterns
        dosage_patterns = ["mg", "ml", "twice", "daily", "morning", "evening"]
        dosage_mentions = sum(1 for pattern in dosage_patterns if pattern in text_lower)
        if dosage_mentions >= 2:
            matching_elements.append("Dosage information provided")
            score_components.append(0.15)
        
        # Check for specific side effects mentioned in trial
        side_effect_matches = sum(1 for side_effect in self.clinical_trial.side_effects_mentioned
                                if side_effect.lower() in text_lower)
        if side_effect_matches > 0:
            matching_elements.append(f"Mentions {side_effect_matches} known side effects")
            score_components.append(min(0.15, side_effect_matches * 0.05))
        
        # Check for medical terminology usage
        medical_terms_found = sum(1 for term_list in self.medical_terminology.values()
                                for term in term_list if term and term in text_lower)
        if medical_terms_found >= 3:
            matching_elements.append("Uses appropriate medical terminology")
            score_components.append(0.1)
        
        match_score = sum(score_components)
        return min(1.0, match_score), matching_elements
    
    def assess_source_credibility(self, metadata: ReviewMetadata) -> Tuple[float, List[str]]:
        """
        Assess the credibility of the review source.
        
        Returns:
            Tuple of (credibility_score, credibility_factors)
        """
        credibility_factors = []
        score_components = []
        
        # Verified user bonus
        if metadata.verified_user:
            credibility_factors.append("Verified user account")
            score_components.append(0.3)
        
        # User history length
        if metadata.user_history_length > 12:  # More than a year of activity
            credibility_factors.append("Established user account")
            score_components.append(0.2)
        elif metadata.user_history_length > 3:  # More than 3 months
            credibility_factors.append("Moderate user history")
            score_components.append(0.1)
        
        # Platform credibility
        credible_platforms = [
            "patientslikeme", "drugs.com", "webmd", "healthgrades",
            "mayoclinic", "reddit.com/r/", "inspire.com"
        ]
        if metadata.platform and any(platform in metadata.platform.lower() 
                                   for platform in credible_platforms):
            credibility_factors.append("Posted on credible medical platform")
            score_components.append(0.25)
        
        # Review length (too short or too long might be suspicious)
        if 50 <= metadata.review_length <= 500:
            credibility_factors.append("Appropriate review length")
            score_components.append(0.15)
        elif metadata.review_length < 20:
            credibility_factors.append("Very short review (suspicious)")
            score_components.append(-0.2)
        elif metadata.review_length > 1000:
            credibility_factors.append("Very long review (potentially AI)")
            score_components.append(-0.1)
        
        # URL structure analysis
        if "?" in metadata.source_url and len(metadata.source_url.split("?")[1]) > 50:
            credibility_factors.append("Complex URL parameters (suspicious)")
            score_components.append(-0.1)
        
        credibility_score = max(0, min(1.0, sum(score_components) + 0.4))  # Base score of 0.4
        return credibility_score, credibility_factors
    
    def assess_temporal_relevance(self, metadata: ReviewMetadata) -> Tuple[float, List[str]]:
        """
        Assess temporal relevance to the clinical trial.
        
        Returns:
            Tuple of (relevance_score, temporal_factors)
        """
        temporal_factors = []
        trial_year = self.clinical_trial.year
        review_year = metadata.date_posted.year
        
        # Calculate years difference
        years_diff = abs(review_year - trial_year)
        
        if years_diff == 0:
            temporal_factors.append("Posted same year as clinical trial")
            relevance_score = 1.0
        elif years_diff <= 2:
            temporal_factors.append("Posted within 2 years of clinical trial")
            relevance_score = 0.8
        elif years_diff <= 5:
            temporal_factors.append("Posted within 5 years of clinical trial")
            relevance_score = 0.6
        elif years_diff <= 10:
            temporal_factors.append("Posted within 10 years of clinical trial")
            relevance_score = 0.4
        else:
            temporal_factors.append(f"Posted {years_diff} years from clinical trial")
            relevance_score = max(0.1, 1.0 - (years_diff * 0.1))
        
        # Bonus for reviews posted after trial (more relevant)
        if review_year >= trial_year:
            temporal_factors.append("Posted after clinical trial completion")
            relevance_score = min(1.0, relevance_score + 0.1)
        
        return relevance_score, temporal_factors
    
    def calculate_overall_reliability(self, review_text: str, metadata: ReviewMetadata) -> ReliabilityScore:
        """
        Calculate comprehensive reliability score for a review.
        
        Args:
            review_text: The text content of the review
            metadata: Associated metadata for the review
            
        Returns:
            ReliabilityScore object with detailed scoring
        """
        # Get individual scores
        authenticity_score, ai_flags = self.detect_ai_generated_content(review_text)
        clinical_match_score, clinical_elements = self.match_clinical_criteria(review_text, metadata)
        source_credibility, credibility_factors = self.assess_source_credibility(metadata)
        temporal_relevance, temporal_factors = self.assess_temporal_relevance(metadata)
        
        # Combine all flags
        all_flags = ai_flags + [f"Clinical: {elem}" for elem in clinical_elements] + \
                   [f"Source: {factor}" for factor in credibility_factors] + \
                   [f"Temporal: {factor}" for factor in temporal_factors]
        
        # Calculate weighted overall score
        weights = {
            'authenticity': 0.35,  # Heavily weight human vs AI
            'clinical': 0.30,      # Important for matching trial criteria
            'credibility': 0.20,   # Source matters
            'temporal': 0.15       # Time relevance
        }
        
        overall_score = (
            authenticity_score * weights['authenticity'] +
            clinical_match_score * weights['clinical'] +
            source_credibility * weights['credibility'] +
            temporal_relevance * weights['temporal']
        )
        
        return ReliabilityScore(
            authenticity_score=authenticity_score,
            clinical_match_score=clinical_match_score,
            source_credibility=source_credibility,
            temporal_relevance=temporal_relevance,
            overall_score=overall_score,
            flags=all_flags
        )
    
    def is_reliable_review(self, review_text: str, metadata: ReviewMetadata, 
                          threshold: float = 0.6) -> Tuple[bool, ReliabilityScore]:
        """
        Determine if a review meets reliability criteria.
        
        Args:
            review_text: The review content
            metadata: Review metadata
            threshold: Minimum overall score to consider reliable (default 0.6)
            
        Returns:
            Tuple of (is_reliable, reliability_score)
        """
        reliability_score = self.calculate_overall_reliability(review_text, metadata)
        is_reliable = reliability_score.overall_score >= threshold
        
        # Additional hard filters
        if reliability_score.authenticity_score < 0.3:  # Very likely AI
            is_reliable = False
            reliability_score.flags.append("REJECTED: Very likely AI-generated")
        
        if reliability_score.clinical_match_score < 0.1:  # No clinical relevance
            is_reliable = False
            reliability_score.flags.append("REJECTED: No clinical relevance")
        
        logger.info(f"Review reliability: {reliability_score.overall_score:.3f} "
                   f"({'RELIABLE' if is_reliable else 'UNRELIABLE'})")
        
        return is_reliable, reliability_score


# Example usage and testing
if __name__ == "__main__":
    # Example clinical trial from 2015
    trial_criteria = ClinicalTrialCriteria(
        therapy_name="Cognitive Behavioral Therapy",
        year=2015,
        duration_weeks=12,
        condition_treated="chronic pain",
        side_effects_mentioned=["initial anxiety", "fatigue"]
    )
    
    detector = ReliableReviewDetector(trial_criteria)
    
    # Example review (human-like)
    human_review = """
    I started CBT for my chronic pain in 2016 after reading about the study. 
    The 12-week program was challenging at first - I felt more anxious initially, 
    but by week 8 I noticed real improvements. The techniques for pain management 
    really helped me cope better. Some fatigue in the beginning but that went away.
    Overall, it made a significant difference in my daily life.
    """
    
    # Example AI-generated review
    ai_review = """
    I hope this helps with your decision about CBT therapy. It's important to note 
    that everyone's experience may vary with this treatment. From my perspective, 
    the cognitive behavioral therapy approach offers several advantages:
    1. Evidence-based treatment methods
    2. Structured approach to pain management  
    3. Long-term coping strategies
    However, it's worth mentioning that results may differ for each individual.
    Please consult with your healthcare provider before starting any new treatment.
    This is not medical advice.
    """
    
    # Create metadata
    metadata_human = ReviewMetadata(
        source_url="https://patientslikeme.com/review/12345",
        date_posted=datetime(2016, 3, 15),
        user_history_length=24,
        platform="patientslikeme.com",
        verified_user=True,
        review_length=len(human_review),
        language_detected="en"
    )
    
    metadata_ai = ReviewMetadata(
        source_url="https://example.com/review/67890?ref=ai&source=generated",
        date_posted=datetime(2024, 1, 1),
        user_history_length=1,
        platform="example.com",
        verified_user=False,
        review_length=len(ai_review),
        language_detected="en"
    )
    
    # Test both reviews
    print("=== HUMAN REVIEW ANALYSIS ===")
    is_reliable_human, score_human = detector.is_reliable_review(human_review, metadata_human)
    print(f"Reliable: {is_reliable_human}")
    print(f"Overall Score: {score_human.overall_score:.3f}")
    print(f"Authenticity: {score_human.authenticity_score:.3f}")
    print(f"Clinical Match: {score_human.clinical_match_score:.3f}")
    print(f"Source Credibility: {score_human.source_credibility:.3f}")
    print(f"Temporal Relevance: {score_human.temporal_relevance:.3f}")
    print("Flags:", score_human.flags[:5])  # Show first 5 flags
    
    print("\n=== AI REVIEW ANALYSIS ===")
    is_reliable_ai, score_ai = detector.is_reliable_review(ai_review, metadata_ai)
    print(f"Reliable: {is_reliable_ai}")
    print(f"Overall Score: {score_ai.overall_score:.3f}")
    print(f"Authenticity: {score_ai.authenticity_score:.3f}")
    print(f"Clinical Match: {score_ai.clinical_match_score:.3f}")
    print(f"Source Credibility: {score_ai.source_credibility:.3f}")
    print(f"Temporal Relevance: {score_ai.temporal_relevance:.3f}")
    print("Flags:", score_ai.flags[:5])  # Show first 5 flags