"""
Shared pytest fixtures for hypr-sessions test suite
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is importable so 'commands.shared.*' resolves
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def session_dir(tmp_path):
    """Create a temporary session directory structure mirroring production layout.

    Returns the base directory (~/.config/hypr-sessions equivalent).
    """
    sessions_dir = tmp_path / "sessions"
    archived_dir = tmp_path / "archived"
    sessions_dir.mkdir()
    archived_dir.mkdir()
    return tmp_path


@pytest.fixture
def populated_session_dir(session_dir):
    """Session directory pre-populated with sample session folders and files."""
    for name in ("work", "dev", "personal"):
        session_path = session_dir / "sessions" / name
        session_path.mkdir()
        (session_path / "session.json").write_text(f'{{"name": "{name}"}}')
    return session_dir


@pytest.fixture
def fresh_cache():
    """Return a brand-new PathCache instance (not the global singleton)."""
    from commands.shared.path_cache import PathCache

    return PathCache(ttl_seconds=5.0, max_size=1000, debug=False)


@pytest.fixture
def small_cache():
    """Return a PathCache with a tiny max_size for eviction testing."""
    from commands.shared.path_cache import PathCache

    return PathCache(ttl_seconds=5.0, max_size=5, debug=False)


@pytest.fixture
def short_ttl_cache():
    """Return a PathCache with a very short TTL for expiration testing."""
    from commands.shared.path_cache import PathCache

    return PathCache(ttl_seconds=0.1, max_size=1000, debug=False)
