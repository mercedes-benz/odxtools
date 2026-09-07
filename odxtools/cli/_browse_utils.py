# SPDX-License-Identifier: MIT
from typing import Any

from InquirerPy.prompts.list import ListPrompt
from InquirerPy.separator import Separator
from prompt_toolkit.keys import Keys


class _ListPromptWithCustomKeys(ListPrompt):  # type: ignore[misc,unused-ignore]
    """InquirerPy prompt for lists that adds support for PageDown, PageUp, Home and End keys."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.kb_maps.setdefault("page-up", []).append({"key": Keys.PageUp})
        self.kb_maps.setdefault("page-down", []).append({"key": Keys.PageDown})
        self.kb_maps.setdefault("home", []).append({"key": Keys.Home})
        self.kb_maps.setdefault("end", []).append({"key": Keys.End})
        self.kb_func_lookup["page-up"] = [{"func": self._handle_page_up}]
        self.kb_func_lookup["page-down"] = [{"func": self._handle_page_down}]
        self.kb_func_lookup["home"] = [{"func": self._handle_home}]
        self.kb_func_lookup["end"] = [{"func": self._handle_end}]

    def _handle_page_up(self, event: Any) -> None:
        page_size = getattr(self, "_dimmension_max_height", 10)
        for _ in range(page_size):
            old_idx = self.content_control.selected_choice_index
            if old_idx == 0:
                break
            self._handle_up(event)
            if self.content_control.selected_choice_index >= old_idx:
                break

    def _handle_page_down(self, event: Any) -> None:
        page_size = getattr(self, "_dimmension_max_height", 10)
        last_idx = self.content_control.choice_count - 1
        for _ in range(page_size):
            old_idx = self.content_control.selected_choice_index
            if old_idx == last_idx:
                break
            self._handle_down(event)
            if self.content_control.selected_choice_index <= old_idx:
                break

    def _handle_home(self, event: Any) -> None:
        for index, choice in enumerate(self.content_control.choices):
            if not isinstance(choice["value"], Separator):
                self.content_control.selected_choice_index = index
                break

    def _handle_end(self, event: Any) -> None:
        for index in range(self.content_control.choice_count - 1, -1, -1):
            if not isinstance(self.content_control.choices[index]["value"], Separator):
                self.content_control.selected_choice_index = index
                break
