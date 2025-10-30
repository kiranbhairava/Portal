import argparse
import sys
from job_scraper import LinkedInJobScraper

def parse_arguments():
    """Parse command-line arguments for the LinkedIn job scraper"""
    parser = argparse.ArgumentParser(description='LinkedIn Job Scraper')
    
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
    
    parser.add_argument('--headless', action='store_true', 
                        help='Run browser in headless mode')
    
    parser.add_argument('--fast', action='store_true', 
                        help='Disable slow mode (human-like delays)')
    
    parser.add_argument('-o', '--output', type=str,
                        help='Output filename (default: linkedin_jobs_TIMESTAMP.csv)')
    
    parser.add_argument('--format', type=str, choices=['csv', 'excel', 'both'], default='csv',
                        help='Output format (default: csv)')
    
    return parser.parse_args()

def main():
    """Main function to run the LinkedIn job scraper from command line"""
    args = parse_arguments()
    
    print("=== LinkedIn Job Scraper ===")
    print(f"Searching for: {args.keywords} in {args.location}")
    
    # Initialize the scraper
    scraper = LinkedInJobScraper(headless=args.headless, slow_mode=not args.fast)
    
    # Search for jobs
    jobs_df = scraper.search_jobs(
        keywords=args.keywords,
        location=args.location,
        limit=args.limit,
        experience_level=args.experience,
        job_type=args.job_type
    )
    
    # Save results
    if not jobs_df.empty:
        if args.format in ('csv', 'both'):
            scraper.save_to_csv(args.output)
        
        if args.format in ('excel', 'both'):
            excel_filename = args.output.replace('.csv', '.xlsx') if args.output else None
            scraper.save_to_excel(excel_filename)
        
        print(f"\nSuccessfully scraped {len(jobs_df)} jobs.")
        return 0
    else:
        print("No jobs found matching your criteria.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

## Installation Instructions

# 1. Create a folder for your project
# 2. Save each file with the correct name (`linkedin_job_scraper.py` and `app.py`)
# 3. Install the required packages:
# ```
#    pip install -r requirements.txt
# ```

# ## Usage Examples

# ### Running with Basic Options
# ```
# python app.py -k "Python Developer" -l "Remote"
# ```

# ### Specifying Experience Level and Job Type
# ```
# python app.py -k "Data Scientist" -l "New York" -e mid_senior -t full_time
# ```

# ### Setting a Limit and Output Format
# ```
# python app.py -k "Software Engineer" -l "San Francisco" -n 50 --format both
# ```

# ### Running in Visible Browser Mode
# ```
# python app.py -k "Product Manager" -l "Boston" --headless False
# ```

# ### Using the Fast Mode (Less Human-like)
# ```
# python app.py -k "DevOps Engineer" -l "Seattle" --fast