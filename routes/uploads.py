import os
import uuid

from flask import url_for

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'uploads')


def save_image(file):
    """Save an uploaded image to static/uploads and return its new filename.

    Returns None if no file was chosen. Raises ValueError for a disallowed file type.
    """
    if file is None or not file.filename:
        return None

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError('Image must be a PNG, JPG, GIF or WEBP file.')

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(UPLOAD_DIR, filename))
    return filename


def delete_image(filename):
    """Remove an uploaded file (used when a database write fails after the upload)."""
    if filename:
        try:
            os.remove(os.path.join(UPLOAD_DIR, filename))
        except OSError:
            pass


STATIC_IMAGES = os.path.join(os.path.dirname(UPLOAD_DIR), 'images')
PLACEHOLDERS = ('image1.jpeg', 'default_vendor.jpeg')


def has_uploaded_file(filename):
    """True if this filename is a file a vendor uploaded (lives in static/uploads)."""
    return bool(filename) and os.path.exists(os.path.join(UPLOAD_DIR, filename))


def has_image(filename):
    """True if a real photo exists for this record (not the shared placeholder, not a missing file)."""
    if not filename or filename in PLACEHOLDERS:
        return False
    return has_uploaded_file(filename) or os.path.exists(os.path.join(STATIC_IMAGES, filename))


def image_url(filename):
    """URL for an image: uploads live in static/uploads, bundled ones in static/images.
    Missing files fall back to the placeholder so a page never shows a broken image."""
    if has_uploaded_file(filename):
        return url_for('static', filename='uploads/' + filename)
    if filename and os.path.exists(os.path.join(STATIC_IMAGES, filename)):
        return url_for('static', filename='images/' + filename)
    return url_for('static', filename='images/image1.jpeg')
