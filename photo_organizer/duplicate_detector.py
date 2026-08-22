import hashlib
from pathlib import Path

def compute_file_hash(path: Path, chunk_size: int = 65536) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()
