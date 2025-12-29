from pathlib import Path
from typing import Dict


class TestOutputMixin:
    """Mixin for printing test results."""

    def print_test_results(
        self,
        results: Dict,
        search_terms: list[str],
        stats_key: str,
        entity_name: str,
        output_pdf_path: Path,
        stats_json_path: Path
    ) -> None:
        """
        Print formatted test results.
        
        Args:
            results: Analysis results dictionary
            search_terms: List of search terms used
            stats_key: Key in results ('word_stats' or 'phrase_stats')
            entity_name: Name of entity type ('words' or 'sentences')
            output_pdf_path: Path to output PDF file
            stats_json_path: Path to stats JSON file
        """
        stats = results[stats_key]

        print(f"Test passed: Found {results['total_matches']} matches")
        print(f"  Search terms: {search_terms}")
        print(f"  {entity_name.capitalize()} stats keys (lemmas): {list(stats.keys())}")
        print(f"  Output PDF: {output_pdf_path}")
        print(f"  Stats JSON: {stats_json_path}")

