"""
Unified Halliburton PDF Extractor using PyMuPDF (fitz)
Extracts text, coordinates, colors, fonts, shapes, and lines from PDF files.
"""

import fitz
import re
import io
import base64
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from collections import deque
import hashlib
import os


@dataclass
class Word:
    """Word with full coordinate and style info"""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    font: str = ""
    size: float = 0.0
    color: int = 0
    block_no: int = 0
    line_no: int = 0
    word_no: int = 0

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2


@dataclass
class Shape:
    """Shape/drawing element"""
    shape_type: str  # 'rect', 'line', 'circle', etc.
    rect: Tuple[float, float, float, float]  # x0, y0, x1, y1
    fill_color: Optional[Tuple[float, ...]] = None
    stroke_color: Optional[Tuple[float, ...]] = None
    items: List = field(default_factory=list)

    @property
    def x0(self) -> float:
        return self.rect[0]

    @property
    def y0(self) -> float:
        return self.rect[1]

    @property
    def x1(self) -> float:
        return self.rect[2]

    @property
    def y1(self) -> float:
        return self.rect[3]

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def is_circle(self) -> bool:
        """Check if shape is approximately circular"""
        return abs(self.width - self.height) < 2 and self.width > 5


@dataclass
class BOMRow:
    """Bill of Materials row"""
    index: int
    size: str
    chamfer: str
    cutter_type: str
    count: int
    mat_number: str
    family_number: str = ""
    fill_color: str = ""  # Hex color extracted from PDF shapes


@dataclass
class PDFData:
    """Complete extracted PDF data"""
    header: Dict[str, str]
    words: List[Word]
    shapes: List[Shape]
    bom_rows: List[BOMRow]
    blades: List[Dict]
    groups: List[int]
    page_width: float
    page_height: float


# Position name mapping (reversed names in PDF)
POS_MAP = {
    "ENOC": "CONE", "ESON": "NOSE", "REDLUOHS": "SHOULDER",
    "EGUAG": "GAUGE", "DAP": "PAD",
    "CONE": "CONE", "NOSE": "NOSE", "SHOULDER": "SHOULDER",
    "GAUGE": "GAUGE", "PAD": "PAD"
}


def extract_pdf_data(pdf_path: str) -> dict:
    """
    Main extraction function - extracts all data from PDF using PyMuPDF.
    Returns dict compatible with existing app.py interface.
    """
    doc = fitz.open(pdf_path)
    page = doc[0]

    # Get page dimensions
    page_width = page.rect.width
    page_height = page.rect.height

    # 1. Extract all words with coordinates and styles
    words = extract_words_with_style(page)

    # 2. Get raw words for accurate number extraction (mat numbers get split in spans)
    raw_words = page.get_text('words')  # (x0, y0, x1, y1, word, block, line, word_no)

    # 3. Extract all shapes/drawings
    shapes = extract_shapes(page)

    # 4. Extract header info (pass raw_words for accurate mat number extraction)
    header = extract_header(words, raw_words)

    # 5. Extract BOM table (pass raw_words for mat numbers)
    bom_rows = extract_bom(words, shapes, raw_words)

    # 6. Extract blade layouts using raw words for accuracy
    blades = extract_blades_v2(raw_words, bom_rows)

    # 7. Extract groups (returns tuple: (groups, has_legend, group_data, group_format))
    groups_result = extract_groups(words, raw_words)
    if len(groups_result) == 4:
        groups, has_group_legend, group_data, group_format = groups_result
    else:
        # Backward compatibility
        groups, has_group_legend = groups_result[:2]
        group_data = []
        group_format = 'unknown'

    # 8. Extract images (drill bit face, group shapes)
    # Pass group_data for matching shapes to groups in vertical format
    images = extract_images(page, doc, group_data, group_format)

    # 9. Cross-validate BOM indices and CL group numbers
    validation = validate_bom_cl_consistency(bom_rows, blades)

    # 10. Extract fill colors for BOM rows from shapes
    bom_colors = extract_bom_colors(shapes, bom_rows, page_height)

    # 11. Extract cutter shape images from CL area
    cutter_shapes = extract_cutter_shapes(page, raw_words, bom_rows)

    # 12. Extract drill bit face image
    drill_bit_image = extract_drill_bit_image(page)

    doc.close()

    # Return in format compatible with app.py
    return {
        'header': header,
        'summary': [
            {
                'index': row.index,
                'size': row.size,
                'chamfer': row.chamfer,
                'type': row.cutter_type,
                'count': row.count,
                'mat_number': row.mat_number,
                'family_number': row.family_number,
                'fill_color': bom_colors.get(row.index, get_default_group_color(row.index))
            }
            for row in bom_rows
        ],
        'groups': groups,
        'has_group_legend': has_group_legend,
        'group_format': group_format,  # 'comma', 'vertical', or 'unknown'
        'blades': blades,
        'images': images,
        'cutter_shapes': cutter_shapes,  # {index: {'width': w, 'height': h, 'data': base64}}
        'drill_bit_image': drill_bit_image,  # {'width': w, 'height': h, 'data': base64}
        'validation': validation,
        'raw_text': ' '.join(w.text for w in words),
        'extraction_stats': {
            'total_words': len(words),
            'total_shapes': len(shapes),
            'page_size': (page_width, page_height)
        }
    }


def extract_words_with_style(page) -> List[Word]:
    """Extract all words with full style information"""
    words = []

    # Get text as dictionary for style info
    text_dict = page.get_text('dict')

    for block in text_dict['blocks']:
        if 'lines' not in block:
            continue

        block_no = block.get('number', 0)

        for line_no, line in enumerate(block['lines']):
            for word_no, span in enumerate(line['spans']):
                text = span['text'].strip()
                if not text:
                    continue

                # Split span into individual words if contains spaces
                span_words = text.split()
                bbox = span['bbox']

                if len(span_words) == 1:
                    words.append(Word(
                        text=text.replace('\xad', '-'),
                        x0=bbox[0],
                        y0=bbox[1],
                        x1=bbox[2],
                        y1=bbox[3],
                        font=span.get('font', ''),
                        size=span.get('size', 0),
                        color=span.get('color', 0),
                        block_no=block_no,
                        line_no=line_no,
                        word_no=word_no
                    ))
                else:
                    # Approximate positions for multiple words in span
                    total_width = bbox[2] - bbox[0]
                    char_width = total_width / len(text) if text else 0
                    current_x = bbox[0]

                    for w in span_words:
                        w_width = len(w) * char_width
                        words.append(Word(
                            text=w.replace('\xad', '-'),
                            x0=current_x,
                            y0=bbox[1],
                            x1=current_x + w_width,
                            y1=bbox[3],
                            font=span.get('font', ''),
                            size=span.get('size', 0),
                            color=span.get('color', 0),
                            block_no=block_no,
                            line_no=line_no,
                            word_no=word_no
                        ))
                        current_x += w_width + char_width  # Add space

    return words


def extract_shapes(page) -> List[Shape]:
    """Extract all shapes/drawings from page"""
    shapes = []

    drawings = page.get_drawings()

    for d in drawings:
        rect = d.get('rect')
        if rect is None:
            continue

        # Determine shape type based on items
        items = d.get('items', [])
        shape_type = 'rect'

        # Check for circles (curve items)
        has_curves = any(item[0] == 'c' for item in items)
        if has_curves:
            shape_type = 'circle'

        # Check for lines
        if len(items) == 1 and items[0][0] == 'l':
            shape_type = 'line'

        shapes.append(Shape(
            shape_type=shape_type,
            rect=(rect.x0, rect.y0, rect.x1, rect.y1),
            fill_color=d.get('fill'),
            stroke_color=d.get('color'),
            items=items
        ))

    return shapes


def get_default_group_color(index: int) -> str:
    """Get default grayscale color for a group index"""
    # Define a palette of distinguishable grays
    colors = {
        1: '#e8e8e8',
        2: '#d0d0d0',
        3: '#b8b8b8',
        4: '#a0a0a0',
        5: '#888888',
        6: '#707070',
        7: '#585858',
        8: '#404040',
        9: '#333333',
        10: '#c0c0c0',
        11: '#989898',
        12: '#686868',
        13: '#505050',
        14: '#383838',
        15: '#f0f0f0',
        16: '#e0e0e0',
        17: '#d0d0d0',
        18: '#b0b0b0',
        19: '#909090',
        20: '#787878',
    }
    return colors.get(index, '#cccccc')


