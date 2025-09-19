#!/usr/bin/env python3
"""
Simple test script to demonstrate the Treatment Review Collector functionality
without requiring external dependencies.
"""

import sys
from datetime import datetime

# Test the core reliability detection
from reliable_review_detector import ReliableReviewDetector, ClinicalTrialCriteria, ReviewMetadata

def test_reliability_detection():
    """Test the reliability detection system with various review examples"""
    
    print("🧪 Testing Treatment Review Collector")
    print("=" * 50)
    
    # Create clinical trial criteria for CBT study from 2015
    trial_criteria = ClinicalTrialCriteria(
        therapy_name="Cognitive Behavioral Therapy",
        year=2015,
        duration_weeks=12,
        condition_treated="chronic pain",
        side_effects_mentioned=["initial anxiety", "fatigue", "emotional sensitivity"]
    )
    
    detector = ReliableReviewDetector(trial_criteria)
    
    # Test cases: [description, review_text, expected_reliable]
    test_cases = [
        (
            "Human review - good match",
            """I started CBT for my chronic pain in 2016 after reading about the clinical trial results. 
            The 12-week program was challenging at first - I felt more anxious initially, but by week 8 
            I noticed real improvements. The techniques for pain management really helped me cope better. 
            Some fatigue in the beginning but that went away. Overall, it made a significant difference 
            in my daily life.""",
            True
        ),
        (
            "AI-generated review - generic advice",
            """I hope this helps with your decision about CBT therapy. It's important to note that 
            everyone's experience may vary with this treatment. From my perspective, the cognitive 
            behavioral therapy approach offers several advantages: 1. Evidence-based treatment methods 
            2. Structured approach to pain management 3. Long-term coping strategies. However, it's worth 
            mentioning that results may differ for each individual. Please consult with your healthcare 
            provider before starting any new treatment. This is not medical advice.""",
            False
        ),
        (
            "Short authentic review",
            """CBT helped my chronic pain after 12 weeks. Had some anxiety at first but got better.""",
            True
        ),
        (
            "Overly promotional review",
            """This is the most amazing treatment ever! Incredible improvement in just days! 
            Miracle cure for everyone! Highly recommend to absolutely everyone! Life-changing results!""",
            False
        ),
        (
            "Medical professional review",
            """As a pain management specialist, I've observed that CBT can be effective for chronic pain 
            patients when implemented properly over 8-12 weeks. The initial increase in anxiety is common 
            and typically resolves by week 6-8. Patient compliance with homework assignments correlates 
            strongly with outcomes.""",
            True  # Professional but relevant
        ),
        (
            "Off-topic review",
            """I tried this medication for my headaches and it worked great. No side effects at all. 
            Would recommend for anyone with headache problems.""",
            False  # Wrong therapy type
        )
    ]
    
    print(f"Testing with Clinical Trial: {trial_criteria.therapy_name} ({trial_criteria.year})")
    print(f"Condition: {trial_criteria.condition_treated}")
    print(f"Duration: {trial_criteria.duration_weeks} weeks")
    print("\n" + "=" * 50)
    
    results = []
    for i, (description, review_text, expected_reliable) in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {description}")
        print(f"📝 Review: {review_text[:100]}{'...' if len(review_text) > 100 else ''}")
        
        # Create metadata
        metadata = ReviewMetadata(
            source_url=f"https://example.com/review/{i}",
            date_posted=datetime(2016, 3, 15),  # Year after trial
            user_history_length=12,
            platform="example.com",
            verified_user=True,
            review_length=len(review_text),
            language_detected="en"
        )
        
        # Test reliability
        is_reliable, score = detector.is_reliable_review(review_text, metadata, threshold=0.6)
        
        # Results
        print(f"✅ Reliable: {is_reliable} (Expected: {expected_reliable})")
        print(f"🎯 Overall Score: {score.overall_score:.3f}")
        print(f"   - Authenticity: {score.authenticity_score:.3f}")
        print(f"   - Clinical Match: {score.clinical_match_score:.3f}")
        print(f"   - Source Credibility: {score.source_credibility:.3f}")
        print(f"   - Temporal Relevance: {score.temporal_relevance:.3f}")
        
        # Check if prediction matches expectation
        correct = is_reliable == expected_reliable
        print(f"🎯 Prediction: {'✅ CORRECT' if correct else '❌ INCORRECT'}")
        
        if score.flags:
            print(f"🚩 Key Flags: {', '.join(score.flags[:3])}")
        
        results.append({
            'description': description,
            'reliable': is_reliable,
            'expected': expected_reliable,
            'correct': correct,
            'score': score.overall_score
        })
        
        print("-" * 40)
    
    # Summary
    correct_predictions = sum(1 for r in results if r['correct'])
    total_tests = len(results)
    accuracy = correct_predictions / total_tests * 100
    
    print(f"\n📊 SUMMARY")
    print(f"✅ Correct predictions: {correct_predictions}/{total_tests} ({accuracy:.1f}%)")
    
    reliable_reviews = [r for r in results if r['reliable']]
    if reliable_reviews:
        avg_reliable_score = sum(r['score'] for r in reliable_reviews) / len(reliable_reviews)
        print(f"📈 Average score (reliable): {avg_reliable_score:.3f}")
    
    unreliable_reviews = [r for r in results if not r['reliable']]
    if unreliable_reviews:
        avg_unreliable_score = sum(r['score'] for r in unreliable_reviews) / len(unreliable_reviews)
        print(f"📉 Average score (unreliable): {avg_unreliable_score:.3f}")
    
    print(f"\n🎯 Test {'PASSED' if accuracy >= 80 else 'FAILED'} (Accuracy: {accuracy:.1f}%)")
    
    return results

