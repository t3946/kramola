import os
import json
from pathlib import Path

from services.analyser.analyser_docx import AnalyserDocx
from services.analyser.analyse_data import AnalyseData
from services.document_service import extract_lines_from_docx


class TestAnalyserDocx:
    test_data_dir = Path(__file__).parent / 'data' / 'single-phrase'
    results_dir = Path(__file__).parent.parent / 'results' / 'test'

    def test_analyse_and_highlight_universal_book_page(self):
        source_docx_path = self.test_data_dir / 'source.docx'
        search_txt_path = self.test_data_dir / 'search.txt'

        assert source_docx_path.exists(), f"Source file not found: {source_docx_path}"
        assert search_txt_path.exists(), f"Search file not found: {search_txt_path}"

        # [start] Load search terms
        with open(search_txt_path, 'r', encoding='utf-8') as f:
            search_terms = [line.strip() for line in f if line.strip()]

        assert len(search_terms) > 0, "No search terms found in search.txt"
        # [end]

        # [start] Create AnalyseData
        analyse_data = AnalyseData()
        analyse_data.read_from_list(search_terms)
        # [end]

        # [start] Create analyser and perform analysis
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
        test_name = self.test_data_dir.name
        test_results_dir = self.results_dir / test_name
        test_results_dir.mkdir(parents=True, exist_ok=True)

        output_docx_path = test_results_dir / 'result.docx'
        analyser.save(str(output_docx_path))

        assert output_docx_path.exists(), f"Output DOCX file was not created: {output_docx_path}"

        # [start] Prepare stats data - ensure all values are JSON-serializable
        word_stats_raw = analysis_results.get('word_stats', {})
        phrase_stats_raw = analysis_results.get('phrase_stats', {})
        total_matches = analysis_results.get('total_matches', 0)

        # Convert to plain dict and ensure all nested structures are JSON-serializable
        word_stats = {}
        for lemma, stats in word_stats_raw.items():
            if isinstance(stats, dict):
                word_stats[lemma] = {
                    'c': int(stats.get('c', stats.get('count', 0))),
                    'f': dict(stats.get('f', stats.get('forms', {})))
                }
            else:
                word_stats[lemma] = {'c': 0, 'f': {}}

        phrase_stats = {}
        for phrase, stats in phrase_stats_raw.items():
            if isinstance(stats, dict):
                phrase_stats[phrase] = {
                    'c': int(stats.get('c', stats.get('count', 0))),
                    'f': dict(stats.get('f', stats.get('forms', {})))
                }
            else:
                phrase_stats[phrase] = {'c': 0, 'f': {}}

        stats_json_path = test_results_dir / 'stats.json'
        stats_data = {
            'word_stats': word_stats,
            'phrase_stats': phrase_stats,
            'total_matches': int(total_matches)
        }

        with open(stats_json_path, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=4)

        assert stats_json_path.exists(), f"Stats JSON file was not created: {stats_json_path}"
        # [end]

        print(f"Test passed:")
        print(f"  Source: {source_docx_path}")
        print(f"  Search terms: {search_terms}")
        print(f"  Total matches: {analysis_results['total_matches']}")
        print(f"  Output DOCX: {output_docx_path}")
        print(f"  Stats JSON: {stats_json_path}")


if __name__ == '__main__':
    test_instance = TestAnalyserDocx()
    test_instance.test_analyse_and_highlight_universal_book_page()
    print("All tests passed!")
