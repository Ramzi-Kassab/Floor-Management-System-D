#!/usr/bin/env python3
"""
Correct Shape Extraction Method for Cutter Map PDFs

This script extracts cutter shapes from PDF files and maps them to BOM indices
using CONTAINMENT-based matching: the index number position must be INSIDE
the shape's bounding rectangle.

Key principles:
1. Use containment-based matching (index position inside shape bounds)
2. Use unique rectangle positions (deduplicated with rounding)
3. Include all valid cutter shapes (no filtering by occurrence count)
4. Use proportional thresholds for dynamic PDF handling
"""

import fitz  # PyMuPDF
import hashlib
from PIL import Image
import io
import os
from collections import defaultdict


def make_transparent_floodfill(pil_img, tolerance=30):
    """
    Make background transparent using flood-fill from edges.
    This removes white/light backgrounds while preserving the shape.
    """
    if pil_img.mode != 'RGBA':
        pil_img = pil_img.convert('RGBA')

    pixels = pil_img.load()
    width, height = pil_img.size

    # Get background color from corner
    bg_color = pixels[0, 0][:3]

    # Flood fill from edges
    to_check = set()
    transparent = set()

    # Add edge pixels
    for x in range(width):
        to_check.add((x, 0))
        to_check.add((x, height - 1))
    for y in range(height):
        to_check.add((0, y))
        to_check.add((width - 1, y))

    while to_check:
        x, y = to_check.pop()
        if (x, y) in transparent:
            continue
        if x < 0 or x >= width or y < 0 or y >= height:
            continue

        pixel = pixels[x, y][:3]
        # Check if similar to background
        if all(abs(pixel[i] - bg_color[i]) <= tolerance for i in range(3)):
            transparent.add((x, y))
            pixels[x, y] = (255, 255, 255, 0)  # Make transparent
            # Add neighbors
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                to_check.add((x + dx, y + dy))

    return pil_img


def extract_cutter_shapes(pdf_path, output_dir=None):
    """
    Extract cutter shapes from a PDF and map them to BOM indices.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Optional directory to save extracted shapes

    Returns:
        dict: {index: {'width': w, 'height': h, 'hash': hash, 'image': PIL.Image}}
    """
    doc = fitz.open(pdf_path)
    page = doc[0]

    page_height = page.rect.height
    page_width = page.rect.width

    # CL (Cutter Layout) area starts ~20% down the page (proportional threshold)
    cl_area_y_threshold = page_height * 0.20

    print(f"Page dimensions: {page_width:.0f} x {page_height:.0f}")
    print(f"CL area starts at y > {cl_area_y_threshold:.0f} ({cl_area_y_threshold/page_height*100:.0f}% of page)")

    # Get raw words to find index positions
    raw_words = page.get_text("words")

    # Get all images from page
    image_list = page.get_images(full=True)

    # Build hash -> image data map with UNIQUE bounding rectangles
    hash_to_image = {}  # hash -> {'width', 'height', 'data', 'pil_img'}
    hash_to_rects = defaultdict(set)  # hash -> set of unique (x0, y0, x1, y1) rectangles

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
                hash_to_image[img_hash] = {
                    'width': w,
                    'height': h,
                    'data': base_image['image'],
                    'pil_img': trans_img
                }

            # Record UNIQUE bounding rectangles for this image hash in CL area
            # Round to 1 decimal to avoid float precision duplicates
            rects = page.get_image_rects(xref)
            for rect in rects:
                if rect.y0 > cl_area_y_threshold:  # CL area only
                    rounded_rect = (
                        round(rect.x0, 1), round(rect.y0, 1),
                        round(rect.x1, 1), round(rect.y1, 1)
                    )
                    hash_to_rects[img_hash].add(rounded_rect)
        except Exception as e:
            continue

    print(f"\nFound {len(hash_to_image)} unique shapes in CL area:")
    for img_hash, info in hash_to_image.items():
        count = len(hash_to_rects.get(img_hash, set()))
        print(f"  {img_hash}: {info['width']}x{info['height']}, {count} positions")

    # Find index number positions in CL area
    # Index numbers are 1-2 digit numbers in the CL area
    index_positions = {}  # index -> (center_x, center_y)
    for rw in raw_words:
        x0, y0, x1, y1, text = rw[0], rw[1], rw[2], rw[3], rw[4]
        if text.isdigit() and len(text) <= 2 and y0 > cl_area_y_threshold:
            idx = int(text)
            if idx > 0 and idx <= 30 and idx not in index_positions:
                center_x = (x0 + x1) / 2
                center_y = (y0 + y1) / 2
                index_positions[idx] = (center_x, center_y)

    print(f"\nFound {len(index_positions)} index positions in CL area:")
    for idx in sorted(index_positions.keys()):
        cx, cy = index_positions[idx]
        print(f"  Index {idx}: center at ({cx:.1f}, {cy:.1f})")

    # Match shapes to indices using CONTAINMENT
    # The index number position should be INSIDE the shape's bounding rectangle
    cutter_shapes = {}

    print(f"\nContainment matching:")
    for idx in sorted(index_positions.keys()):
        idx_x, idx_y = index_positions[idx]
        found_shape = None

        for img_hash, rects in hash_to_rects.items():
            for (x0, y0, x1, y1) in rects:
                # Check if index position is inside shape bounds
                if x0 <= idx_x <= x1 and y0 <= idx_y <= y1:
                    found_shape = img_hash
                    break
            if found_shape:
                break

        if found_shape and found_shape in hash_to_image:
            img_data = hash_to_image[found_shape]
            cutter_shapes[idx] = {
                'width': img_data['width'],
                'height': img_data['height'],
                'hash': found_shape,
                'image': img_data['pil_img']
            }
            print(f"  Index {idx}: shape {found_shape} ({img_data['width']}x{img_data['height']})")
        else:
            print(f"  Index {idx}: NO SHAPE")

    # Save shapes if output directory provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        for idx, shape_info in cutter_shapes.items():
            filename = f"cutter_index_{idx}_{shape_info['hash']}.png"
            filepath = os.path.join(output_dir, filename)
            shape_info['image'].save(filepath)
            print(f"Saved: {filepath}")

    doc.close()

    # Summary
    with_shapes = sorted(cutter_shapes.keys())
    without_shapes = sorted(set(index_positions.keys()) - set(cutter_shapes.keys()))

    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"{'='*60}")
    print(f"  Indices WITH shapes: {with_shapes}")
    print(f"  Indices WITHOUT shapes: {without_shapes}")

    return cutter_shapes


