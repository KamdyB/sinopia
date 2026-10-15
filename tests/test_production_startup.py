import os
import subprocess
import sys
from pathlib import Path


def test_production_startup_without_database_url_never_creates_local_sqlite(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["SINOPIA_ENV"] = "production"
    env.pop("DATABASE_URL", None)
    env.pop("SINOPIA_DB_PATH", None)
    env["PYTHONPATH"] = str(repo_root)

    result = subprocess.run(
        [sys.executable, "-c", "import backend.main"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode != 0
    assert "DATABASE_URL is required in production" in result.stderr
    assert not (tmp_path / "sinopia.db").exists()
