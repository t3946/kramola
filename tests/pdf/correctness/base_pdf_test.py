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
        result_json_path = test_dir / 'result.json'

        instance.validate_test_files(source_pdf_path, search_txt_path)

        search_terms = instance.load_search_terms_from_file(search_txt_path)

        analyser, analysis_results = instance.setup_analysis(source_pdf_path, search_terms)

        instance.validate_results_structure(analysis_results)
        instance.validate_expected_count(analysis_results, result_json_path)

        results_subdir = instance._get_results_subdir(test_file_path)
        output_pdf_path, stats_json_path = instance.save_analysis_results(
            analyser,
            analysis_results,
            results_subdir
        )

        instance.print_test_results(
            analysis_results,
            search_terms,
            output_pdf_path,
            stats_json_path
        )
