"""Package only reviewable assignment deliverables; exclude environments and secrets."""

from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    destination = ROOT / "C5_Yasmina_Hanna_Submission.zip"
    files = [ROOT / name for name in (
        "START_HERE.md", "README.md", "requirements.txt", "requirements-lock.txt",
        "pyproject.toml", ".env.example", ".gitignore",
    )]
    for folder in ("campus_library", "scripts", "tests", "docs", "verification", "deliverables"):
        files.extend(p for p in (ROOT / folder).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts
                     and p.suffix not in {".pyc", ".pyo"})
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(files):
            archive.write(file, arcname="C5_Yasmina_Hanna/" + file.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert all("/.venv/" not in n and "/.tools/" not in n and not n.endswith("/.env") for n in names)
        assert all("sqlite3" not in n for n in names)
        assert len(names) == len(set(names))
    print(f"Packaged {len(files)} files: {destination.name} ({destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
