from pathlib import Path
from typing import Dict

from services.analysis.analyser_pdf import AnalyserPdf
from services.analysis.analysis_data import AnalysisData


class AnalysisSetupMixin:
    """Mixin for setting up PDF analysis."""

    def setup_analysis(self, source_path: Path, search_terms: list[str]) -> tuple[AnalyserPdf, Dict]:
        """
        Create analyser and perform analysis.
        
        Args:
            source_path: Path to source PDF file
            search_terms: List of search terms to find
            
        Returns:
            Tuple of (analyser, analysis_results)
        """
        analyse_data = AnalysisData()
        analyse_data.read_from_list(search_terms)

        analyser = AnalyserPdf(str(source_path))
        analyser.set_analyse_data(analyse_data)
        analysis_results: Dict = analyser.analyse_and_highlight()

        return analyser, analysis_results

