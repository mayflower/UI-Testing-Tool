"""Unit-Tests fuer pure Helper aus utils/discovery.py (kein Playwright noetig)."""

from __future__ import annotations

import pytest

from utils.discovery import _pick_stable_class


class TestPickStableClass:
    def test_returns_first_stable_class(self):
        assert _pick_stable_class("chat-widget jsx-abc123") == "chat-widget"

    def test_skips_styled_jsx(self):
        assert _pick_stable_class("jsx-abc123 message-list") == "message-list"

    def test_skips_emotion_css(self):
        assert _pick_stable_class("css-1abc2d real-class") == "real-class"

    def test_skips_styled_components(self):
        assert _pick_stable_class("sc-AxiKw real-class") == "real-class"

    def test_skips_hex_hash(self):
        assert _pick_stable_class("a1b2c3d4 stable") == "stable"

    def test_skips_underscore_prefix(self):
        assert _pick_stable_class("_abc12 real") == "real"

    def test_all_generated_returns_none(self):
        assert _pick_stable_class("jsx-abc css-xy sc-AxiKw a1b2c3d4") is None

    def test_empty_returns_none(self):
        assert _pick_stable_class("") is None

    def test_single_stable_class(self):
        assert _pick_stable_class("widget") == "widget"
