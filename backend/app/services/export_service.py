"""Script export converters: YAML, Fountain, PDF, FDX."""

import io
import uuid
import zipfile
from datetime import datetime

import os
import re

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.schemas.script import ScriptV1

# Register a CJK font so Chinese characters don't render as black boxes.
# STHeiti ships on macOS; on Linux we fall back to a system-available font.
def _register_cjk_font() -> str:
    candidates = [
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
        ("/System/Library/Fonts/PingFang.ttc", 0),
        ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0),
        ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 0),
    ]
    for path, idx in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("CJKFont", path, subfontIndex=idx))
                return "CJKFont"
            except Exception:
                continue
    return None


_CJK_FONT = _register_cjk_font()


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


class ExportService:
    """Convert ScriptV1 to various export formats."""

    # ── 10.1 YAML ──

    @staticmethod
    def to_yaml(script: ScriptV1) -> str:
        """Serialize ScriptV1 to YAML string."""
        import yaml
        return yaml.safe_dump(script.model_dump(mode="json"), allow_unicode=True, sort_keys=False)

    # ── 10.2 Fountain ──

    @staticmethod
    def to_fountain(script: ScriptV1) -> str:
        """Convert ScriptV1 to Fountain syntax."""
        lines = []
        meta = script.metadata
        lines.append(f"Title: {meta.title}")
        if meta.subtitle:
            lines.append(f"Credit: {meta.subtitle}")
        lines.append(f"Author: {meta.source_author or 'Unknown'}")
        lines.append("")

        for scene in script.scenes:
            slug = scene.slug
            lines.append(f"{slug.location_type.value} {slug.location_name} - {slug.time.value}")
            lines.append("")

            for block in scene.blocks:
                if block.type == "action":
                    lines.append(block.text or "")
                    lines.append("")
                elif block.type == "dialogue":
                    if block.parenthetical:
                        lines.append(f"{block.char_name or 'UNKNOWN'}")
                        lines.append(f"({block.parenthetical})")
                        lines.append(block.line or "")
                    else:
                        lines.append(f"{block.char_name or 'UNKNOWN'}")
                        lines.append(block.line or "")
                    lines.append("")

        return "\n".join(lines)

    # ── 10.3 PDF ──

    @staticmethod
    def to_pdf(script: ScriptV1) -> bytes:
        """Convert ScriptV1 to PDF using reportlab.

        Produces a print-ready screenplay with:
        - Title page (title, author, date)
        - Page numbers top-right (after title page)
        - Scene numbers in left/right margins
        - (CONTINUED) markers when a scene spans a page break
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Standard screenplay margins
        left_margin = 1.5 * inch
        right_margin = 1.0 * inch
        top_margin = 1.0 * inch
        bottom_margin = 1.0 * inch
        content_width = width - left_margin - right_margin

        meta = script.metadata
        page_num = 0

        def _new_page():
            nonlocal page_num
            c.showPage()
            page_num += 1
            # Page number top-right (not on title page)
            if page_num >= 2:
                c.setFont("Courier", 10)
                c.drawRightString(width - right_margin, height - 0.5 * inch, str(page_num - 1))
            return height - top_margin

        def _resolve_font(text: str, western_font: str) -> str:
            """Use CJK font when text contains Chinese characters."""
            return _CJK_FONT if (_CJK_FONT and _contains_chinese(text)) else western_font

        def _draw_wrapped_text(text: str, x: float, y: float, max_width: float, font: str, size: int) -> float:
            """Draw wrapped text, returning the new y position."""
            actual_font = _resolve_font(text, font)
            c.setFont(actual_font, size)
            words = (text or "").split()
            line_words = []
            for word in words:
                test = " ".join(line_words + [word])
                if c.stringWidth(test, actual_font, size) < max_width:
                    line_words.append(word)
                else:
                    c.drawString(x, y, " ".join(line_words))
                    y -= 0.2 * inch
                    line_words = [word]
                    if y < bottom_margin + 0.3 * inch:
                        y = _new_page()
            if line_words:
                c.drawString(x, y, " ".join(line_words))
                y -= 0.2 * inch
            return y

        # ── Title page ──
        page_num = 1
        title_text = meta.title or "Untitled"
        c.setFont(_resolve_font(title_text, "Courier-Bold"), 24)
        title_width = c.stringWidth(title_text, _resolve_font(title_text, "Courier-Bold"), 24)
        c.drawCentredString(width / 2, height * 0.55, title_text)

        if meta.subtitle:
            c.setFont(_resolve_font(meta.subtitle, "Courier"), 14)
            c.drawCentredString(width / 2, height * 0.55 - 0.4 * inch, meta.subtitle)

        author_text = f"by {meta.source_author or 'Unknown'}"
        c.setFont(_resolve_font(author_text, "Courier"), 12)
        c.drawCentredString(width / 2, height * 0.55 - 1.0 * inch, author_text)

        c.setFont("Courier", 10)
        c.drawCentredString(width / 2, height * 0.55 - 1.6 * inch, datetime.now().strftime("%B %d, %Y"))

        y = _new_page()
        current_scene_number: int | None = None
        scene_continued = False

        for scene in script.scenes:
            slug = scene.slug
            slug_text = f"{slug.location_type.value} {slug.location_name} - {slug.time.value}"
            current_scene_number = scene.scene_number

            # Estimate scene height to decide if we need a page break
            scene_height = 0.3 * inch  # slug
            for block in scene.blocks:
                if block.type == "action":
                    words = (block.text or "").split()
                    lines = max(1, (len(words) // 8) + 1)  # rough estimate
                    scene_height += lines * 0.2 * inch
                elif block.type == "dialogue":
                    scene_height += 0.2 * inch  # char name
                    if block.parenthetical:
                        scene_height += 0.2 * inch
                    words = (block.line or "").split()
                    lines = max(1, (len(words) // 6) + 1)
                    scene_height += lines * 0.2 * inch
            scene_height += 0.2 * inch  # trailing spacing

            # If scene won't fit on current page and we're not at top, start new page
            if y < height - top_margin - 0.5 * inch and scene_height > (y - bottom_margin):
                y = _new_page()
                scene_continued = False

            # Scene number in left margin
            if page_num >= 2:
                c.setFont("Courier", 8)
                c.drawString(0.4 * inch, y, str(scene.scene_number))

            # Scene slug
            c.setFont(_resolve_font(slug_text, "Courier-Bold"), 12)
            c.drawString(left_margin, y, slug_text)
            y -= 0.3 * inch

            # If scene was continued from previous page, add header
            if scene_continued and page_num >= 2:
                c.setFont("Courier", 10)
                c.drawString(left_margin, y, "CONTINUED:")
                y -= 0.2 * inch

            for block in scene.blocks:
                # Check for page break within block
                if y < bottom_margin + 0.5 * inch:
                    # Add (CONTINUED) at bottom if scene continues
                    c.setFont("Courier", 10)
                    c.drawRightString(width - right_margin, bottom_margin + 0.1 * inch, "(CONTINUED)")
                    y = _new_page()
                    scene_continued = True

                    # Re-draw scene number and slug on new page
                    if current_scene_number is not None:
                        c.setFont("Courier", 8)
                        c.drawString(0.4 * inch, y, str(current_scene_number))
                    c.setFont(_resolve_font(slug_text, "Courier-Bold"), 12)
                    c.drawString(left_margin, y, slug_text)
                    y -= 0.2 * inch
                    c.setFont("Courier", 10)
                    c.drawString(left_margin, y, "CONTINUED:")
                    y -= 0.2 * inch
                else:
                    scene_continued = False

                if block.type == "action":
                    y = _draw_wrapped_text(
                        block.text or "", left_margin, y, content_width, "Courier", 12
                    )
                elif block.type == "dialogue":
                    char_name = block.char_name or "UNKNOWN"
                    line = block.line or ""
                    parenthetical = block.parenthetical

                    c.setFont(_resolve_font(char_name, "Courier-Bold"), 12)
                    name_x = left_margin + 2 * inch
                    c.drawString(name_x, y, char_name.upper())
                    y -= 0.2 * inch

                    if y < bottom_margin + 0.3 * inch:
                        c.setFont("Courier", 10)
                        c.drawRightString(width - right_margin, bottom_margin + 0.1 * inch, "(CONTINUED)")
                        y = _new_page()
                        scene_continued = True

                    if parenthetical:
                        c.setFont(_resolve_font(parenthetical, "Courier"), 12)
                        paren_x = left_margin + 1.5 * inch
                        c.drawString(paren_x, y, f"({parenthetical})")
                        y -= 0.2 * inch
                        if y < bottom_margin + 0.3 * inch:
                            c.setFont("Courier", 10)
                            c.drawRightString(width - right_margin, bottom_margin + 0.1 * inch, "(CONTINUED)")
                            y = _new_page()
                            scene_continued = True

                    dialog_x = left_margin + 1 * inch
                    dialog_width = content_width - 2 * inch
                    y = _draw_wrapped_text(line, dialog_x, y, dialog_width, "Courier", 12)

            y -= 0.2 * inch  # spacing between scenes

        c.save()
        buffer.seek(0)
        return buffer.read()

    # ── 10.4 FDX ──

    @staticmethod
    def to_fdx(script: ScriptV1) -> str:
        """Convert ScriptV1 to Final Draft XML (FDX)."""
        lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>',
            '<FinalDraft DocumentType="Script" Template="No" Version="3">',
            '  <Content>',
        ]

        para_id = 1
        for scene in script.scenes:
            slug = scene.slug
            slug_text = f"{slug.location_type.value} {slug.location_name} - {slug.time.value}"
            lines.append(f'    <Paragraph Type="Scene Heading" Number="{scene.scene_number}">')
            lines.append(f'      <Text>{_xml_escape(slug_text)}</Text>')
            lines.append('    </Paragraph>')

            for block in scene.blocks:
                if block.type == "action":
                    lines.append('    <Paragraph Type="Action">')
                    lines.append(f'      <Text>{_xml_escape(block.text or "")}</Text>')
                    lines.append('    </Paragraph>')
                elif block.type == "dialogue":
                    lines.append('    <Paragraph Type="Character">')
                    lines.append(f'      <Text>{_xml_escape((block.char_name or "UNKNOWN").upper())}</Text>')
                    lines.append('    </Paragraph>')
                    if block.parenthetical:
                        lines.append('    <Paragraph Type="Parenthetical">')
                        lines.append(f'      <Text>{_xml_escape(f"({block.parenthetical})")}</Text>')
                        lines.append('    </Paragraph>')
                    lines.append('    <Paragraph Type="Dialogue">')
                    lines.append(f'      <Text>{_xml_escape(block.line or "")}</Text>')
                    lines.append('    </Paragraph>')

        lines.extend([
            '  </Content>',
            '</FinalDraft>',
        ])
        return "\n".join(lines)

    # ── 10.5 Batch ZIP ──

    @staticmethod
    def to_zip(script: ScriptV1, formats: list[str]) -> bytes:
        """Export multiple formats as a ZIP archive."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            safe_title = "".join(c if c.isalnum() else "_" for c in script.metadata.title)
            if "yaml" in formats:
                zf.writestr(f"{safe_title}.yaml", ExportService.to_yaml(script))
            if "fountain" in formats:
                zf.writestr(f"{safe_title}.fountain", ExportService.to_fountain(script))
            if "pdf" in formats:
                zf.writestr(f"{safe_title}.pdf", ExportService.to_pdf(script))
            if "fdx" in formats:
                zf.writestr(f"{safe_title}.fdx", ExportService.to_fdx(script))
        buffer.seek(0)
        return buffer.read()


def _xml_escape(text: str) -> str:
    """Escape XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
