"""
Halliburton PDF Generator - Multi-backend PDF generation

Supports multiple rendering backends with automatic fallback:
1. Playwright (browser-based, best quality)
2. WeasyPrint (pure Python, good quality)
3. HTML export (fallback, user prints to PDF)
"""

import os
import tempfile
import shutil
from jinja2 import Environment, FileSystemLoader

# Try to import rendering backends
PLAYWRIGHT_AVAILABLE = False
WEASYPRINT_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    pass

# Get the templates directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')


def has_cells_filter(row_data):
    """Custom Jinja2 filter to check if a row has any cutter cells"""
    if not row_data:
        return False
    for pos in ["CONE", "NOSE", "SHOULDER", "GAUGE", "PAD"]:
        if row_data.get(pos):
            return True
    return False


class HalliburtonPDFGenerator:
    """Generates Halliburton-style PDFs using Playwright browser-based rendering"""

    def __init__(self):
        """Initialize Jinja2 environment with custom filters"""
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True
        )
        # Register custom filters
        self.env.filters['has_cells'] = has_cells_filter
        self.env.tests['has_cells'] = has_cells_filter

    def _calculate_max_cutters(self, blades: list) -> int:
        """Calculate the maximum number of cutters in any single row across all blades."""
        max_cutters = 0
        for blade in blades:
            for row_key in ['r1', 'r2', 'r3', 'r4']:
                row = blade.get(row_key, {})
                if row:
                    cutter_count = 0
                    for pos in ['CONE', 'NOSE', 'SHOULDER', 'GAUGE', 'PAD']:
                        cells = row.get(pos, [])
                        cutter_count += len(cells)
                    if cutter_count > max_cutters:
                        max_cutters = cutter_count
        return max_cutters

    def _calculate_scale(self, max_cutters: int) -> float:
        """
        Calculate scale factor based on max cutters.
        Reference: 17 cutters = 100% (scale 1.0)
        Formula: scale = min(1.0, 17 / max_cutters)
        Minimum scale: 0.42 (for ~40 cutters) to ensure readability
        """
        if max_cutters <= 17:
            return 1.0
        scale = 17.0 / max_cutters
        # Minimum scale to ensure readability
        return max(0.42, scale)

    def generate(self, data: dict, output_path: str) -> str:
        """
        Generate PDF from data dictionary using HTML template.

        Tries multiple backends in order:
        1. Playwright (browser-based, best quality)
        2. WeasyPrint (pure Python, good quality)
        3. Falls back to HTML file if no PDF backend available

        Args:
            data: Dictionary containing header, summary, blades, images, groups
            output_path: Path to save the generated PDF

        Returns:
            Path to the generated PDF file
        """
        # Load the template
        template = self.env.get_template('pdf_template.html')

        # Calculate dynamic scale based on max cutters
        blades = data.get('blades', [])
        max_cutters = self._calculate_max_cutters(blades)
        scale = self._calculate_scale(max_cutters)

        # Normalize cutter_shapes keys to strings for consistent template access
        raw_cutter_shapes = data.get('cutter_shapes', {})
        cutter_shapes = {str(k): v for k, v in raw_cutter_shapes.items()} if raw_cutter_shapes else {}

        # Normalize cell.group values to strings in blades data for consistent template access
        for blade in blades:
            for row_key in ['r1', 'r2', 'r3', 'r4']:
                row = blade.get(row_key, {})
                if row:
                    for pos, cells in row.items():
                        for cell in cells:
                            if 'group' in cell:
                                cell['group'] = str(cell['group'])

        # Prepare template context
        context = {
            'header': data.get('header', {}),
            'summary': data.get('summary', []),
            'blades': blades,
            'images': data.get('images', {}),
            'cutter_shapes': cutter_shapes,  # {str_index: {'data': base64}}
            'drill_bit_image': data.get('drill_bit_image', None),  # {'data': base64}
            'groups': data.get('groups', []),
            'has_group_legend': data.get('has_group_legend', bool(data.get('groups'))),
            'group_format': data.get('group_format', 'comma'),
            'scale': scale,
            'max_cutters': max_cutters
        }

        # Render HTML
        html_content = template.render(**context)

        # Try Playwright first (best quality)
        if PLAYWRIGHT_AVAILABLE:
            try:
                return self._generate_with_playwright(html_content, output_path)
            except Exception as e:
                print(f"Playwright failed: {e}, trying WeasyPrint...")

        # Try WeasyPrint as fallback
        if WEASYPRINT_AVAILABLE:
            try:
                return self._generate_with_weasyprint(html_content, output_path)
            except Exception as e:
                print(f"WeasyPrint failed: {e}, saving as HTML...")

        # Last resort: save as HTML file
        return self._save_as_html(html_content, output_path)

    def _generate_with_playwright(self, html_content: str, output_path: str) -> str:
        """Generate PDF using Playwright browser rendering."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp:
            tmp.write(html_content)
            tmp_path = tmp.name

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(f'file:///{tmp_path}')
                page.wait_for_load_state('networkidle')
                page.pdf(
                    path=output_path,
                    format='Tabloid',
                    print_background=True,
                    margin={
                        'top': '0.2in',
                        'right': '0.25in',
                        'bottom': '0.2in',
                        'left': '0.25in'
                    }
                )
                browser.close()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return output_path

    def _generate_with_weasyprint(self, html_content: str, output_path: str) -> str:
        """Generate PDF using WeasyPrint."""
        html_doc = HTML(string=html_content)
        html_doc.write_pdf(output_path)
        return output_path

    def _save_as_html(self, html_content: str, output_path: str) -> str:
        """Save as HTML file (fallback when no PDF backend available)."""
        # Change extension to .html
        html_path = output_path.rsplit('.', 1)[0] + '.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return html_path


# Standalone function for direct PDF generation from dict
def generate_pdf_from_dict(data: dict, output_path: str) -> str:
    """Generate PDF from data dictionary"""
    generator = HalliburtonPDFGenerator()
    return generator.generate(data, output_path)
