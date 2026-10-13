import os
import qrcode
from PIL import Image

def generate_qr_code(student_id: str, output_dir: str) -> str:
    """
    Generate a high-resolution QR code image for a student and save as PNG.
    Returns the filename of the saved QR code.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{student_id}.png"
    filepath = os.path.join(output_dir, filename)

    # Configure QR code generator
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(student_id)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff").convert("RGBA")
    img.save(filepath, format="PNG")
    return filename
