import json
from pathlib import Path
from typing import Dict, Optional, List

from services.analysis.analysis_data import AnalysisData


class BaseTestHelper:
    """
    Base test helper class providing common functionality for test classes.
    
    Provides methods for:
    - Finding test directories with source and search files
    - Loading search terms from .txt or .docx files
    - Loading expected results from result.json
    
    Note: This class is not a test class itself, so it doesn't start with 'Test'
    to avoid pytest collection warnings.
    """
    
    test_data_subdir: str = ''
    results_subdir: str = ''
    
    @property
    def test_data_dir(self) -> Path:
        """Get test data directory based on test_data_subdir class attribute."""
        if not self.test_data_subdir:
            raise ValueError("test_data_subdir must be set as class attribute")
        return Path(__file__).parent / 'data' / self.test_data_subdir
    
    @property
    def results_dir(self) -> Path:
        """Get results directory based on results_subdir class attribute."""
        if not self.results_subdir:
            raise ValueError("results_subdir must be set as class attribute")
        return Path(__file__).parent.parent.parent / 'results' / 'test' / self.results_subdir

    def get_test_directories(
            self,
            source_filename: str = 'source.docx',
            search_filenames: Optional[List[str]] = None
    ) -> List[Path]:
        """
        Get all test subdirectories from test_data_dir.
        
        Args:
            source_filename: Name of the source file to look for (default: 'source.docx')
            search_filenames: List of possible search file names to look for.
                            If None, defaults to ['search.txt']
        
        Returns:
            List of Path objects to test directories that contain required files
        """
        if search_filenames is None:
            search_filenames = ['search.txt']

        if not self.test_data_dir.exists():
            return []

        test_dirs = []

        for subdir in self.test_data_dir.iterdir():
            if not subdir.is_dir():
                continue

            source_path = subdir / source_filename
            if not source_path.exists():
                continue

            has_search_file = any((subdir / search_file).exists() for search_file in search_filenames)
            if not has_search_file:
                continue

            test_dirs.append(subdir)

        return test_dirs

    def find_search_file(self, test_dir: Path, search_filenames: Optional[List[str]] = None) -> Path:
        """
        Find search file in test directory.
        
        Args:
            test_dir: Path to test directory
            search_filenames: List of possible search file names.
                            If None, defaults to ['search.txt', 'search.docx']
        
        Returns:
            Path to the found search file
        
        Raises:
            FileNotFoundError: If no search file is found
        """
        if search_filenames is None:
            search_filenames = ['search.txt', 'search.docx']

        for search_filename in search_filenames:
            search_path = test_dir / search_filename
            if search_path.exists():
                return search_path

        raise FileNotFoundError(
            f"Search file not found in {test_dir}. "
            f"Expected one of: {', '.join(search_filenames)}"
        )

    def load_search_terms(self, search_path: Path) -> List[str]:
        """
        Load search terms from search.txt or search.docx file.
        
        Args:
            search_path: Path to search file (.txt or .docx)
        
        Returns:
            List of search terms (strings)
        
        Raises:
            AssertionError: If no search terms found
        """
        if search_path.suffix == '.docx':
            analyse_data = AnalysisData()
            analyse_data.read_from_docx(str(search_path))
            search_terms = list(analyse_data.tokens.keys())
        else:
            with open(search_path, 'r', encoding='utf-8') as f:
                search_terms = [line.strip() for line in f if line.strip()]

        assert len(search_terms) > 0, f"No search terms found in {search_path.name}"
        return search_terms

    def load_expected_results(self, test_dir: Path) -> Optional[Dict]:
        """
        Load expected results from result.json if it exists.
        
        Args:
            test_dir: Path to test directory
        
        Returns:
            Dictionary with expected results or None if result.json doesn't exist
        """
        result_json_path = test_dir / 'result.json'

        if not result_json_path.exists():
            return None

        with open(result_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def validate_test_directory(
            self,
            test_dir: Path,
            source_filename: str = 'source.docx',
            search_filenames: Optional[List[str]] = None
    ) -> None:
        """
        Validate that test directory contains required files.
        
        Args:
            test_dir: Path to test directory
            source_filename: Name of the source file (default: 'source.docx')
            search_filenames: List of possible search file names.
                            If None, defaults to ['search.txt', 'search.docx']
        
        Raises:
            ValueError: If directory is missing required files
        """
        if not test_dir.exists() or not test_dir.is_dir():
            raise ValueError(f"Test directory not found: {test_dir}")

        source_path = test_dir / source_filename
        if not source_path.exists():
            raise ValueError(f"Test directory {test_dir.name} is missing required file ({source_filename})")

        if search_filenames is None:
            search_filenames = ['search.txt', 'search.docx']

        has_search_file = any((test_dir / search_file).exists() for search_file in search_filenames)
        if not has_search_file:
            raise ValueError(
                f"Test directory {test_dir.name} is missing required file "
                f"(one of: {', '.join(search_filenames)})"
            )


class BaseTest(BaseTestHelper):
    """
    Base test class for pytest test classes.
    
    This class extends BaseTestHelper and provides properties for test_data_dir
    and results_dir based on class attributes test_data_subdir and results_subdir.
    
    Test classes should inherit from this class and set test_data_subdir and
    results_subdir as class attributes instead of using __init__.
    """