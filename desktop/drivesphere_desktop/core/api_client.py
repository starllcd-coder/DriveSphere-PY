from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from drivesphere_desktop.core.offline_store import OfflineStore
from drivesphere_desktop.core.settings import BASE_DIR


@dataclass
class LoginFormData:
	csrf_token: str
	branches: list[tuple[str, str]]


class ApiClient:
	def __init__(self, base_url: str) -> None:
		self.base_url = base_url.rstrip("/")
		self.session = requests.Session()
		self.session.headers.update({"User-Agent": "DriveSphereDesktop/0.1"})
		self.csrf_token = ""
		self._is_online = True
		self._sync_in_progress = False
		self.offline = OfflineStore(Path(BASE_DIR) / ".desktop_data" / "offline_store.db")

	def _url(self, path: str) -> str:
		if path.startswith("http"):
			return path
		if not path.startswith("/"):
			path = f"/{path}"
		return f"{self.base_url}{path}"

	def absolute_url(self, path: str) -> str:
		return self._url(path)

	@property
	def is_online(self) -> bool:
		return self._is_online

	@property
	def pending_actions_count(self) -> int:
		return self.offline.queue_size()

	def connection_label(self) -> str:
		if self.is_online:
			if self.pending_actions_count > 0:
				return f"Online | {self.pending_actions_count} pending sync"
			return "Online"
		if self.pending_actions_count > 0:
			return f"Offline | {self.pending_actions_count} queued"
		return "Offline"

	def _mark_online(self) -> None:
		self._is_online = True

	def _mark_offline(self) -> None:
		self._is_online = False

	def _cached_json(self, path: str) -> dict[str, Any] | None:
		cached = self.offline.get_cache(path)
		if isinstance(cached, dict):
			return cached
		if "?" in path:
			base = path.split("?", 1)[0]
			cached_base = self.offline.get_cache(base)
			if isinstance(cached_base, dict):
				return cached_base
		return None

	def _save_json_cache(self, path: str, payload: dict[str, Any]) -> None:
		self.offline.save_cache(path, payload)
		if "?" in path:
			self.offline.save_cache(path.split("?", 1)[0], payload)

	def _ensure_csrf(self) -> None:
		if self.csrf_token:
			return
		self.fetch_login_form()

	def fetch_login_form(self) -> LoginFormData:
		response = self.session.get(self._url("/login/"), timeout=15)
		response.raise_for_status()

		soup = BeautifulSoup(response.text, "html.parser")
		csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
		csrf_token = csrf_input.get("value", "") if csrf_input else ""

		branches: list[tuple[str, str]] = []
		select = soup.find("select", {"name": "branch"})
		if select:
			for option in select.find_all("option"):
				value = (option.get("value") or "").strip()
				label = option.text.strip() or value
				branches.append((value, label))

		self.csrf_token = csrf_token
		return LoginFormData(csrf_token=csrf_token, branches=branches)

	def login(self, identifier: str, password: str, branch_id: str, remember_me: bool) -> tuple[bool, str]:
		try:
			form = self.fetch_login_form()
		except Exception as exc:
			self._mark_offline()
			return False, f"Server unreachable: {exc}"
		payload = {
			"csrfmiddlewaretoken": form.csrf_token,
			"identifier": identifier,
			"password": password,
			"branch": branch_id,
		}
		if remember_me:
			payload["remember_me"] = "on"

		response = self.session.post(
			self._url("/login/"),
			data=payload,
			headers={"Referer": self._url("/login/")},
			allow_redirects=True,
			timeout=15,
		)

		if response.url.endswith("/login/") or "Invalid Username/Email Or Password" in response.text:
			return False, "Invalid Username/Email Or Password"
		if response.status_code >= 400:
			return False, f"Login failed: HTTP {response.status_code}"
		self._mark_online()
		self.sync_queue()
		return True, ""

	def logout(self) -> None:
		try:
			self.session.get(self._url("/logout/"), timeout=10)
		except Exception:
			self._mark_offline()

	def get_json(self, path: str) -> dict[str, Any]:
		try:
			response = self.session.get(
				self._url(path),
				headers={"X-Requested-With": "XMLHttpRequest"},
				timeout=20,
			)
			response.raise_for_status()
			payload = response.json()
			if isinstance(payload, dict):
				self._save_json_cache(path, payload)
			self._mark_online()
			self.sync_queue()
			return payload
		except Exception as exc:
			self._mark_offline()
			cached = self._cached_json(path)
			if cached is not None:
				return cached
			raise RuntimeError(f"Offline and no local cache: {exc}") from exc

	def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
		try:
			self._ensure_csrf()
			response = self.session.post(
				self._url(path),
				json=payload,
				headers={
					"X-Requested-With": "XMLHttpRequest",
					"X-CSRFToken": self.csrf_token,
					"Referer": self._url("/"),
				},
				timeout=20,
			)
			response.raise_for_status()
			body = response.json()
			self._mark_online()
			self.sync_queue()
			return body if isinstance(body, dict) else {"ok": True}
		except Exception:
			self._mark_offline()
			self.offline.enqueue("POST_JSON", path, payload)
			return {
				"ok": True,
				"queued_offline": True,
				"message": "Saved offline and queued for sync.",
			}

	def post_form(
		self,
		path: str,
		data: dict[str, Any],
		files: dict[str, tuple[str, bytes, str]] | None = None,
	) -> dict[str, Any]:
		try:
			self._ensure_csrf()
			response = self.session.post(
				self._url(path),
				data=data,
				files=files,
				headers={
					"X-Requested-With": "XMLHttpRequest",
					"X-CSRFToken": self.csrf_token,
					"Referer": self._url("/"),
				},
				timeout=30,
			)
			response.raise_for_status()
			body = response.json()
			self._mark_online()
			self.sync_queue()
			return body if isinstance(body, dict) else {"ok": True}
		except Exception:
			self._mark_offline()
			files_payload = self.offline.encode_files_for_queue(files)
			self.offline.enqueue("POST_FORM", path, data, files_payload=files_payload)
			return {
				"ok": True,
				"queued_offline": True,
				"message": "Form saved offline and queued for sync.",
			}

	def download_file(self, path: str) -> bytes:
		response = self.session.get(self._url(path), timeout=30)
		response.raise_for_status()
		return response.content

	def sync_queue(self) -> None:
		if self._sync_in_progress or not self.is_online:
			return
		self._sync_in_progress = True
		try:
			for action in self.offline.get_due_actions():
				action_id = int(action["id"])
				method = str(action["method"])
				path = str(action["path"])
				data = dict(action["data"])
				attempts = int(action["attempts"] or 0)
				try:
					if method == "POST_JSON":
						self._ensure_csrf()
						resp = self.session.post(
							self._url(path),
							json=data,
							headers={
								"X-Requested-With": "XMLHttpRequest",
								"X-CSRFToken": self.csrf_token,
								"Referer": self._url("/"),
							},
							timeout=20,
						)
						resp.raise_for_status()
					elif method == "POST_FORM":
						self._ensure_csrf()
						files_payload = action.get("files_payload")
						files = None
						if isinstance(files_payload, dict):
							files = self.offline.decode_files_from_queue(files_payload)
						resp = self.session.post(
							self._url(path),
							data=data,
							files=files,
							headers={
								"X-Requested-With": "XMLHttpRequest",
								"X-CSRFToken": self.csrf_token,
								"Referer": self._url("/"),
							},
							timeout=30,
						)
						resp.raise_for_status()
					self.offline.remove_action(action_id)
				except Exception as exc:
					self.offline.mark_failed(action_id, str(exc), attempts + 1)
					self._mark_offline()
					break
		finally:
			self._sync_in_progress = False

	def set_language(self, lang: str) -> None:
		self.post_json("/settings/api/language/", {"language": lang})

	def fetch_dashboard_bundle(self, period: str = "today") -> dict[str, Any]:
		def safe_get(path: str) -> dict[str, Any]:
			try:
				payload = self.get_json(path)
				return payload if isinstance(payload, dict) else {}
			except Exception:
				return {}

		overview_payload = safe_get(f"/api/reports/overview/?period={period}")
		if not overview_payload.get("data"):
			overview_payload = safe_get(f"/api/reports/overview/table/?period={period}")
		bookings_payload = safe_get("/api/bookings/?status=")
		payments_payload = safe_get("/api/payments/")

		overview_data = overview_payload.get("data") or {}
		if not overview_data and isinstance(overview_payload.get("rows"), list) and overview_payload["rows"]:
			overview_data = overview_payload["rows"][0]

		return {
			"overview": overview_data,
			"bookings": bookings_payload.get("results", bookings_payload.get("rows", [])),
			"payments": payments_payload.get("results", payments_payload.get("rows", [])),
		}

	def fetch_notifications(self) -> dict[str, Any]:
		return self.get_json("/settings/api/notifications/")

	def clear_notifications(self) -> dict[str, Any]:
		return self.post_json("/settings/api/notifications/clear/", {})
