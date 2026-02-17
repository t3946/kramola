import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from services.analysis.analyser_docx import AnalyserDocx
from services.analysis.analysis_data import AnalysisData

from tests.analysis.test_speed_base import BaseSpeedTest


class TestSpeedFlList(BaseSpeedTest):
    """Speed test for fl-list dataset using Redis lists."""
    
    test_dir_name = 'fl-list'
    source_filename = 'source.docx'

    def validate_test_directory(
            self,
            test_dir: Path,
            source_filename: str = 'source.docx',
            search_filenames: Optional[List[str]] = None
    ) -> None:
        """Validate that test directory contains required files (only source file for Redis-based tests)."""
        if not test_dir.exists() or not test_dir.is_dir():
            raise ValueError(f"Test directory not found: {test_dir}")

        source_path = test_dir / source_filename
        if not source_path.exists():
            raise ValueError(f"Test directory {test_dir.name} is missing required file ({source_filename})")

        # Skip search file validation for Redis-based tests
        if search_filenames is not None and len(search_filenames) == 0:
            return

        # If search_filenames provided and not empty, validate them
        if search_filenames is None:
            search_filenames = ['search.txt', 'search.docx']

        has_search_file = any((test_dir / search_file).exists() for search_file in search_filenames)
        if not has_search_file:
            raise ValueError(
                f"Test directory {test_dir.name} is missing required file "
                f"(one of: {', '.join(search_filenames)})"
            )

    def run_single_test(self, test_dir: Path) -> Dict:
        """Run analysis for a single test directory with timing measurements."""
        source_docx_path = test_dir / self.source_filename

        assert source_docx_path.exists(), f"Source file not found: {source_docx_path}"

        timing_results = {}
        
        # [start] Create AnalyseData and load from Redis - TIMED
        start_time = time.time()
        analyse_data = AnalysisData()
        from services.enum import PredefinedListKey
        analyse_data.load_predefined_lists([PredefinedListKey.FOREIGN_AGENTS_PERSONS])
        timing_results['create_analyse_data'] = time.time() - start_time
        # [end]

        # [start] Create analysis - TIMED
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
        assert 'stats' in analysis_results, "Missing stats in results"
        assert 'total_matches' in analysis_results, "Missing total_matches in results"
        assert isinstance(analysis_results['stats'], list), "stats should be list"
        assert isinstance(analysis_results['total_matches'], int), "total_matches should be int"
        # [end]

        # [start] Save results - TIMED
        start_time = time.time()
        test_name = test_dir.name
        test_results_dir = self.results_dir / test_name
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

        phrases_count = len(analyse_data.phrases)

        return {
            'test_dir': test_dir,
            'source_docx_path': source_docx_path,
            'phrases_count': phrases_count,
            'analysis_results': analysis_results,
            'output_docx_path': output_docx_path,
            'stats_json_path': stats_json_path,
            'timing_results': timing_results
        }

    def test_speed(self) -> None:
        """Run speed test for specific test directory."""
        test_dir = self.test_dir
        
        self.validate_test_directory(
            test_dir,
            source_filename=self.source_filename,
            search_filenames=[]  # No search file needed - using Redis
        )

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
        print(f"Phrases count (from Redis): {test_result['phrases_count']}", flush=True)
        print(f"Total matches: {test_result['analysis_results']['total_matches']}", flush=True)
        print(f"\nTiming Results:", flush=True)
        print(f"  Create AnalyseData (Redis): {test_result['timing_results']['create_analyse_data']:.4f} sec", flush=True)
        print(f"  Create analyser:            {test_result['timing_results']['create_analyser']:.4f} sec", flush=True)
        print(f"  Analyse and highlight:      {test_result['timing_results']['analyse_and_highlight']:.4f} sec", flush=True)
        print(f"  Save DOCX:                  {test_result['timing_results']['save_docx']:.4f} sec", flush=True)
        print(f"  Save stats JSON:            {test_result['timing_results']['save_stats_json']:.4f} sec", flush=True)
        print(f"  {'-'*40}", flush=True)
        print(f"  TOTAL TIME:                 {test_result['timing_results']['total_time']:.4f} sec", flush=True)
        print(f"\nOutput files:", flush=True)
        print(f"  DOCX: {test_result['output_docx_path']}", flush=True)
        print(f"  JSON: {test_result['stats_json_path']}", flush=True)
        print(f"{'='*60}\n", flush=True)
        # [end]

        # Save timing results to JSON
        test_name = test_dir.name
        test_results_dir = self.results_dir / test_name
        timing_json_path = test_results_dir / 'timing.json'
        with open(timing_json_path, 'w', encoding='utf-8') as f:
            json.dump(test_result['timing_results'], f, ensure_ascii=False, indent=4)
        print(f"Timing results saved to: {timing_json_path}\n", flush=True)

