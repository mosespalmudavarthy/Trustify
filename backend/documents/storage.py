import hashlib
import codecs
import re

from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import FileSystemStorage


private_storage = FileSystemStorage(
    location=settings.PRIVATE_STORAGE_ROOT,
    base_url=None,
)

MAX_FILE_SIZE = 20 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    '.pdf': 'application/pdf',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.txt': 'text/plain',
}

SAFE_STORAGE_KEY_PATTERN = re.compile(
    r'^documents/[0-9a-f]{32}\.(pdf|jpg|jpeg|png|txt)$'
)


def validate_file(uploaded_file):
    """
    Validate file size, extension, signature and content.
    """

    if uploaded_file.size <= 0:
        raise ValueError('Empty files are not allowed.')

    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValueError('Maximum file size is 20 MB.')

    extension = Path(uploaded_file.name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError('File format is not supported.')

    uploaded_file.seek(0)

    header = uploaded_file.read(8)

    uploaded_file.seek(0)

    if extension == '.pdf':
        valid = header.startswith(b'%PDF-')

    elif extension in ('.jpg', '.jpeg'):
        valid = header.startswith(b'\xff\xd8\xff')

    elif extension == '.png':
        valid = header.startswith(b'\x89PNG\r\n\x1a\n')

    elif extension == '.txt':
        valid = True

        decoder = codecs.getincrementaldecoder('utf-8')(
            errors='strict'
        )

        try:
            uploaded_file.seek(0)

            for chunk in uploaded_file.chunks():
                if b'\x00' in chunk:
                    valid = False
                    break

                decoder.decode(chunk)

            if valid:
                decoder.decode(b'', final=True)

        except UnicodeDecodeError:
            valid = False

        finally:
            uploaded_file.seek(0)

    else:
        valid = False

    if not valid:
        raise ValueError(
            'File content does not match its extension '
            'or contains invalid text data.'
        )

    return ALLOWED_EXTENSIONS[extension]


def calculate_checksum(uploaded_file):
    """
    Calculate the SHA-256 checksum of the complete file.
    """

    sha256 = hashlib.sha256()

    try:
        uploaded_file.seek(0)

        for chunk in uploaded_file.chunks():
            sha256.update(chunk)

        return sha256.hexdigest()

    finally:
        uploaded_file.seek(0)


def save_private_file(uploaded_file):
    """
    Save a file under a random, non-user-controlled filename.
    """

    extension = Path(uploaded_file.name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError('File format is not supported.')

    storage_name = (
        f'documents/{uuid4().hex}{extension}'
    )

    saved_name = private_storage.save(
        storage_name,
        uploaded_file,
    )

    if not SAFE_STORAGE_KEY_PATTERN.fullmatch(saved_name):
        private_storage.delete(saved_name)

        raise ValueError('Generated storage key is invalid.')

    return saved_name


def delete_private_file(storage_key):
    """
    Delete a private file only when no database record references it.

    Returns True when deleted, False when retained or unavailable.
    """

    if not isinstance(storage_key, str):
        return False

    if not SAFE_STORAGE_KEY_PATTERN.fullmatch(storage_key):
        return False

    # Import models locally to avoid circular imports.
    from .models import Document, DocumentVersion

    # Never delete a file referenced by a document.
    if Document.objects.filter(
        storage_key=storage_key
    ).exists():
        return False

    # Never delete a file referenced by a document version.
    if DocumentVersion.objects.filter(
        storage_key=storage_key
    ).exists():
        return False

    if not private_storage.exists(storage_key):
        return False

    private_storage.delete(storage_key)

    return True