def extract_bom_colors(shapes: List[Shape], bom_rows: List, page_height: float) -> Dict[int, str]:
    """
    Extract fill colors from shapes in the BOM area and map them to BOM row indices.

    Returns dict mapping index -> hex color string.
    If all extracted colors are the same (uniform background), returns empty dict
    so that default palette is used instead.
    """
    bom_colors = {}

    if not bom_rows:
        return bom_colors

    # Find the y-range of BOM rows (based on typical PDF layout)
    # BOM is usually in top 20% of page, starting around y=50-150
    bom_y_start = 50
    bom_y_end = min(200, page_height * 0.2)

    # Find shapes in BOM area - look for small rectangles (row indicator boxes)
    # These are typically at the leftmost position (x < 70) with heights around 10-20px
    bom_shapes = []
    for shape in shapes:
        if (shape.y0 >= bom_y_start and shape.y0 <= bom_y_end and
            shape.x0 < 70 and  # Leftmost column
            shape.fill_color and
            10 < shape.width < 50 and
            8 < shape.height < 25):
            bom_shapes.append(shape)

    # Sort shapes by y position
    bom_shapes.sort(key=lambda s: s.y0)

    # Try to match shapes to BOM rows by y-position
    for row in bom_rows:
        # We don't have exact y positions for rows, but we can use index to estimate
        # Typical row height is about 13-15 pixels
        estimated_y = bom_y_start + 15 + (row.index - 1) * 14

        # Find closest shape to this estimated y
        best_shape = None
        best_dist = float('inf')
        for shape in bom_shapes:
            dist = abs(shape.y0 - estimated_y)
            if dist < best_dist and dist < 20:  # Within 20px
                best_dist = dist
                best_shape = shape

        if best_shape and best_shape.fill_color:
            # Convert fill color (RGB tuple 0-1) to hex string
            fill = best_shape.fill_color
            hex_color = '#%02x%02x%02x' % (
                int(fill[0] * 255),
                int(fill[1] * 255),
                int(fill[2] * 255)
            )
            bom_colors[row.index] = hex_color

    # Check if all colors are the same (uniform background)
    # If so, return empty dict to use default palette instead
    unique_colors = set(bom_colors.values())
    if len(unique_colors) <= 1:
        # All colors are the same or no colors found - use defaults
        return {}

    return bom_colors


