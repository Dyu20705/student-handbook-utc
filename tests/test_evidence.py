"""Offline publication regressions: tampering, privacy, provenance and packaging."""
import importlib.util
import io
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evidence", ROOT / "scripts/evidence.py")
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


@pytest.fixture
def bundle(tmp_path):
    directory = tmp_path / "qualification"
    directory.mkdir()
    for name in (*evidence.NAMES, *evidence.REPORTS, "evidence-manifest.json", "evidence-summary.md"):
        shutil.copyfile(ROOT / evidence.DIRECTORY / name, directory / name)
    shutil.copyfile(ROOT / "docs/security.md", tmp_path / "security.md")
    return directory


def edit_json(path, mutate):
    value = evidence.read_json(path.read_bytes())
    mutate(value)
    path.write_bytes(evidence.json_bytes(value))


def refresh_artifact_hash(directory, name):
    edit_json(directory / "evidence-manifest.json",
              lambda m: m["artifacts"][name].update(sha256=evidence.sha((directory / name).read_bytes())))


def refresh_report_hash(directory, name):
    edit_json(directory / "evidence-manifest.json",
              lambda m: m["report_sha256_lf"].update({name: evidence.sha(evidence.lf((directory / name).read_bytes()))}))


def test_published_bundle_verifies_without_network_or_runtime():
    evidence.verify(ROOT)


@pytest.mark.parametrize("field,value", [
    ("schema_version", 99),
    ("commit", "0" * 40),
    ("hostname", "PRIVATE-COMPUTER"),
    ("excerpt", "private source text"),
])
def test_schema_provenance_and_private_fields_rejected_even_with_updated_sha(bundle, field, value):
    name = "benchmark-8b71494.json"
    edit_json(bundle / name, lambda data: data.update({field: value}))
    refresh_artifact_hash(bundle, name)
    with pytest.raises(ValueError, match="Manifest"):
        evidence.verify(ROOT, bundle)


def test_stale_artifact_sha_fails(bundle):
    with (bundle / "benchmark-8b71494.json").open("ab") as file:
        file.write(b" ")
    with pytest.raises(ValueError, match="Artifact SHA"):
        evidence.verify(ROOT, bundle)


def test_changed_metric_with_new_hash_does_not_become_evidence(bundle):
    name = "benchmark-8b71494.json"
    edit_json(bundle / name, lambda data: data["metrics"].update(hit_at_1=1.0))
    refresh_artifact_hash(bundle, name)
    with pytest.raises(ValueError, match="Manifest"):
        evidence.verify(ROOT, bundle)


def test_runtime_hash_cannot_be_replaced(bundle):
    name = "benchmark-8b71494.json"
    edit_json(bundle / name, lambda data: data["provenance"]["runtime_sha256_lf"].update({"uv.lock": "0" * 64}))
    refresh_artifact_hash(bundle, name)
    with pytest.raises(ValueError, match="Manifest"):
        evidence.verify(ROOT, bundle)


def test_smoke_reference_is_bound_to_benchmark(bundle):
    name = evidence.SMOKE
    edit_json(bundle / name, lambda data: data.update(benchmark_sha256="0" * 64))
    refresh_artifact_hash(bundle, name)
    with pytest.raises(ValueError, match="Manifest"):
        evidence.verify(ROOT, bundle)


def test_raw_metrics_are_recomputed_from_responses():
    raw = evidence.read_json(evidence.raw_artifacts(ROOT)["benchmark-8b71494.json"])
    raw["responses"][0]["answer"] = "unrelated answer"
    with pytest.raises(ValueError, match="Raw generation metric mismatch"):
        evidence.benchmark_summary(ROOT, evidence.json_bytes(raw), evidence.QUALIFIED_COMMIT)


def test_proxy_arithmetic_distinguishes_error_refusal_and_missing_citation():
    gold = [
        {"id": "a", "answerable": True, "expected_page": 3, "book_page": 1, "gold_keywords": ["a"]},
        {"id": "b", "answerable": True, "expected_page": 4, "book_page": 2, "gold_keywords": ["b"]},
        {"id": "c", "answerable": False},
    ]
    cases = [
        {"id": "a", "status": "answered", "is_insufficient_context": False, "keyword_indices": [0],
         "retrieved_pages": [9, 3], "citations": []},
        {"id": "b", "status": "error", "is_insufficient_context": False, "keyword_indices": [0],
         "retrieved_pages": [9], "citations": [{"page": 4, "book_page": 2}]},
        {"id": "c", "status": "error"},
    ]
    assert evidence.metrics(cases, gold) == {
        "answerable": 2, "unanswerable": 1, "hit_at_1": 0, "hit_at_3": .5, "hit_at_5": .5,
        "mrr": .25, "keyword_matches": 1, "citation_page_matches": 0, "refusals": 0, "operational_errors": 2,
    }


