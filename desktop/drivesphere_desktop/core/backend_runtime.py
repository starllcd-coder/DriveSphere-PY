from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from drivesphere_desktop.core.settings import BASE_DIR


class BackendRuntime:
	def __init__(self, base_url: str) -> None:
		self.base_url = (base_url or "").rstrip("/")
		self._process: subprocess.Popen | None = None
		self._started_by_app = False
		self._parsed = urlparse(self.base_url)

	def _health_url(self) -> str:
		return f"{self.base_url}/healthz/"

	def _is_local_target(self) -> bool:
		parsed = urlparse(self.base_url)
		host = (parsed.hostname or "").lower()
		return host in {"127.0.0.1", "localhost"}

	def _host_port(self) -> str:
		host = self._parsed.hostname or "127.0.0.1"
		port = self._parsed.port or 8000
		return f"{host}:{port}"

	def _build_base_url(self, host: str, port: int) -> str:
		scheme = self._parsed.scheme or "http"
		return f"{scheme}://{host}:{port}"

	def _is_port_available(self, host: str, port: int) -> bool:
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.settimeout(0.2)
			try:
				sock.bind((host, port))
				return True
			except OSError:
				return False

	def _candidate_ports(self) -> list[int]:
		start = self._parsed.port or 8000
		return [start + i for i in range(0, 8)]

	def is_healthy(self) -> bool:
		try:
			resp = requests.get(self._health_url(), timeout=2)
			return resp.status_code < 500
		except Exception:
			return False

	def _python_candidates(self) -> list[str]:
		candidates: list[str] = []
		env_python = os.getenv("DRIVESPHERE_BACKEND_PYTHON", "").strip()
		if env_python:
			candidates.append(env_python)

		venv_python = BASE_DIR / "web" / ".venv" / "Scripts" / "python.exe"
		if venv_python.exists():
			candidates.append(str(venv_python))

		if Path(sys.executable).exists():
			candidates.append(sys.executable)

		return candidates

	def _desktop_data_dir(self) -> Path:
		env_dir = os.getenv("DRIVESPHERE_DESKTOP_DATA_DIR", "").strip()
		if env_dir:
			target = Path(env_dir)
		else:
			local_appdata = os.getenv("LOCALAPPDATA", "").strip()
			if local_appdata:
				target = Path(local_appdata) / "DriveSphereDesktop" / "data"
			else:
				target = BASE_DIR / "desktop" / ".runtime-data"
		target.mkdir(parents=True, exist_ok=True)
		return target

	def _pick_python(self) -> str | None:
		for candidate in self._python_candidates():
			try:
				path = Path(candidate)
				if path.exists() and path.is_file():
					return str(path)
			except Exception:
				continue
		return None

	def _packaged_backend_exe(self) -> Path | None:
		# Only use bundled backend when running a frozen desktop executable.
		# In dev/source mode we should use manage.py to avoid stale dist artifacts.
		if not getattr(sys, "frozen", False):
			return None

		exe_dir = Path(sys.executable).resolve().parent
		candidates = [
			exe_dir / "DriveSphereBackend" / "DriveSphereBackend.exe",
			exe_dir / "DriveSphereBackend.exe",
			exe_dir.parent / "DriveSphereBackend" / "DriveSphereBackend.exe",
		]
		for candidate in candidates:
			if candidate.exists() and candidate.is_file():
				return candidate
		return None

	def start(self) -> tuple[bool, str]:
		autostart = os.getenv("DRIVESPHERE_AUTOSTART_BACKEND", "1").strip().lower()
		if autostart in {"0", "false", "no"}:
			return True, "Backend autostart disabled by environment."

		if not self._is_local_target():
			return True, "External backend URL configured; skipping local backend launch."

		if self.is_healthy():
			return True, "Backend already running."

		python_exe = self._pick_python()
		desktop_data = self._desktop_data_dir()
		env = os.environ.copy()
		env["DRIVESPHERE_DESKTOP_DATA_DIR"] = str(desktop_data)
		packaged_backend = self._packaged_backend_exe()

		if packaged_backend is not None:
			migrate_cmd = [str(packaged_backend), "migrate", "--noinput"]
			working_dir = packaged_backend.parent
		else:
			if not python_exe:
				return False, "No Python interpreter found for local backend startup."
			manage_py = BASE_DIR / "web" / "manage.py"
			if not manage_py.exists():
				return False, "web/manage.py not found; cannot auto-start backend."
			web_dir = manage_py.parent
			env["DJANGO_SETTINGS_MODULE"] = "config.settings.desktop"
			migrate_cmd = [python_exe, "manage.py", "migrate", "--noinput"]
			working_dir = web_dir

		creationflags = 0
		if os.name == "nt":
			creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

		try:
			migrate_proc = subprocess.run(
				migrate_cmd,
				cwd=str(working_dir),
				env=env,
				stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT,
				text=True,
				creationflags=creationflags,
				check=False,
			)
			if migrate_proc.returncode != 0:
				out = (migrate_proc.stdout or "").strip()
				if out:
					preview = out[-400:].replace("\r", " ").replace("\n", " ")
					return False, f"Desktop backend migration failed: {preview}"
				return False, "Desktop backend migration failed."
		except Exception as exc:
			return False, f"Failed to launch backend migration: {exc}"

		host = self._parsed.hostname or "127.0.0.1"
		last_error = "Backend process exited before becoming healthy."
		timeout_s = int(os.getenv("DRIVESPHERE_BACKEND_START_TIMEOUT", "45"))
		per_try_timeout = max(6, int(max(10, timeout_s) / 3))

		for port in self._candidate_ports():
			self.base_url = self._build_base_url(host, port)
			self._parsed = urlparse(self.base_url)

			if self.is_healthy():
				return True, f"Backend already running on {self.base_url}."

			if not self._is_port_available(host, port):
				last_error = f"Port {port} is busy."
				continue

			if packaged_backend is not None:
				cmd = [str(packaged_backend), "runserver", self._host_port(), "--noreload"]
			else:
				cmd = [python_exe, "manage.py", "runserver", self._host_port(), "--noreload"]

			try:
				self._process = subprocess.Popen(
					cmd,
					cwd=str(working_dir),
					env=env,
					stdout=subprocess.DEVNULL,
					stderr=subprocess.DEVNULL,
					creationflags=creationflags,
				)
				self._started_by_app = True
			except Exception as exc:
				last_error = f"Failed to launch backend: {exc}"
				continue

			deadline = time.time() + per_try_timeout
			while time.time() < deadline:
				if self.is_healthy():
					return True, f"Backend started on {self.base_url}."
				if self._process.poll() is not None:
					last_error = f"Backend process exited on port {port}."
					break
				time.sleep(0.6)

		return False, last_error

	def stop(self) -> None:
		if not self._started_by_app or self._process is None:
			return
		if self._process.poll() is not None:
			return
		try:
			self._process.terminate()
			self._process.wait(timeout=6)
		except Exception:
			try:
				self._process.kill()
			except Exception:
				pass
