# import os
# import sys
# import json
# import subprocess
# import tempfile
# from flask import Flask, request, jsonify, send_from_directory, render_template
# from flask_cors import CORS
# from job_scraper import LinkedInJobScraper
# import pandas as pd
# from datetime import datetime
# import threading

# app = Flask(__name__, static_folder='static')
# CORS(app)  # Enable CORS to allow requests from any origin

# # Store scraper jobs in memory
# active_jobs = {}
# job_results = {}

# @app.route('/')
# def index():
#     """Serve the main HTML page"""
#     return send_from_directory('.', 'simple_jobs_ui.html')

# @app.route('/api/scrape', methods=['POST'])
# def scrape_jobs():
#     """API endpoint to start a scraping job"""
#     data = request.json
    
#     # Extract parameters
#     keywords = data.get('keywords', '')
#     location = data.get('location', '')
#     limit = int(data.get('limit', 25))
#     experience = data.get('experience', None)
#     job_type = data.get('job_type', None)
#     headless = data.get('headless', True)
#     fast = data.get('fast', False)
    
#     # Validate required parameters
#     if not keywords or not location:
#         return jsonify({'success': False, 'error': 'Keywords and location are required'}), 400
    
#     # Generate a job ID
#     job_id = f"job_{int(datetime.now().timestamp())}"
    
#     # Start the scraper in a new thread
#     thread = threading.Thread(
#         target=run_scraper,
#         args=(job_id, keywords, location, limit, experience, job_type, headless, not fast)
#     )
#     thread.daemon = True
#     thread.start()
    
#     # Store job status
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
    
#     return jsonify({
#         'success': True,
#         'job_id': job_id,
#         'message': 'Scraping job started'
#     })

# @app.route('/api/status/<job_id>', methods=['GET'])
# def job_status(job_id):
#     """Get the status of a scraping job"""
#     if job_id not in active_jobs:
#         return jsonify({'success': False, 'error': 'Job not found'}), 404
    
#     return jsonify({
#         'success': True,
#         'status': active_jobs[job_id]
#     })

# @app.route('/api/results/<job_id>', methods=['GET'])
# def job_results_api(job_id):
#     """Get the results of a completed job"""
#     if job_id not in job_results:
#         return jsonify({'success': False, 'error': 'Results not found'}), 404
    
#     return jsonify({
#         'success': True,
#         'results': job_results[job_id]
#     })

# def run_scraper(job_id, keywords, location, limit, experience, job_type, headless, slow_mode):
#     """Run the LinkedIn job scraper in a separate thread"""
#     try:
#         # Update job status
#         active_jobs[job_id]['status'] = 'running'
#         active_jobs[job_id]['progress'] = 5
#         active_jobs[job_id]['message'] = 'Initializing scraper...'
        
#         # Create scraper instance
#         scraper = LinkedInJobScraper(headless=headless, slow_mode=slow_mode)
        
#         # Update job status
#         active_jobs[job_id]['progress'] = 10
#         active_jobs[job_id]['message'] = f'Searching for {keywords} jobs in {location}...'
        
#         # Run the search
#         jobs_df = scraper.search_jobs(
#             keywords=keywords,
#             location=location,
#             limit=limit,
#             experience_level=experience,
#             job_type=job_type
#         )
        
#         # Process results
#         if not jobs_df.empty:
#             # Update job status
#             active_jobs[job_id]['progress'] = 90
#             active_jobs[job_id]['message'] = 'Processing results...'
            
#             # Convert DataFrame to list of dictionaries
#             jobs_list = jobs_df.to_dict('records')
            
#             # Store the results
#             job_results[job_id] = jobs_list
            
#             # Save to CSV and Excel
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             csv_filename = f"linkedin_jobs_{timestamp}.csv"
#             excel_filename = f"linkedin_jobs_{timestamp}.xlsx"
            
