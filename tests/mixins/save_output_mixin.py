import json
from pathlib import Path
from typing import Dict, Tuple

from services.analysis.analyser_pdf import AnalyserPdf
from services.utils.get_project_root import get_project_root


class SaveOutputMixin:
    """Mixin for saving analysis results to files."""

    def save_analysis_results(
        self,
        analyser: AnalyserPdf,
        results: Dict,
        results_subdir: str
    ) -> Tuple[Path, Path]:
        """
        Save analysis results to PDF and JSON files.
        
        Args:
            analyser: AnalyserPdf instance
            results: Analysis results dictionary
            results_subdir: Subdirectory name for results (e.g., '1-word', '1-sentences')
            
        Returns:
            Tuple of (output_pdf_path, stats_json_path)
            
        Raises:
            AssertionError: If files were not created
        """
        project_root = get_project_root()
        results_dir = project_root / 'results' / 'test' / 'pdf' / results_subdir
        results_dir.mkdir(parents=True, exist_ok=True)

        output_pdf_path = results_dir / 'result.pdf'
        analyser.save(str(output_pdf_path))

        assert output_pdf_path.exists(), f"Output PDF file was not created: {output_pdf_path}"

        stats_json_path = results_dir / 'stats.json'

        with open(stats_json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

        assert stats_json_path.exists(), f"Stats JSON file was not created: {stats_json_path}"

        return output_pdf_path, stats_json_path

