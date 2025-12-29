from pathlib import Path


def get_project_root() -> Path:
    """Get project root directory by searching for marker files."""
    current = Path(__file__).resolve()
    
    for parent in current.parents:
        if (parent / 'app.py').exists() or (parent / 'requirements.txt').exists():
            return parent
    
    raise RuntimeError("Could not find project root directory")

