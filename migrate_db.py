#!/usr/bin/env python3
"""
Database Migration Script
Adds the new columns for improved job scraper
"""

import os
import psycopg2
import sqlite3
from dotenv import load_dotenv

load_dotenv()

def migrate_database():
    """Add new columns to existing jobs table"""
    
    db_type = os.getenv("DB_TYPE", "sqlite")
    
    print("🔧 Starting database migration...")
    
    if db_type == "postgres":
        # PostgreSQL migration
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                database=os.getenv("DB_NAME", "linkedin_jobs"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres"),
                port=os.getenv("DB_PORT", "5432")
            )
            
            cursor = conn.cursor()
            
            # Check if columns already exist
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'jobs' AND column_name IN ('extracted_skills', 'salary_range', 'applicant_count')
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            # Add missing columns
            new_columns = {
                'extracted_skills': 'TEXT',
                'salary_range': 'TEXT', 
                'applicant_count': 'TEXT'
            }
            
            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    print(f"  ➕ Adding column: {column_name}")
                    cursor.execute(f"ALTER TABLE jobs ADD COLUMN {column_name} {column_type}")
                else:
                    print(f"  ✅ Column already exists: {column_name}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ PostgreSQL migration completed!")
            
        except Exception as e:
            print(f"❌ PostgreSQL migration failed: {e}")
            return False
            
    else:
        # SQLite migration
        try:
            os.makedirs("data", exist_ok=True)
            conn = sqlite3.connect("data/linkedin_jobs.db")
            cursor = conn.cursor()
            
            # Check if columns exist
            cursor.execute("PRAGMA table_info(jobs)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            # Add missing columns
            new_columns = ['extracted_skills', 'salary_range', 'applicant_count']
            
            for column_name in new_columns:
                if column_name not in existing_columns:
                    print(f"  ➕ Adding column: {column_name}")
                    cursor.execute(f"ALTER TABLE jobs ADD COLUMN {column_name} TEXT")
                else:
                    print(f"  ✅ Column already exists: {column_name}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ SQLite migration completed!")
            
        except Exception as e:
            print(f"❌ SQLite migration failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = migrate_database()
    
    if success:
        print("\n🎉 Database migration successful!")
        print("You can now run your improved app:")
        print("  python app.py")
    else:
        print("\n💥 Migration failed. Check the error messages above.")