def extract_drill_bit_image(pdf_path, output_path=None):
    """
    Extract drill bit face image from PDF.

    The drill bit is typically:
    - In the top-right area (x > 65% of page, y < 25% of page)
    - Size 140-300px
    - Has >50% non-white content (to avoid blank placeholders)
    """
    doc = fitz.open(pdf_path)
    page = doc[0]

    page_width = page.rect.width
    page_height = page.rect.height

    # Proportional thresholds
    drill_x_threshold = page_width * 0.65   # Right 35% of page
    drill_y_threshold = page_height * 0.25  # Top 25% of page

    image_list = page.get_images(full=True)

    for img_info in image_list:
        xref = img_info[0]
        try:
            base_image = doc.extract_image(xref)
            rects = page.get_image_rects(xref)
        except:
            continue

        w = base_image['width']
        h = base_image['height']

        # Drill bit face is typically 140-300 pixels, roughly square
        if 140 <= w <= 300 and 140 <= h <= 300:
            if rects:
                rect = rects[0]
                # Check position using proportional thresholds
                if rect.x0 > drill_x_threshold and rect.y0 < drill_y_threshold:
                    # Verify content - must have >50% non-white pixels
                    image_bytes = base_image['image']
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    pixels = list(pil_img.convert('RGB').getdata())
                    non_white = sum(1 for p in pixels if p[0] < 250 or p[1] < 250 or p[2] < 250)
                    content_pct = (non_white / len(pixels)) * 100

                    if content_pct > 50:  # Has actual content
                        print(f"Found drill bit: {w}x{h}, {content_pct:.1f}% content")
                        trans_img = make_transparent_floodfill(pil_img)

                        if output_path:
                            trans_img.save(output_path)
                            print(f"Saved: {output_path}")

                        doc.close()
                        return trans_img

    doc.close()
    print("No drill bit image found")
    return None


if __name__ == "__main__":
    import sys

    # Default PDF path
    pdf_path = "docs/1283277_B.pdf"
    output_dir = "docs/shape_samples"

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]

    print(f"Extracting shapes from: {pdf_path}")
    print("=" * 60)

    # Extract cutter shapes
    shapes = extract_cutter_shapes(pdf_path, output_dir)

    print()
    print("=" * 60)
    print("Extracting drill bit...")
    print("=" * 60)

    # Extract drill bit
    drill_bit = extract_drill_bit_image(pdf_path, f"{output_dir}/drillbit.png")
