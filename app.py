# import os
# import sys
# import json
# import subprocess
# import tempfile
# import threading
# import pandas as pd
# from datetime import datetime
# from flask import Flask, request, jsonify, send_from_directory, render_template
# from flask_cors import CORS
# from dotenv import load_dotenv  # ✅ NEW: for .env secrets
# from job_scraper import LinkedInJobScraper
# from database import JobDatabase

# # ✅ Load environment variables from .env
# load_dotenv()

# # Flask setup
# app = Flask(__name__, static_folder='static')
# CORS(app)

# # ✅ Initialize database using secrets from .env
# db = JobDatabase()

# # In-memory job tracking
# active_jobs = {}
# job_results = {}

# @app.route('/')
# def index():
#     """Serve main HTML page"""
#     return send_from_directory('templates', 'marketplace.html')

# @app.route('/api/scrape', methods=['POST'])
# def scrape_jobs():
#     """Start a scraping job"""
#     data = request.json
#     keywords = data.get('keywords', '')
#     location = data.get('location', '')
#     limit = int(data.get('limit', 25))
#     experience = data.get('experience', None)
#     job_type = data.get('job_type', None)
#     headless = data.get('headless', True)
#     fast = data.get('fast', False)

#     if not keywords or not location:
#         return jsonify({'success': False, 'error': 'Keywords and location are required'}), 400

#     job_id = f"job_{int(datetime.now().timestamp())}"

#     active_jobs[job_id] = {
#         'status': 'running',
#         'progress': 0,
#         'message': 'Starting job...',
#         'parameters': {
#             'keywords': keywords,
#             'location': location,
#             'limit': limit,
#             'experience': experience,
#             'job_type': job_type
#         }
#     }

#     thread = threading.Thread(
#         target=run_scraper,
#         args=(job_id, keywords, location, limit, experience, job_type, headless, not fast)
#     )
#     thread.daemon = True
#     thread.start()

#     return jsonify({
#         'success': True,
#         'job_id': job_id,
#         'message': 'Scraping job started'
#     })

# @app.route('/api/status/<job_id>', methods=['GET'])
# def job_status(job_id):
#     """Get scraping job status"""
#     if job_id not in active_jobs:
#         return jsonify({'success': False, 'error': 'Job not found'}), 404
#     return jsonify({'success': True, 'status': active_jobs[job_id]})

# @app.route('/api/results/<job_id>', methods=['GET'])
# def job_results_api(job_id):
#     """Get completed job results"""
#     if job_id not in job_results:
#         return jsonify({'success': False, 'error': 'Results not found'}), 404
#     return jsonify({'success': True, 'results': job_results[job_id]})

# def run_scraper(job_id, keywords, location, limit, experience, job_type, headless, slow_mode):
#     """Run LinkedIn scraper in a thread"""
#     try:
#         if job_id not in active_jobs:
#             print(f"⚠️ Warning: Job {job_id} not found in active_jobs")
#             return

#         active_jobs[job_id].update({
#             'status': 'running',
#             'progress': 5,
#             'message': 'Initializing scraper...'
#         })

#         scraper = LinkedInJobScraper(headless=headless, slow_mode=slow_mode)

#         active_jobs[job_id].update({
#             'progress': 10,
#             'message': f'Searching for {keywords} jobs in {location}...'
#         })

#         jobs_df = scraper.search_jobs(
#             keywords=keywords,
#             location=location,
#             limit=limit,
#             experience_level=experience,
#             job_type=job_type
#         )

#         if not jobs_df.empty:
#             active_jobs[job_id].update({
#                 'progress': 70,
#                 'message': 'Saving jobs to database...'
#             })

#             jobs_list = jobs_df.to_dict('records')
#             job_results[job_id] = jobs_list

#             search_params = {
#                 'keywords': keywords,
#                 'location': location,
#                 'limit': limit,
#                 'experience_level': experience,
#                 'job_type': job_type
#             }

#             # ✅ Save directly to database
#             try:
#                 db_saved = db.save_jobs(jobs_list, search_params)
#                 if db_saved:
#                     print(f"✅ Saved {len(jobs_list)} jobs to DB")
#                 else:
#                     print("❌ Failed to save jobs to DB")
#             except Exception as db_error:
#                 print(f"❌ Database error: {db_error}")
#                 db_saved = False

