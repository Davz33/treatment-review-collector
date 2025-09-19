#!/usr/bin/env python3
"""
Test script for the improved review crawler
"""

import sys
from datetime import datetime
from review_crawler import ReliableReviewCollector
from reliable_review_detector import ClinicalTrialCriteria

def test_improved_crawler():
    """Test the improved crawler with real sources"""
    
    print("🧪 Testing Improved Review Crawler")
    print("=" * 50)
    
    # Create clinical trial criteria for CBT study from 2015
    trial_criteria = ClinicalTrialCriteria(
        therapy_name="Cognitive Behavioral Therapy",
        year=2015,
        duration_weeks=12,
        condition_treated="chronic pain",
        side_effects_mentioned=["initial anxiety", "fatigue"]
    )
    
    print(f"Testing with Clinical Trial: {trial_criteria.therapy_name} ({trial_criteria.year})")
    print(f"Condition: {trial_criteria.condition_treated}")
    print(f"Duration: {trial_criteria.duration_weeks} weeks")
    print("\n" + "=" * 50)
    
    # Initialize collector
    collector = ReliableReviewCollector(trial_criteria, reliability_threshold=0.6)
    
    # Test each source individually
    sources_to_test = [
        ("PubMed", lambda: collector.crawler.crawl_pubmed_comments("Cognitive Behavioral Therapy", "chronic pain")),
        ("Healthline", lambda: collector.crawler.crawl_healthline_community("Cognitive Behavioral Therapy", "chronic pain")),
        ("ClinicalTrials.gov", lambda: collector.crawler.crawl_clinicaltrials_gov("Cognitive Behavioral Therapy", "chronic pain"))
    ]
    
    total_found = 0
    
    for source_name, source_func in sources_to_test:
        print(f"\n🔍 Testing {source_name}...")
        try:
            count = 0
            for review_data in source_func():
                count += 1
                print(f"  📝 Found review {count}: {review_data.text[:100]}...")
                
                if count >= 3:  # Limit to first 3 for testing
                    break
            
            if count > 0:
                print(f"  ✅ {source_name}: Found {count} reviews")
                total_found += count
            else:
                print(f"  ⚠️  {source_name}: No reviews found")
                
        except Exception as e:
            print(f"  ❌ {source_name}: Error - {e}")
    
    print(f"\n📊 SUMMARY")
    print(f"Total reviews found: {total_found}")
    
    if total_found > 0:
        print("✅ Crawler is working - found real content!")
        
        # Test full collection
        print(f"\n🎯 Testing full collection process...")
        reviews = collector.collect_reliable_reviews("Cognitive Behavioral Therapy", max_reviews=10)
        
        print(f"Reliable reviews collected: {len(reviews)}")
        
        if reviews:
            print("\n📈 Sample reliable review:")
            sample = reviews[0]
            print(f"Source: {sample['source']}")
            print(f"Score: {sample['reliability_score']['overall_score']:.3f}")
            print(f"Text: {sample['text'][:200]}...")
            
    else:
        print("⚠️  No content found. This could be due to:")
        print("- Network connectivity issues")
        print("- API rate limiting")
        print("- Temporary server issues")
        print("- Need for API keys or authentication")

if __name__ == "__main__":
    try:
        test_improved_crawler()
        print(f"\n🎉 Test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)