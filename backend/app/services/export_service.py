"""Script export converters: YAML, Fountain, PDF, FDX."""

import io
import uuid
import zipfile
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from app.schemas.script import ScriptV1


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
        """Convert ScriptV1 to PDF using reportlab."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Standard screenplay margins: 1.5" left/right, 1" top/bottom
        left_margin = 1.5 * inch
        right_margin = 1.5 * inch
        top_margin = 1 * inch
        bottom_margin = 1 * inch
        content_width = width - left_margin - right_margin

        def draw_header(page_num):
            c.setFont("Courier", 10)
            c.drawRightString(width - right_margin, height - 0.5 * inch, f"{script.metadata.title}")
            c.drawCentredString(width / 2, 0.5 * inch, str(page_num))

        page_num = 1
        y = height - top_margin
        draw_header(page_num)

        for scene in script.scenes:
            # Scene slug
            slug = scene.slug
            slug_text = f"{slug.location_type.value} {slug.location_name} - {slug.time.value}"

            if y < bottom_margin + 0.5 * inch:
                c.showPage()
                page_num += 1
                y = height - top_margin
                draw_header(page_num)

            c.setFont("Courier-Bold", 12)
            c.drawString(left_margin, y, slug_text)
            y -= 0.3 * inch

            for block in scene.blocks:
                if y < bottom_margin + 0.5 * inch:
                    c.showPage()
                    page_num += 1
                    y = height - top_margin
                    draw_header(page_num)

                if block.type == "action":
                    c.setFont("Courier", 12)
                    text = block.text or ""
                    # Simple word wrap
                    words = text.split()
                    line_words = []
                    for word in words:
                        test = " ".join(line_words + [word])
                        if c.stringWidth(test, "Courier", 12) < content_width:
                            line_words.append(word)
                        else:
                            c.drawString(left_margin, y, " ".join(line_words))
                            y -= 0.2 * inch
                            line_words = [word]
                    if line_words:
                        c.drawString(left_margin, y, " ".join(line_words))
                        y -= 0.2 * inch

                elif block.type == "dialogue":
                    char_name = block.char_name or "UNKNOWN"
                    line = block.line or ""
                    parenthetical = block.parenthetical

                    # Character name (centered, offset right)
                    c.setFont("Courier-Bold", 12)
                    name_x = left_margin + 2 * inch
                    c.drawString(name_x, y, char_name.upper())
                    y -= 0.2 * inch

                    if parenthetical:
                        c.setFont("Courier", 12)
                        paren_x = left_margin + 1.5 * inch
                        c.drawString(paren_x, y, f"({parenthetical})")
                        y -= 0.2 * inch

                    # Dialogue line (centered block)
                    c.setFont("Courier", 12)
                    dialog_x = left_margin + 1 * inch
                    dialog_width = content_width - 2 * inch
                    words = line.split()
                    line_words = []
                    for word in words:
                        test = " ".join(line_words + [word])
                        if c.stringWidth(test, "Courier", 12) < dialog_width:
                            line_words.append(word)
                        else:
                            c.drawString(dialog_x, y, " ".join(line_words))
                            y -= 0.2 * inch
                            line_words = [word]
                    if line_words:
                        c.drawString(dialog_x, y, " ".join(line_words))
                        y -= 0.2 * inch

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