#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             os.makedirs('static/downloads', exist_ok=True)
#             csv_filename = f"linkedin_jobs_{timestamp}.csv"
#             excel_filename = f"linkedin_jobs_{timestamp}.xlsx"
#             jobs_df.to_csv(f"static/downloads/{csv_filename}", index=False)
#             jobs_df.to_excel(f"static/downloads/{excel_filename}", index=False)

#             active_jobs[job_id].update({
#                 'status': 'completed',
#                 'progress': 100,
#                 'message': f"Scraped and saved {len(jobs_df)} jobs" if db_saved else "Scraped jobs (DB save failed)",
#                 'files': {'csv': csv_filename, 'excel': excel_filename}
#             })
#         else:
#             active_jobs[job_id].update({
#                 'status': 'completed',
#                 'progress': 100,
#                 'message': 'No jobs found',
#             })
#             job_results[job_id] = []

#     except Exception as e:
#         if job_id in active_jobs:
#             active_jobs[job_id].update({
#                 'status': 'error',
#                 'progress': 100,
#                 'message': f'Error: {str(e)}'
#             })
#         print(f"❌ Error in job {job_id}: {e}")

# @app.route('/downloads/<filename>')
# def download_file(filename):
#     """Serve downloaded files"""
#     return send_from_directory('static/downloads', filename)

# @app.route('/api/export/csv/<job_id>', methods=['GET'])
# def export_csv(job_id):
#     """Export job results to CSV"""
#     if job_id not in job_results:
#         return jsonify({'success': False, 'error': 'Results not found'}), 404

#     df = pd.DataFrame(job_results[job_id])
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"linkedin_jobs_{timestamp}.csv"
#     os.makedirs('static/downloads', exist_ok=True)
#     df.to_csv(f"static/downloads/{filename}", index=False)

#     return jsonify({'success': True, 'file_url': f'/downloads/{filename}'})

# @app.route('/api/export/excel/<job_id>', methods=['GET'])
# def export_excel(job_id):
#     """Export job results to Excel"""
#     if job_id not in job_results:
#         return jsonify({'success': False, 'error': 'Results not found'}), 404

#     df = pd.DataFrame(job_results[job_id])
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"linkedin_jobs_{timestamp}.xlsx"
#     os.makedirs('static/downloads', exist_ok=True)
#     df.to_excel(f"static/downloads/{filename}", index=False)

#     return jsonify({'success': True, 'file_url': f'/downloads/{filename}'})

# @app.route('/api/jobs', methods=['GET'])
# def get_all_jobs():
#     """Fetch all jobs stored in DB (latest first, include full metadata)."""
#     try:
#         cursor = db.conn.cursor()
#         cursor.execute("""
#             SELECT 
#                 id, title, company, location, posted_time, 
#                 description, employment_type, seniority_level, industries, job_function,
#                 company_url, company_logo, company_about, company_stats,
#                 job_url, keywords, search_location, scraped_at
#             FROM jobs
#             ORDER BY scraped_at DESC
#             LIMIT 100
#         """)
#         rows = cursor.fetchall()
#         cursor.close()

#         # Build JSON response
#         jobs = []
#         for row in rows:
#             jobs.append({
#                 'id': row[0],
#                 'title': row[1],
#                 'company': row[2],
#                 'location': row[3],
#                 'posted_time': row[4],
#                 'description': row[5] or "No description available",
#                 'employment_type': row[6],
#                 'seniority_level': row[7],
#                 'industries': row[8],
#                 'job_function': row[9],
#                 'company_url': row[10],
#                 'company_logo': row[11],  # ✅ FIXED: company logo added
#                 'company_about': row[12],
#                 'company_stats': row[13],
#                 'job_url': row[14],
#                 'keywords': row[15],
#                 'search_location': row[16],
#                 'scraped_at': row[17].isoformat() if row[17] else None,
#             })

#         return jsonify({'success': True, 'jobs': jobs}), 200

#     except Exception as e:
#         print(f"❌ Error fetching jobs: {e}")
#         return jsonify({'success': False, 'error': str(e)}), 500


#         return jsonify({'success': True, 'jobs': jobs})

