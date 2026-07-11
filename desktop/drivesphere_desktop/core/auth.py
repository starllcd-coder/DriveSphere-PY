from __future__ import annotations

from drivesphere_desktop.core.api_client import ApiClient


class AuthService:
	def __init__(self, api_client: ApiClient) -> None:
		self.api_client = api_client
		self._is_authenticated = False
		self.last_error = ""

	def login(self, identifier: str, password: str, branch: str, remember_me: bool) -> bool:
		ok, error = self.api_client.login(identifier, password, branch, remember_me)
		self._is_authenticated = ok
		self.last_error = error
		return ok

	def logout(self) -> None:
		self.api_client.logout()
		self._is_authenticated = False

	@property
	def is_authenticated(self) -> bool:
		return self._is_authenticated
