import json
from pathlib import Path
from typing import Dict

from services.analysis.analyser_pdf import AnalyserPdf
from services.analysis.analysis_data import AnalysisData
from services.utils.get_project_root import get_project_root


def test_find_words_in_pdf() -> None:
    """Test finding words from search.txt in source.pdf."""
    test_dir = Path(__file__).parent / 'data'
    source_pdf_path = test_dir / 'source.pdf'
    search_txt_path = test_dir / 'search.txt'

    assert source_pdf_path.exists(), f"Source PDF not found: {source_pdf_path}"
    assert search_txt_path.exists(), f"Search file not found: {search_txt_path}"

    # [start] Load search terms
    with open(search_txt_path, 'r', encoding='utf-8') as f:
        search_terms: list[str] = [line.strip() for line in f if line.strip()]
    # [end]

    assert len(search_terms) > 0, f"No search terms found in {search_txt_path}"

    # [start] Create AnalyseData
    analyse_data = AnalysisData()
    analyse_data.read_from_list(search_terms)
    # [end]

    # [start] Create analyser and perform analysis
    analyser = AnalyserPdf(str(source_pdf_path))
    analyser.set_analyse_data(analyse_data)
    analysis_results: Dict = analyser.analyse_and_highlight()
    # [end]

    # [start] Validate results
    assert analysis_results is not None, "Analysis returned None"
    assert 'word_stats' in analysis_results, "Missing word_stats in results"
    assert 'phrase_stats' in analysis_results, "Missing phrase_stats in results"
    assert 'total_matches' in analysis_results, "Missing total_matches in results"
    assert isinstance(analysis_results['total_matches'], int), "total_matches should be int"
    # [end]

    # [start] Check that words were found
    word_stats = analysis_results['word_stats']
    
    assert analysis_results['total_matches'] > 0, (
        f"No matches found. Expected to find words from {search_terms}"
    )
    
    # Check if search terms appear in word_stats (as lemmas) or in forms
    for search_term in search_terms:
        search_term_lower = search_term.lower()
        word_found = False
        
        for lemma, stats in word_stats.items():
            # Check if lemma matches
            if lemma.lower() == search_term_lower:
                word_found = True
                break
            
            # Check if search term appears in forms
            forms = stats.get('forms', {})
            if any(form.lower() == search_term_lower for form in forms.keys()):
                word_found = True
                break
        
        assert word_found, f"Word '{search_term}' not found in PDF"
    # [end]

    # [start] Save results
    project_root = get_project_root()
    results_dir = project_root / 'results' / 'test' / 'pdf' / '1-word'
    results_dir.mkdir(parents=True, exist_ok=True)

    output_pdf_path = results_dir / 'result.pdf'
    analyser.save(str(output_pdf_path))

    assert output_pdf_path.exists(), f"Output PDF file was not created: {output_pdf_path}"

    stats_json_path = results_dir / 'stats.json'

    with open(stats_json_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=4)

    assert stats_json_path.exists(), f"Stats JSON file was not created: {stats_json_path}"
    # [end]

    print(f"Test passed: Found {analysis_results['total_matches']} matches")
    print(f"  Search terms: {search_terms}")
    print(f"  Word stats keys (lemmas): {list(word_stats.keys())}")
    print(f"  Output PDF: {output_pdf_path}")
    print(f"  Stats JSON: {stats_json_path}")


if __name__ == '__main__':
    test_find_words_in_pdf()
    print("Test passed!")