#             os.makedirs('static/downloads', exist_ok=True)
#             jobs_df.to_csv(f"static/downloads/{csv_filename}", index=False)
#             jobs_df.to_excel(f"static/downloads/{excel_filename}", index=False)
            
#             # Update job status
#             active_jobs[job_id]['status'] = 'completed'
#             active_jobs[job_id]['progress'] = 100
#             active_jobs[job_id]['message'] = f'Successfully scraped {len(jobs_df)} jobs'
#             active_jobs[job_id]['files'] = {
#                 'csv': csv_filename,
#                 'excel': excel_filename
#             }
#         else:
#             # Update job status for no results
#             active_jobs[job_id]['status'] = 'completed'
#             active_jobs[job_id]['progress'] = 100
#             active_jobs[job_id]['message'] = 'No jobs found matching your criteria'
#             job_results[job_id] = []
    
#     except Exception as e:
#         # Update job status for error
#         active_jobs[job_id]['status'] = 'error'
#         active_jobs[job_id]['progress'] = 100
#         active_jobs[job_id]['message'] = f'Error: {str(e)}'
#         print(f"Error in scraping job {job_id}: {str(e)}")

# @app.route('/downloads/<filename>')
# def download_file(filename):
#     """Serve the downloaded files"""
#     return send_from_directory('static/downloads', filename)

# @app.route('/api/export/csv/<job_id>', methods=['GET'])
# def export_csv(job_id):
#     """Export job results to CSV"""
#     if job_id not in job_results:
#         return jsonify({'success': False, 'error': 'Results not found'}), 404
    
#     # Create a DataFrame from the results
#     df = pd.DataFrame(job_results[job_id])
    
#     # Save to CSV
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"linkedin_jobs_{timestamp}.csv"
    
#     os.makedirs('static/downloads', exist_ok=True)
#     df.to_csv(f"static/downloads/{filename}", index=False)
    
#     return jsonify({
#         'success': True,
#         'file_url': f'/downloads/{filename}'
#     })

# @app.route('/api/export/excel/<job_id>', methods=['GET'])
# def export_excel(job_id):
#     """Export job results to Excel"""
#     if job_id not in job_results:
#         return jsonify({'success': False, 'error': 'Results not found'}), 404
    
#     # Create a DataFrame from the results
#     df = pd.DataFrame(job_results[job_id])
    
#     # Save to Excel
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"linkedin_jobs_{timestamp}.xlsx"
    
#     os.makedirs('static/downloads', exist_ok=True)
#     df.to_excel(f"static/downloads/{filename}", index=False)
    
#     return jsonify({
#         'success': True,
#         'file_url': f'/downloads/{filename}'
#     })

# if __name__ == '__main__':
#     # Create required directories
#     os.makedirs('static/downloads', exist_ok=True)
    
#     # Start the Flask app
#     app.run(host='0.0.0.0', port=5000, debug=True)


import os
import sys
import json
import subprocess
import tempfile
import threading
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv  # ✅ NEW: for .env secrets
from job_scraper import LinkedInJobScraper
from database import JobDatabase

# ✅ Load environment variables from .env
load_dotenv()

# Flask setup
app = Flask(__name__, static_folder='static')
CORS(app)

# ✅ Initialize database using secrets from .env
db = JobDatabase()

# In-memory job tracking
active_jobs = {}
job_results = {}

@app.route('/')
def index():
    """Serve main HTML page"""
    return send_from_directory('.', 'simple_jobs_ui.html')

@app.route('/api/scrape', methods=['POST'])
def scrape_jobs():
    """Start a scraping job"""
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
        'message': 'Starting job...',
        'parameters': {
            'keywords': keywords,
            'location': location,
            'limit': limit,
            'experience': experience,
            'job_type': job_type
        }
    }

    thread = threading.Thread(
        target=run_scraper,
        args=(job_id, keywords, location, limit, experience, job_type, headless, not fast)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': 'Scraping job started'
    })

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

