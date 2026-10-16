"""Check wheel/sdist membership independently of historical RAG qualification."""

import argparse
import stat
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path, PurePosixPath

# Reviewed files only: do not infer this inventory from archive contents or globs.
WHEEL_FILES = {
    f"student_handbook_rag/{name}"
    for name in (
        "__init__.py",
        "api.py",
        "ask.py",
        "chain.py",
        "config.py",
        "doctor.py",
        "evaluate.py",
        "ingest.py",
        "lexical.py",
        "loader.py",
        "retriever.py",
        "vectorstore.py",
    )
}
SDIST_FILES = {f"src/{name}" for name in WHEEL_FILES} | {
    ".env.example",
    "README.md",
    "CHANGELOG.md",
    "MANIFEST.in",
    "pyproject.toml",
    "uv.lock",
    "data/README.md",
    "docs/architecture.md",
    "docs/api.md",
    "docs/configuration.md",
    "docs/operations.md",
    "docs/security.md",
    "docs/limitations.md",
    "scripts/check_distribution.py",
    "scripts/run_qualification.py",
    "scripts/setup.sh",
    "scripts/setup-local.ps1",
    "scripts/start-local.ps1",
    "scripts/stop-local.ps1",
    "scripts/local-server-state.ps1",
    "tests/conftest.py",
    "tests/contract/test_api.py",
    "tests/contract/test_browser_contract.py",
    "tests/integration/test_baseline_rag.py",
    "tests/integration/test_vectorstore.py",
    "tests/unit/test_distribution.py",
    "tests/unit/test_llm.py",
    "tests/unit/test_loader.py",
    "tests/unit/test_evaluation_proxies.py",
    "tests/unit/test_failure_modes_unit.py",
    "tests/unit/test_lexical.py",
    "tests/unit/test_local_config.py",
    "tests/unit/test_page_continuation.py",
    "tests/unit/test_production.py",
    "tests/unit/test_retriever_unit.py",
    "tests/unit/test_windows_lifecycle.py",
}
WHEEL_METADATA = {"METADATA", "WHEEL", "RECORD", "entry_points.txt", "top_level.txt"}
SDIST_METADATA = {"PKG-INFO", "setup.cfg"} | {
    f"src/student_handbook_rag.egg-info/{name}"
    for name in (
        "PKG-INFO",
        "SOURCES.txt",
        "dependency_links.txt",
        "entry_points.txt",
        "requires.txt",
        "top_level.txt",
    )
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_archive_members(members, allowed, archive_name):
    directories = {
        str(parent)
        for name in allowed
        for parent in PurePosixPath(name).parents
        if str(parent) != "."
    }
    seen = set()
    for name, is_directory, is_regular in members:
        require(
            is_directory or is_regular,
            f"Unsupported distribution member type: {archive_name}/{name}",
        )
        canonical = name.removesuffix("/") if is_directory else name
        require(
            canonical in (directories if is_directory else allowed),
            f"Unapproved distribution member: {archive_name}/{name}",
        )
        require(canonical not in seen, f"Duplicate distribution member: {archive_name}/{name}")
        seen.add(canonical)


def verify_archives(directory):
    """Reject unapproved files/types; this is not a secret scan of approved text."""
    project = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )
    stem = f"student_handbook_rag-{project['project']['version']}"
    wheel_allowed = WHEEL_FILES | {f"{stem}.dist-info/{name}" for name in WHEEL_METADATA}
    sdist_allowed = {f"{stem}/{name}" for name in SDIST_FILES | SDIST_METADATA}
    archives = sorted(directory.glob("*.whl")) + sorted(directory.glob("*.tar.gz"))
    require(
        any(p.suffix == ".whl" for p in archives)
        and any(p.name.endswith(".tar.gz") for p in archives),
        "Expected both wheel and sdist",
    )
    for path in archives:
        if path.suffix == ".whl":
            with zipfile.ZipFile(path) as archive:
                members = []
                for member in archive.infolist():
                    mode = stat.S_IFMT(member.external_attr >> 16)
                    is_directory = member.is_dir() and mode in (0, stat.S_IFDIR)
                    is_regular = not member.is_dir() and mode in (0, stat.S_IFREG)
                    members.append((member.filename, is_directory, is_regular))
                check_archive_members(members, wheel_allowed, path.name)
        else:
            with tarfile.open(path) as archive:
                check_archive_members(
                    ((m.name, m.isdir(), m.isfile()) for m in archive), sdist_allowed, path.name
                )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Directory containing both wheel and sdist")
    args = parser.parse_args()
    try:
        verify_archives(args.directory)
    except (ValueError, OSError, tarfile.TarError, zipfile.BadZipFile) as error:
        print(f"Distribution check failed: {error}", file=sys.stderr)
        return 1
    print("Wheel and sdist contain only reviewed files and metadata.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
