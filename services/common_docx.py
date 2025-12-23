import copy
import logging
from typing import Optional
from docx.shared import RGBColor, Pt
from docx.text.paragraph import ParagraphFormat
from docx.text.run import Run
from services.fulltext_search.fulltext_search import FulltextSearch

logger_cd = logging.getLogger(__name__)


def _safe_copy_paragraph_format(source_pf: Optional[ParagraphFormat], target_pf: Optional[ParagraphFormat]) -> None:
    """
    Safely copies basic paragraph formatting attributes.
    (Copied from footnotes_service.py / highlight_service.py)
    """
    if not source_pf or not target_pf:
        return

    attrs_to_copy = [
        'alignment',
        'first_line_indent',
        'keep_together',
        'keep_with_next',
        'left_indent',
        'line_spacing',
        'line_spacing_rule',
        'page_break_before',
        'right_indent',
        'space_after',
        'space_before',
        'widow_control'
    ]

    for attr in attrs_to_copy:
        try:
            val = getattr(source_pf, attr, None)

            if val is not None:
                setattr(target_pf, attr, val)
        except (AttributeError, ValueError, TypeError) as e:
            logger_cd.warning(f"Warning when copying paragraph format '{attr}': {e}", exc_info=False)


def _apply_run_style(source_run: Optional[Run], target_run: Optional[Run], document_cache, copy_highlight: bool = False) -> None:
    """
    Applies style and formatting from source_run to target_run.
    (Copied from footnotes_service.py / highlight_service.py and adapted)
    copy_highlight: If True, copies highlight color from source run.
    """
    if not source_run or not target_run:
        return

    try:
        source_run_style = source_run.style

        if source_run_style and source_run_style.name:
            try:
                target_run.style = document_cache.getStyle(source_run_style.name)
            except Exception as e:
                logger_cd.warning(f"Failed to assign run style '{getattr(source_run_style, 'name', 'N/A')}': {e}")

        bool_attrs = [
            'bold',
            'italic',
            'underline',
            'small_caps',
            'all_caps',
            'strike',
            'double_strike',
            'outline',
            'shadow',
            'imprint',
            'emboss',
            'spec_vanish',
            'no_proof',
            'snap_to_grid',
            'rtl',
            'cs_bold',
            'cs_italic',
            'web_hidden'
        ]

        for attr in bool_attrs:
            try:
                val = getattr(source_run, attr, None)

                if val is not None:
                    setattr(target_run, attr, val)
            except (AttributeError, ValueError, TypeError):
                pass
            except Exception as e_bool:
                logger_cd.warning(f"Unexpected error when copying bool attribute '{attr}': {e_bool}")

        s_font = source_run.font

        if s_font:
            t_font = target_run.font
            font_attrs = [
                'name',
                'size',
                'color',
                'underline',
                'highlight_color'
            ]

            for attr in font_attrs:
                try:
                    val = getattr(s_font, attr, None)

                    if val is not None:
                        if attr == 'color':
                            if hasattr(val, 'rgb') and isinstance(val.rgb, RGBColor):
                                try:
                                    t_font.color.rgb = copy.deepcopy(val.rgb)
                                except Exception as e_assign_rgb:
                                    logger_cd.warning(f"Failed to assign RGB color: {e_assign_rgb}")
                        elif attr == 'size':
                            if hasattr(val, 'pt') and val.pt is not None:
                                try:
                                    pt_size = int(val.pt)

                                    if pt_size > 0:
                                        t_font.size = Pt(pt_size)
                                except (ValueError, TypeError):
                                    pass
                        elif attr == 'underline':
                            t_font.underline = val
                        elif attr == 'name' and val:
                            t_font.name = val
                        elif attr == 'highlight_color' and copy_highlight:
                            t_font.highlight_color = val
                except Exception as e:
                    logger_cd.warning(f"Error copying font attribute '{attr}': {e}", exc_info=False)

            misc_font_attrs = [
                'kerning',
                'subscript',
                'superscript'
            ]

            for attr in misc_font_attrs:
                try:
                    val = getattr(s_font, attr, None)

                    if val is not None:
                        setattr(t_font, attr, val)
                except (AttributeError, ValueError, TypeError):
                    pass
                except Exception as e_misc:
                    logger_cd.warning(f"Unexpected error when copying misc font attribute '{attr}': {e_misc}")

    except Exception as e:
        logger_cd.error(f"Critical error in _apply_run_style: {e}", exc_info=True)


def tokenize_paragraph_universal(paragraph) -> list:
    """
    Tokenizes paragraph text using FulltextSearch.
    """
    text = paragraph.text if paragraph else ""

    return FulltextSearch.tokenize_text(text)   