def run_scraper(job_id, keywords, location, limit, experience, job_type, headless, slow_mode):
    """Run LinkedIn scraper in a thread"""
    try:
        if job_id not in active_jobs:
            print(f"⚠️ Warning: Job {job_id} not found in active_jobs")
            return

        active_jobs[job_id].update({
            'status': 'running',
            'progress': 5,
            'message': 'Initializing scraper...'
        })

        scraper = LinkedInJobScraper(headless=headless, slow_mode=slow_mode)

        active_jobs[job_id].update({
            'progress': 10,
            'message': f'Searching for {keywords} jobs in {location}...'
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
                'message': 'Saving jobs to database...'
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

            # ✅ Save directly to database
            try:
                db_saved = db.save_jobs(jobs_list, search_params)
                if db_saved:
                    print(f"✅ Saved {len(jobs_list)} jobs to DB")
                else:
                    print("❌ Failed to save jobs to DB")
            except Exception as db_error:
                print(f"❌ Database error: {db_error}")
                db_saved = False

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs('static/downloads', exist_ok=True)
            csv_filename = f"linkedin_jobs_{timestamp}.csv"
            excel_filename = f"linkedin_jobs_{timestamp}.xlsx"
            jobs_df.to_csv(f"static/downloads/{csv_filename}", index=False)
            jobs_df.to_excel(f"static/downloads/{excel_filename}", index=False)

            active_jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'message': f"Scraped and saved {len(jobs_df)} jobs" if db_saved else "Scraped jobs (DB save failed)",
                'files': {'csv': csv_filename, 'excel': excel_filename}
            })
        else:
            active_jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'No jobs found',
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
    filename = f"linkedin_jobs_{timestamp}.csv"
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
    filename = f"linkedin_jobs_{timestamp}.xlsx"
    os.makedirs('static/downloads', exist_ok=True)
    df.to_excel(f"static/downloads/{filename}", index=False)

    return jsonify({'success': True, 'file_url': f'/downloads/{filename}'})

@app.route('/api/jobs', methods=['GET'])
def get_all_jobs():
    """Fetch all jobs stored in DB (latest first, include full metadata)."""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT 
                id, title, company, location, posted_time, 
                description, employment_type, seniority_level, industries, job_function,
                company_url, company_logo, company_about, company_stats,
                job_url, keywords, search_location, scraped_at
            FROM jobs
            ORDER BY scraped_at DESC
            LIMIT 100
        """)
        rows = cursor.fetchall()
        cursor.close()

        # Build JSON response
        jobs = []
        for row in rows:
            jobs.append({
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
                'company_logo': row[11],  # ✅ FIXED: company logo added
                'company_about': row[12],
                'company_stats': row[13],
                'job_url': row[14],
                'keywords': row[15],
                'search_location': row[16],
                'scraped_at': row[17].isoformat() if row[17] else None,
            })

        return jsonify({'success': True, 'jobs': jobs}), 200

    except Exception as e:
        print(f"❌ Error fetching jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


        return jsonify({'success': True, 'jobs': jobs})

    except Exception as e:
        print(f"❌ Error fetching jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/marketplace')
def marketplace_jobs():
    """Serve the Marketplace Jobs page (list view)"""
    return send_from_directory('.', 'simple_jobs_ui.html')


@app.route('/scraper')
def scraper_page():
    """Serve the Scraper UI page"""
    return send_from_directory('.', 'scraper_ui.html')


if __name__ == '__main__':
    os.makedirs('static/downloads', exist_ok=True)
    print("🚀 Starting LinkedIn Job Scraper")
    print("🌐 Web Interface: http://localhost:5000")
    print(f"🗄️  Database: {os.getenv('DB_NAME')} ({os.getenv('DB_HOST')}:{os.getenv('DB_PORT')})")
    app.run(host='0.0.0.0', port=5000, debug=True)
