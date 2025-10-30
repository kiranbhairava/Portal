# database.py
import os
import psycopg2
from psycopg2.extras import execute_batch
import sqlite3

class JobDatabase:
    def __init__(self):
        """Initialize DB connection (Postgres or fallback to SQLite)."""
        self.db_type = os.getenv("DB_TYPE", "sqlite")  # 'postgres' or 'sqlite'

        if self.db_type == "postgres":
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                database=os.getenv("DB_NAME", "linkedin_jobs"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres"),
                port=os.getenv("DB_PORT", "5432")
            )
        else:
            os.makedirs("data", exist_ok=True)
            self.conn = sqlite3.connect("data/linkedin_jobs.db")

        self.create_tables()

    def create_tables(self):
        """Create jobs table with extended company/job fields."""
        cursor = self.conn.cursor()

        if self.db_type == "postgres":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    posted_time TEXT,
                    description TEXT,
                    employment_type TEXT,
                    seniority_level TEXT,
                    industries TEXT,
                    job_function TEXT,
                    company_url TEXT,
                    company_logo TEXT,
                    company_about TEXT,
                    company_stats TEXT,
                    job_url TEXT UNIQUE,
                    keywords TEXT,
                    search_location TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    posted_time TEXT,
                    description TEXT,
                    employment_type TEXT,
                    seniority_level TEXT,
                    industries TEXT,
                    job_function TEXT,
                    company_url TEXT,
                    company_logo TEXT,
                    company_about TEXT,
                    company_stats TEXT,
                    job_url TEXT UNIQUE,
                    keywords TEXT,
                    search_location TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        self.conn.commit()
        cursor.close()

    def save_jobs(self, jobs_list, search_params):
        """Save scraped jobs (with extended metadata) to DB."""
        if not jobs_list:
            print("⚠️ No jobs to save to DB.")
            return False

        cursor = self.conn.cursor()

        insert_query = """
            INSERT INTO jobs (
                title, company, location, posted_time, description,
                employment_type, seniority_level, industries, job_function,
                company_url, company_logo, company_about, company_stats,
                job_url, keywords, search_location
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_url) DO NOTHING
        """ if self.db_type == "postgres" else """
            INSERT OR IGNORE INTO jobs (
                title, company, location, posted_time, description,
                employment_type, seniority_level, industries, job_function,
                company_url, company_logo, company_about, company_stats,
                job_url, keywords, search_location
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # Prepare values
        values = [
            (
                job.get("title"),
                job.get("company"),
                job.get("location"),
                job.get("posted_time"),
                job.get("description"),
                job.get("employment_type"),
                job.get("seniority_level"),
                job.get("industries"),
                job.get("job_function"),
                job.get("company_url"),
                job.get("company_logo"),
                job.get("company_about"),
                job.get("company_stats"),
                job.get("job_url"),
                search_params.get("keywords"),
                search_params.get("location")
            )
            for job in jobs_list
        ]

        try:
            execute_batch(cursor, insert_query, values)
            self.conn.commit()
            print(f"✅ Saved {len(jobs_list)} jobs to database.")
            return True
        except Exception as e:
            print(f"❌ Error saving to DB: {e}")
            self.conn.rollback()
            return False
        finally:
            cursor.close()

    def fetch_all_jobs(self):
        """Fetch all stored jobs (latest first)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT title, company, location, posted_time, job_url
            FROM jobs
            ORDER BY scraped_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def close(self):
        """Close DB connection."""
        if self.conn:
            self.conn.close()