def make_image_transparent(image_bytes: bytes, tolerance: int = 30) -> 'Image':
    """
    Remove background from image using flood-fill from edges.
    Only removes pixels connected to edges that match the background color.
    Preserves all original colors in the image content.

    Args:
        image_bytes: Raw image bytes
        tolerance: Color distance threshold for flood-fill (lower = more conservative)
    """
    if not HAS_PIL:
        return None

    img = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
    pixels = img.load()
    w, h = img.size

    # Get corner colors to detect background
    corners = [pixels[0, 0][:3], pixels[w-1, 0][:3], pixels[0, h-1][:3], pixels[w-1, h-1][:3]]

    # Use darkest corner as background
    dark_corners = [c for c in corners if sum(c) < 150]
    bg_color = dark_corners[0] if dark_corners else (0, 0, 0)

    def color_dist(c1, c2):
        return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5

    visited = set()
    queue = deque()

    # Start from all edges
    for x in range(w):
        queue.append((x, 0))
        queue.append((x, h-1))
    for y in range(h):
        queue.append((0, y))
        queue.append((w-1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or x < 0 or x >= w or y < 0 or y >= h:
            continue
        visited.add((x, y))

        current = pixels[x, y][:3]
        if color_dist(current, bg_color) <= tolerance:
            pixels[x, y] = (current[0], current[1], current[2], 0)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                queue.append((x + dx, y + dy))

    return img


def image_to_base64(img: 'Image') -> str:
    """Convert PIL Image to base64 data URL"""
    if not HAS_PIL or img is None:
        return ""

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f'data:image/png;base64,{b64}'


def extract_cutter_shapes(page, raw_words: List, bom_rows: List) -> Dict[int, Dict]:
    """
    Extract cutter shape images from the CL (Cutter Layout) area.
    Maps each BOM index to its shape image using hybrid matching:
    1. First try containment (index center inside shape bounds)
    2. Fall back to looking for shapes directly below the index

    Uses proportional thresholds for dynamic PDF handling.
    Returns dict: {index: {'width': w, 'height': h, 'data': base64_url}}
    """
    if not HAS_PIL:
        return {}

    import hashlib

    cutter_shapes = {}
    image_list = page.get_images(full=True)
    bom_indices = set(row.index for row in bom_rows)
    doc = page.parent

    # Use proportional threshold for CL area (below header/BOM area)
    page_height = page.rect.height
    cl_area_y_threshold = page_height * 0.15  # CL area starts ~15% down

    # Build hash -> image data map and collect all shape rectangles
    hash_to_image = {}
    shape_rects = []  # List of (hash, w, h, x0, y0, x1, y1)

    # Method 1: Extract XObject images via get_images()
    for img_info in image_list:
        xref = img_info[0]
        try:
            base_image = doc.extract_image(xref)
            w, h = base_image['width'], base_image['height']

            # Only cutter-sized images (20-200px)
            if not (20 < w < 200 and 20 < h < 200):
                continue

            img_hash = hashlib.md5(base_image['image']).hexdigest()[:12]

            # Store image data (deduplicated by hash)
            if img_hash not in hash_to_image:
                pil_img = Image.open(io.BytesIO(base_image['image']))
                trans_img = make_transparent_floodfill(pil_img)
                if trans_img:
                    hash_to_image[img_hash] = {
                        'width': w,
                        'height': h,
                        'data': image_to_base64(trans_img)
                    }

            # Collect all rectangles in CL area
            rects = page.get_image_rects(xref)
            for rect in rects:
                if rect.y0 > cl_area_y_threshold:
                    shape_rects.append((img_hash, w, h, rect.x0, rect.y0, rect.x1, rect.y1))
        except:
            continue

    # Method 2: Extract inline images via get_text() - these are NOT in get_images()
    # Some PDFs embed shapes as inline images in the content stream
    try:
        import fitz as fitz_module
        text_dict = page.get_text('dict', flags=fitz_module.TEXT_PRESERVE_IMAGES)
        for block in text_dict.get('blocks', []):
            if block.get('type') == 1:  # Image block
                bbox = block.get('bbox', [])
                if len(bbox) < 4 or bbox[1] <= cl_area_y_threshold:
                    continue

                w = block.get('width', 0)
                h = block.get('height', 0)
                img_data = block.get('image')

                if not img_data or not (20 < w < 200 and 20 < h < 200):
                    continue

                img_hash = hashlib.md5(img_data).hexdigest()[:12]
                x0, y0, x1, y1 = bbox

                # Store image data (deduplicated by hash)
                if img_hash not in hash_to_image:
                    try:
                        pil_img = Image.open(io.BytesIO(img_data))
                        trans_img = make_transparent_floodfill(pil_img)
                        if trans_img:
                            hash_to_image[img_hash] = {
                                'width': w,
                                'height': h,
                                'data': image_to_base64(trans_img)
                            }
                    except:
                        continue

                # Add to shape rects
                if img_hash in hash_to_image:
                    shape_rects.append((img_hash, w, h, x0, y0, x1, y1))
    except:
        pass  # If inline image extraction fails, continue with XObject images only

    # Get ALL occurrences of each index in CL area
    index_occurrences = {idx: [] for idx in bom_indices}
    for rw in raw_words:
        x0, y0, x1, y1, text = rw[0], rw[1], rw[2], rw[3], rw[4]
        if text.isdigit() and len(text) <= 2 and y0 > cl_area_y_threshold:
            idx = int(text)
            if idx in bom_indices:
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                index_occurrences[idx].append((x0, y0, x1, y1, cx, cy))

    # Match shapes to indices using CONTAINMENT only
    # The index number must be INSIDE the shape's bounding rectangle
    # This correctly handles indices without shapes (like WCMAT400 matrix pads)
    for idx in bom_indices:
        occurrences = index_occurrences[idx]
        if not occurrences:
            continue

        found_hash = None

        # Containment matching - index center must be inside shape bounds
        for ox0, oy0, ox1, oy1, ocx, ocy in occurrences:
            for shash, w, h, sx0, sy0, sx1, sy1 in shape_rects:
                if sx0 <= ocx <= sx1 and sy0 <= ocy <= sy1:
                    found_hash = shash
                    break
            if found_hash:
                break

        if found_hash and found_hash in hash_to_image:
            img_data = hash_to_image[found_hash]
            cutter_shapes[idx] = {
                'width': img_data['width'],
                'height': img_data['height'],
                'data': img_data['data']
            }

    return cutter_shapes


def extract_drill_bit_image(page) -> Optional[Dict]:
    """Extract drill bit face image with transparent background"""
    if not HAS_PIL:
        return None

    image_list = page.get_images(full=True)
    doc = page.parent

    for img_info in image_list:
        xref = img_info[0]
        try:
            base_image = doc.extract_image(xref)
            rects = page.get_image_rects(xref)
        except:
            continue

        w = base_image['width']
        h = base_image['height']

        # Drill bit face is typically 150-250 pixels, roughly square
        # Must be in header/BOM area (y < 200) and right side (x > 500)
        if 140 <= w <= 300 and 140 <= h <= 300:
            # Check position - should be in upper right area
            if rects:
                rect = rects[0]
                if rect.x0 > 500 and rect.y0 < 200:
                    image_bytes = base_image['image']
                    trans_img = make_image_transparent(image_bytes)
                    if trans_img:
                        return {
                            'width': w,
                            'height': h,
                            'data': image_to_base64(trans_img)
                        }

    return None


def extract_header(words: List[Word], raw_words: List = None) -> Dict[str, str]:
    """Extract header information from words using position-based matching"""
    header = {
        'sn_number': '0',
        'mat_number': '',
        'date_created': '',
        'revision_level': '',
        'software_version': ''
    }

    # Get header region words (top 60 pixels - expanded for different layouts)
    header_words = [w for w in words if w.y0 < 60]

    # SN Number - find after "SN Number:"
    sn_words = [w for w in header_words if w.text == 'SN']
    if sn_words:
        sn_word = sn_words[0]
        # Find numeric value on same line after SN
        nearby = [w for w in header_words
                  if w.x0 > sn_word.x0 and abs(w.y0 - sn_word.y0) < 5
                  and w.text.isdigit()]
        if nearby:
            header['sn_number'] = min(nearby, key=lambda w: w.x0).text

    # Mat Number - use raw_words for accurate extraction (styled words may split numbers)
    # First find "Mat" or "Number:" label position
    mat_label = [w for w in header_words if w.text == 'Mat' or ('Mat' in w.text and 'Number' in w.text)]
    if mat_label and raw_words:
        mat_word = mat_label[0]

        # Find "Date" word to know where to stop on first line
        date_word = [w for w in header_words if w.text == 'Date']
        date_x = date_word[0].x0 if date_word else 9999

        # Use raw_words for mat number extraction - raw words preserve full numbers
        raw_header = [(rw[0], rw[1], rw[4]) for rw in raw_words if rw[1] < 40]

        # Find mat number value - digits after "Number:" label and before "Date"
        mat_value_candidates = sorted([
            (x, y, text) for x, y, text in raw_header
            if x > mat_word.x1 - 10 and x < date_x
            and abs(y - mat_word.y0) < 10
            and text and text[0].isdigit()
        ], key=lambda t: t[0])

        if mat_value_candidates:
            mat_x, mat_y, mat_text = mat_value_candidates[0]

            # Collect all text at similar x-position (multi-line mat number)
            mat_parts = [mat_text]

            # Check for continuation on next lines (same x-position)
            next_line_parts = sorted([
                (x, y, text) for x, y, text in [(rw[0], rw[1], rw[4]) for rw in raw_words]
                if abs(x - mat_x) < 30
                and y > mat_y + 3 and y < mat_y + 25
                and text not in ['Revision', 'Level:', 'ADesc', 'Software', 'Version:', 'D', '-']
                and not re.match(r'^\d+/\d+/\d+$', text)
            ], key=lambda t: (t[1], t[0]))

            for x, y, text in next_line_parts:
                if re.match(r'^\d+/\d+/\d+$', text):
                    continue
                if text in ['Revision', 'Level:', 'ADesc', 'Software', 'Version:', 'D', '-']:
                    continue
                mat_parts.append(text)

            # Join parts, preserving underscores
            mat_num = ' '.join(mat_parts).replace('_ ', '_').strip()
            header['mat_number'] = mat_num

    # Fallback: If MAT number is empty, try to find it with different patterns
    if not header.get('mat_number') and raw_words:
        # Look for any text that looks like a MAT number (digits possibly followed by M/M1/M2 etc)
        raw_header = [(rw[0], rw[1], rw[4]) for rw in raw_words if rw[1] < 50]

        # Try to find MAT number pattern: 6-7 digits optionally followed by M, M1, M2, etc.
        for x, y, text in raw_header:
            if re.match(r'^\d{6,7}[A-Z]?\d*$', text):  # e.g., 1251085, 1251085M, 1251085M2
                # Make sure it's not a date or version number
                if not re.match(r'^\d+/\d+/\d+', text) and 'Version' not in text:
                    header['mat_number'] = text
                    break

    # Date Created - format: MM/DD/YYYY HH:MM:SS AM/PM
    date_label = [w for w in header_words if 'Created' in w.text]
    if date_label:
        date_word = date_label[0]
        nearby = sorted([w for w in header_words
                        if w.x0 > date_word.x1 - 5 and abs(w.y0 - date_word.y0) < 8
                        and w.text not in ['Date', 'Created:']],
                       key=lambda w: w.x0)
        if nearby:
            # Collect date/time parts - might be in various formats
            date_parts = []
            for w in nearby[:4]:  # date, time, AM/PM (up to 4 parts)
                if w.text and w.text not in ['Date', 'Created:', 'Revision', 'Level:']:
                    date_parts.append(w.text)
            header['date_created'] = ' '.join(date_parts)

    # Revision Level - can be "D 390254", "D-390254", "390254", or text after digits
    rev_label = [w for w in header_words if w.text == 'Level:' or 'Level' in w.text]
    if rev_label:
        rev_word = rev_label[0]

        # Find the x-position of "ADesc" or "Software" to know where to stop
        stop_x = 9999
        for w in header_words:
            if 'ADesc' in w.text or w.text == 'Software':
                if abs(w.y0 - rev_word.y0) < 5:
                    stop_x = w.x0
                    break

        # Find all words after "Level:" until we hit the stop position
        # Use x1 - small margin to catch words that might slightly overlap
        nearby = sorted([w for w in header_words
                        if w.x0 >= rev_word.x1 - 5 and w.x0 < stop_x
                        and abs(w.y0 - rev_word.y0) < 5
                        and w.text != 'Level:'],
                       key=lambda w: w.x0)
        if nearby:
            # Collect all parts of the revision level (prefix + number + suffix)
            rev_parts = []
            for w in nearby:
                clean = w.text.replace('\xad', '-').replace('–', '-').replace('�', '-').strip()
                if clean and clean not in ['-', '–']:
                    rev_parts.append(clean)
            if rev_parts:
                # Join parts with space, preserving the original format
                header['revision_level'] = ' '.join(rev_parts)

    # Software Version - format: 1.0.XXXX.XXXXX
    ver_label = [w for w in header_words if w.text == 'Version:']
    if ver_label:
        ver_word = ver_label[0]
        # Use >= to catch version numbers that start exactly where label ends
        nearby = [w for w in header_words
                  if w.x0 >= ver_word.x1 - 5 and abs(w.y0 - ver_word.y0) < 5
                  and re.match(r'^\d+\.\d+\.', w.text)]
        if nearby:
            header['software_version'] = min(nearby, key=lambda w: w.x0).text

    return header


def extract_bom(words: List[Word], shapes: List[Shape], raw_words: List = None) -> List[BOMRow]:
    """Extract BOM table using dynamic column-position-based parsing"""
    bom_rows = []
    seen_indices = set()

    # Find BOM header row and column positions
    # The BOM header row contains multiple labels (SIZE, CHAMFER, TYPE, COUNT, MAT) on the same line
    header_labels = ['SIZE', 'CHAMFER', 'TYPE', 'COUNT', 'MAT']

    # Group potential header labels by y-position to find the actual BOM header row
    labels_by_y = defaultdict(dict)  # y_key -> {label: (x, y)}
    for w in words:
        text_upper = w.text.upper().strip()
        for label in header_labels:
            # Require exact match or very close match (e.g., "Mat" for "MAT", "Size" for "SIZE")
            # Don't match labels embedded in other words (like "MAT" in "WC-MAT400")
            if text_upper == label or (text_upper == label.capitalize()):
                y_key = round(w.y0 / 5) * 5
                # Only store first occurrence of each label at this y-level
                if label not in labels_by_y[y_key]:
                    labels_by_y[y_key][label] = (w.x0, w.y0)
                break

    # Find the y-position with the most DISTINCT header labels (this is the BOM header row)
    column_positions = {}
    header_y = None
    best_y = None
    best_count = 0

    for y_key, labels_dict in labels_by_y.items():
        distinct_count = len(labels_dict)
        if distinct_count > best_count:
            best_count = distinct_count
            best_y = y_key

    if best_y is not None and best_count >= 2:  # Need at least 2 distinct labels
        for label, (x, y) in labels_by_y[best_y].items():
            column_positions[label] = x
            if header_y is None:
                header_y = y

    # Find leftmost column position for index
    if column_positions:
        min_x = min(column_positions.values())
        # Index column is typically to the left of SIZE
        index_x = min_x - 30

    # Build mat number lookup from raw_words
    mat_numbers_by_row = {}
    mat_col_x = column_positions.get('MAT', 280)  # default if not found

    if raw_words:
        for rw in raw_words:
            x0, y0, x1, y1, text = rw[0], rw[1], rw[2], rw[3], rw[4]
            # Mat numbers are 5+ digits near mat column
            if text.isdigit() and len(text) >= 5:
                if abs(x0 - mat_col_x) < 50:  # Within 50px of mat column
                    row_key = round(y0 / 5) * 5
                    mat_numbers_by_row[row_key] = text

    # Find BOM data region dynamically
    # BOM ends where the Cutter Layout (CL) area begins
    # CL indicators: blade markers (B1, B2, etc.) or position labels (CONE, NOSE, SHOULDER, GAUGE, PAD)
    if header_y is not None:
        bom_y_start = header_y + 5

        # Find the start of CL area by looking for blade markers or position labels
        cl_indicators = []
        if raw_words:
            for rw in raw_words:
                x0, y0, text = rw[0], rw[1], rw[4]
                # Blade markers: B1, B2, B3, etc.
                if re.match(r'^B\d+$', text):
                    cl_indicators.append(y0)
                # Position labels (may appear reversed in some PDFs)
                elif text.upper() in ['CONE', 'NOSE', 'SHOULDER', 'GAUGE', 'PAD',
                                       'ENOC', 'ESON', 'REDLUOHS', 'EGUAG', 'DAP']:
                    cl_indicators.append(y0)

        # BOM ends at the first CL indicator (with margin), or use fallback
        if cl_indicators:
            bom_y_end = min(cl_indicators) - 10  # 10px margin before CL starts
        else:
            bom_y_end = bom_y_start + 200  # Fallback if no CL indicators found

        # Also use raw_words for more accurate extraction
        if raw_words:
            # First, find the index column by looking for sequential digits (1, 2, 3...)
            # at consistent X positions before the SIZE column
            size_x = column_positions.get('SIZE', 70)
            potential_indices = []  # [(x, y, digit)]

            for rw in raw_words:
                x0, y0, text = rw[0], rw[1], rw[4]
                # Index digits: 1-2 digits (1-99), before SIZE column, in BOM area
                if (text.isdigit() and len(text) <= 2 and 1 <= int(text) <= 99
                    and x0 < size_x - 10
                    and bom_y_start <= y0 <= bom_y_end):
                    potential_indices.append((x0, y0, int(text)))

            # Group potential indices by X position to find the index column
            index_col_x = None
            if potential_indices:
                # Find X position where we have sequential indices (may not start at 1)
                x_groups = defaultdict(list)
                for x, y, digit in potential_indices:
                    x_key = round(x / 10) * 10  # Group within 10px
                    x_groups[x_key].append((y, digit))

                # Find the X group with the most indices that appear sequential
                best_x_key = None
                best_count = 0
                for x_key, indices in x_groups.items():
                    indices_sorted = sorted(indices, key=lambda i: i[0])  # Sort by Y
                    digits = [d for _, d in indices_sorted]
                    # Check for sequential pattern (each digit is prev+1)
                    if len(digits) >= 2:
                        sequential_count = 1
                        for i in range(1, len(digits)):
                            if digits[i] == digits[i-1] + 1:
                                sequential_count += 1
                        if sequential_count > best_count:
                            best_count = sequential_count
                            best_x_key = x_key
                    elif len(digits) == 1 and digits[0] >= 1:
                        # Single index is valid too
                        if best_count == 0:
                            best_x_key = x_key
                            best_count = 1

                if best_x_key is not None:
                    index_col_x = best_x_key

            # Collect all BOM data
            bom_data = []
            for rw in raw_words:
                x0, y0, x1, y1, text = rw[0], rw[1], rw[2], rw[3], rw[4]
                text = text.replace('\xad', '-').strip()
                if bom_y_start <= y0 <= bom_y_end and text:
                    bom_data.append((x0, y0, text))

            # Use detected index positions as row anchors
            # Each row is defined by its index digit position, with data gathered from surrounding y-range
            index_positions = []  # [(y, index_value)]
            if index_col_x is not None:
                for x, y, text in bom_data:
                    if text.isdigit() and len(text) <= 2 and 1 <= int(text) <= 99:
                        if abs(x - index_col_x) < 15:
                            index_positions.append((y, int(text)))

            # Sort by y position and build rows around each index
            index_positions.sort(key=lambda p: p[0])

            # Group data into rows based on index positions
            # Assign each data point to the CLOSEST index row (not all rows within range)
            rows_dict = defaultdict(list)
            for x, y, text in bom_data:
                # Find the closest index position for this data point
                closest_idx_y = None
                min_dist = float('inf')
                for idx_y, idx_val in index_positions:
                    dist = abs(y - idx_y)
                    if dist < min_dist and dist <= 10:  # Max 10px from index
                        min_dist = dist
                        closest_idx_y = idx_y
                if closest_idx_y is not None:
                    rows_dict[closest_idx_y].append((x, text))

            # Fallback: if no index positions found, use simple y-grouping
            if not rows_dict and bom_data:
                for x, y, text in bom_data:
                    row_key = round(y / 8) * 8  # Larger grouping
                    rows_dict[row_key].append((x, text))

            # First pass: collect count values in count column separately
            # (counts sometimes appear at slightly different y than rest of row)
            count_col_x = column_positions.get('COUNT', 244)
            count_values = []  # [(y, count_value)]
            for x, y, text in bom_data:
                # Allow count values up to 3 digits (1-999)
                if text.isdigit() and len(text) <= 3 and int(text) > 0:
                    if abs(x - count_col_x) < 30:
                        count_values.append((y, int(text)))

            # Parse each row - validate using index column position
            parsed_rows = []  # [(row_y, row_data)]
            expected_index = 1  # Track expected sequential index

            for row_y in sorted(rows_dict.keys()):
                row_items = sorted(rows_dict[row_y], key=lambda item: item[0])

                row_data = {
                    'index': None,
                    'size': None,
                    'chamfer': None,
                    'type': None,
                    'count': None,
                    'mat_number': None,
                    'actual_y': row_y
                }

                for x, text in row_items:
                    # Index: 1-2 digits (1-99) at index column position
                    # Validate: must be at expected X position and match expected sequence
                    if text.isdigit() and len(text) <= 2 and 1 <= int(text) <= 99:
                        if row_data['index'] is None:
                            # Use detected index column or fallback to before SIZE
                            if index_col_x is not None:
                                if abs(x - index_col_x) < 15:  # Within 15px of index column
                                    row_data['index'] = int(text)
                            elif 'SIZE' in column_positions and x < column_positions['SIZE'] - 10:
                                row_data['index'] = int(text)

                    # Type: CT pattern (full match like CT31NL, CT217NL)
                    if re.match(r'^CT\d+\w*$', text, re.I):
                        row_data['type'] = text
                    # Type: standalone "CT" - may need to combine with next word
                    elif text.upper() == 'CT' and row_data['type'] is None:
                        row_data['type'] = 'CT'  # Placeholder, will try to combine with digits
                        row_data['_ct_x'] = x  # Store position for later combining

                    # Type: WC-MAT pattern
                    if re.match(r'^WC[-\u00ad]?MAT\d*$', text, re.I):
                        row_data['type'] = text

                    # Type: PMT pattern
                    if text.upper() == 'PMT' or re.match(r'^PMT\d*\w*$', text, re.I):
                        row_data['type'] = text

                    # Type: CR pattern (variant of CT, possibly typos or alternate naming)
                    if re.match(r'^CR\d+\w*$', text, re.I):
                        row_data['type'] = text

                    # Type: ABS pattern
                    if text.upper() == 'ABS' or re.match(r'^ABS\d*\w*$', text, re.I):
                        row_data['type'] = text

                    # Type: CIA pattern (another cutter type)
                    if text.upper() == 'CIA' or re.match(r'^CIA\d*\w*$', text, re.I):
                        row_data['type'] = text

                    # FALLBACK: Capture ANY text in the TYPE column area if no type matched yet
                    # This ensures we don't miss unknown cutter types
                    if row_data['type'] is None and 'TYPE' in column_positions:
                        type_x = column_positions['TYPE']
                        # Check if this text is in the TYPE column (within 40px)
                        if abs(x - type_x) < 40:
                            # Skip if it looks like a known non-type field
                            if not text.isdigit() and text.upper() not in ['SIZE', 'CHAMFER', 'TYPE', 'COUNT', 'MAT', 'FAMILY', '#', 'NA', 'N/A']:
                                row_data['type'] = text

                    # Size: 4-digit number or with MM
                    if text.isdigit() and len(text) == 4:
                        if 'SIZE' in column_positions:
                            if abs(x - column_positions['SIZE']) < 30:
                                row_data['size'] = text
                    if 'MM' in text.upper():
                        row_data['size'] = text

                    # Count: 1-3 digit number in count column (initial assignment)
                    if text.isdigit() and len(text) <= 3:
                        if 'COUNT' in column_positions:
                            if abs(x - count_col_x) < 30:
                                row_data['count'] = int(text)

                    # Chamfer patterns - in CHAMFER column area
                    chamfer_x = column_positions.get('CHAMFER', 140)
                    if abs(x - chamfer_x) < 60:
                        # Various chamfer patterns
                        if re.match(r'^\d+C-?\d*$', text, re.I):  # 10C, 18C, 18C-60, 18C60
                            # Normalize format: add hyphen if missing
                            if re.match(r'^\d+C\d+$', text, re.I):  # 18C60 -> 18C-60
                                row_data['chamfer'] = text[:text.upper().index('C')+1] + '-' + text[text.upper().index('C')+1:]
                            else:
                                row_data['chamfer'] = text
                        elif re.match(r'^\d+-\d+$', text):  # 18-60 (chamfer without C)
                            row_data['chamfer'] = text
                        elif re.match(r'^U-?\d*$', text, re.I):  # U, U-60, U60
                            row_data['chamfer'] = text
                        elif text.upper() in ['NA', 'N/A']:
                            row_data['chamfer'] = 'NA'
                        elif 'DROP' in text.upper():  # DROP-IN, DROP IN
                            row_data['chamfer'] = 'DROP-IN'
                        elif text.upper() == 'IN':
                            # Could be part of DROP-IN
                            if row_data['chamfer'] and 'DROP' in row_data['chamfer'].upper():
                                row_data['chamfer'] = 'DROP-IN'
                            else:
                                # Check if previous item was DROP
                                row_data['chamfer'] = 'DROP-IN'

                    # Mat number: 5+ digit number in mat column area
                    mat_x = column_positions.get('MAT', 300)
                    if text.isdigit() and len(text) >= 5:
                        # Check if in mat column or nearby (use larger tolerance for varied layouts)
                        if abs(x - mat_x) < 100:
                            row_data['mat_number'] = text
                        elif row_data['mat_number'] is None and x > chamfer_x:
                            # Fallback: take any 5+ digit number after chamfer column as mat_number
                            row_data['mat_number'] = text

                    # Family number: pattern after mat number (often smaller numbers)
                    family_x = mat_x + 70  # Family # is usually after Mat #
                    if text.isdigit() and len(text) >= 3 and x > mat_x + 50:
                        if 'family_number' not in row_data or not row_data.get('family_number'):
                            row_data['family_number'] = text

                # Handle split CT types (e.g., "CT" and "179" as separate words)
                if row_data['type'] == 'CT' and '_ct_x' in row_data:
                    ct_x = row_data['_ct_x']
                    type_col_x = column_positions.get('TYPE', 240)
                    # Look for digits immediately after "CT" in the Type column area
                    for x, text in row_items:
                        # Digit/alphanumeric word close to CT position and in Type column
                        if x > ct_x and x < ct_x + 30 and abs(x - type_col_x) < 60:
                            if re.match(r'^\d+\w*$', text):  # Like "179", "31NL", "217NL"
                                row_data['type'] = 'CT' + text
                                break
                    # Clean up temporary marker
                    del row_data['_ct_x']

                # Store parsed row if valid
                if row_data['index'] and row_data['type']:
                    parsed_rows.append((row_y, row_data))

            # Second pass: assign orphan counts to nearest rows
            # This handles cases where count appears at slightly different y than rest of row
            for count_y, count_val in count_values:
                # Find which parsed row this count should belong to
                best_row = None
                best_dist = float('inf')
                for row_y, row_data in parsed_rows:
                    dist = abs(count_y - row_y)
                    if dist < best_dist and dist < 10:  # Within 10 pixels
                        best_dist = dist
                        best_row = row_data

                # Assign count if row doesn't have one or this is closer
                if best_row and best_row['count'] is None:
                    best_row['count'] = count_val

            # Create BOM rows from parsed data
            for row_y, row_data in parsed_rows:
                if row_data['index'] not in seen_indices:
                    bom_rows.append(BOMRow(
                        index=row_data['index'],
                        size=row_data['size'] or '',
                        chamfer=row_data['chamfer'] or '',
                        cutter_type=row_data['type'],
                        count=row_data['count'] or 0,
                        mat_number=row_data['mat_number'] or '',
                        family_number=row_data.get('family_number', '')
                    ))
                    seen_indices.add(row_data['index'])

    return sorted(bom_rows, key=lambda r: r.index)


def extract_blades(words: List[Word], shapes: List[Shape], bom_rows: List[BOMRow]) -> List[Dict]:
    """Extract blade layouts using word positions and shapes"""
    blades = []

    # Find blade markers (B1, B2, etc.)
    blade_markers = []
    for w in words:
        if re.match(r'^B\d+$', w.text):
            blade_markers.append((w.text, w.x0, w.y0, w.x1, w.y1))

    # Sort by y position
    blade_markers.sort(key=lambda b: b[2])

    if not blade_markers:
        return blades

    # Find circular shapes (cutter indicators)
    circles = [s for s in shapes if s.is_circle and s.width > 10]

    # Create type mapping from BOM
    type_map = {row.index: row.cutter_type for row in bom_rows}

    for i, (blade_name, bx0, by0, bx1, by1) in enumerate(blade_markers):
        # Define blade region
        y_start = blade_markers[i-1][2] + 20 if i > 0 else by0 - 80
        y_end = blade_markers[i+1][2] - 20 if i < len(blade_markers) - 1 else by0 + 80

        # Get words in blade region
        blade_words = [w for w in words if y_start <= w.y0 <= y_end]

        # Get circles in blade region
        blade_circles = [c for c in circles if y_start <= c.y0 <= y_end]

        # Parse R1 (above blade marker) and R2 (below blade marker)
        r1_words = [w for w in blade_words if w.y0 < by0]
        r2_words = [w for w in blade_words if w.y0 > by1]

        r1_circles = [c for c in blade_circles if c.y0 < by0]
        r2_circles = [c for c in blade_circles if c.y0 > by1]

        blade_data = {
            'name': blade_name,
            'r1': parse_row_layout(r1_words, r1_circles, type_map, is_r1=True),
            'r2': parse_row_layout(r2_words, r2_circles, type_map, is_r1=False)
        }

        blades.append(blade_data)

    return blades


def parse_row_layout(words: List[Word], circles: List[Shape], type_map: Dict[int, str], is_r1: bool) -> Dict:
    """Parse a row (R1 or R2) layout from words and circles"""
    result = {}

    # Find position labels
    positions_found = {}
    for w in words:
        pos_name = POS_MAP.get(w.text.upper())
        if pos_name:
            positions_found[pos_name] = (w.x0, w.y0)

    # Find cutter type words
    cutter_words = [w for w in words if re.match(r'^(CT\d+\w*|WC[-\u00ad]?MAT\d+)$', w.text)]

    # Find group numbers (single digits 1-4)
    group_words = [w for w in words if w.text.isdigit() and len(w.text) == 1 and 1 <= int(w.text) <= 4]

    # Find chamfer words
    chamfer_words = [w for w in words if re.match(r'^\d+C-?\d+$|^U-?\d+$', w.text, re.I)]

    # Match cutters to positions based on x-coordinate proximity
    for cutter_word in cutter_words:
        # Find closest position
        closest_pos = None
        min_dist = float('inf')

        for pos_name, (px, py) in positions_found.items():
            dist = abs(cutter_word.x0 - px)
            if dist < min_dist:
                min_dist = dist
                closest_pos = pos_name

        if closest_pos and min_dist < 100:
            if closest_pos not in result:
                result[closest_pos] = []

            # Find associated group number
            group = 1
            for gw in group_words:
                if abs(gw.x0 - cutter_word.x0) < 30 and abs(gw.y0 - cutter_word.y0) < 30:
                    group = int(gw.text)
                    break

            # Find associated chamfer
            chamfer = get_default_chamfer(cutter_word.text, is_r1)
            for cw in chamfer_words:
                if abs(cw.x0 - cutter_word.x0) < 50 and abs(cw.y0 - cutter_word.y0) < 20:
                    chamfer = cw.text
                    break

            result[closest_pos].append({
                'type': cutter_word.text,
                'group': group,
                'chamfer': chamfer
            })

    return result


def extract_blades_v2(raw_words: List, bom_rows: List[BOMRow]) -> List[Dict]:
    """
    Extract blade layouts using raw words for accuracy.
    Dynamically handles R1-R4 row markers.
    """
    blades = []

    # Create group to cutter type/chamfer mapping from BOM
    group_to_type = {row.index: row.cutter_type for row in bom_rows}
    group_to_chamfer = {row.index: row.chamfer for row in bom_rows}

    # Convert raw_words to easier format: (x, y, text)
    words_list = [(rw[0], rw[1], rw[4].replace('\xad', '-')) for rw in raw_words]

    # Find blade markers (B1, B2, etc.)
    blade_markers = [(x, y, text) for x, y, text in words_list if re.match(r'^B\d+$', text)]
    blade_markers.sort(key=lambda b: b[1])

    if not blade_markers:
        return blades

    # Find all row markers dynamically (R1, R2, R3, R4)
    row_markers = {}
    for row_name in ['R1', 'R2', 'R3', 'R4']:
        markers = [(x, y) for x, y, text in words_list if text == row_name]
        if markers:
            row_markers[row_name] = sorted(markers, key=lambda m: m[1])

    # Position labels
    position_labels = ['CONE', 'NOSE', 'SHOULDER', 'GAUGE', 'PAD']

    # Find all 1-2 digit numbers (potential group numbers)
    all_digits = [(x, y, int(text)) for x, y, text in words_list
                  if text.isdigit() and len(text) <= 2 and 1 <= int(text) <= 99]

    # Find all position labels with their locations
    all_positions = [(x, y, text.upper()) for x, y, text in words_list
                     if text.upper() in position_labels]

    # Find all chamfer patterns in blade areas
    # Patterns: 18C, 18C-60, 18-60, U, U-60, DROP-IN, NA
    chamfer_patterns = [(x, y, text) for x, y, text in words_list
                        if re.match(r'^\d+[cC](-\d+)?$', text) or      # 18C, 18C-60
                           re.match(r'^\d+-\d+$', text) or              # 18-60
                           re.match(r'^U-?\d*$', text, re.I) or         # U, U-60
                           'DROP' in text.upper() or                    # DROP-IN
                           text.upper() == 'NA']

    # Find all cutter type text (CT*, WC-MAT*, PMT, ABS, CR*) for position grouping
    all_cutter_types = [(x, y, text) for x, y, text in words_list
                        if re.match(r'^CT\d*', text, re.I) or
                           re.match(r'^WC[-\u00ad]?MAT', text, re.I) or
                           text.upper() in ['PMT', 'ABS', 'CIA'] or
                           re.match(r'^CR\d+', text, re.I) or
                           re.match(r'^CIA\d*', text, re.I)]

    # Get all row marker y-positions for better boundary detection
    all_r1_positions = sorted([y for x, y in row_markers.get('R1', [])])

    for blade_idx, (bx, by, blade_name) in enumerate(blade_markers):
        blade_data = {
            'name': blade_name,
            'r1': {},
            'r2': {},
            'r3': {},
            'r4': {}
        }

        # Define blade region
        # Use the next blade's first R marker as boundary (more accurate than blade marker)
        next_blade_y = blade_markers[blade_idx + 1][1] if blade_idx + 1 < len(blade_markers) else by + 120

        # Find the next blade's R1 position (which may be before the blade marker)
        blade_region_end = next_blade_y - 10
        for r1_y in all_r1_positions:
            if r1_y > by + 50:  # R1 that's clearly after this blade's content
                # Use this R1's position as boundary (with small margin)
                blade_region_end = min(blade_region_end, r1_y - 5)
                break

        # Find the R1 marker for THIS blade - R1 appears slightly BELOW the blade marker
        # Find the closest R1 to this blade marker (not just the first in range)
        this_blade_r1_y = None
        closest_distance = float('inf')
        for r1_y in all_r1_positions:
            # R1 should be close to blade marker (typically 5-15 units below)
            if by - 30 <= r1_y <= by + 40:
                distance = abs(r1_y - by)
                if distance < closest_distance:
                    closest_distance = distance
                    this_blade_r1_y = r1_y

        # Use R1 position if found, otherwise use blade marker
        if this_blade_r1_y is not None:
            # Blade content starts above R1 marker (cutter types/groups appear above R1)
            blade_region_start = this_blade_r1_y - 30
        else:
            blade_region_start = by - 50  # Fallback

        # Find row markers in this blade's region
        blade_rows = {}
        for row_name, markers in row_markers.items():
            row_in_blade = [(x, y) for x, y in markers if blade_region_start <= y <= blade_region_end]
            if row_in_blade:
                blade_rows[row_name] = row_in_blade[0][1]  # y position of this row

        # Find position labels and digits in blade region
        blade_positions = [(x, y, pos) for x, y, pos in all_positions
                          if blade_region_start <= y <= blade_region_end]
        blade_digits = [(x, y, g) for x, y, g in all_digits
                       if blade_region_start <= y <= blade_region_end]
        blade_chamfers = [(x, y, text) for x, y, text in chamfer_patterns
                         if blade_region_start <= y <= blade_region_end]

        # Process each row found in this blade
        if blade_rows:
            sorted_rows = sorted(blade_rows.items(), key=lambda r: r[1])

            for i, (row_name, row_y) in enumerate(sorted_rows):
                # Define y-range for this row's digits
                # IMPORTANT: Never extend beyond blade_region_end
                if i + 1 < len(sorted_rows):
                    next_row_y = sorted_rows[i + 1][1]
                    row_end = min((row_y + next_row_y) / 2, blade_region_end)
                else:
                    row_end = min(row_y + 45, blade_region_end)
                row_range = (row_y - 25, row_end)

                # Get digits in this row's range
                row_digits = [(x, y, g) for x, y, g in blade_digits
                             if row_range[0] <= y <= row_range[1]]

                # Filter to main y-level
                if row_digits:
                    y_counts = defaultdict(int)
                    for x, y, g in row_digits:
                        y_counts[round(y / 8) * 8] += 1
                    if y_counts:
                        main_y = max(y_counts.keys(), key=lambda k: y_counts[k])
                        row_digits = [(x, y, g) for x, y, g in row_digits if abs(y - main_y) <= 12]

                row_digits.sort(key=lambda d: d[0])

                # Get position labels for this row
                # Position labels appear ABOVE or AT the row marker level, not below
                # Use row_range to filter - labels should be within the row's y-range
                row_positions = {}
                for x, y, pos in blade_positions:
                    # Position label should be within row's range (above row marker, but within row content area)
                    # Labels appear at top of row content, so check if y is within row_range
                    if row_range[0] <= y <= row_range[1]:
                        if pos not in row_positions:
                            row_positions[pos] = x

                # Get cutter type positions for this row (cutter types appear above digits)
                row_cutter_types = [(x, y, text) for x, y, text in all_cutter_types
                                   if row_range[0] <= y <= row_range[1]]
                row_cutter_types.sort(key=lambda ct: ct[0])  # Sort by x

                # Get chamfers for this row - chamfers appear BELOW digits
                # Expand range to include chamfers below the row
                row_chamfers = [(x, y, text) for x, y, text in blade_chamfers
                               if row_range[0] - 10 <= y <= row_range[1] + 35]

                # Map row name to key
                row_key = row_name.lower()

                # Simple X-coordinate-based position assignment:
                # Sort position labels by X (left to right)
                # For each digit, find the position label that is to its LEFT
                # (the position with the largest X that is still <= digit X)
                sorted_positions = sorted(row_positions.items(), key=lambda p: p[1])

                for gx, gy, group_num in row_digits:
                    # Find position by X coordinate - the position whose X is closest to the LEFT of this digit
                    closest_pos = None
                    if sorted_positions:
                        # Find the rightmost position label that is <= digit X
                        for pos_name, pos_x in sorted_positions:
                            if pos_x <= gx:
                                closest_pos = pos_name
                            else:
                                break
                        # If no position is to the left, use the first position
                        if closest_pos is None:
                            closest_pos = sorted_positions[0][0]
                    else:
                        # No position labels found - use fallback
                        closest_pos = find_closest_position(gx, row_positions, position_labels)

                    if closest_pos not in blade_data[row_key]:
                        blade_data[row_key][closest_pos] = []

                    cutter_type = group_to_type.get(group_num, f'TYPE{group_num}')

                    # Find chamfer near this digit - chamfers are typically BELOW the digit
                    # Look for chamfer with similar x-coordinate and y below the digit
                    chamfer = ''
                    nearby_chamfers = [(x, y, text) for x, y, text in row_chamfers
                                      if abs(x - gx) < 20 and y > gy]  # Below the digit
                    if nearby_chamfers:
                        # Take the closest one below
                        nearby_chamfers.sort(key=lambda c: c[1])  # Sort by y
                        chamfer = nearby_chamfers[0][2]
                    else:
                        # Fallback: any chamfer within x-range
                        nearby_chamfers = [(x, y, text) for x, y, text in row_chamfers
                                          if abs(x - gx) < 20]
                        if nearby_chamfers:
                            chamfer = nearby_chamfers[0][2]

                    blade_data[row_key][closest_pos].append({
                        'type': cutter_type,
                        'group': group_num,
                        'chamfer': chamfer
                    })
        else:
            # No row markers - try to extract from blade area directly
            if blade_digits:
                y_counts = defaultdict(int)
                for x, y, g in blade_digits:
                    y_counts[round(y / 8) * 8] += 1
                if y_counts:
                    main_y = max(y_counts.keys(), key=lambda k: y_counts[k])
                    main_digits = [(x, y, g) for x, y, g in blade_digits if abs(y - main_y) <= 12]
                    main_digits.sort(key=lambda d: d[0])

                    row_positions = {pos: x for x, y, pos in blade_positions}

                    for gx, gy, group_num in main_digits:
                        closest_pos = find_closest_position(gx, row_positions, position_labels)
                        if closest_pos not in blade_data['r1']:
                            blade_data['r1'][closest_pos] = []

                        cutter_type = group_to_type.get(group_num, f'TYPE{group_num}')
                        chamfer = group_to_chamfer.get(group_num, '')

                        blade_data['r1'][closest_pos].append({
                            'type': cutter_type,
                            'group': group_num,
                            'chamfer': chamfer
                        })

        # Remove empty rows
        blade_data = {k: v for k, v in blade_data.items() if k == 'name' or v}
        if 'name' not in blade_data:
            blade_data['name'] = blade_name

        blades.append(blade_data)

    return blades


def find_closest_position(x: float, positions_dict: Dict[str, float], all_positions: List[str]) -> str:
    """
    Find position label for a given x coordinate.
    Uses nearest-neighbor approach: assigns cutter to the closest position label.
    """
    if positions_dict:
        # Find the nearest position label
        closest_pos = None
        min_dist = float('inf')
        for pos_name, pos_x in positions_dict.items():
            dist = abs(x - pos_x)
            if dist < min_dist:
                min_dist = dist
                closest_pos = pos_name

        if closest_pos:
            return closest_pos

    # Fallback: assign based on typical x ranges (if no position labels found)
    if x < 160:
        return 'CONE'
    elif x < 210:
        return 'NOSE'
    elif x < 290:
        return 'SHOULDER'
    elif x < 350:
        return 'GAUGE'
    else:
        return 'PAD'


def extract_groups(words: List[Word], raw_words: List = None, page=None) -> Tuple[List[dict], bool]:
    """
    Extract group numbers from legend with their Y positions for shape matching.
    Returns (group_list, has_legend, group_data, group_format) where group_data contains:
    - For multi-row comma format: [{'values': '8,9', 'y': 78}, {'values': '7,11', 'y': 105}]
    - For vertical: [{'value': 2, 'y': 55}, {'value': 5, 'y': 70}]

    Handles various formats:
    - Multiple rows of comma-separated values (each row has its own shape)
    - Single comma-separated values like "1,4,6" (one shared shape)
    - Vertical list (each group has its own shape)
    """
    group_data = []
    has_legend = False
    group_format = 'unknown'
    all_groups = []  # Flat list of all group numbers

    # Find "Group" word
    group_label = None
    for w in words:
        if w.text.upper() == 'GROUP':
            group_label = w
            break

    if group_label:
        # Look for ALL comma-separated group values (can be multiple rows)
        comma_rows = []

        # Check raw_words for comma-separated values (more reliable)
        if raw_words:
            for rw in raw_words:
                x0, y0, text = rw[0], rw[1], rw[4]
                # Look for comma-separated numbers near Group column (within 50px of x, and below header)
                if y0 > group_label.y0 and y0 < group_label.y0 + 80:
                    if ',' in text:
                        parts = text.replace(' ', '').split(',')
                        parsed_groups = []
                        for part in parts:
                            if part.isdigit() and 1 <= int(part) <= 20:
                                parsed_groups.append(int(part))
                        if parsed_groups:
                            comma_rows.append({'values': text, 'parsed': parsed_groups, 'y': y0})
                            all_groups.extend(parsed_groups)

        # Also check styled words
        for w in words:
            if w.y0 > group_label.y0 and w.y0 < group_label.y0 + 80:
                if ',' in w.text:
                    parts = w.text.replace(' ', '').split(',')
                    parsed_groups = []
                    for part in parts:
                        if part.isdigit() and 1 <= int(part) <= 20:
                            parsed_groups.append(int(part))
                    if parsed_groups:
                        # Check if already added (by Y position)
                        if not any(abs(cr['y'] - w.y0) < 5 for cr in comma_rows):
                            comma_rows.append({'values': w.text, 'parsed': parsed_groups, 'y': w.y0})
                            all_groups.extend(parsed_groups)

        if comma_rows:
            # Sort by Y position
            comma_rows.sort(key=lambda r: r['y'])
            group_data = comma_rows
            has_legend = True
            group_format = 'multi_row' if len(comma_rows) > 1 else 'comma'

        # Check for vertical format: individual numbers below Group label
        if not group_data:
            vertical_groups = []
            for w in words:
                if (w.text.isdigit() and len(w.text) == 1 and 1 <= int(w.text) <= 9
                    and abs(w.x0 - group_label.x0) < 50
                    and w.y0 > group_label.y0 and w.y0 < group_label.y0 + 60):
                    vertical_groups.append({'value': int(w.text), 'y': w.y0})

            # Also check raw_words for vertical format
            if raw_words:
                for rw in raw_words:
                    x0, y0, text = rw[0], rw[1], rw[4]
                    if (text.isdigit() and len(text) == 1 and 1 <= int(text) <= 9
                        and abs(x0 - group_label.x0) < 50
                        and y0 > group_label.y0 and y0 < group_label.y0 + 60):
                        # Check if already added
                        if not any(g['value'] == int(text) and abs(g['y'] - y0) < 5 for g in vertical_groups):
                            vertical_groups.append({'value': int(text), 'y': y0})

            if vertical_groups:
                # Sort by Y position
                vertical_groups.sort(key=lambda g: g['y'])
                for g in vertical_groups:
                    g['format'] = 'vertical'
                group_data = vertical_groups
                has_legend = True
                group_format = 'vertical'

    # Return simplified format for backward compatibility
    if group_data:
        if group_format in ['comma', 'multi_row']:
            # Flatten all group numbers for backward compatibility
            all_nums = []
            for row in group_data:
                all_nums.extend(row.get('parsed', []))
            return (all_nums, has_legend, group_data, group_format)
        else:  # vertical
            return ([g['value'] for g in group_data], has_legend, group_data, group_format)
    else:
        return ([1, 3, 4], False, [], 'unknown')


def get_default_chamfer(cutter_type: str, is_r1: bool) -> str:
    """Get default chamfer for cutter type"""
    ctype = cutter_type.upper()
    if 'MAT' in ctype:
        return ''
    elif '179' in ctype or '200' in ctype:
        return 'U-60'
    else:
        return '18C-60' if is_r1 else ''


# Helper function to find words near a coordinate
def find_words_near(words: List[Word], x: float, y: float, radius: float = 20) -> List[Word]:
    """Find words within radius of a point"""
    return [
        w for w in words
        if abs(w.center_x - x) < radius and abs(w.center_y - y) < radius
    ]


# Helper function to find shapes containing a point
def find_shapes_containing(shapes: List[Shape], x: float, y: float) -> List[Shape]:
    """Find shapes that contain a point"""
    return [
        s for s in shapes
        if s.x0 <= x <= s.x1 and s.y0 <= y <= s.y1
    ]


def extract_images(page, doc, group_data=None, group_format='unknown') -> Dict:
    """
    Extract key images from the PDF page:
    - Halliburton logo (wide horizontal image in header)
    - Drill bit face (large image or small preview in header)
    - Group table shape(s) (cutter shape(s) near Group label)
      - For comma format: single shared shape
      - For vertical format: one shape per group, matched by Y position

    Returns dict with base64-encoded images.
    """
    import base64

    images_data = {
        'halliburton_logo': None,
        'drill_bit_face': None,
        'drill_bit_preview': None,
        'group_shape': None,        # Single shape (comma format)
        'group_shapes': [],         # Multiple shapes (vertical format)
        'group_format': group_format,
        'has_images': False
    }

    if group_data is None:
        group_data = []

    try:
        # Get all images on the page
        image_list = page.get_images(full=True)
        page_width = page.rect.width

        # Proportional thresholds
        drill_x_threshold = page_width * 0.55  # ~55% from left for drill bit
        group_x_threshold = page_width * 0.45  # ~45% from left for group shapes

        # Collect all image info with positions
        image_infos = []
        for img_info in image_list:
            xref = img_info[0]
            width = img_info[2]
            height = img_info[3]
            rects = page.get_image_rects(xref)
            if rects:
                image_infos.append((xref, width, height, rects[0]))

        # Collect potential group shapes (for vertical format matching)
        potential_group_shapes = []

        for xref, width, height, rect in image_infos:
            try:
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue

                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                b64_data = base64.b64encode(image_bytes).decode('utf-8')
                data_url = f"data:image/{image_ext};base64,{b64_data}"

                # 1. Halliburton logo - wide horizontal image in header (y < 50)
                if rect.y0 < 50 and width > height * 3 and width > 200:
                    if images_data['halliburton_logo'] is None:
                        images_data['halliburton_logo'] = {
                            'data': data_url,
                            'width': width,
                            'height': height
                        }
                        images_data['has_images'] = True

                # 2. Drill bit face/preview - in header area (far right, y < 180, larger size)
                # Must be position-based AND size-based to differentiate from group shapes
                # Drill bit: typically 100-300px, in far right (x > 75% of page width)
                elif rect.x0 > page_width * 0.75 and rect.y0 < 180 and 100 < width < 400 and 100 < height < 400:
                    # Store as drill_bit_face (the main one used in template)
                    if images_data['drill_bit_face'] is None:
                        images_data['drill_bit_face'] = {
                            'data': data_url,
                            'width': width,
                            'height': height,
                            'position': (rect.x0, rect.y0, rect.x1, rect.y1)
                        }
                        images_data['has_images'] = True
                    # Also keep as drill_bit_preview for fallback
                    if images_data['drill_bit_preview'] is None:
                        images_data['drill_bit_preview'] = {
                            'data': data_url,
                            'width': width,
                            'height': height,
                            'position': (rect.x0, rect.y0, rect.x1, rect.y1)
                        }

                # 3. Group shape(s) - small shapes in group area (middle-right, header)
                # Proper group shapes are typically smaller than CL shapes (which are 100x100, 81x90, 100x80)
                # Group shapes are usually around 70x66 or similar - exclude CL-sized shapes
                elif rect.x0 > group_x_threshold and rect.y0 < 130 and 20 < width < 80 and 20 < height < 80:
                    shape_info = {
                        'data': data_url,
                        'width': width,
                        'height': height,
                        'y0': rect.y0,
                        'y1': rect.y1,
                        'y_center': (rect.y0 + rect.y1) / 2
                    }
                    potential_group_shapes.append(shape_info)
                    images_data['has_images'] = True

            except Exception as e:
                continue

        # Process group shapes - match each shape with its group row by Y position
        if potential_group_shapes:
            # Sort by Y position
            potential_group_shapes.sort(key=lambda s: s['y0'])

            # Match each shape with its group row text by Y position
            for shape_info in potential_group_shapes:
                shape_y = shape_info['y_center']
                group_text = ''

                # Find the group row closest to this shape (by Y)
                if group_data and group_format in ['comma', 'multi_row']:
                    best_match = None
                    best_dist = float('inf')
                    for row in group_data:
                        row_y = row.get('y', 0)
                        dist = abs(shape_y - row_y)
                        if dist < best_dist and dist < 30:  # Within 30px
                            best_dist = dist
                            best_match = row
                    if best_match:
                        group_text = best_match.get('values', '')
                elif group_data and group_format == 'vertical':
                    # For vertical format, find the closest single number by Y position
                    best_match = None
                    best_dist = float('inf')
                    for row in group_data:
                        row_y = row.get('y', 0)
                        dist = abs(shape_y - row_y)
                        if dist < best_dist and dist < 30:  # Within 30px
                            best_dist = dist
                            best_match = row
                    if best_match:
                        group_text = str(best_match.get('value', ''))

                # Only include shapes that have a valid group_text match
                # This filters out CL shapes that happen to appear in header area
                if group_text:
                    images_data['group_shapes'].append({
                        'data': shape_info['data'],
                        'width': shape_info['width'],
                        'height': shape_info['height'],
                        'y0': shape_info['y0'],
                        'group_text': group_text
                    })

            # Set group_shape to first matched shape (not just first potential)
            if images_data['group_shapes']:
                images_data['group_shape'] = {
                    'data': images_data['group_shapes'][0]['data'],
                    'width': images_data['group_shapes'][0]['width'],
                    'height': images_data['group_shapes'][0]['height']
                }

        # Render drill bit preview from page (cleaner than extracted JPEG)
        if images_data.get('_drill_preview_rect'):
            try:
                x0, y0, x1, y1 = images_data['_drill_preview_rect']
                # Add small padding
                clip = fitz.Rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2)
                pix = page.get_pixmap(clip=clip, matrix=fitz.Matrix(1.5, 1.5), alpha=False)

                # Convert to PNG base64
                img_bytes = pix.tobytes("png")
                b64_data = base64.b64encode(img_bytes).decode('utf-8')

                images_data['drill_bit_preview'] = {
                    'data': f"data:image/png;base64,{b64_data}",
                    'width': int(x1 - x0),
                    'height': int(y1 - y0)
                }
                images_data['has_images'] = True
                del images_data['_drill_preview_rect']
            except Exception as e:
                pass

    except Exception as e:
        pass

    return images_data


def make_transparent_floodfill(img, tolerance=30):
    """
    Remove background using flood-fill from edges - creates clean transparent backgrounds.
    Only removes pixels connected to edges that match the background color.
    Preserves all original colors in the shape content.

    Args:
        img: PIL Image
        tolerance: Color distance threshold for flood-fill (lower = more conservative)

    Returns:
        PIL Image with transparent background
    """
    img = img.convert('RGBA')
    pixels = img.load()
    w, h = img.size

    # Get corner colors to detect background
    corners = [pixels[0, 0][:3], pixels[w-1, 0][:3], pixels[0, h-1][:3], pixels[w-1, h-1][:3]]

    # Use darkest corner as background (works for these PDFs)
    dark_corners = [c for c in corners if sum(c) < 150]
    bg_color = dark_corners[0] if dark_corners else (0, 0, 0)

    def color_dist(c1, c2):
        return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5

    visited = set()
    queue = deque()

    # Start from all edges
    for x in range(w):
        queue.append((x, 0))
        queue.append((x, h-1))
    for y in range(h):
        queue.append((0, y))
        queue.append((w-1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or x < 0 or x >= w or y < 0 or y >= h:
            continue
        visited.add((x, y))

        current = pixels[x, y][:3]
        if color_dist(current, bg_color) <= tolerance:
            pixels[x, y] = (current[0], current[1], current[2], 0)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                queue.append((x + dx, y + dy))

    # No additional color removal - preserve all original colors in the shape

    return img


def save_cutter_shapes_to_folder(pdf_path: str, output_folder: str = None) -> Dict[int, str]:
    """
    Extract cutter shapes (side view) from PDF and save them with transparent backgrounds.
    Shapes are named by their BOM index: Cutter_7.png, Cutter_8.png, etc.

    This extracts shapes from the CL area near group numbers, mapping each unique
    shape to its corresponding BOM index.

    Args:
        pdf_path: Path to the PDF file
        output_folder: Folder to save shapes. If None, creates 'extracted_shapes_<basename>/final_transparent/'

    Returns:
        Dict mapping index -> saved file path
    """
    if not HAS_PIL:
        print("PIL not available - cannot extract shapes")
        return {}

    # Determine output folder
    if output_folder is None:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        parent_dir = os.path.dirname(pdf_path)
        output_folder = os.path.join(parent_dir, f'extracted_shapes_{base_name}', 'final_transparent')

    os.makedirs(output_folder, exist_ok=True)

    doc = fitz.open(pdf_path)
    page = doc[0]

    # Get raw words for locating group numbers
    raw_words = page.get_text('words')

    # Extract BOM to get valid indices
    words = extract_words_with_style(page)
    shapes = extract_shapes(page)
    bom_rows = extract_bom(words, shapes, raw_words)
    bom_indices = set(row.index for row in bom_rows)

    # Find group number positions in CL area (y > 150 = below header/BOM)
    group_positions = {}
    for rw in raw_words:
        x0, y0, x1, y1, text = rw[0], rw[1], rw[2], rw[3], rw[4]
        if text.isdigit() and len(text) <= 2 and y0 > 150:
            group = int(text)
            if group in bom_indices and group not in group_positions:
                group_positions[group] = {
                    'cx': (x0 + x1) / 2,
                    'cy': (y0 + y1) / 2
                }

    # Build hash -> image map for deduplication
    image_list = page.get_images(full=True)
    hash_to_image = {}

    for img_info in image_list:
        xref = img_info[0]
        try:
            base_image = doc.extract_image(xref)
            w, h = base_image['width'], base_image['height']

            # Only cutter-sized images (20-200px)
            if not (20 < w < 200 and 20 < h < 200):
                continue

            img_bytes = base_image['image']
            img_hash = hashlib.md5(img_bytes).hexdigest()[:12]

            if img_hash not in hash_to_image:
                # Create transparent version using flood-fill
                pil_img = Image.open(io.BytesIO(img_bytes))
                trans_img = make_transparent_floodfill(pil_img)

                hash_to_image[img_hash] = {
                    'width': w,
                    'height': h,
                    'image': trans_img,
                    'xref': xref
                }
        except Exception as e:
            continue

    # Map each group to its nearest shape
    saved_files = {}

    for group, pos in group_positions.items():
        best_hash = None
        best_dist = float('inf')

        for img_hash, img_data in hash_to_image.items():
            xref = img_data['xref']
            try:
                rects = page.get_image_rects(xref)
            except:
                continue

            for rect in rects:
                if rect.y0 < 150:  # Skip header area images
                    continue

                img_cx = (rect.x0 + rect.x1) / 2
                img_cy = (rect.y0 + rect.y1) / 2
                dist = ((pos['cx'] - img_cx)**2 + (pos['cy'] - img_cy)**2)**0.5

                if dist < best_dist and dist < 65:  # Within 65px
                    best_dist = dist
                    best_hash = img_hash

        if best_hash:
            img_data = hash_to_image[best_hash]
            output_path = os.path.join(output_folder, f'Cutter_{group}.png')
            img_data['image'].save(output_path, 'PNG')
            saved_files[group] = output_path
            print(f"  Saved Cutter_{group}.png ({img_data['width']}x{img_data['height']})")

    doc.close()

    return saved_files


def validate_bom_cl_consistency(bom_rows: List[BOMRow], blades: List[Dict]) -> Dict:
    """
    Cross-validate BOM indices and CL (Cutter Layout) group numbers.
    Ensures consistency between BOM table and blade layouts.

    Returns a validation report with:
    - bom_indices: set of indices found in BOM
    - cl_groups: set of group numbers found in CL
    - is_valid: True if BOM and CL are consistent
    - messages: list of validation messages/warnings
    """
    validation = {
        'bom_indices': [],
        'cl_groups': [],
        'max_index': 0,
        'is_valid': True,
        'messages': []
    }

    # Collect BOM indices
    bom_indices = set()
    for row in bom_rows:
        bom_indices.add(row.index)

    # Collect CL group numbers from all blades
    cl_groups = set()
    for blade in blades:
        for row_key in ['r1', 'r2', 'r3', 'r4']:
            if row_key in blade and blade[row_key]:
                for pos, cells in blade[row_key].items():
                    for cell in cells:
                        if 'group' in cell:
                            cl_groups.add(cell['group'])

    validation['bom_indices'] = sorted(bom_indices)
    validation['cl_groups'] = sorted(cl_groups)

    # Determine the expected range (1 to max)
    all_indices = bom_indices | cl_groups
    if all_indices:
        max_index = max(all_indices)
        validation['max_index'] = max_index
        expected_range = set(range(1, max_index + 1))

        # Check for indices in BOM but not in CL
        bom_only = bom_indices - cl_groups
        if bom_only:
            validation['is_valid'] = False
            validation['messages'].append({
                'type': 'warning',
                'code': 'BOM_ONLY',
                'message': f"Index(es) {sorted(bom_only)} found in BOM but not used in CL"
            })

        # Check for groups in CL but not in BOM
        cl_only = cl_groups - bom_indices
        if cl_only:
            validation['is_valid'] = False
            validation['messages'].append({
                'type': 'error',
                'code': 'CL_ONLY',
                'message': f"Group(s) {sorted(cl_only)} used in CL but not defined in BOM"
            })

        # Check for gaps in sequence (missing from both)
        missing_from_both = expected_range - all_indices
        if missing_from_both:
            validation['messages'].append({
                'type': 'info',
                'code': 'SEQUENCE_GAP',
                'message': f"Sequence gap(s): {sorted(missing_from_both)} missing from both BOM and CL"
            })

        # Check if BOM and CL match exactly
        if bom_indices == cl_groups:
            if missing_from_both:
                validation['messages'].append({
                    'type': 'info',
                    'code': 'CONSISTENT_WITH_GAPS',
                    'message': f"BOM and CL are consistent (both have same indices: {sorted(bom_indices)})"
                })
            else:
                validation['messages'].append({
                    'type': 'success',
                    'code': 'FULLY_CONSISTENT',
                    'message': f"BOM and CL are fully consistent with complete sequence 1-{max_index}"
                })

        # Check for count mismatches between BOM and CL
        bom_counts = {row.index: row.count for row in bom_rows}
        cl_counts = {}
        for blade in blades:
            for row_key in ['r1', 'r2', 'r3', 'r4']:
                if row_key in blade and blade[row_key]:
                    for pos, cells in blade[row_key].items():
                        for cell in cells:
                            grp = cell.get('group')
                            if grp:
                                cl_counts[grp] = cl_counts.get(grp, 0) + 1

        for idx in bom_indices:
            bom_count = bom_counts.get(idx, 0)
            cl_count = cl_counts.get(idx, 0)
            if bom_count != cl_count:
                validation['is_valid'] = False
                validation['messages'].append({
                    'type': 'warning',
                    'code': 'COUNT_MISMATCH',
                    'message': f"Count mismatch: BOM index {idx} has Qty={bom_count}, but CL has {cl_count} cutters"
                })

    else:
        validation['messages'].append({
            'type': 'warning',
            'code': 'NO_DATA',
            'message': "No indices found in BOM or CL"
        })

    return validation
