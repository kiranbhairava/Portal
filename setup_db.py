#!/usr/bin/env python3
"""
Database setup script for LinkedIn Job Scraper
This script helps create the PostgreSQL database and user if they don't exist.
"""

import os
import sys
import getpass
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create the PostgreSQL database and user if they don't exist"""
    
    print("LinkedIn Job Scraper - Database Setup")
    print("=" * 40)
    
    # Get PostgreSQL admin credentials
    print("\nEnter PostgreSQL admin credentials (usually 'postgres' user):")
    admin_user = input("Admin username (default: postgres): ").strip() or 'postgres'
    admin_password = getpass.getpass("Admin password: ")
    host = input("Database host (default: localhost): ").strip() or 'localhost'
    port = input("Database port (default: 5432): ").strip() or '5432'
    
    # Database and user to create
    db_name = input("\nDatabase name (default: linkedin_jobs): ").strip() or 'linkedin_jobs'
    db_user = input("Database user (default: linkedin_user): ").strip() or 'linkedin_user'
    db_password = getpass.getpass("Database password: ")
    
    try:
        # Connect to PostgreSQL server
        print(f"\nConnecting to PostgreSQL server at {host}:{port}...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password,
            database='postgres'  # Connect to default database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
        db_exists = cursor.fetchone()
        
        if not db_exists:
            print(f"Creating database '{db_name}'...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print("✓ Database created successfully")
        else:
            print(f"✓ Database '{db_name}' already exists")
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (db_user,))
        user_exists = cursor.fetchone()
        
        if not user_exists:
            print(f"Creating user '{db_user}'...")
            cursor.execute(f"CREATE USER \"{db_user}\" WITH PASSWORD %s", (db_password,))
            print("✓ User created successfully")
        else:
            print(f"✓ User '{db_user}' already exists")
        
        # Grant privileges
        print("Granting privileges...")
        cursor.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO "{db_user}"')
        
        # Connect to the target database and grant schema privileges
        cursor.close()
        conn.close()
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password,
            database=db_name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(f'GRANT ALL ON SCHEMA public TO "{db_user}"')
        cursor.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{db_user}"')
        cursor.execute(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{db_user}"')
        cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{db_user}"')
        cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{db_user}"')
        
        print("✓ Privileges granted successfully")
        
        cursor.close()
        conn.close()
        
        # Create environment file
        env_content = f"""# LinkedIn Job Scraper Database Configuration
DB_HOST={host}
DB_PORT={port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("\n✓ Database setup completed successfully!")
        print(f"✓ Configuration saved to .env file")
        print(f"\nDatabase details:")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Database: {db_name}")
        print(f"  User: {db_user}")
        print(f"\nYou can now run the application with:")
        print(f"  python connector.py")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)