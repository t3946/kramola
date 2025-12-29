from pathlib import Path

from tests.mixins.analysis_setup_mixin import AnalysisSetupMixin
from tests.mixins.file_loader_mixin import FileLoaderMixin
from tests.mixins.results_validation_mixin import ResultsValidationMixin
from tests.mixins.save_output_mixin import SaveOutputMixin
from tests.mixins.test_output_mixin import TestOutputMixin


class BasePdfTest(
    FileLoaderMixin,
    AnalysisSetupMixin,
    ResultsValidationMixin,
    SaveOutputMixin,
    TestOutputMixin
):
    """Base class for PDF correctness tests."""

    def _get_results_subdir(self, test_file_path: Path) -> str:
        """Get subdirectory name for results from test file path."""
        return test_file_path.parent.name

    def _get_stats_key(self, test_file_path: Path) -> str:
        """Get stats key to check based on directory name."""
        dir_name = test_file_path.parent.name.lower()
        
        if 'word' in dir_name:
            return 'word_stats'
        elif 'sentence' in dir_name:
            return 'phrase_stats'
        
        raise ValueError(f"Cannot determine stats_key from directory name: {dir_name}")

    def _get_entity_name(self, test_file_path: Path) -> str:
        """Get entity name for messages based on directory name."""
        dir_name = test_file_path.parent.name.lower()
        
        if 'word' in dir_name:
            return 'words'
        elif 'sentence' in dir_name:
            return 'sentences'
        
        raise ValueError(f"Cannot determine entity_name from directory name: {dir_name}")

    @classmethod
    def run_test(cls, test_file_path: Path) -> None:
        """
        Run complete PDF analysis test.
        
        Args:
            test_file_path: Path to the test file (use Path(__file__) in test function)
        """
        instance = cls()
        test_dir = test_file_path.parent / 'data'
        source_pdf_path = test_dir / 'source.pdf'
        search_txt_path = test_dir / 'search.txt'

        instance.validate_test_files(source_pdf_path, search_txt_path)

        search_terms = instance.load_search_terms_from_file(search_txt_path)

        analyser, analysis_results = instance.setup_analysis(source_pdf_path, search_terms)

        instance.validate_results_structure(analysis_results)

        stats_key = instance._get_stats_key(test_file_path)
        entity_name = instance._get_entity_name(test_file_path)

        instance.validate_search_terms_found(
            analysis_results,
            search_terms,
            stats_key,
            entity_name
        )

        results_subdir = instance._get_results_subdir(test_file_path)
        output_pdf_path, stats_json_path = instance.save_analysis_results(
            analyser,
            analysis_results,
            results_subdir
        )

        instance.print_test_results(
            analysis_results,
            search_terms,
            stats_key,
            entity_name,
            output_pdf_path,
            stats_json_path
        )

