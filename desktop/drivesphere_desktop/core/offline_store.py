from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class OfflineStore:
	def __init__(self, db_path: Path) -> None:
		self.db_path = db_path
		self.db_path.parent.mkdir(parents=True, exist_ok=True)
		self._init_db()

	def _connect(self) -> sqlite3.Connection:
		conn = sqlite3.connect(str(self.db_path))
		conn.row_factory = sqlite3.Row
		return conn

	def _init_db(self) -> None:
		with self._connect() as conn:
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS cache_entries(
					key TEXT PRIMARY KEY,
					payload TEXT NOT NULL,
					updated_at INTEGER NOT NULL
				)
				"""
			)
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS sync_queue(
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					method TEXT NOT NULL,
					path TEXT NOT NULL,
					data_json TEXT NOT NULL,
					files_json TEXT NOT NULL,
					fingerprint TEXT NOT NULL UNIQUE,
					attempts INTEGER NOT NULL DEFAULT 0,
					last_error TEXT NOT NULL DEFAULT '',
					next_retry_at INTEGER NOT NULL DEFAULT 0,
					created_at INTEGER NOT NULL,
					updated_at INTEGER NOT NULL
				)
				"""
			)

	def save_cache(self, key: str, payload: Any) -> None:
		now = int(time.time() * 1000)
		raw = json.dumps(payload, ensure_ascii=False)
		with self._connect() as conn:
			conn.execute(
				"""
				INSERT INTO cache_entries(key, payload, updated_at)
				VALUES (?, ?, ?)
				ON CONFLICT(key) DO UPDATE SET
					payload=excluded.payload,
					updated_at=excluded.updated_at
				""",
				(key, raw, now),
			)

	def get_cache(self, key: str) -> dict[str, Any] | list[Any] | None:
		with self._connect() as conn:
			row = conn.execute(
				"SELECT payload FROM cache_entries WHERE key = ? LIMIT 1",
				(key,),
			).fetchone()
		if row is None:
			return None
		try:
			return json.loads(str(row["payload"]))
		except Exception:
			return None

	def _fingerprint(
		self,
		method: str,
		path: str,
		data: dict[str, Any],
		files_json: str,
	) -> str:
		normalized = json.dumps(data, sort_keys=True, ensure_ascii=False)
		raw = f"{method}|{path}|{normalized}|{files_json}"
		return hashlib.sha256(raw.encode("utf-8")).hexdigest()

	def encode_files_for_queue(
		self,
		files: dict[str, tuple[str, bytes, str]] | None,
	) -> dict[str, dict[str, str]]:
		if not files:
			return {}
		encoded: dict[str, dict[str, str]] = {}
		for field, triple in files.items():
			file_name, content, content_type = triple
			encoded[field] = {
				"name": file_name,
				"content_type": content_type,
				"bytes_b64": base64.b64encode(content).decode("ascii"),
			}
		return encoded

	def decode_files_from_queue(
		self,
		payload: dict[str, dict[str, str]],
	) -> dict[str, tuple[str, bytes, str]]:
		files: dict[str, tuple[str, bytes, str]] = {}
		for field, spec in payload.items():
			raw_b64 = spec.get("bytes_b64", "")
			files[field] = (
				spec.get("name", "upload.bin"),
				base64.b64decode(raw_b64.encode("ascii")) if raw_b64 else b"",
				spec.get("content_type", "application/octet-stream"),
			)
		return files

	def enqueue(
		self,
		method: str,
		path: str,
		data: dict[str, Any] | None,
		files_payload: dict[str, dict[str, str]] | None = None,
	) -> None:
		now = int(time.time() * 1000)
		data_obj = data or {}
		files_obj = files_payload or {}
		data_json = json.dumps(data_obj, ensure_ascii=False)
		files_json = json.dumps(files_obj, ensure_ascii=False)
		fp = self._fingerprint(method, path, data_obj, files_json)
		with self._connect() as conn:
			row = conn.execute(
				"SELECT id FROM sync_queue WHERE fingerprint = ? LIMIT 1",
				(fp,),
			).fetchone()
			if row is None:
				conn.execute(
					"""
					INSERT INTO sync_queue(
						method, path, data_json, files_json, fingerprint,
						attempts, last_error, next_retry_at, created_at, updated_at
					)
					VALUES (?, ?, ?, ?, ?, 0, '', 0, ?, ?)
					""",
					(method, path, data_json, files_json, fp, now, now),
				)
				return
			conn.execute(
				"""
				UPDATE sync_queue
				SET data_json = ?, files_json = ?, updated_at = ?
				WHERE id = ?
				""",
				(data_json, files_json, now, int(row["id"])),
			)

	def get_due_actions(self) -> list[dict[str, Any]]:
		now = int(time.time() * 1000)
		with self._connect() as conn:
			rows = conn.execute(
				"""
				SELECT id, method, path, data_json, files_json, attempts
				FROM sync_queue
				WHERE next_retry_at <= ?
				ORDER BY id ASC
				""",
				(now,),
			).fetchall()
		items: list[dict[str, Any]] = []
		for row in rows:
			try:
				data = json.loads(str(row["data_json"]))
				files_payload = json.loads(str(row["files_json"]))
			except Exception:
				data = {}
				files_payload = {}
			items.append(
				{
					"id": int(row["id"]),
					"method": str(row["method"]),
					"path": str(row["path"]),
					"data": data if isinstance(data, dict) else {},
					"files_payload": files_payload if isinstance(files_payload, dict) else {},
					"attempts": int(row["attempts"] or 0),
				}
			)
		return items

	def remove_action(self, action_id: int) -> None:
		with self._connect() as conn:
			conn.execute("DELETE FROM sync_queue WHERE id = ?", (action_id,))

	def mark_failed(self, action_id: int, error: str, attempts: int) -> None:
		now = int(time.time() * 1000)
		backoff_seconds = 15 if attempts <= 1 else (60 if attempts <= 3 else 300)
		with self._connect() as conn:
			conn.execute(
				"""
				UPDATE sync_queue
				SET attempts = ?, last_error = ?, next_retry_at = ?, updated_at = ?
				WHERE id = ?
				""",
				(attempts, error[:300], now + (backoff_seconds * 1000), now, action_id),
			)

	def queue_size(self) -> int:
		with self._connect() as conn:
			row = conn.execute("SELECT COUNT(*) AS c FROM sync_queue").fetchone()
		return int(row["c"]) if row else 0
