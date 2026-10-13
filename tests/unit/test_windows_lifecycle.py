"""Exercise actual PowerShell process management with a lightweight HTTP server."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import uuid

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows lifecycle scripts")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def listening(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


@pytest.fixture
def server_project(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    original = Path(__file__).resolve().parents[2] / "scripts"
    for name in ("start-local.ps1", "stop-local.ps1", "local-server-state.ps1"):
        shutil.copy2(original / name, scripts / name)
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(tmp_path / ".venv")], check=True)
    package = tmp_path / "student_handbook_rag"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "doctor.py").write_text("print('test doctor ready')")
    (package / "api.py").write_text('''
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int)
args = parser.parse_args()
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ready"}')
HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
''')
    shell = shutil.which("pwsh") or shutil.which("powershell")
    assert shell, "PowerShell required on Windows"

    def run(name, *args):
        # A detached Windows child can inherit pipe handles, keeping communicate()
        # blocked after PowerShell exits. Capture to a file, as a real launcher does.
        with (tmp_path / f"command-{uuid.uuid4().hex}.log").open("w+", encoding="utf-8") as log:
            result = subprocess.run([shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(scripts / name), *map(str, args)],
                                    env={**os.environ, "PYTHONPATH": str(tmp_path)}, stdout=log, stderr=subprocess.STDOUT, timeout=90)
            log.seek(0)
            result.stdout, result.stderr = log.read(), ""
            return result

    yield tmp_path, run
    stopped = run("stop-local.ps1")
    assert stopped.returncode == 0, stopped.stderr


def test_second_port_does_not_replace_managed_pid(server_project):
    project, run = server_project
    first, second = free_port(), free_port()
    start = run("start-local.ps1", "-Background", "-Port", first)
    assert start.returncode == 0, start.stdout + start.stderr
    pidfile = project / "data/runtime/server.pid"
    original_pid = pidfile.read_text()
    duplicate = run("start-local.ps1", "-Background", "-Port", second)
    assert duplicate.returncode != 0
    assert "still running" in duplicate.stdout
    assert pidfile.read_text() == original_pid
    assert listening(first) and not listening(second)
    assert run("stop-local.ps1").returncode == 0
    for _ in range(30):
        if not listening(first):
            break
        time.sleep(.1)
    assert not listening(first)
    assert not pidfile.exists()


def test_concurrent_starts_leave_one_managed_server(server_project):
    project, run = server_project
    ports = [free_port(), free_port()]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, "start-local.ps1", "-Background", "-Port", port) for port in ports]
        results = [future.result() for future in futures]
    assert sorted(result.returncode == 0 for result in results) == [False, True], [r.stderr for r in results]
    assert sum(listening(port) for port in ports) == 1
    assert (project / "data/runtime/server.pid").exists()
    assert run("stop-local.ps1").returncode == 0
    assert not any(listening(port) for port in ports)
