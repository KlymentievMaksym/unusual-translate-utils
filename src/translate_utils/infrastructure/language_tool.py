from typing import Any

import requests
from requests.adapters import HTTPAdapter

from translate_utils.core.exceptions import LanguageToolConnectionError, LanguageToolResponseError


class LanguageToolClient:
    def __init__(
        self,
        api_url: str = "https://api.languagetool.org/v2",
        api_username: str | None = None,
        api_key: str | None = None,
        language: str = "auto",
        disabled_rules: list[str] | None = None,
        dicts: list[str] | None = None,
        max_workers: int = 20,
        timeout: int = 60,
    ) -> None:

        self.api_url = api_url
        self.api_username = api_username
        self.api_key = api_key
        self.language = language
        self.disabled_rules = disabled_rules
        self.dicts = dicts
        self.timeout = timeout

        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=max_workers,
            pool_maxsize=max_workers,
            max_retries=3
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def check_text(self, text: str) -> dict[str, Any]:
        payload = {
            "text": text,
            "language": self.language,
        }

        if self.api_username:
            payload["username"] = self.api_username
        if self.api_key:
            payload["apiKey"] = self.api_key
        if self.disabled_rules:
            payload["disabledRules"] = ",".join(self.disabled_rules)
        if self.dicts:
            payload["dicts"] = ",".join(self.dicts)

        check_head = "check"
        if self.api_url[-1] != "/":
            check_head = "/" + check_head

        try:
            response = self.session.post(
                self.api_url + check_head,
                data=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            raise LanguageToolConnectionError(f"HTTP request failed: {exc}") from exc
        except ValueError as exc:
            raise LanguageToolResponseError(f"Failed to parse response JSON: {exc}") from exc
