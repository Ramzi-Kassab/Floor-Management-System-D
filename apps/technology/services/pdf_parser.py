"""
ARDT FMS - BOM PDF Parser Service (Enhanced)

Parses ADesc-format PDFs to extract:
- Header info (SN Number, Mat Number, Date, Revision, Software Version)
- BOM Summary Table (Order, Size, Chamfer, Type, Count, Mat #, Family #, Group)
- Cutter Layout Grid (Blades B1-B7, Rows R1-R4, Locations CONE/NOSE/SHOULDER/GAUGE/PAD)

This parser uses multiple extraction strategies to handle various PDF formats.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Tuple


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
    tables_data: list = field(default_factory=list)  # For debugging


class BOMPDFParser:
    """Enhanced parser for ADesc-format BOM PDFs."""

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

    # Known cutter type patterns
    CUTTER_TYPE_PATTERNS = [
        r'CT\d+[A-Z]*',      # CT418, CT179T, CT200NL
        r'WC-[A-Z0-9]+',     # WC-MAT400
        r'PDC\d+',           # PDC cutters
        r'TSP\d+',           # TSP cutters
    ]

    # Known chamfer patterns
    CHAMFER_PATTERNS = [
        r'\d+C-\d+',         # 18C-60
        r'U-\d+',            # U-60
        r'DROP-IN',
        r'NA',
    ]

    def __init__(self, pdf_path: str = None, pdf_bytes: bytes = None):
        """Initialize parser with PDF file path or bytes."""
        self.pdf_path = pdf_path
        self.pdf_bytes = pdf_bytes
        self.doc = None
        self.page = None
        self.raw_text = ""
        self.tables_data = []

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

            # Extract tables for debugging
            try:
                tables = self.page.find_tables()
                if tables and hasattr(tables, 'tables'):
                    for table in tables.tables:
                        try:
                            self.tables_data.append(table.extract())
                        except:
                            pass
                result.tables_data = self.tables_data
            except:
                pass

            # Parse components using multiple strategies
            result.header = self._parse_header()
            result.bom_lines = self._parse_bom_lines_smart()
            result.cutter_positions = self._parse_cutter_grid_smart()

        except Exception as e:
            result.errors.append(f"Error parsing PDF: {str(e)}")
        finally:
            if self.doc:
                self.doc.close()

        return result

    def _parse_header(self) -> BOMHeaderInfo:
        """Parse header information from PDF text."""
        header = BOMHeaderInfo()
        text = self.raw_text.replace('\xad', '-')

        # SN Number
        match = re.search(r'SN\s*Number[:\s]*(\S+)', text, re.IGNORECASE)
        if match:
            header.sn_number = match.group(1).strip()

        # Mat Number
        match = re.search(r'Mat\s*Number[:\s]*(\d+)', text, re.IGNORECASE)
        if match:
            header.mat_number = match.group(1).strip()

        # Date Created - try multiple formats
        date_patterns = [
            r'Date\s*Created[:\s]*(\d+/\d+/\d+\s+\d+:\d+:\d+\s*(?:AM|PM)?)',
            r'Date\s*Created[:\s]*(\d+-\d+-\d+\s+\d+:\d+:\d+)',
            r'Date\s*Created[:\s]*(\d+/\d+/\d+)',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                for fmt in ['%m/%d/%Y %I:%M:%S %p', '%m/%d/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y']:
                    try:
                        header.date_created = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                if header.date_created:
                    break

        # Revision Level
        match = re.search(r'Revision\s*Level[:\s]*([^\n]+)', text, re.IGNORECASE)
        if match:
            header.revision_level = match.group(1).strip().replace('\xad', '-')

        # Software Version
        match = re.search(r'ADesc\s*Software\s*Version[:\s]*([^\n]+)', text, re.IGNORECASE)
        if match:
            header.software_version = match.group(1).strip()

        return header

    def _parse_bom_lines_smart(self) -> List[BOMLineInfo]:
        """Smart BOM line extraction using multiple strategies."""
        bom_lines = []
        text = self.raw_text.replace('\xad', '-')

        # Strategy 1: Look for consolidated cell with all BOM data
        for table_data in self.tables_data:
            for row in table_data:
                if not row:
                    continue
                for cell in row:
                    if cell and 'Size' in str(cell) and 'Chamfer' in str(cell) and 'Type' in str(cell):
                        # This cell contains the BOM table header and data
                        lines = self._extract_bom_from_consolidated_cell(str(cell))
                        if lines:
                            bom_lines.extend(lines)

        # Strategy 2: Parse line-by-line format (each field on separate line)
        if not bom_lines:
            bom_lines = self._extract_bom_line_by_line_format(text)

        # Strategy 3: Look for structured table data from PyMuPDF
        if not bom_lines:
            for table_data in self.tables_data:
                lines = self._extract_bom_from_table(table_data)
                if lines:
                    bom_lines.extend(lines)

        # Strategy 4: Pattern matching on raw text
        if not bom_lines:
            bom_lines = self._extract_bom_from_text_patterns(text)

        # Strategy 5: Generic line-by-line analysis
        if not bom_lines:
            bom_lines = self._extract_bom_line_by_line(text)

        # Deduplicate by order number
        seen_orders = set()
        unique_lines = []
        for line in bom_lines:
            if line.order_number not in seen_orders:
                seen_orders.add(line.order_number)
                unique_lines.append(line)

        # Sort by order number
        unique_lines.sort(key=lambda x: x.order_number)

        return unique_lines

    def _extract_bom_line_by_line_format(self, text: str) -> List[BOMLineInfo]:
        """Extract BOM when each field is on a separate line.

        Format detected:
        Order#
        Size
        Chamfer
        Type
        Count
        Mat#
        """
        lines = []
        text_lines = text.split('\n')

        # Look for pattern: header followed by sequential field values
        # First, find where the BOM data starts (after headers)
        start_idx = 0
        for i, line in enumerate(text_lines):
            if 'Size' in line and 'Chamfer' in line and 'Type' in line:
                start_idx = i + 1
                break
            # Also check for single-word headers
            if line.strip() == 'Group':
                start_idx = i + 1
                break

        # Now parse sequential groups of 6 values
        i = start_idx
        while i < len(text_lines):
            line = text_lines[i].strip()

            # Check if this is an order number (1-2 digits alone on a line)
            if line.isdigit() and 1 <= int(line) <= 20:
                order_num = int(line)

                # Try to read the next 5 fields
                try:
                    # Collect the next few lines that are single values
                    fields = [line]  # order_number
                    j = i + 1
                    while j < len(text_lines) and len(fields) < 6:
                        next_line = text_lines[j].strip()
                        # Stop if we hit another order number or grid marker
                        if next_line and next_line.isdigit() and 1 <= int(next_line) <= 20 and len(fields) >= 5:
                            break
                        if next_line in ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'R1', 'R2', 'R3', 'R4']:
                            break
                        if next_line and next_line not in ['Group']:
                            fields.append(next_line)
                        j += 1

                    # Parse the fields if we have enough
                    if len(fields) >= 5:
                        bom_line = BOMLineInfo()
                        bom_line.order_number = order_num
                        bom_line.size = fields[1] if len(fields) > 1 else ""
                        bom_line.chamfer = fields[2] if len(fields) > 2 else ""
                        bom_line.cutter_type = fields[3] if len(fields) > 3 else ""

                        # Count should be a number
                        count_str = fields[4] if len(fields) > 4 else "0"
                        # Sometimes count has trailing space/text
                        count_match = re.match(r'^(\d+)', count_str)
                        bom_line.count = int(count_match.group(1)) if count_match else 0

                        bom_line.mat_number = fields[5] if len(fields) > 5 else ""

                        # Validate: count should be reasonable (1-200)
                        if bom_line.count > 0 and bom_line.count < 500:
                            # Validate cutter_type looks like a cutter
                            if re.match(r'^(CT|WC-|PDC|TSP)', bom_line.cutter_type):
                                color_idx = (bom_line.order_number - 1) % len(self.DEFAULT_COLORS)
                                bom_line.color_code = self.DEFAULT_COLORS[color_idx]
                                if not any(l.order_number == bom_line.order_number for l in lines):
                                    lines.append(bom_line)
                                i = j - 1  # Continue from where we left off

                except (ValueError, IndexError):
                    pass

            i += 1

        return lines

    def _extract_bom_from_consolidated_cell(self, cell_content: str) -> List[BOMLineInfo]:
        """Extract BOM lines from a cell that contains all BOM data."""
        lines = []
        cell_content = cell_content.replace('\xad', '-')

        # Split by newlines
        rows = cell_content.split('\n')

        # Skip header row
        for row_text in rows:
            row_text = row_text.strip()
            if not row_text:
                continue

            # Skip header line
            if 'Size' in row_text and 'Chamfer' in row_text:
                continue

            # Try to parse as BOM line
            parts = row_text.split()
            if not parts:
                continue

            first_part = parts[0]
            if not first_part.isdigit():
                continue

            order_num = int(first_part)
            if order_num < 1 or order_num > 20:
                continue

            # Check if this line has enough parts for a complete BOM line
            if len(parts) >= 4:
                try:
                    line = BOMLineInfo()
                    line.order_number = order_num

                    # Smart field detection - find the cutter type first
                    # Cutter types match patterns like CT###, WC-XXX, etc.
                    cutter_idx = -1
                    for idx, part in enumerate(parts[1:], 1):
                        if re.match(r'^(CT\d+|WC-\w+|PDC\d+|TSP\d+)', part):
                            cutter_idx = idx
                            break

                    if cutter_idx > 0:
                        # Fields before cutter_type are size and/or chamfer
                        pre_cutter_parts = parts[1:cutter_idx]
                        post_cutter_parts = parts[cutter_idx+1:]

                        line.cutter_type = parts[cutter_idx]

                        # Assign pre-cutter fields (could be size, chamfer, or both)
                        if len(pre_cutter_parts) >= 2:
                            line.size = pre_cutter_parts[0]
                            line.chamfer = pre_cutter_parts[1]
                        elif len(pre_cutter_parts) == 1:
                            # Single field - could be size or chamfer
                            val = pre_cutter_parts[0]
                            if re.match(r'^\d+$|^\d+MM$', val):
                                line.size = val
                            else:
                                line.chamfer = val

                        # Post-cutter fields: count, mat_number, family_number
                        if len(post_cutter_parts) >= 1 and post_cutter_parts[0].isdigit():
                            line.count = int(post_cutter_parts[0])
                        if len(post_cutter_parts) >= 2:
                            line.mat_number = post_cutter_parts[1]
                        if len(post_cutter_parts) >= 3:
                            line.family_number = post_cutter_parts[2]
                    else:
                        # Fallback to positional parsing
                        line.size = parts[1] if len(parts) > 1 else ""
                        line.chamfer = parts[2] if len(parts) > 2 else ""
                        line.cutter_type = parts[3] if len(parts) > 3 else ""
                        line.count = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                        line.mat_number = parts[5] if len(parts) > 5 else ""

                    color_idx = (line.order_number - 1) % len(self.DEFAULT_COLORS)
                    line.color_code = self.DEFAULT_COLORS[color_idx]

                    if line.count > 0 and line.cutter_type:
                        if not any(l.order_number == line.order_number for l in lines):
                            lines.append(line)
                except (ValueError, IndexError):
                    continue

        return lines

    def _extract_bom_from_table(self, table_data: List[List]) -> List[BOMLineInfo]:
        """Extract BOM lines from a table structure."""
        lines = []
        if not table_data:
            return lines

        for row in table_data:
            if not row or len(row) < 5:
                continue

            first_cell = str(row[0] or "").strip()

            # Check if first cell is an order number (1-2 digits)
            if first_cell.isdigit() and 1 <= int(first_cell) <= 99:
                try:
                    line = BOMLineInfo()
                    line.order_number = int(first_cell)

                    # Clean and assign values
                    if len(row) >= 2:
                        line.size = self._clean_cell(row[1])
                    if len(row) >= 3:
                        line.chamfer = self._clean_cell(row[2])
                    if len(row) >= 4:
                        line.cutter_type = self._clean_cell(row[3])
                    if len(row) >= 5:
                        count_str = self._clean_cell(row[4])
                        line.count = int(count_str) if count_str.isdigit() else 0
                    if len(row) >= 6:
                        line.mat_number = self._clean_cell(row[5])
                    if len(row) >= 7:
                        line.family_number = self._clean_cell(row[6])

                    # Assign color
                    color_idx = (line.order_number - 1) % len(self.DEFAULT_COLORS)
                    line.color_code = self.DEFAULT_COLORS[color_idx]

                    if line.count > 0 and (line.size or line.cutter_type):
                        lines.append(line)
                except (ValueError, IndexError):
                    continue

        return lines

    def _extract_bom_from_text_patterns(self, text: str) -> List[BOMLineInfo]:
        """Extract BOM lines using regex patterns on raw text."""
        lines = []

        # Pattern: Order Size Chamfer Type Count Mat#
        # Handle various spacing and formats
        patterns = [
            # Standard format: 1 1313 18C-60 CT418 17 1146346
            r'(\d{1,2})\s+(\d+(?:MM)?)\s+([\w\-]+)\s+((?:CT|WC-|PDC|TSP)[\w\-]+)\s+(\d+)\s+(\d+)',
            # With possible extra whitespace
            r'^(\d{1,2})\s+(\d+(?:MM)?)\s+([\w\-]+)\s+([\w\-]+)\s+(\d+)\s*(\d*)',
            # Tab separated
            r'(\d{1,2})\t+(\d+(?:MM)?)\t+([\w\-]+)\t+([\w\-]+)\t+(\d+)\t*(\d*)',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                try:
                    order_num = int(match.group(1))

                    # Skip if already found
                    if any(l.order_number == order_num for l in lines):
                        continue

                    line = BOMLineInfo()
                    line.order_number = order_num
                    line.size = match.group(2)
                    line.chamfer = match.group(3)
                    line.cutter_type = match.group(4)
                    line.count = int(match.group(5))
                    if len(match.groups()) >= 6 and match.group(6):
                        line.mat_number = match.group(6)

                    color_idx = (line.order_number - 1) % len(self.DEFAULT_COLORS)
                    line.color_code = self.DEFAULT_COLORS[color_idx]

                    if line.count > 0:
                        lines.append(line)
                except (ValueError, IndexError):
                    continue

        return lines

    def _extract_bom_line_by_line(self, text: str) -> List[BOMLineInfo]:
        """Last resort: analyze text line by line for BOM data."""
        lines_text = text.split('\n')
        bom_lines = []

        # Look for lines that start with a number and contain cutter-like data
        for i, line_text in enumerate(lines_text):
            line_text = line_text.strip()
            if not line_text:
                continue

            # Check if line starts with order number
            parts = line_text.split()
            if not parts:
                continue

            first_part = parts[0]
            if first_part.isdigit() and 1 <= int(first_part) <= 20:
                # This might be a BOM line
                # Try to parse remaining parts
                if len(parts) >= 5:
                    try:
                        line = BOMLineInfo()
                        line.order_number = int(first_part)

                        # Look for size (usually 4 digits or with MM)
                        for j, part in enumerate(parts[1:], 1):
                            if re.match(r'^\d{3,4}$|^\d+MM$', part):
                                line.size = part
                            elif re.match(r'^\d+C-\d+$|^U-\d+$|^NA$', part, re.IGNORECASE):
                                line.chamfer = part
                            elif re.match(r'^CT\d+|^WC-|^PDC|^TSP', part):
                                line.cutter_type = part
                            elif part.isdigit() and not line.count:
                                line.count = int(part)
                            elif part.isdigit() and line.count and not line.mat_number:
                                line.mat_number = part

                        color_idx = (line.order_number - 1) % len(self.DEFAULT_COLORS)
                        line.color_code = self.DEFAULT_COLORS[color_idx]

                        if line.count > 0 and (line.size or line.cutter_type):
                            if not any(l.order_number == line.order_number for l in bom_lines):
                                bom_lines.append(line)
                    except (ValueError, IndexError):
                        continue

        return bom_lines

    def _clean_cell(self, value) -> str:
        """Clean a table cell value."""
        if value is None:
            return ""
        return str(value).strip().replace('\xad', '-').replace('\n', ' ')

    def _parse_cutter_grid_smart(self) -> List[CutterPositionInfo]:
        """Smart cutter grid extraction."""
        positions = []
        text = self.raw_text.replace('\xad', '-')

        # Build a map of order_number -> cutter info from BOM lines
        # This helps us identify cutters in the grid

        # Find blade and row markers in text
        # Pattern: B1, B2, etc. followed by R1, R2, etc.
        current_blade = 0
        current_row = 0

        lines = text.split('\n')
        location_keywords = ['CONE', 'NOSE', 'SHOULDER', 'GAUGE', 'PAD']

        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check for blade marker
            blade_match = re.match(r'^B(\d+)$', line)
            if blade_match:
                current_blade = int(blade_match.group(1))
                current_row = 0
                continue

            # Check for row marker
            row_match = re.match(r'^R(\d+)$', line)
            if row_match:
                current_row = int(row_match.group(1))
                continue

            # Check for location data
            for loc in location_keywords:
                if loc in line:
                    # Extract cutters for this location
                    # Look for order numbers and cutter types nearby
                    loc_positions = self._extract_location_cutters(
                        lines, line_idx, current_blade, current_row, loc
                    )
                    positions.extend(loc_positions)

        return positions

    def _extract_location_cutters(
        self, lines: List[str], start_idx: int, blade: int, row: int, location: str
    ) -> List[CutterPositionInfo]:
        """Extract cutter positions for a specific location."""
        positions = []
        if blade == 0 or row == 0:
            return positions

        # Look at surrounding lines for order numbers and cutter types
        context_lines = lines[max(0, start_idx-2):min(len(lines), start_idx+3)]
        context = ' '.join(context_lines)

        # Find order numbers in context
        order_matches = re.findall(r'\b(\d)\b', context)

        position_count = 0
        for order_str in order_matches:
            order_num = int(order_str)
            if 1 <= order_num <= 10:  # Valid order range
                position_count += 1
                pos = CutterPositionInfo()
                pos.blade_number = blade
                pos.row_number = row
                pos.location = location
                pos.position_in_location = position_count
                pos.order_number = order_num
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
