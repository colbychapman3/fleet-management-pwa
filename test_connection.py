#!/usr/bin/env python3
"""
Test database connection script
"""
import os
import psycopg2
from urllib.parse import urlparse

def test_database_connection():
    """Test direct connection to database"""
    
    # Try the connection string
    database_url = 'postgresql://postgres:HobokenHome3!@db.mjalobwwhnrgqqlnnbfa.supabase.co:5432/postgres'
    
    print(f"Testing connection to: {database_url}")
    
    try:
        # Parse the URL
        parsed = urlparse(database_url)
        
        print(f"Host: {parsed.hostname}")
        print(f"Port: {parsed.port}")
        print(f"Database: {parsed.path[1:]}")
        print(f"Username: {parsed.username}")
        
        # Try to connect
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"Connected successfully! PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()