def demonstrate_clinical_matching():
    """Demonstrate how clinical trial matching works"""
    
    print("\n" + "=" * 50)
    print("🏥 CLINICAL TRIAL MATCHING DEMONSTRATION")
    print("=" * 50)
    
    # Different trial criteria
    trials = [
        ClinicalTrialCriteria(
            therapy_name="Mindfulness-Based Stress Reduction",
            year=2018,
            duration_weeks=8,
            condition_treated="anxiety disorder",
            side_effects_mentioned=["initial restlessness"]
        ),
        ClinicalTrialCriteria(
            therapy_name="Dialectical Behavior Therapy",
            year=2019,
            duration_weeks=24,
            condition_treated="borderline personality disorder",
            side_effects_mentioned=["emotional intensity", "initial distress"]
        )
    ]
    
    # Sample review
    review = """I participated in an 8-week mindfulness program in 2019 for my anxiety. 
    The first few sessions made me feel restless, but by week 4 I was sleeping better. 
    The breathing exercises and body scan techniques really helped with my panic attacks."""
    
    metadata = ReviewMetadata(
        source_url="https://anxietysupport.com/review/123",
        date_posted=datetime(2019, 6, 15),
        platform="anxietysupport.com",
        review_length=len(review)
    )
    
    print(f"📝 Sample Review: {review}")
    print(f"\nTesting against different clinical trials:")
    
    for i, trial in enumerate(trials, 1):
        print(f"\n🧪 Trial {i}: {trial.therapy_name}")
        print(f"   Year: {trial.year}, Duration: {trial.duration_weeks} weeks")
        print(f"   Condition: {trial.condition_treated}")
        
        detector = ReliableReviewDetector(trial)
        is_reliable, score = detector.is_reliable_review(review, metadata)
        
        print(f"   ✅ Match Score: {score.clinical_match_score:.3f}")
        print(f"   🎯 Overall Score: {score.overall_score:.3f}")
        print(f"   📊 Reliable: {is_reliable}")

if __name__ == "__main__":
    try:
        # Run main test
        results = test_reliability_detection()
        
        # Demonstrate clinical matching
        demonstrate_clinical_matching()
        
        print(f"\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)