#     except Exception as e:
#         print(f"❌ Error fetching jobs: {e}")
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/marketplace')
# def marketplace_jobs():
#     """Serve the Marketplace Jobs page (list view)"""
#     return send_from_directory('templates', 'marketplace.html')


# @app.route('/scraper')
# def scraper_page():
#     """Serve the Scraper UI page"""
#     return send_from_directory('templates', 'scraper.html')


# if __name__ == '__main__':
#     os.makedirs('static/downloads', exist_ok=True)
#     print("🚀 Starting LinkedIn Job Scraper")
#     print("🌐 Web Interface: http://localhost:5000")
#     print(f"🗄️  Database: {os.getenv('DB_NAME')} ({os.getenv('DB_HOST')}:{os.getenv('DB_PORT')})")
#     app.run(host='0.0.0.0', port=5000, debug=True)



#!/usr/bin/env python3
"""
Enhanced Flask app with Add New Job functionality
"""

import os
import sys
import json
import subprocess
import tempfile
import threading
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from job_scraper import LinkedInJobScraper  # Using improved scraper
from database import JobDatabase

# Load environment variables from .env
load_dotenv()

# Flask setup
app = Flask(__name__, static_folder='static')
CORS(app)

# Initialize database using secrets from .env
db = JobDatabase()

# In-memory job tracking
active_jobs = {}
job_results = {}

@app.route('/')
def index():
    """Serve main HTML page"""
    return send_from_directory('templates', 'marketplace.html')

@app.route('/api/scrape', methods=['POST'])
def scrape_jobs():
    """Start a scraping job with improved scraper"""
    data = request.json
    keywords = data.get('keywords', '')
    location = data.get('location', '')
    limit = int(data.get('limit', 25))
    experience = data.get('experience', None)
    job_type = data.get('job_type', None)
    headless = data.get('headless', True)
    fast = data.get('fast', False)

    if not keywords or not location:
        return jsonify({'success': False, 'error': 'Keywords and location are required'}), 400

    job_id = f"job_{int(datetime.now().timestamp())}"

    active_jobs[job_id] = {
        'status': 'running',
        'progress': 0,
        'message': 'Starting improved job scraper...',
        'parameters': {
            'keywords': keywords,
            'location': location,
            'limit': limit,
            'experience': experience,
            'job_type': job_type
        }
    }

    thread = threading.Thread(
        target=run_improved_scraper,
        args=(job_id, keywords, location, limit, experience, job_type, headless, not fast)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': 'Improved scraping job started'
    })

def run_improved_scraper(job_id, keywords, location, limit, experience, job_type, headless, slow_mode):
    """Run improved LinkedIn scraper in a thread"""
    try:
        if job_id not in active_jobs:
            print(f"⚠️ Warning: Job {job_id} not found in active_jobs")
            return

        active_jobs[job_id].update({
            'status': 'running',
            'progress': 5,
            'message': 'Initializing improved scraper...'
        })

        # Use improved scraper
        scraper = LinkedInJobScraper(headless=headless, slow_mode=slow_mode)

        active_jobs[job_id].update({
            'progress': 10,
            'message': f'Searching for {keywords} jobs in {location} with better accuracy...'
        })

        jobs_df = scraper.search_jobs(
            keywords=keywords,
            location=location,
            limit=limit,
            experience_level=experience,
            job_type=job_type
        )

        if not jobs_df.empty:
            active_jobs[job_id].update({
                'progress': 70,
                'message': 'Processing enhanced job data...'
            })

            jobs_list = jobs_df.to_dict('records')
            job_results[job_id] = jobs_list

            search_params = {
                'keywords': keywords,
                'location': location,
                'limit': limit,
                'experience_level': experience,
                'job_type': job_type
            }

            # Save to database
            try:
                db_saved = db.save_jobs(jobs_list, search_params)
                if db_saved:
                    print(f"✅ Saved {len(jobs_list)} jobs to DB")
                else:
                    print("❌ Failed to save jobs to DB")
            except Exception as db_error:
                print(f"❌ Database error: {db_error}")
                db_saved = False

            # Save files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs('static/downloads', exist_ok=True)
            csv_filename = f"improved_linkedin_jobs_{timestamp}.csv"
            excel_filename = f"improved_linkedin_jobs_{timestamp}.xlsx"
            jobs_df.to_csv(f"static/downloads/{csv_filename}", index=False)
            jobs_df.to_excel(f"static/downloads/{excel_filename}", index=False)

            # Calculate quality stats
            skills_count = sum(1 for job in jobs_list if job.get('extracted_skills') and job.get('extracted_skills') != 'N/A')
            company_info_count = sum(1 for job in jobs_list if job.get('company_about') and job.get('company_about') != 'N/A')
            salary_count = sum(1 for job in jobs_list if job.get('salary_range') and job.get('salary_range') != 'N/A')

            active_jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'message': f"Successfully scraped {len(jobs_df)} jobs with enhanced data!",
                'files': {'csv': csv_filename, 'excel': excel_filename},
                'database_saved': db_saved,
                'quality_stats': {
                    'total_jobs': len(jobs_df),
                    'jobs_with_skills': skills_count,
                    'jobs_with_company_info': company_info_count,
                    'jobs_with_salary': salary_count,
                    'companies': jobs_df['company'].nunique(),
                    'locations': jobs_df['location'].nunique()
                }
            })
        else:
            active_jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'No jobs found matching your criteria',
            })
            job_results[job_id] = []

    except Exception as e:
        if job_id in active_jobs:
            active_jobs[job_id].update({
                'status': 'error',
                'progress': 100,
                'message': f'Error: {str(e)}'
            })
        print(f"❌ Error in job {job_id}: {e}")

