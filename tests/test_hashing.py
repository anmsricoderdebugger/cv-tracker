import os
import tempfile

from backend.utils.hashing import compute_file_hash


def test_compute_file_hash():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"test content for hashing")
        f.flush()
        path = f.name

    try:
        hash1 = compute_file_hash(path)
        assert len(hash1) == 64  # SHA-256 hex digest length
        hash2 = compute_file_hash(path)
        assert hash1 == hash2  # Same content = same hash
    finally:
        os.unlink(path)


def test_different_content_different_hash():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f1:
        f1.write(b"content A")
        f1.flush()
        path1 = f1.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f2:
        f2.write(b"content B")
        f2.flush()
        path2 = f2.name

    try:
        assert compute_file_hash(path1) != compute_file_hash(path2)
    finally:
        os.unlink(path1)
        os.unlink(path2)
