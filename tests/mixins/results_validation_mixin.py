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

    def validate_search_terms_found(
        self,
        results: Dict,
        search_terms: list[str],
        stats_key: str,
        entity_name: str
    ) -> None:
        """
        Validate that all search terms were found in results.
        
        Args:
            results: Analysis results dictionary
            search_terms: List of search terms that should be found
            stats_key: Key in results to check ('word_stats' or 'phrase_stats')
            entity_name: Name of entity type for error messages ('words' or 'sentences')
            
        Raises:
            AssertionError: If terms not found or no matches
        """
        stats = results[stats_key]

        assert results['total_matches'] > 0, (
            f"No matches found. Expected to find {entity_name} from {search_terms}"
        )

        for search_term in search_terms:
            search_term_lower = search_term.lower()
            term_found = False

            for lemma, stats_data in stats.items():
                if lemma.lower() == search_term_lower:
                    term_found = True
                    break

                forms = stats_data.get('forms', {})
                if any(form.lower() == search_term_lower for form in forms.keys()):
                    term_found = True
                    break

            assert term_found, f"{entity_name.capitalize()} '{search_term}' not found in PDF"