@app.route('/api/status/<job_id>', methods=['GET'])
def job_status(job_id):
    """Get scraping job status"""
    if job_id not in active_jobs:
        return jsonify({'success': False, 'error': 'Job not found'}), 404
    return jsonify({'success': True, 'status': active_jobs[job_id]})

@app.route('/api/results/<job_id>', methods=['GET'])
def job_results_api(job_id):
    """Get completed job results"""
    if job_id not in job_results:
        return jsonify({'success': False, 'error': 'Results not found'}), 404
    return jsonify({'success': True, 'results': job_results[job_id]})

@app.route('/downloads/<filename>')
def download_file(filename):
    """Serve downloaded files"""
    return send_from_directory('static/downloads', filename)

@app.route('/api/export/csv/<job_id>', methods=['GET'])
def export_csv(job_id):
    """Export job results to CSV"""
    if job_id not in job_results:
        return jsonify({'success': False, 'error': 'Results not found'}), 404

    df = pd.DataFrame(job_results[job_id])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"improved_linkedin_jobs_{timestamp}.csv"
    os.makedirs('static/downloads', exist_ok=True)
    df.to_csv(f"static/downloads/{filename}", index=False)

    return jsonify({'success': True, 'file_url': f'/downloads/{filename}'})

@app.route('/api/export/excel/<job_id>', methods=['GET'])
def export_excel(job_id):
    """Export job results to Excel"""
    if job_id not in job_results:
        return jsonify({'success': False, 'error': 'Results not found'}), 404

    df = pd.DataFrame(job_results[job_id])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"improved_linkedin_jobs_{timestamp}.xlsx"
    os.makedirs('static/downloads', exist_ok=True)
    df.to_excel(f"static/downloads/{filename}", index=False)

    return jsonify({'success': True, 'file_url': f'/downloads/{filename}'})

