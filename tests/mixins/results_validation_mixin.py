import json
from pathlib import Path
from typing import Dict


class ResultsValidationMixin:
    """Mixin for validating analysis results."""

    def validate_results_structure(self, results: Dict) -> None:
        """
        Validate basic structure of analysis results.
        
        Args:
            results: Analysis results dictionary
            
        Raises:
            AssertionError: If structure is invalid
        """
        assert results is not None, "Analysis returned None"
        assert 'word_stats' in results, "Missing word_stats in results"
        assert 'phrase_stats' in results, "Missing phrase_stats in results"
        assert 'total_matches' in results, "Missing total_matches in results"
        assert isinstance(results['total_matches'], int), "total_matches should be int"

    def validate_expected_count(self, results: Dict, result_json_path: Path) -> None:
        """
        Validate that total_matches matches expected count from result.json.
        
        Args:
            results: Analysis results dictionary
            result_json_path: Path to result.json file with expected count
            
        Raises:
            AssertionError: If count doesn't match or file doesn't exist
        """
        assert result_json_path.exists(), f"Result JSON file not found: {result_json_path}"

        with open(result_json_path, 'r', encoding='utf-8') as f:
            expected_results = json.load(f)

        assert 'total_matches' in expected_results, (
            f"Missing 'total_matches' in {result_json_path}"
        )

        expected_count = expected_results['total_matches']
        actual_count = results['total_matches']
        assert actual_count == expected_count, (
            f"Expected {expected_count} matches, but got {actual_count}"
        )
