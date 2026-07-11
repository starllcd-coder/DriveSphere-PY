from dataclasses import dataclass


@dataclass
class AppState:
	base_url: str = "http://127.0.0.1:8000"
	ui_lang: str = "en"
	is_rtl: bool = False
	user_display_name: str = ""
	active_branch_name: str = ""

	def set_language(self, lang: str) -> None:
		lang = (lang or "en").lower()
		self.ui_lang = lang
		self.is_rtl = lang == "ar"
