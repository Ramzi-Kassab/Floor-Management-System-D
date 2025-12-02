"""
ARDT FMS - Work Orders Utilities
Version: 5.4 - Sprint 1.5

Utility functions for work order management.
"""

import base64
from io import BytesIO


def generate_qr_code_base64(data, size=10, border=4):
    """
    Generate a QR code as a base64-encoded PNG image.

    Args:
        data: The data to encode in the QR code (URL, serial number, etc.)
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
        img.save(buffer, format='PNG')
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"

    except ImportError:
        # Return placeholder if qrcode not installed
        return generate_placeholder_qr()


def generate_placeholder_qr():
    """Generate a placeholder QR code SVG when qrcode library is not available."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="150" height="150">
        <rect width="100" height="100" fill="white" stroke="#ccc" stroke-width="2"/>
        <rect x="10" y="10" width="25" height="25" fill="#333"/>
        <rect x="65" y="10" width="25" height="25" fill="#333"/>
        <rect x="10" y="65" width="25" height="25" fill="#333"/>
        <rect x="40" y="40" width="20" height="20" fill="#333"/>
        <text x="50" y="95" font-size="8" text-anchor="middle" fill="#666">QR Code</text>
    </svg>'''
    encoded = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


def generate_work_order_qr(work_order, base_url=None):
    """
    Generate QR code for a work order linking to its detail page.

    Args:
        work_order: WorkOrder instance
        base_url: Base URL for the site (e.g., 'https://fms.ardt.com')

    Returns:
        Base64-encoded QR code data URL
    """
    from django.urls import reverse

    relative_url = reverse('workorders:detail', kwargs={'pk': work_order.pk})

    if base_url:
        url = f"{base_url.rstrip('/')}{relative_url}"
    else:
        url = relative_url

    return generate_qr_code_base64(url)


def generate_drill_bit_qr(drill_bit, base_url=None):
    """
    Generate QR code for a drill bit linking to its detail page.

    Args:
        drill_bit: DrillBit instance
        base_url: Base URL for the site

    Returns:
        Base64-encoded QR code data URL
    """
    from django.urls import reverse

    relative_url = reverse('workorders:drillbit_detail', kwargs={'pk': drill_bit.pk})

    if base_url:
        url = f"{base_url.rstrip('/')}{relative_url}"
    else:
        # Use the QR code identifier for offline scanning
        url = f"ARDT-BIT:{drill_bit.serial_number}"

    return generate_qr_code_base64(url)


def format_duration(minutes):
    """Format minutes as human-readable duration."""
    if not minutes:
        return "--"

    hours = minutes // 60
    mins = minutes % 60

    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def calculate_progress(work_order):
    """Calculate work order progress based on completed steps."""
    # If using procedure execution, calculate based on steps
    if hasattr(work_order, 'procedure_execution') and work_order.procedure_execution:
        execution = work_order.procedure_execution
        total_steps = execution.procedure.steps.count()
        if total_steps > 0:
            completed = execution.completed_steps.count()
            return int((completed / total_steps) * 100)

    # Otherwise return stored progress
    return work_order.progress_percent or 0
