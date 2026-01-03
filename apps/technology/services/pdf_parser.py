"""
ARDT FMS - BOM PDF Parser Service

Parses ADesc-format PDFs to extract:
- Header info (SN Number, Mat Number, Date, Revision, Software Version)
- BOM Summary Table (Order, Size, Chamfer, Type, Count, Mat #, Family #, Group)
- Cutter Layout Grid (Blades B1-B7, Rows R1-R4, Locations CONE/NOSE/SHOULDER/GAUGE/PAD)
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class BOMHeaderInfo:
    """Header information from PDF."""
    sn_number: str = ""
    mat_number: str = ""
    date_created: Optional[datetime] = None
    revision_level: str = ""
    software_version: str = ""


@dataclass
class BOMLineInfo:
    """Single BOM line from summary table."""
    order_number: int = 1
    size: str = ""
    chamfer: str = ""
    cutter_type: str = ""
    count: int = 0
    mat_number: str = ""
    family_number: str = ""
    group: str = ""
    color_code: str = ""


@dataclass
class CutterPositionInfo:
    """Single cutter position in the grid."""
    blade_number: int = 1
    row_number: int = 1
    location: str = ""  # CONE, NOSE, SHOULDER, GAUGE, PAD
    position_in_location: int = 1
    cutter_type: str = ""
    order_number: int = 1
    chamfer: str = ""


@dataclass
class ParsedBOMData:
    """Complete parsed data from PDF."""
    header: BOMHeaderInfo = field(default_factory=BOMHeaderInfo)
    bom_lines: list = field(default_factory=list)
    cutter_positions: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    raw_text: str = ""


class BOMPDFParser:
    """Parser for ADesc-format BOM PDFs."""

    # Default color palette matching BOMLine.DEFAULT_COLORS
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

    def __init__(self, pdf_path: str = None, pdf_bytes: bytes = None):
        """Initialize parser with PDF file path or bytes."""
        self.pdf_path = pdf_path
        self.pdf_bytes = pdf_bytes
        self.doc = None
        self.page = None
        self.raw_text = ""

    def parse(self) -> ParsedBOMData:
        """Parse the PDF and return structured data."""
        try:
            import fitz
        except ImportError:
            result = ParsedBOMData()
            result.errors.append("PyMuPDF (fitz) is not installed. Run: pip install pymupdf")
            return result

        result = ParsedBOMData()

        try:
            # Open PDF
            if self.pdf_bytes:
                self.doc = fitz.open(stream=self.pdf_bytes, filetype="pdf")
            elif self.pdf_path:
                self.doc = fitz.open(self.pdf_path)
            else:
                result.errors.append("No PDF source provided")
                return result

            if self.doc.page_count == 0:
                result.errors.append("PDF has no pages")
                return result

            self.page = self.doc[0]
            self.raw_text = self.page.get_text()
            result.raw_text = self.raw_text

            # Parse components
            result.header = self._parse_header()
            result.bom_lines = self._parse_bom_table()
            result.cutter_positions = self._parse_cutter_grid()

        except Exception as e:
            result.errors.append(f"Error parsing PDF: {str(e)}")
        finally:
            if self.doc:
                self.doc.close()

        return result

    def _parse_header(self) -> BOMHeaderInfo:
        """Parse header information from PDF text."""
        header = BOMHeaderInfo()

        # SN Number
        match = re.search(r'SN\s*Number[:\s]*(\S+)', self.raw_text, re.IGNORECASE)
        if match:
            header.sn_number = match.group(1).strip()

        # Mat Number
        match = re.search(r'Mat\s*Number[:\s]*(\d+)', self.raw_text, re.IGNORECASE)
        if match:
            header.mat_number = match.group(1).strip()

        # Date Created
        match = re.search(r'Date\s*Created[:\s]*(\d+/\d+/\d+\s*\d+:\d+:\d+\s*(?:AM|PM)?)', self.raw_text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            try:
                # Try common date formats
                for fmt in ['%m/%d/%Y %I:%M:%S %p', '%m/%d/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S']:
                    try:
                        header.date_created = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        # Revision Level
        match = re.search(r'Revision\s*Level[:\s]*(.+?)(?=\n|ADesc)', self.raw_text, re.IGNORECASE | re.DOTALL)
        if match:
            header.revision_level = match.group(1).strip().replace('\xad', '-')

        # Software Version
        match = re.search(r'ADesc\s*Software\s*Version[:\s]*(.+?)(?=\n|Size)', self.raw_text, re.IGNORECASE | re.DOTALL)
        if match:
            header.software_version = match.group(1).strip()

        return header

    def _parse_bom_table(self) -> list:
        """Parse BOM summary table from PDF."""
        bom_lines = []

        # Look for the structured table data
        # Format: Order Size Chamfer Type Count Mat# [Family#] [Group]
        # Example: 1 1313 18C-60 CT418 17 1146346
        # The table finder extracts this in a structured way

        try:
            tables = self.page.find_tables()
            if tables and hasattr(tables, 'tables'):
                for table in tables.tables:
                    try:
                        data = table.extract()
                        for row in data:
                            # Look for rows that match BOM line pattern
                            if row and len(row) >= 5:  # Reduced minimum to 5 for flexibility
                                first_cell = str(row[0] or "").strip()

                                # Check if first cell is a 1-2 digit number (order number)
                                if first_cell.isdigit() and len(first_cell) <= 2:
                                    try:
                                        line = BOMLineInfo()
                                        line.order_number = int(first_cell)

                                        # Try to extract fields, being flexible about column positions
                                        if len(row) >= 6:
                                            line.size = str(row[1] or "").strip().replace('\xad', '-')
                                            line.chamfer = str(row[2] or "").strip().replace('\xad', '-')
                                            line.cutter_type = str(row[3] or "").strip().replace('\xad', '-')
                                            line.count = int(str(row[4] or "0").strip() or "0")
                                            line.mat_number = str(row[5] or "").strip()

                                            if len(row) > 6 and row[6]:
                                                line.family_number = str(row[6]).strip()
                                        elif len(row) >= 5:
                                            # Compressed format
                                            line.size = str(row[1] or "").strip().replace('\xad', '-')
                                            line.chamfer = str(row[2] or "").strip().replace('\xad', '-')
                                            line.cutter_type = str(row[3] or "").strip().replace('\xad', '-')
                                            line.count = int(str(row[4] or "0").strip() or "0")

                                        # Assign default color
                                        color_idx = (line.order_number - 1) % len(self.DEFAULT_COLORS)
                                        line.color_code = self.DEFAULT_COLORS[color_idx]

                                        # Only add if we have valid data (size or cutter_type, and count > 0)
                                        if (line.size or line.cutter_type) and line.count > 0:
                                            # Check we don't already have this order number
                                            if not any(l.order_number == line.order_number for l in bom_lines):
                                                bom_lines.append(line)
                                    except (ValueError, IndexError) as e:
                                        continue
                    except Exception as table_err:
                        # Continue with next table if one fails
                        continue
        except Exception as e:
            # Table extraction completely failed, will use text fallback
            pass

        # Fallback: parse from raw text if table extraction failed or found nothing
        if not bom_lines:
            bom_lines = self._parse_bom_from_text()

        # Sort by order number
        bom_lines.sort(key=lambda x: x.order_number)

        return bom_lines

    def _parse_bom_from_text(self) -> list:
        """Fallback parser for BOM lines from raw text."""
        bom_lines = []
        text = self.raw_text.replace('\xad', '-')

        # Try multiple patterns for different PDF formats

        # Pattern 1: Standard format - Order Size Chamfer Type Count Mat#
        # Example: 1 1313 18C-60 CT418 17 1146346
        pattern1 = r'(\d{1,2})\s+(\d+(?:MM)?)\s+([\w\-]+)\s+([\w\-]+)\s+(\d+)\s+(\d+)'

        # Pattern 2: Flexible whitespace - handles various column alignments
        pattern2 = r'^(\d{1,2})\s+([A-Z0-9]+)\s+([\w\-]+)\s+([\w\-]+)\s+(\d+)\s+(\d+)'

        # Pattern 3: Tab-separated or multiple spaces
        pattern3 = r'(\d{1,2})[\s\t]+(\d+)[\s\t]+([\w\-]+)[\s\t]+([\w\-]+)[\s\t]+(\d+)[\s\t]+(\d+)'

        for pattern in [pattern1, pattern2, pattern3]:
            for match in re.finditer(pattern, text, re.MULTILINE):
                order_num = int(match.group(1))
                # Skip if we already have this order number
                if any(l.order_number == order_num for l in bom_lines):
                    continue

                line = BOMLineInfo()
                line.order_number = order_num
                line.size = match.group(2)
                line.chamfer = match.group(3)
                line.cutter_type = match.group(4)
                line.count = int(match.group(5))
                line.mat_number = match.group(6)

                # Assign default color
                color_idx = (line.order_number - 1) % len(self.DEFAULT_COLORS)
                line.color_code = self.DEFAULT_COLORS[color_idx]

                bom_lines.append(line)

        # Sort by order number
        bom_lines.sort(key=lambda x: x.order_number)

        return bom_lines

    def _parse_cutter_grid(self) -> list:
        """Parse cutter layout grid from PDF."""
        positions = []

        # The grid has structure:
        # B1 - R1 - [CONE locations] [NOSE] [SHOULDER] [GAUGE] [PAD]
        #    - R2 - [locations...]
        # etc.

        # Look for blade/row markers and their associated cutter data
        tables = self.page.find_tables()

        for table in tables.tables:
            data = table.extract()
            current_blade = 0
            current_row = 0

            for row in data:
                if not row:
                    continue

                first_cell = str(row[0] or "").strip()

                # Check for blade marker (B1, B2, etc.)
                blade_match = re.match(r'B(\d+)', first_cell)
                if blade_match:
                    current_blade = int(blade_match.group(1))
                    continue

                # Check for row marker (R1, R2, etc.) in any cell
                for cell_idx, cell in enumerate(row):
                    if cell:
                        row_match = re.search(r'R(\d+)', str(cell))
                        if row_match:
                            current_row = int(row_match.group(1))

                            # Parse the rest of the row for cutter data
                            # Look for patterns like: CT418 SHOULDER\n1 4 PAD\n18C-60 18C-60
                            for other_cell in row[cell_idx + 1:]:
                                if other_cell:
                                    positions.extend(
                                        self._parse_grid_cell(
                                            str(other_cell),
                                            current_blade,
                                            current_row
                                        )
                                    )
                            break

        return positions

    def _parse_grid_cell(self, cell_text: str, blade: int, row: int) -> list:
        """Parse a grid cell containing cutter data."""
        positions = []
        cell_text = cell_text.replace('\xad', '-')

        # Locations to look for
        locations = ['CONE', 'NOSE', 'SHOULDER', 'GAUGE', 'PAD']

        # Split by newlines
        lines = cell_text.split('\n')

        # Parse each section
        current_location = None
        cutter_types = []
        order_numbers = []
        chamfers = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line contains a location marker
            for loc in locations:
                if loc in line:
                    # Save previous location data
                    if current_location and cutter_types:
                        for idx, ct in enumerate(cutter_types):
                            pos = CutterPositionInfo()
                            pos.blade_number = blade
                            pos.row_number = row
                            pos.location = current_location
                            pos.position_in_location = idx + 1
                            pos.cutter_type = ct
                            if idx < len(order_numbers):
                                try:
                                    pos.order_number = int(order_numbers[idx])
                                except ValueError:
                                    pos.order_number = 1
                            if idx < len(chamfers):
                                pos.chamfer = chamfers[idx]
                            positions.append(pos)

                        cutter_types = []
                        order_numbers = []
                        chamfers = []

                    current_location = loc
                    # Extract cutter types from this line (before location marker)
                    parts = line.split(loc)[0].strip().split()
                    cutter_types.extend([p for p in parts if p and not p.isdigit()])
                    break
            else:
                # Line doesn't contain location, could be order numbers, chamfers, or cutter types
                parts = line.split()
                for part in parts:
                    if part.isdigit():
                        order_numbers.append(part)
                    elif re.match(r'[\d\w]+-\d+|U-\d+|NA', part):
                        chamfers.append(part)
                    elif re.match(r'CT\d+|WC-\w+', part):
                        cutter_types.append(part)

        # Save last location data
        if current_location and cutter_types:
            for idx, ct in enumerate(cutter_types):
                pos = CutterPositionInfo()
                pos.blade_number = blade
                pos.row_number = row
                pos.location = current_location
                pos.position_in_location = idx + 1
                pos.cutter_type = ct
                if idx < len(order_numbers):
                    try:
                        pos.order_number = int(order_numbers[idx])
                    except ValueError:
                        pos.order_number = 1
                if idx < len(chamfers):
                    pos.chamfer = chamfers[idx]
                positions.append(pos)

        return positions


def parse_bom_pdf(file_path: str = None, file_bytes: bytes = None) -> ParsedBOMData:
    """
    Convenience function to parse a BOM PDF.

    Args:
        file_path: Path to PDF file
        file_bytes: PDF file content as bytes

    Returns:
        ParsedBOMData with extracted information
    """
    parser = BOMPDFParser(pdf_path=file_path, pdf_bytes=file_bytes)
    return parser.parse()
