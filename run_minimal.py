"""
Simplified script to run Lyra with minimal dependencies
"""
import os
import sys
from pathlib import Path

def setup_paths():
    """Add necessary directories to Python path"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(project_root, "src")
    
    # Ensure src is in the path
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        
    # Ensure project root is in the path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print(f"Python path: {sys.path}")
    
def ensure_required_dirs():
    """Ensure all required directories exist"""
    dirs = [
        "src/lyra",
        "src/lyra/memory",
        "src/lyra/integration",
        "actions"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py if it doesn't exist
        init_file = os.path.join(dir_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f'"""\n{dir_path} module\n"""\n')

def run_minimal():
    """Run Lyra with minimal functionality"""
    setup_paths()
    ensure_required_dirs()
    
    # Check environment
    try:
        import numpy
        print("✅ NumPy is available")
    except ImportError:
        print("❌ NumPy is not installed. Using fallbacks.")
        
    # Try to run main
    try:
        from lyra.main import main
        print("\n🚀 Starting Lyra in minimal mode...\n")
        main()
    except ImportError as e:
        print(f"❌ Error importing Lyra main module: {e}")
        print("\nTry running setup_environment.py first to install all dependencies")
    except Exception as e:
        print(f"❌ Error running Lyra: {e}")
        
if __name__ == "__main__":
    run_minimal()
