"""
ARDT FMS - Inventory Utilities
QR Code and Barcode generation for inventory items.
"""

import base64
from io import BytesIO


def generate_qr_code_base64(data, size=10, border=4):
    """
    Generate a QR code as a base64-encoded PNG image.

    Args:
        data: The data to encode in the QR code
        size: Box size for the QR code (default 10)
        border: Border size (default 4)

    Returns:
        Base64-encoded data URL string for embedding in HTML
    """
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_L

        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"

    except ImportError:
        return generate_placeholder_qr()


def generate_barcode_base64(data, barcode_type='code128'):
    """
    Generate a barcode as a base64-encoded PNG image.

    Args:
        data: The data to encode
        barcode_type: Type of barcode (code128, ean13, code39, etc.)

    Returns:
        Base64-encoded data URL string for embedding in HTML
    """
    try:
        import barcode
        from barcode.writer import ImageWriter

        # Get the barcode class
        barcode_class = barcode.get_barcode_class(barcode_type)

        # Create barcode with ImageWriter
        bc = barcode_class(data, writer=ImageWriter())

        buffer = BytesIO()
        bc.write(buffer)
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"

    except (ImportError, Exception):
        return generate_placeholder_barcode()


def generate_placeholder_qr():
    """Generate a placeholder QR code SVG."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="150" height="150">
        <rect width="100" height="100" fill="white" stroke="#ccc" stroke-width="2"/>
        <rect x="10" y="10" width="25" height="25" fill="#333"/>
        <rect x="65" y="10" width="25" height="25" fill="#333"/>
        <rect x="10" y="65" width="25" height="25" fill="#333"/>
        <rect x="40" y="40" width="20" height="20" fill="#333"/>
        <text x="50" y="95" font-size="8" text-anchor="middle" fill="#666">QR Code</text>
    </svg>"""
    encoded = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


def generate_placeholder_barcode():
    """Generate a placeholder barcode SVG."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80" width="200" height="80">
        <rect width="200" height="80" fill="white" stroke="#ccc" stroke-width="2"/>
        <rect x="10" y="10" width="2" height="50" fill="#333"/>
        <rect x="15" y="10" width="4" height="50" fill="#333"/>
        <rect x="22" y="10" width="2" height="50" fill="#333"/>
        <rect x="28" y="10" width="3" height="50" fill="#333"/>
        <rect x="35" y="10" width="2" height="50" fill="#333"/>
        <rect x="42" y="10" width="4" height="50" fill="#333"/>
        <rect x="50" y="10" width="2" height="50" fill="#333"/>
        <rect x="58" y="10" width="3" height="50" fill="#333"/>
        <rect x="65" y="10" width="2" height="50" fill="#333"/>
        <rect x="72" y="10" width="4" height="50" fill="#333"/>
        <rect x="80" y="10" width="2" height="50" fill="#333"/>
        <text x="100" y="75" font-size="10" text-anchor="middle" fill="#666">Barcode</text>
    </svg>"""
    encoded = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


def generate_inventory_item_qr(item, base_url=None):
    """
    Generate QR code for an inventory item.

    Args:
        item: InventoryItem instance
        base_url: Base URL for the site

    Returns:
        Base64-encoded QR code data URL
    """
    from django.urls import reverse

    relative_url = reverse("inventory:item_detail", kwargs={"pk": item.pk})

    if base_url:
        url = f"{base_url.rstrip('/')}{relative_url}"
    else:
        # Use item code for offline scanning
        url = f"ARDT-INV:{item.code}"

    return generate_qr_code_base64(url)


def generate_identifier_image(identifier):
    """
    Generate the appropriate code image for an ItemIdentifier.

    Args:
        identifier: ItemIdentifier instance

    Returns:
        Base64-encoded image data URL
    """
    code_type = identifier.identifier_type
    value = identifier.value

    if code_type == 'QR':
        return generate_qr_code_base64(value)
    elif code_type in ['EAN13', 'EAN14', 'UPC']:
        return generate_barcode_base64(value, 'ean13')
    elif code_type in ['CODE128', 'CODE39']:
        return generate_barcode_base64(value, code_type.lower())
    elif code_type == 'ITF14':
        return generate_barcode_base64(value, 'itf')
    else:
        # Default to QR for unknown types
        return generate_qr_code_base64(value)
