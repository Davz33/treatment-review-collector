#!/usr/bin/env python3
"""
Treatment Review Collector - Main CLI Application

This is the main entry point for collecting and analyzing reliable medical treatment reviews.
"""

import click
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from reliable_review_detector import ReliableReviewDetector, ClinicalTrialCriteria
from review_crawler import ReliableReviewCollector
from config import config, MEDICAL_KEYWORDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.logs_dir / 'treatment_review_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Treatment Review Collector - AI-powered system for collecting reliable medical treatment reviews."""
    pass


@cli.command()
@click.option('--therapy-name', '-t', required=True, help='Name of the therapy/treatment')
@click.option('--condition', '-c', required=True, help='Medical condition being treated')
@click.option('--trial-year', '-y', type=int, required=True, help='Year of the clinical trial')
@click.option('--duration-weeks', '-d', type=int, help='Duration of treatment in weeks')
@click.option('--max-reviews', '-m', default=100, help='Maximum number of reviews to collect')
@click.option('--threshold', default=0.6, help='Reliability threshold (0-1)')
@click.option('--output', '-o', help='Output file path (JSON)')
@click.option('--include-unreliable', is_flag=True, help='Include unreliable reviews in output')
def collect(therapy_name: str, condition: str, trial_year: int, duration_weeks: Optional[int],
           max_reviews: int, threshold: float, output: Optional[str], include_unreliable: bool):
    """Collect reliable reviews for a specific therapy and clinical trial."""
    
    click.echo(f"🔍 Collecting reviews for: {therapy_name}")
    click.echo(f"📊 Condition: {condition}")
    click.echo(f"📅 Trial year: {trial_year}")
    click.echo(f"🎯 Reliability threshold: {threshold}")
    
    # Create clinical trial criteria
    trial_criteria = ClinicalTrialCriteria(
        therapy_name=therapy_name,
        year=trial_year,
        duration_weeks=duration_weeks,
        condition_treated=condition,
        side_effects_mentioned=[]  # Could be expanded based on user input
    )
    
    # Initialize collector
    collector = ReliableReviewCollector(trial_criteria, reliability_threshold=threshold)
    
    try:
        # Collect reviews
        with click.progressbar(length=max_reviews, label='Collecting reviews') as bar:
            all_reviews = []
            reliable_count = 0
            
            # This would be integrated with the actual collection process
            reviews = collector.collect_reliable_reviews(therapy_name, max_reviews)
            
            for review in reviews:
                all_reviews.append(review)
                if review['is_reliable']:
                    reliable_count += 1
                bar.update(1)
        
        click.echo(f"\n✅ Collection complete!")
        click.echo(f"📈 Found {reliable_count} reliable reviews out of {len(all_reviews)} total")
        
        # Filter results if not including unreliable reviews
        if not include_unreliable:
            reviews_to_save = [r for r in all_reviews if r['is_reliable']]
        else:
            reviews_to_save = all_reviews
        
        # Determine output file
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_therapy_name = therapy_name.replace(' ', '_').lower()
            output = f"{safe_therapy_name}_reviews_{timestamp}.json"
        
        # Save results
        output_path = Path(output)
        collector.save_results(reviews_to_save, str(output_path))
        
        click.echo(f"💾 Saved {len(reviews_to_save)} reviews to: {output_path}")
        
        # Display summary statistics
        if reviews_to_save:
            avg_score = sum(r['reliability_score']['overall_score'] for r in reviews_to_save) / len(reviews_to_save)
            click.echo(f"📊 Average reliability score: {avg_score:.3f}")
            
            # Show score distribution
            score_ranges = {
                "Excellent (0.8-1.0)": len([r for r in reviews_to_save if r['reliability_score']['overall_score'] >= 0.8]),
                "Good (0.6-0.8)": len([r for r in reviews_to_save if 0.6 <= r['reliability_score']['overall_score'] < 0.8]),
                "Fair (0.4-0.6)": len([r for r in reviews_to_save if 0.4 <= r['reliability_score']['overall_score'] < 0.6]),
                "Poor (0.0-0.4)": len([r for r in reviews_to_save if r['reliability_score']['overall_score'] < 0.4])
            }
            
            click.echo("\n📈 Score Distribution:")
            for range_name, count in score_ranges.items():
                if count > 0:
                    click.echo(f"  {range_name}: {count} reviews")
        
    except Exception as e:
        logger.error(f"Error during collection: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('review_file', type=click.Path(exists=True))
@click.option('--therapy-name', '-t', required=True, help='Name of the therapy/treatment')
@click.option('--condition', '-c', required=True, help='Medical condition being treated')
@click.option('--trial-year', '-y', type=int, required=True, help='Year of the clinical trial')
@click.option('--threshold', default=0.6, help='Reliability threshold (0-1)')
def analyze(review_file: str, therapy_name: str, condition: str, trial_year: int, threshold: float):
    """Analyze reliability of reviews from a JSON file."""
    
    click.echo(f"🔍 Analyzing reviews from: {review_file}")
    
    # Load reviews
    try:
        with open(review_file, 'r', encoding='utf-8') as f:
            reviews_data = json.load(f)
    except Exception as e:
        click.echo(f"❌ Error loading file: {e}", err=True)
        raise click.Abort()
    
    # Create clinical trial criteria
    trial_criteria = ClinicalTrialCriteria(
        therapy_name=therapy_name,
        year=trial_year,
        condition_treated=condition
    )
    
    # Initialize detector
    detector = ReliableReviewDetector(trial_criteria)
    
    # Analyze each review
    results = []
    reliable_count = 0
    
    with click.progressbar(reviews_data, label='Analyzing reviews') as bar:
        for review_data in bar:
            # Extract review text and metadata
            if isinstance(review_data, dict):
                review_text = review_data.get('text', '')
                metadata_dict = review_data.get('metadata', {})
            else:
                # Handle different data formats
                review_text = str(review_data)
                metadata_dict = {}
            
            if not review_text:
                continue
            
            # Create metadata object (simplified)
            from reliable_review_detector import ReviewMetadata
            metadata = ReviewMetadata(
                source_url=metadata_dict.get('source_url', 'unknown'),
                date_posted=datetime.now(),  # Would parse actual date
                platform=metadata_dict.get('platform', 'unknown'),
                review_length=len(review_text)
            )
            
            # Analyze reliability
            is_reliable, score = detector.is_reliable_review(review_text, metadata, threshold)
            
            if is_reliable:
                reliable_count += 1
            
            results.append({
                'text': review_text[:200] + "..." if len(review_text) > 200 else review_text,
                'is_reliable': is_reliable,
                'overall_score': score.overall_score,
                'authenticity_score': score.authenticity_score,
                'clinical_match_score': score.clinical_match_score,
                'source_credibility': score.source_credibility,
                'temporal_relevance': score.temporal_relevance,
                'flags': score.flags[:3]  # Show first 3 flags
            })
    
    # Display results
    click.echo(f"\n📊 Analysis Results:")
    click.echo(f"✅ Reliable reviews: {reliable_count}/{len(results)} ({reliable_count/len(results)*100:.1f}%)")
    
    if results:
        avg_score = sum(r['overall_score'] for r in results) / len(results)
        click.echo(f"📈 Average reliability score: {avg_score:.3f}")
        
        # Show top reliable reviews
        reliable_reviews = [r for r in results if r['is_reliable']]
        reliable_reviews.sort(key=lambda x: x['overall_score'], reverse=True)
        
        if reliable_reviews:
            click.echo(f"\n🏆 Top {min(5, len(reliable_reviews))} Most Reliable Reviews:")
            for i, review in enumerate(reliable_reviews[:5], 1):
                click.echo(f"\n{i}. Score: {review['overall_score']:.3f}")
                click.echo(f"   Text: {review['text']}")
                click.echo(f"   Flags: {', '.join(review['flags']) if review['flags'] else 'None'}")


@cli.command()
@click.option('--therapy-name', '-t', required=True, help='Name of the therapy/treatment')
@click.option('--condition', '-c', help='Medical condition (optional)')
def search_trials(therapy_name: str, condition: Optional[str]):
    """Search for clinical trials related to a therapy."""
    
    click.echo(f"🔍 Searching clinical trials for: {therapy_name}")
    if condition:
        click.echo(f"📊 Condition: {condition}")
    
    from review_crawler import ReviewCrawler
    crawler = ReviewCrawler()
    
    try:
        trials = list(crawler.crawl_clinicaltrials_gov(therapy_name, condition or ""))
        
        if not trials:
            click.echo("❌ No trials found")
            return
        
        click.echo(f"\n✅ Found {len(trials)} clinical trials:")
        
        for i, trial in enumerate(trials[:10], 1):  # Show first 10
            click.echo(f"\n{i}. {trial.get('title', 'No title')}")
            click.echo(f"   NCT ID: {trial.get('nct_id', 'N/A')}")
            click.echo(f"   Study Type: {trial.get('study_type', 'N/A')}")
            
            conditions = trial.get('conditions', [])
            if conditions:
                click.echo(f"   Conditions: {', '.join(conditions[:3])}")
            
            phases = trial.get('phases', [])
            if phases:
                click.echo(f"   Phases: {', '.join(phases)}")
    
    except Exception as e:
        logger.error(f"Error searching trials: {e}")
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.option('--condition', '-c', type=click.Choice(list(MEDICAL_KEYWORDS.keys())), 
              help='Medical condition category')
def list_keywords(condition: Optional[str]):
    """List medical keywords for different conditions."""
    
    if condition:
        keywords = MEDICAL_KEYWORDS.get(condition, [])
        click.echo(f"🏥 Keywords for {condition.replace('_', ' ').title()}:")
        for keyword in keywords:
            click.echo(f"  • {keyword}")
    else:
        click.echo("🏥 Available medical condition categories:")
        for category in MEDICAL_KEYWORDS.keys():
            click.echo(f"  • {category.replace('_', ' ').title()}")
        click.echo(f"\nUse --condition to see keywords for a specific category")


@cli.command()
def config_info():
    """Display current configuration settings."""
    
    click.echo("⚙️  Current Configuration:")
    click.echo(f"  Reliability threshold: {config.reliability.reliability_threshold}")
    click.echo(f"  Crawler delay: {config.crawler.delay_between_requests}s")
    click.echo(f"  Max retries: {config.crawler.max_retries}")
    click.echo(f"  Advanced AI detection: {config.reliability.enable_advanced_ai_detection}")
    click.echo(f"  Database enabled: {config.database.use_database}")
    click.echo(f"  Redis cache enabled: {config.database.use_redis_cache}")
    
    click.echo(f"\n📁 Directories:")
    click.echo(f"  Data: {config.data_dir}")
    click.echo(f"  Logs: {config.logs_dir}")
    click.echo(f"  Models: {config.models_dir}")
    
    click.echo(f"\n🔑 API Keys Configured:")
    api_keys = {
        "Reddit": bool(config.api.reddit_client_id),
        "Google": bool(config.api.google_api_key),
        "OpenAI": bool(config.api.openai_api_key),
        "HuggingFace": bool(config.api.huggingface_api_key)
    }
    
    for service, configured in api_keys.items():
        status = "✅" if configured else "❌"
        click.echo(f"  {service}: {status}")


@cli.command()
@click.argument('text')
@click.option('--therapy-name', '-t', default='Generic Therapy', help='Name of the therapy')
@click.option('--condition', '-c', default='General', help='Medical condition')
@click.option('--trial-year', '-y', type=int, default=2020, help='Year of clinical trial')
def test_review(text: str, therapy_name: str, condition: str, trial_year: int):
    """Test the reliability detection on a single review text."""
    
    click.echo(f"🧪 Testing review reliability...")
    click.echo(f"📝 Review text: {text[:100]}{'...' if len(text) > 100 else ''}")
    
    # Create trial criteria
    trial_criteria = ClinicalTrialCriteria(
        therapy_name=therapy_name,
        year=trial_year,
        condition_treated=condition
    )
    
    # Create detector
    detector = ReliableReviewDetector(trial_criteria)
    
    # Create metadata
    from reliable_review_detector import ReviewMetadata
    metadata = ReviewMetadata(
        source_url="test://example.com",
        date_posted=datetime.now(),
        platform="test",
        review_length=len(text)
    )
    
    # Analyze
    is_reliable, score = detector.is_reliable_review(text, metadata)
    
    # Display results
    click.echo(f"\n📊 Results:")
    click.echo(f"✅ Reliable: {is_reliable}")
    click.echo(f"🎯 Overall Score: {score.overall_score:.3f}")
    click.echo(f"🤖 Authenticity: {score.authenticity_score:.3f}")
    click.echo(f"🏥 Clinical Match: {score.clinical_match_score:.3f}")
    click.echo(f"🔗 Source Credibility: {score.source_credibility:.3f}")
    click.echo(f"⏰ Temporal Relevance: {score.temporal_relevance:.3f}")
    
    if score.flags:
        click.echo(f"\n🚩 Flags:")
        for flag in score.flags[:10]:  # Show first 10 flags
            click.echo(f"  • {flag}")


if __name__ == '__main__':
    cli()