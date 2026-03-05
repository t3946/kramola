from pathlib import Path
from typing import Dict, Optional, List

from services.analysis.analyser_pdf import AnalyserPdf
from services.analysis.analysis_data import AnalysisData
from services.enum import PredefinedListKey
from services.words_list.list_from_text import ListFromText


class AnalysisSetupMixin:
    """Mixin for setting up PDF analysis."""

    def setup_analysis(
        self, 
        source_path: Path, 
        search_terms: list[str],
        predefined_lists: Optional[List[PredefinedListKey]] = None
    ) -> tuple[AnalyserPdf, Dict]:
        """
        Create analyser and perform analysis.
        
        Args:
            source_path: Path to source PDF file
            search_terms: List of search terms to find
            predefined_lists: Optional list of predefined list keys to load from Redis
            
        Returns:
            Tuple of (analyser, analysis_results)
        """
        analyse_data = AnalysisData()
        
        # Load predefined lists if provided
        if predefined_lists:
            analyse_data.load_predefined_lists(predefined_lists)
        
        ListFromText("task_test").save_from_text(search_terms)
        analyse_data.load_user_list("task_test")

        analyser = AnalyserPdf(str(source_path))
        analyser.set_analyse_data(analyse_data)
        analysis_results: Dict = analyser.analyse_and_highlight()

        return analyser, analysis_results

