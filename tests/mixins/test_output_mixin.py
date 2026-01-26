from pathlib import Path
from typing import Dict


class TestOutputMixin:
    """Mixin for printing test results."""

    def print_test_results(
        self,
        results: Dict,
        search_terms: list[str],
        output_pdf_path: Path,
        stats_json_path: Path
    ) -> None:
        """
        Print formatted test results.
        
        Args:
            results: Analysis results dictionary
            search_terms: List of search terms used
            output_pdf_path: Path to output PDF file
            stats_json_path: Path to stats JSON file
        """
        print(f"Test passed: Found {results['total_matches']} matches")
        print(f"  Search terms: {search_terms}")
        print(f"  Stats items count: {len(results['stats'])}")
        print(f"  Output PDF: {output_pdf_path}")
        print(f"  Stats JSON: {stats_json_path}")