@app.route('/api/jobs', methods=['GET'])
def get_all_jobs():
    """Fetch all jobs with enhanced data (handles missing columns gracefully)"""
    try:
        cursor = db.conn.cursor()
        
        # First, check which columns exist
        if db.db_type == "postgres":
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'jobs'
            """)
        else:
            cursor.execute("PRAGMA table_info(jobs)")
        
        existing_columns = [row[0] if db.db_type == "postgres" else row[1] for row in cursor.fetchall()]
        
        # Build query based on available columns
        base_columns = [
            'id', 'title', 'company', 'location', 'posted_time', 
            'description', 'employment_type', 'seniority_level', 'industries', 'job_function',
            'company_url', 'company_logo', 'company_about', 'company_stats',
            'job_url', 'keywords', 'search_location', 'scraped_at'
        ]
        
        enhanced_columns = ['extracted_skills', 'salary_range', 'applicant_count']
        
        # Add enhanced columns if they exist
        select_columns = base_columns.copy()
        for col in enhanced_columns:
            if col in existing_columns:
                select_columns.append(col)
        
        query = f"""
            SELECT {', '.join(select_columns)}
            FROM jobs
            ORDER BY scraped_at DESC
            LIMIT 100
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()

        jobs = []
        for row in rows:
            job = {
                'id': row[0],
                'title': row[1],
                'company': row[2],
                'location': row[3],
                'posted_time': row[4],
                'description': row[5] or "No description available",
                'employment_type': row[6],
                'seniority_level': row[7],
                'industries': row[8],
                'job_function': row[9],
                'company_url': row[10],
                'company_logo': row[11],
                'company_about': row[12],
                'company_stats': row[13],
                'job_url': row[14],
                'keywords': row[15],
                'search_location': row[16],
                'scraped_at': row[17].isoformat() if row[17] else None,
            }
            
            # Add enhanced fields if available
            col_index = 18
            if 'extracted_skills' in existing_columns:
                job['extracted_skills'] = row[col_index] if len(row) > col_index else None
                col_index += 1
            
            if 'salary_range' in existing_columns:
                job['salary_range'] = row[col_index] if len(row) > col_index else None
                col_index += 1
                
            if 'applicant_count' in existing_columns:
                job['applicant_count'] = row[col_index] if len(row) > col_index else None

            jobs.append(job)

        return jsonify({'success': True, 'jobs': jobs}), 200

    except Exception as e:
        print(f"❌ Error fetching jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs', methods=['POST'])
def add_new_job():
    """Add a new job manually to the database"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['title', 'company', 'location', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'error': f'{field.title()} is required'
                }), 400
        
        # Prepare job data
        job_data = {
            'title': data.get('title'),
            'company': data.get('company'),
            'location': data.get('location'),
            'posted_time': data.get('posted_time', datetime.now().strftime('%Y-%m-%d')),
            'description': data.get('description'),
            'employment_type': data.get('employment_type'),
            'seniority_level': data.get('seniority_level'),
            'industries': data.get('industries'),
            'job_function': data.get('job_function'),
            'company_url': data.get('company_url'),
            'company_logo': data.get('company_logo'),
            'company_about': data.get('company_about'),
            'company_stats': data.get('company_stats', ''),
            'job_url': data.get('job_url', ''),
            'extracted_skills': data.get('extracted_skills'),
            'salary_range': data.get('salary_range'),
            'applicant_count': data.get('applicant_count'),
        }
        
        # Search parameters for manual entries
        search_params = {
            'keywords': 'manual_entry',
            'location': data.get('location'),
            'limit': 1,
            'experience_level': data.get('seniority_level'),
            'job_type': data.get('employment_type')
        }
        
        # Save to database
        success = db.save_jobs([job_data], search_params)
        
        if success:
            print(f"✅ Manual job added: {job_data['title']} at {job_data['company']}")
            return jsonify({
                'success': True, 
                'message': 'Job added successfully',
                'job': job_data
            }), 201
        else:
            return jsonify({
                'success': False, 
                'error': 'Failed to save job to database'
            }), 500
            
    except Exception as e:
        print(f"❌ Error adding job: {e}")
        return jsonify({
            'success': False, 
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/marketplace')
def marketplace_jobs():
    """Serve the Marketplace Jobs page"""
    return send_from_directory('templates', 'marketplace.html')

@app.route('/scraper')
def scraper_page():
    """Serve the Scraper UI page"""
    return send_from_directory('templates', 'scraper.html')

if __name__ == '__main__':
    os.makedirs('static/downloads', exist_ok=True)
    print("🚀 Starting Enhanced LinkedIn Job Scraper with Manual Job Entry")
    print("🌐 Web Interface: http://localhost:5000")
    print("📊 Enhanced scraping with better accuracy and data extraction")
    print("➕ Manual job entry feature available")
    print(f"🗄️ Database: {os.getenv('DB_NAME', 'SQLite')} ({os.getenv('DB_HOST', 'local')}:{os.getenv('DB_PORT', 'N/A')})")
    app.run(host='0.0.0.0', port=5000, debug=True)