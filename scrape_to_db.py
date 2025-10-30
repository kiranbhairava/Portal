#!/usr/bin/env python3
"""
Simple Terminal LinkedIn Job Scraper with PostgreSQL Storage
Run this script to scrape jobs and save them to the database.
"""

import argparse
import sys
from job_scraper import LinkedInJobScraper
from database import JobDatabase

def main():
    """Main function to run the scraper from terminal"""
    parser = argparse.ArgumentParser(description='LinkedIn Job Scraper with Database Storage')
    
    parser.add_argument('-k', '--keywords', type=str, required=True, 
                        help='Job keywords or title to search for')
    
    parser.add_argument('-l', '--location', type=str, required=True, 
                        help='Job location to search for')
    
    parser.add_argument('-n', '--limit', type=int, default=25,
                        help='Maximum number of jobs to scrape (default: 25)')
    
    parser.add_argument('-e', '--experience', type=str, choices=[
                        'internship', 'entry_level', 'associate', 'mid_senior', 'director', 'executive'],
                        help='Experience level filter')
    
    parser.add_argument('-t', '--job-type', type=str, choices=[
                        'full_time', 'part_time', 'contract', 'temporary', 'volunteer', 'internship', 'other'],
                        dest='job_type',
                        help='Job type filter')
    
    parser.add_argument('--headless', action='store_true', default=True,
                        help='Run browser in headless mode (default: True)')
    
    parser.add_argument('--visible', action='store_true',
                        help='Run browser in visible mode (for debugging)')
    
    parser.add_argument('--fast', action='store_true', 
                        help='Disable slow mode (human-like delays)')
    
    args = parser.parse_args()
    
    print("=== LinkedIn Job Scraper with Database Storage ===")
    print(f"Searching for: {args.keywords} in {args.location}")
    print(f"Limit: {args.limit} jobs")
    
    if args.experience:
        print(f"Experience: {args.experience}")
    if args.job_type:
        print(f"Job Type: {args.job_type}")
    
    # Set headless mode
    headless = args.headless and not args.visible
    
    try:
        # Initialize database
        print("\n🗄️  Connecting to database...")
        db = JobDatabase()
        
        # Initialize the scraper
        print("🚀 Initializing scraper...")
        scraper = LinkedInJobScraper(headless=headless, slow_mode=not args.fast)
        
        # Search for jobs
        print("🔍 Scraping jobs...")
        jobs_df = scraper.search_jobs(
            keywords=args.keywords,
            location=args.location,
            limit=args.limit,
            experience_level=args.experience,
            job_type=args.job_type
        )
        
        if not jobs_df.empty:
            print(f"✅ Found {len(jobs_df)} jobs!")
            
            # Save to database
            print("💾 Saving jobs to database...")
            jobs_list = jobs_df.to_dict('records')
            
            search_params = {
                'keywords': args.keywords,
                'location': args.location,
                'limit': args.limit,
                'experience_level': args.experience,
                'job_type': args.job_type
            }
            
            success = db.save_jobs(jobs_list, search_params)
            
            if success:
                print("✅ Jobs saved to database successfully!")
                print(f"\n📊 Summary:")
                print(f"  - Jobs scraped: {len(jobs_df)}")
                print(f"  - Keywords: {args.keywords}")
                print(f"  - Location: {args.location}")
                
                # Show some sample jobs
                print(f"\n📋 Sample jobs:")
                for i, job in enumerate(jobs_df.head(3).itertuples(), 1):
                    print(f"  {i}. {job.title} at {job.company} ({job.location})")
                
                print(f"\n🌐 View all jobs at: http://localhost:5000")
                print(f"📱 Start dashboard: python connector.py")
                
            else:
                print("❌ Failed to save jobs to database")
                return 1
                
        else:
            print("❌ No jobs found matching your criteria")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())