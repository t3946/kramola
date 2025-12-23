import json
import sys
import time
from pathlib import Path
from typing import Dict, Optional, List

from services.analyser.analyser_docx import AnalyserDocx
from services.analyser.analyse_data import AnalyseData


class TestAnalyserDocxSpeed:
    """
    Test class for measuring AnalyserDocx performance/speed.
    Independent test class focused on timing measurements.
    
    Examples:
        Run speed test (direct execution):
            python tests/test_analyser_docx_speed.py
            python tests/test_analyser_docx_speed.py big-data-27-pages
        
        Run via pytest (use -s flag to see output):
            pytest tests/test_analyser_docx_speed.py -s
            pytest tests/test_analyser_docx_speed.py::TestAnalyserDocxSpeed::test_speed -s
    """
    test_data_dir = Path(__file__).parent / 'data' / 'docx-speed'
    results_dir = Path(__file__).parent.parent / 'results' / 'test'
    
    def get_test_directories(self) -> List[Path]:
        """Get all test subdirectories from data/docx-speed, supporting both search.txt and search.docx."""
        if not self.test_data_dir.exists():
            return []

        return [
            subdir for subdir in self.test_data_dir.iterdir()
            if subdir.is_dir() and (subdir / 'source.docx').exists() and 
            ((subdir / 'search.txt').exists() or (subdir / 'search.docx').exists())
        ]

    def load_search_terms(self, search_path: Path) -> List[str]:
        """Load search terms from search.txt or search.docx file."""
        if search_path.suffix == '.docx':
            # Load from DOCX using AnalyseData
            analyse_data = AnalyseData()
            analyse_data.read_from_docx(str(search_path))
            search_terms = list(analyse_data.tokens.keys())
        else:
            # Load from TXT (original method)
            with open(search_path, 'r', encoding='utf-8') as f:
                search_terms = [line.strip() for line in f if line.strip()]

        assert len(search_terms) > 0, f"No search terms found in {search_path.name}"
        return search_terms

    def run_single_test(self, test_dir: Path) -> Dict:
        """Run analysis for a single test directory with timing measurements."""
        source_docx_path = test_dir / 'source.docx'
        search_txt_path = test_dir / 'search.txt'
        search_docx_path = test_dir / 'search.docx'
        
        # Determine which search file exists
        if search_docx_path.exists():
            search_path = search_docx_path
        elif search_txt_path.exists():
            search_path = search_txt_path
        else:
            raise FileNotFoundError(f"Neither search.txt nor search.docx found in {test_dir}")

        assert source_docx_path.exists(), f"Source file not found: {source_docx_path}"

        timing_results = {}
        
        # [start] Load search terms - TIMED
        start_time = time.time()
        search_terms = self.load_search_terms(search_path)
        timing_results['load_search_terms'] = time.time() - start_time
        # [end]

        # [start] Create AnalyseData - TIMED
        start_time = time.time()
        analyse_data = AnalyseData()
        analyse_data.read_from_list(search_terms)
        timing_results['create_analyse_data'] = time.time() - start_time
        # [end]

        # [start] Create analyser - TIMED
        start_time = time.time()
        analyser = AnalyserDocx(str(source_docx_path))
        analyser.set_analyse_data(analyse_data)
        timing_results['create_analyser'] = time.time() - start_time
        # [end]

        # [start] Perform analysis - TIMED
        start_time = time.time()
        analysis_results = analyser.analyse_and_highlight()
        timing_results['analyse_and_highlight'] = time.time() - start_time
        # [end]

        # [start] Basic validation (no expected results check)
        assert analysis_results is not None, "Analysis returned None"
        assert 'word_stats' in analysis_results, "Missing word_stats in results"
        assert 'phrase_stats' in analysis_results, "Missing phrase_stats in results"
        assert 'total_matches' in analysis_results, "Missing total_matches in results"
        assert isinstance(analysis_results['total_matches'], int), "total_matches should be int"
        # [end]

        # [start] Save results - TIMED
        start_time = time.time()
        test_name = test_dir.name
        test_results_dir = self.results_dir / 'docx-speed' / test_name
        test_results_dir.mkdir(parents=True, exist_ok=True)

        output_docx_path = test_results_dir / 'result.docx'
        analyser.save(str(output_docx_path))
        timing_results['save_docx'] = time.time() - start_time
        # [end]

        assert output_docx_path.exists(), f"Output DOCX file was not created: {output_docx_path}"

        # [start] Save stats JSON - TIMED
        start_time = time.time()
        stats_json_path = test_results_dir / 'stats.json'
        with open(stats_json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=4)
        timing_results['save_stats_json'] = time.time() - start_time
        # [end]

        assert stats_json_path.exists(), f"Stats JSON file was not created: {stats_json_path}"

        # Calculate total time (sum of all individual timings)
        total_time = sum(timing_results.values())
        timing_results['total_time'] = total_time

        return {
            'test_dir': test_dir,
            'source_docx_path': source_docx_path,
            'search_terms': search_terms,
            'analysis_results': analysis_results,
            'output_docx_path': output_docx_path,
            'stats_json_path': stats_json_path,
            'timing_results': timing_results
        }

    def load_expected_results(self, test_dir: Path) -> Optional[Dict]:
        """Load expected results from result.json if it exists."""
        result_json_path = test_dir / 'result.json'

        if not result_json_path.exists():
            return None

        with open(result_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def validate_test_result(self, analysis_results: Dict, expected_results: Optional[Dict], test_dir: Path) -> None:
        """Skip validation for speed tests - we only care about performance."""
        pass

    def test_speed(self, test_name: Optional[str] = None) -> None:
        """Run speed tests for all subdirectories in data/docx or specific test if test_name is provided."""
        test_directories = self.get_test_directories()

        if test_name:
            test_dir_path = self.test_data_dir / test_name
            if not test_dir_path.exists() or not test_dir_path.is_dir():
                raise ValueError(f"Test directory not found: {test_name}")
            if not (test_dir_path / 'source.docx').exists():
                raise ValueError(f"Test directory {test_name} is missing required file (source.docx)")
            if not (test_dir_path / 'search.txt').exists() and not (test_dir_path / 'search.docx').exists():
                raise ValueError(f"Test directory {test_name} is missing required file (search.txt or search.docx)")
            test_directories = [test_dir_path]
        else:
            assert len(test_directories) > 0, f"No test directories found in {self.test_data_dir}"

        for test_dir in test_directories:
            # [start] Run test
            test_result = self.run_single_test(test_dir)
            # [end]

            # [start] Load expected results (but don't validate - we skip validation in speed tests)
            expected_results = self.load_expected_results(test_dir)
            self.validate_test_result(test_result['analysis_results'], expected_results, test_dir)
            # [end]

            # [start] Print test results with timing information
            print(f"\n{'='*60}", flush=True)
            print(f"Speed Test: {test_dir.name}", flush=True)
            print(f"{'='*60}", flush=True)
            print(f"Source: {test_result['source_docx_path']}", flush=True)
            print(f"Search terms count: {len(test_result['search_terms'])}", flush=True)
            print(f"Total matches: {test_result['analysis_results']['total_matches']}", flush=True)
            print(f"\nTiming Results:", flush=True)
            print(f"  Load search terms:     {test_result['timing_results']['load_search_terms']:.4f} sec", flush=True)
            print(f"  Create AnalyseData:    {test_result['timing_results']['create_analyse_data']:.4f} sec", flush=True)
            print(f"  Create analyser:       {test_result['timing_results']['create_analyser']:.4f} sec", flush=True)
            print(f"  Analyse and highlight: {test_result['timing_results']['analyse_and_highlight']:.4f} sec", flush=True)
            print(f"  Save DOCX:             {test_result['timing_results']['save_docx']:.4f} sec", flush=True)
            print(f"  Save stats JSON:       {test_result['timing_results']['save_stats_json']:.4f} sec", flush=True)
            print(f"  {'-'*40}", flush=True)
            print(f"  TOTAL TIME:            {test_result['timing_results']['total_time']:.4f} sec", flush=True)
            print(f"\nOutput files:", flush=True)
            print(f"  DOCX: {test_result['output_docx_path']}", flush=True)
            print(f"  JSON: {test_result['stats_json_path']}", flush=True)
            print(f"{'='*60}\n", flush=True)
            # [end]

            # Save timing results to JSON
            test_name = test_dir.name
            test_results_dir = self.results_dir / 'docx-speed' / test_name
            timing_json_path = test_results_dir / 'timing.json'
            with open(timing_json_path, 'w', encoding='utf-8') as f:
                json.dump(test_result['timing_results'], f, ensure_ascii=False, indent=4)
            print(f"Timing results saved to: {timing_json_path}\n", flush=True)


if __name__ == '__main__':
    test_instance = TestAnalyserDocxSpeed()
    test_name = sys.argv[1] if len(sys.argv) > 1 else None
    test_instance.test_speed(test_name)
    print("All speed tests completed!", flush=True)

