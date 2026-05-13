import hashlib
from typing import Union


def generate_hash(content: Union[bytes, str]) -> str:
    """
    Generate SHA-256 hash of the given content for forensic integrity.

    Args:
        content: The file content as bytes or string.

    Returns:
        str: The SHA-256 hash as a hexadecimal string.
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()