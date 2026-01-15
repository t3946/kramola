from pathlib import Path

from services.document_service import extract_lines_from_docx
from tests.mixins.analysis_setup_mixin import AnalysisSetupMixin
from tests.mixins.file_loader_mixin import FileLoaderMixin
from tests.mixins.results_validation_mixin import ResultsValidationMixin
from tests.mixins.save_output_mixin import SaveOutputMixin
from tests.mixins.test_output_mixin import TestOutputMixin


class BasePdfLongListsTest(
    FileLoaderMixin,
    AnalysisSetupMixin,
    ResultsValidationMixin,
    SaveOutputMixin,
    TestOutputMixin
):
    """Base class for PDF long-lists tests."""

    def _get_results_subdir(self, test_file_path: Path) -> str:
        """Get subdirectory name for results from test file path."""
        return test_file_path.parent.name

    @classmethod
    def run_test(cls, test_file_path: Path) -> None:
        """
        Run complete PDF long-lists analysis test.

        Args:
            test_file_path: Path to the test file (use Path(__file__) in test function)
        """
        instance = cls()
        test_dir = test_file_path.parent / 'data'
        source_pdf_path = test_dir / 'source.pdf'
        search_txt_path = test_dir / 'search.txt'
        source_docx_path = test_dir / 'source.docx'
        result_json_path = test_dir / 'result.json'

        assert source_pdf_path.exists(), f"Source PDF not found: {source_pdf_path}"

        if search_txt_path.exists():
            instance.validate_test_files(source_pdf_path, search_txt_path)

            search_terms = instance.load_search_terms_from_file(search_txt_path)
        else:
            assert source_docx_path.exists(), (
                f"Search terms file not found: {search_txt_path} and {source_docx_path}"
            )

            search_terms = extract_lines_from_docx(str(source_docx_path))

            assert len(search_terms) > 0, f"No search terms found in {source_docx_path}"

        analyser, analysis_results = instance.setup_analysis(source_pdf_path, search_terms)

        results_subdir = instance._get_results_subdir(test_file_path)
        output_pdf_path, stats_json_path = instance.save_analysis_results(
            analyser,
            analysis_results,
            results_subdir
        )

        instance.validate_results_structure(analysis_results)
        instance.validate_expected_count(analysis_results, result_json_path)

        instance.print_test_results(
            analysis_results,
            search_terms,
            output_pdf_path,
            stats_json_path
        )

