import json
import sys
from pathlib import Path
from typing import Dict, Optional, List

from services.analysis.analyser_docx import AnalyserDocx
from services.analysis.analysis_data import AnalysisData
from tests.analysis.test_base import BaseTest


class TestAnalyserDocx(BaseTest):
    """
    Test class for AnalyserDocx functionality.
    
    Examples:
        Run all tests via tests:
            tests tests/test_analyser_docx.py
            python -m tests tests/test_analyser_docx.py
        
        Run specific test (direct execution):
            python tests/test_analyser_docx.py
            python tests/test_analyser_docx.py single-phrase
    """
    
    test_data_subdir = 'docx'
    results_subdir = 'docx'

    def run_single_test(self, test_dir: Path) -> Dict:
        """Run analysis for a single test directory."""
        source_docx_path = test_dir / 'source.docx'
        search_path = self.find_search_file(test_dir, search_filenames=['search.txt'])

        assert source_docx_path.exists(), f"Source file not found: {source_docx_path}"

        # [start] Load search terms
        search_terms = self.load_search_terms(search_path)
        # [end]

        # [start] Create AnalyseData
        analyse_data = AnalysisData()
        analyse_data.read_from_list(search_terms)
        # [end]

        # [start] Create analysis and perform analysis
        analyser = AnalyserDocx(str(source_docx_path))
        analyser.set_analyse_data(analyse_data)
        analysis_results = analyser.analyse_and_highlight()
        # [end]

        # [start] Validate results
        assert analysis_results is not None, "Analysis returned None"
        assert 'word_stats' in analysis_results, "Missing word_stats in results"
        assert 'phrase_stats' in analysis_results, "Missing phrase_stats in results"
        assert 'total_matches' in analysis_results, "Missing total_matches in results"
        assert isinstance(analysis_results['total_matches'], int), "total_matches should be int"
        # [end]

        # [start] Save results
        test_name = test_dir.name
        test_results_dir = self.results_dir / test_name
        test_results_dir.mkdir(parents=True, exist_ok=True)

        output_docx_path = test_results_dir / 'result.docx'
        analyser.save(str(output_docx_path))

        assert output_docx_path.exists(), f"Output DOCX file was not created: {output_docx_path}"

        # [start] save results
        stats_json_path = test_results_dir / 'stats.json'

        with open(stats_json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=4)

        assert stats_json_path.exists(), f"Stats JSON file was not created: {stats_json_path}"
        # [end]

        return {
            'test_dir': test_dir,
            'source_docx_path': source_docx_path,
            'search_terms': search_terms,
            'analysis_results': analysis_results,
            'output_docx_path': output_docx_path,
            'stats_json_path': stats_json_path
        }

    def validate_test_result(self, analysis_results: Dict, expected_results: Optional[Dict], test_dir: Path) -> None:
        """Validate test results against expected results from result.json."""
        if expected_results is None:
            return

        if 'total_matches' in expected_results:
            expected_total = expected_results['total_matches']
            actual_total = analysis_results['total_matches']

            assert actual_total == expected_total, (
                f"Test {test_dir.name} failed: expected total_matches={expected_total}, "
                f"but got {actual_total}"
            )

    def test(self, test_name: Optional[str] = None) -> None:
        """Run tests for all subdirectories in data/docx or specific test if test_name is provided."""
        test_directories = self.get_test_directories(
            source_filename='source.docx',
            search_filenames=['search.txt']
        )

        if test_name:
            test_dir_path = self.test_data_dir / test_name
            self.validate_test_directory(
                test_dir_path,
                source_filename='source.docx',
                search_filenames=['search.txt']
            )
            test_directories = [test_dir_path]
        else:
            assert len(test_directories) > 0, f"No test directories found in {self.test_data_dir}"

        for test_dir in test_directories:
            # [start] Run test
            test_result = self.run_single_test(test_dir)
            # [end]

            # [start] Load and validate expected results
            expected_results = self.load_expected_results(test_dir)
            self.validate_test_result(test_result['analysis_results'], expected_results, test_dir)
            # [end]

            # [start] Print test results
            print(f"Test passed: {test_dir.name}")
            print(f"  Source: {test_result['source_docx_path']}")
            print(f"  Search terms: {test_result['search_terms']}")
            print(f"  Total matches: {test_result['analysis_results']['total_matches']}")
            print(f"  Output DOCX: {test_result['output_docx_path']}")
            print(f"  Stats JSON: {test_result['stats_json_path']}")
            # [end]

if __name__ == '__main__':
    test_instance = TestAnalyserDocx()
    test_name = sys.argv[1] if len(sys.argv) > 1 else None
    test_instance.test(test_name)
    print("All tests passed!")
