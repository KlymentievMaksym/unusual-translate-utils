from typing import Any

import requests


class LanguageToolClient:
    def __init__(
        self,
        api_url: str = "https://api.languagetool.org/v2",
        api_username: str | None = None,
        api_key: str | None = None,
        language: str = "auto",
        disabled_rules: list[str] | None = None,
        timeout: int = 10,
    ) -> None:

        self.api_url = api_url
        self.api_username = api_username
        self.api_key = api_key
        self.language = language
        self.disabled_rules = disabled_rules
        self.timeout = timeout

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

        check_head = "check"
        if self.api_url[-1] != "/":
            check_head = "/" + check_head

        response = requests.post(
            self.api_url + check_head,
            data=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
