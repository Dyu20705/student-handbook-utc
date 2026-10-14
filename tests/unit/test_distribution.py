"""Packaging regressions run offline, without Git history or private evidence."""

import importlib.util
import io
import stat
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "distribution", ROOT / "scripts/check_distribution.py"
)
distribution = importlib.util.module_from_spec(spec)
spec.loader.exec_module(distribution)


@pytest.mark.parametrize(
    "leaked", ["docs/qualification/benchmark.json", "data/runtime/audit.json", ".env"]
)
@pytest.mark.parametrize("archive_kind", ["wheel", "sdist"])
def test_archives_reject_evidence_and_private_data(tmp_path, leaked, archive_kind):
    write_archive_pair(tmp_path, leaked, archive_kind)
    with pytest.raises(ValueError, match="Unapproved distribution member"):
        distribution.verify_archives(tmp_path)


def write_archive_pair(directory, extra=None, archive_kind=None):
    """Minimal archive fixtures with real package paths and metadata exceptions."""
    stem = "student_handbook_rag-0.2.0"
    wheel_files = [
        "student_handbook_rag/__init__.py",
        f"{stem}.dist-info/METADATA",
        f"{stem}.dist-info/WHEEL",
        f"{stem}.dist-info/RECORD",
    ]
    sdist_files = [
        "src/student_handbook_rag/__init__.py",
        "PKG-INFO",
        "setup.cfg",
        "src/student_handbook_rag.egg-info/SOURCES.txt",
    ]
    if extra is not None:
        (wheel_files if archive_kind == "wheel" else sdist_files).append(extra)
    with zipfile.ZipFile(directory / f"{stem}-py3-none-any.whl", "w") as wheel:
        for name in wheel_files:
            wheel.writestr(name, b"")
    with tarfile.open(directory / f"{stem}.tar.gz", "w:gz") as sdist:
        for name in sdist_files:
            sdist.addfile(tarfile.TarInfo(f"{stem}/{name}"), io.BytesIO(b""))


@pytest.mark.parametrize(
    "archive_kind,unlisted",
    [
        ("wheel", "student_handbook_rag/private_snapshot.json"),
        ("sdist", "src/student_handbook_rag/private_snapshot.json"),
        ("wheel", "student_handbook_rag/private_snapshot.py"),
        ("sdist", "tests/private_snapshot.py"),
        ("wheel", "student_handbook_rag-0.2.0.dist-info/private_snapshot.json"),
        ("sdist", "src/student_handbook_rag.egg-info/private_snapshot.json"),
    ],
)
def test_archives_reject_unlisted_files_outside_old_blacklist(tmp_path, archive_kind, unlisted):
    write_archive_pair(tmp_path, unlisted, archive_kind)
    with pytest.raises(ValueError, match="Unapproved distribution member"):
        distribution.verify_archives(tmp_path)


def test_archives_accept_known_files_and_metadata(tmp_path):
    write_archive_pair(tmp_path)
    distribution.verify_archives(tmp_path)


@pytest.mark.parametrize("archive_kind", ["wheel", "sdist"])
def test_archives_reject_links_at_allowed_paths(tmp_path, archive_kind):
    write_archive_pair(tmp_path)
    if archive_kind == "wheel":
        path = next(tmp_path.glob("*.whl"))
        with zipfile.ZipFile(path, "w") as archive:
            member = zipfile.ZipInfo("student_handbook_rag/__init__.py")
            member.create_system = 3
            member.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(member, "../../private_snapshot.json")
    else:
        path = next(tmp_path.glob("*.tar.gz"))
        with tarfile.open(path, "w:gz") as archive:
            member = tarfile.TarInfo(
                "student_handbook_rag-0.2.0/src/student_handbook_rag/__init__.py"
            )
            member.type = tarfile.SYMTYPE
            member.linkname = "../../private_snapshot.json"
            archive.addfile(member)
    with pytest.raises(ValueError, match="Unsupported distribution member type"):
        distribution.verify_archives(tmp_path)


@pytest.mark.parametrize("archive_kind", ["wheel", "sdist"])
def test_archives_reject_duplicate_allowed_members(tmp_path, archive_kind):
    if archive_kind == "wheel":
        with pytest.warns(UserWarning, match="Duplicate name"):
            write_archive_pair(tmp_path, "student_handbook_rag/__init__.py", archive_kind)
    else:
        write_archive_pair(tmp_path, "src/student_handbook_rag/__init__.py", archive_kind)
    with pytest.raises(ValueError, match="Duplicate distribution member"):
        distribution.verify_archives(tmp_path)
