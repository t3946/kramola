import json
from pathlib import Path
from typing import Dict, Tuple

from services.analysis.analyser_docx import AnalyserDocx
from services.analysis.analysis_data import AnalysisData
from tests.analysis.test_base import BaseTest


class BaseDocxTest(BaseTest):
    """Base class for DOCX correctness tests. Uses test file path and data/ next to it."""

    test_data_subdir = 'docx'
    results_subdir = 'docx'

    @classmethod
    def run_test(cls, test_file_path: Path) -> None:
        """
        Run complete DOCX analysis test.

        Args:
            test_file_path: Path to the test file (use Path(__file__) in test function)
        """
        instance = cls()
        test_dir = test_file_path.parent / 'data'
        source_docx_path = test_dir / 'source.docx'
        search_txt_path = test_dir / 'search.txt'
        result_json_path = test_dir / 'result.json'

        instance.validate_test_directory(
            test_dir,
            source_filename='source.docx',
            search_filenames=['search.txt'],
            require_search=False
        )

        if search_txt_path.exists():
            search_terms = instance.load_search_terms(instance.find_search_file(test_dir, ['search.txt']))
        else:
            search_terms = []

        analyser, analysis_results = cls._run_analysis(cls, source_docx_path, search_terms)

        results_subdir = instance._get_results_subdir(test_file_path)
        output_docx_path, stats_json_path = cls._save_results(
            analyser,
            analysis_results,
            results_subdir
        )

        instance._validate_results_structure(analysis_results)
        instance._validate_expected_count(analysis_results, result_json_path)

        instance._print_test_results(
            analysis_results,
            search_terms,
            output_docx_path,
            stats_json_path
        )

    @staticmethod
    def _run_analysis(cls, source_docx_path: Path, search_terms: list[str]) -> Tuple[AnalyserDocx, Dict]:
        analyse_data = AnalysisData()
        analyse_data.read_from_list(search_terms)

        # load lists
        predefined_lists = getattr(cls, 'predefined_lists', None)
        analyse_data.load_predefined_lists(predefined_lists)

        analyser = AnalyserDocx(str(source_docx_path))
        analyser.set_analyse_data(analyse_data)
        analysis_results: Dict = analyser.analyse_and_highlight()
        return analyser, analysis_results

    def _get_results_subdir(self, test_file_path: Path) -> str:
        return test_file_path.parent.name

    def _validate_results_structure(self, results: Dict) -> None:
        assert results is not None, "Analysis returned None"
        assert 'stats' in results, "Missing stats in results"
        assert 'total_matches' in results, "Missing total_matches in results"
        assert isinstance(results['stats'], list), "stats should be list"
        assert isinstance(results['total_matches'], int), "total_matches should be int"

    def _validate_expected_count(self, results: Dict, result_json_path: Path) -> None:
        if not result_json_path.exists():
            return

        with open(result_json_path, 'r', encoding='utf-8') as f:
            expected_results = json.load(f)

        if 'total_matches' not in expected_results:
            return

        expected_count = expected_results['total_matches']
        actual_count = results['total_matches']
        assert actual_count == expected_count, (
            f"Expected {expected_count} matches, but got {actual_count}"
        )

    @staticmethod
    def _save_results(
        analyser: AnalyserDocx,
        results: Dict,
        results_subdir: str
    ) -> Tuple[Path, Path]:
        from services.utils.get_project_root import get_project_root

        project_root = get_project_root()
        results_dir = project_root / 'results' / 'test' / 'docx' / results_subdir
        results_dir.mkdir(parents=True, exist_ok=True)

        output_docx_path = results_dir / 'result.docx'
        analyser.save(str(output_docx_path))

        assert output_docx_path.exists(), f"Output DOCX file was not created: {output_docx_path}"

        stats_json_path = results_dir / 'stats.json'
        with open(stats_json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

        assert stats_json_path.exists(), f"Stats JSON file was not created: {stats_json_path}"

        return output_docx_path, stats_json_path

    def _print_test_results(
        self,
        results: Dict,
        search_terms: list[str],
        output_docx_path: Path,
        stats_json_path: Path
    ) -> None:
        print(f"Test passed: Found {results['total_matches']} matches")
        print(f"  Search terms: {search_terms}")
        print(f"  Stats items count: {len(results['stats'])}")
        print(f"  Output DOCX: {output_docx_path}")
        print(f"  Stats JSON: {stats_json_path}")
