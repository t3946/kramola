from pathlib import Path


class FileLoaderMixin:
    """Mixin for loading search terms from files and validating test files."""

    def load_search_terms_from_file(self, path: Path) -> list[str]:
        """
        Load search terms from text file.
        
        Args:
            path: Path to search.txt file
            
        Returns:
            List of search terms (non-empty lines)
            
        Raises:
            AssertionError: If no search terms found
        """
        with open(path, 'r', encoding='utf-8') as f:
            search_terms: list[str] = [line.strip() for line in f if line.strip()]

        assert len(search_terms) > 0, f"No search terms found in {path}"
        return search_terms

    def validate_test_files(self, source_path: Path, search_path: Path) -> None:
        """
        Validate that test files exist.
        
        Args:
            source_path: Path to source PDF file
            search_path: Path to search.txt file
            
        Raises:
            AssertionError: If files don't exist
        """
        assert source_path.exists(), f"Source PDF not found: {source_path}"
        assert search_path.exists(), f"Search file not found: {search_path}"

