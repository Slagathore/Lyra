"""
Helper script to verify and fix the database
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def install_required_packages():
    """Install required packages if missing"""
    print("Checking and installing required packages...")
    # Try importing sqlalchemy
    try:
        import sqlalchemy
        print("SQLAlchemy is already installed.")
    except ImportError:
        print("Installing SQLAlchemy...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "sqlalchemy<2.0.0", "sqlalchemy-utils"])
        print("SQLAlchemy installed successfully.")
        try:
            import sqlalchemy
        except ImportError as e:
            print(f"Failed to import SQLAlchemy after installation: {e}")
            raise

def reset_database():
    """Remove and recreate the database file"""
    # First ensure we have required packages
    install_required_packages()
    
    db_file = Path("conversation_history.db")
    
    # Check if database file exists
    if db_file.exists():
        # Backup the existing database
        backup_path = db_file.with_suffix(".db.bak")
        print(f"Backing up database to {backup_path}")
        shutil.copy2(db_file, backup_path)
        
        # Remove the existing database
        print(f"Removing existing database: {db_file}")
        db_file.unlink()
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    # Import the SQL memory manager which will recreate the database
    print("Initializing new database...")
    from lyra.memory.sql_memory_manager import init_db
    init_db()
    
    print("Database reset complete!")

if __name__ == "__main__":
    reset_database()