def test_junit_minimization_preserves_historical_failure():
    raw = evidence.raw_artifacts(ROOT)["integration-d540993-retry.xml"]
    public = evidence.xml_summary(raw)
    suite = ET.fromstring(public)[0]
    assert suite.attrib["tests"] == "9"
    assert suite.attrib["failures"] == "1"
    failure = suite.find(".//failure")
    assert failure is not None and not failure.attrib and not failure.text
    assert b"hostname" not in public and b"Traceback" not in public and b"C:\\" not in public


def test_junit_counts_cannot_hide_failure():
    raw = evidence.raw_artifacts(ROOT)["integration-d540993-retry.xml"]
    corrupt = raw.replace(b'failures="1"', b'failures="0"')
    with pytest.raises(ValueError, match="JUnit count"):
        evidence.xml_summary(corrupt)


def test_public_artifacts_have_no_private_text_fields():
    for name in evidence.NAMES:
        text = (ROOT / evidence.DIRECTORY / name).read_text(encoding="utf-8")
        assert not re.search(r'[A-Za-z]:\\|/Users/|/home/|hostname|"managed_pid"|"excerpt"|"answer"|"page_content"|"query"', text)


def test_report_hash_drift_is_detected(bundle):
    with (bundle / "semantic-review.md").open("a", encoding="utf-8") as file:
        file.write("\nChanged narrative\n")
    with pytest.raises(ValueError, match="report hash"):
        evidence.verify(ROOT, bundle)


def test_broken_report_reference_is_detected_with_refreshed_hash(bundle):
    path = bundle / "local-production-readiness.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n[missing](missing.json)\n", encoding="utf-8")
    refresh_report_hash(bundle, path.name)
    with pytest.raises(ValueError, match="Broken report reference"):
        evidence.verify(ROOT, bundle)


def test_semantic_verdict_drift_is_detected_with_refreshed_hash(bundle):
    path = bundle / "semantic-review.md"
    path.write_text(path.read_text(encoding="utf-8").replace("Không đạt: thêm Điều 2", "Đạt"), encoding="utf-8")
    refresh_report_hash(bundle, path.name)
    with pytest.raises(ValueError, match="Semantic report verdict drift"):
        evidence.verify(ROOT, bundle)


def test_generated_summary_cannot_overstate_results(bundle):
    path = bundle / "evidence-summary.md"
    path.write_text(path.read_text(encoding="utf-8").replace("19/22", "22/22"), encoding="utf-8")
    with pytest.raises(ValueError, match="Generated report"):
        evidence.verify(ROOT, bundle)


def test_modified_runtime_is_not_qualified(monkeypatch):
    read_bytes = Path.read_bytes

    def modified(path):
        content = read_bytes(path)
        return content + b"\nchanged runtime\n" if path == ROOT / "src/student_handbook_rag/api.py" else content

    monkeypatch.setattr(Path, "read_bytes", modified)
    with pytest.raises(ValueError, match="Runtime changed"):
        evidence.verify(ROOT)


def test_missing_history_fails_closed(monkeypatch):
    git = evidence.git

    def missing(repo, *args):
        if args[0] == "merge-base":
            raise subprocess.CalledProcessError(1, ["git", *args])
        return git(repo, *args)

    monkeypatch.setattr(evidence, "git", missing)
    with pytest.raises(subprocess.CalledProcessError):
        evidence.verify(ROOT)


def test_private_raw_corruption_is_detected(tmp_path):
    for name, raw in evidence.raw_artifacts(ROOT).items():
        (tmp_path / name).write_bytes(raw)
    (tmp_path / "benchmark-8b71494.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="Private raw mismatch"):
        evidence.verify(ROOT, raw_directory=tmp_path)


@pytest.mark.parametrize("leaked", ["docs/qualification/benchmark.json", "data/runtime/audit.json", ".env"])
@pytest.mark.parametrize("archive_kind", ["wheel", "sdist"])
def test_archives_reject_evidence_and_private_data(tmp_path, leaked, archive_kind):
    with zipfile.ZipFile(tmp_path / "package.whl", "w") as wheel:
        wheel.writestr(leaked if archive_kind == "wheel" else "pkg/__init__.py", b"")
    with tarfile.open(tmp_path / "package.tar.gz", "w:gz") as sdist:
        member = tarfile.TarInfo("package/" + (leaked if archive_kind == "sdist" else "src/pkg/__init__.py"))
        sdist.addfile(member, io.BytesIO(b""))
    with pytest.raises(ValueError, match="Evidence/private data in distribution"):
        evidence.verify_archives(tmp_path)
