"""
ARDT FMS - BOM PDF Generator Service

Generates ADesc-format PDFs from BOM data with:
- Header info (SN Number, Mat Number, Date, Revision, Software Version)
- BOM Summary Table (Order, Size, Chamfer, Type, Count, Mat #, Family #, Group)
- Cutter Layout Grid (Blades B1-B7, Rows R1-R4, Locations)
"""

import io
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class BOMPDFGenerator:
    """Generator for ADesc-format BOM PDFs."""

    # Color palette matching BOMLine.DEFAULT_COLORS
    DEFAULT_COLORS = [
        "#4A4A4A",  # Order 1: Dark gray
        "#9E9E9E",  # Order 2: Light gray
        "#6B6B6B",  # Order 3: Medium gray
        "#E0E0E0",  # Order 4: White/Light
        "#2196F3",  # Order 5: Blue
        "#FF9800",  # Order 6: Orange
        "#4CAF50",  # Order 7: Green
        "#9C27B0",  # Order 8: Purple
        "#F44336",  # Order 9: Red
        "#00BCD4",  # Order 10: Cyan
    ]

    def __init__(self, bom):
        """Initialize generator with BOM instance."""
        self.bom = bom
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            'Header',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
        ))
        self.styles.add(ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            alignment=1,  # Center
        ))
        self.styles.add(ParagraphStyle(
            'TableCell',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=1,  # Center
        ))

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple (0-1 range)."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def generate(self) -> bytes:
        """Generate PDF and return as bytes."""
        buffer = io.BytesIO()

        # Create document - landscape A4 for better table fit
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        # Build story (content)
        story = []

        # Header section
        story.extend(self._build_header())
        story.append(Spacer(1, 10 * mm))

        # BOM Summary table
        story.extend(self._build_bom_table())
        story.append(Spacer(1, 10 * mm))

        # Cutter layout grid (if positions exist)
        cutter_positions = self.bom.cutter_positions.all()
        if cutter_positions.exists():
            story.extend(self._build_cutter_grid(cutter_positions))

        # Build document
        doc.build(story)

        return buffer.getvalue()

    def _build_header(self) -> list:
        """Build header section with BOM info."""
        elements = []

        # Header info table
        header_data = [
            ['SN Number:', self.bom.source_sn_number or '0',
             'Mat Number:', self.bom.source_mat_number or self.bom.code,
             'Date Created:', datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')],
            ['Revision Level:', self.bom.source_revision_level or self.bom.revision,
             'ADesc Software Version:', self.bom.source_software_version or '1.0',
             '', ''],
        ]

        header_table = Table(header_data, colWidths=[80, 80, 90, 100, 80, 120])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTNAME', (4, 0), (4, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(header_table)
        return elements

    def _build_bom_table(self) -> list:
        """Build BOM summary table."""
        elements = []

        # Table header
        header_row = ['Order', 'Size', 'Chamfer', 'Type', 'Count', 'Mat #', 'Family #', 'Group']

        # Get BOM lines ordered by order_number
        lines = self.bom.lines.all().order_by('order_number', 'line_number')

        # Build table data
        table_data = [header_row]

        for line in lines:
            row = [
                str(line.order_number),
                line.cutter_size or '-',
                line.cutter_chamfer or '-',
                line.cutter_type or '-',
                str(line.quantity),
                line.hdbs_code or '-',
                line.family_number or '',
                '',  # Group (color) - will be shown as background
            ]
            table_data.append(row)

        if len(table_data) == 1:
            # No lines
            table_data.append(['No BOM lines', '', '', '', '', '', '', ''])

        # Create table
        col_widths = [50, 60, 70, 80, 50, 70, 60, 50]
        bom_table = Table(table_data, colWidths=col_widths)

        # Style
        style_commands = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # All cells
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ROWHEIGHT', (0, 0), (-1, -1), 20),
        ]

        # Add color backgrounds for Group column based on order number
        for idx, line in enumerate(lines, start=1):
            try:
                color_hex = line.color_code or self.DEFAULT_COLORS[(line.order_number - 1) % len(self.DEFAULT_COLORS)]
                rgb = self._hex_to_rgb(color_hex)
                style_commands.append(('BACKGROUND', (0, idx), (0, idx), colors.Color(*rgb)))
                style_commands.append(('TEXTCOLOR', (0, idx), (0, idx), colors.white))
                style_commands.append(('BACKGROUND', (-1, idx), (-1, idx), colors.Color(*rgb)))
            except (ValueError, IndexError):
                pass

        bom_table.setStyle(TableStyle(style_commands))
        elements.append(bom_table)

        # Total row
        total_count = sum(line.quantity for line in lines)
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph(
            f"<b>Total Cutters: {total_count}</b>",
            self.styles['Normal']
        ))

        return elements

    def _build_cutter_grid(self, positions) -> list:
        """Build cutter layout grid section."""
        elements = []

        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph(
            "<b>Cutter Layout Grid</b>",
            self.styles['Heading2']
        ))
        elements.append(Spacer(1, 3 * mm))

        # Group positions by blade and row
        grid_data = {}
        for pos in positions:
            key = (pos.blade_number, pos.row_number)
            if key not in grid_data:
                grid_data[key] = []
            grid_data[key].append(pos)

        # Build grid table
        # Locations as columns
        locations = ['CONE', 'NOSE', 'SHOULDER', 'GAUGE', 'PAD']
        header_row = ['Blade', 'Row'] + locations
        table_data = [header_row]

        # Get unique blade/row combinations
        blade_rows = sorted(grid_data.keys())

        for blade_num, row_num in blade_rows:
            row = [f'B{blade_num}', f'R{row_num}']
            positions_in_row = grid_data.get((blade_num, row_num), [])

            for loc in locations:
                loc_positions = [p for p in positions_in_row if p.blade_location == loc]
                if loc_positions:
                    # Show cutter type and order
                    cell_content = '\n'.join([
                        f"{p.cutter_type_display or p.bom_line.cutter_type if p.bom_line else ''}\n{p.order_number_display or ''}"
                        for p in loc_positions
                    ])
                    row.append(cell_content)
                else:
                    row.append('')

            table_data.append(row)

        if len(table_data) > 1:
            grid_table = Table(table_data, colWidths=[40, 30, 80, 80, 80, 80, 80])
            grid_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ]))
            elements.append(grid_table)
        else:
            elements.append(Paragraph(
                "<i>No cutter positions defined</i>",
                self.styles['Normal']
            ))

        return elements


def generate_bom_pdf(bom) -> bytes:
    """
    Convenience function to generate a BOM PDF.

    Args:
        bom: BOM model instance

    Returns:
        PDF content as bytes
    """
    generator = BOMPDFGenerator(bom)
    return generator.generate()
