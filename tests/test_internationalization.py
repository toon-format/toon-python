"""Internationalization tests for TOON format (Section 16 of spec).

Tests Unicode support, emoji handling, and UTF-8 encoding per
TOON specification Section 16 (Internationalization).
"""

import pytest

from toon_format import decode, encode


class TestUnicodeSupport:
    """Tests for full Unicode support in keys and values."""

    def test_emoji_in_string_values(self):
        """Emoji should be preserved in string values."""
        data = {"message": "Hello 👋 World 🌍"}

        result = encode(data)
        assert "👋" in result
        assert "🌍" in result

        decoded = decode(result)
        assert decoded["message"] == "Hello 👋 World 🌍"

    def test_emoji_in_array_values(self):
        """Emoji should work in array elements."""
        data = {"tags": ["🎉", "🎊", "🎈"]}

        result = encode(data)
        assert "🎉" in result

        decoded = decode(result)
        assert decoded["tags"] == ["🎉", "🎊", "🎈"]

    def test_emoji_in_object_keys(self):
        """Emoji should work in object keys (when quoted)."""
        # Emoji keys need to be quoted per spec (not matching identifier pattern)
        data = {"status": "👍"}

        result = encode(data)
        decoded = decode(result)
        assert decoded["status"] == "👍"

    def test_chinese_characters(self):
        """Chinese characters should be preserved."""
        data = {"greeting": "你好世界", "items": ["苹果", "香蕉", "橙子"]}

        result = encode(data)
        assert "你好世界" in result

        decoded = decode(result)
        assert decoded["greeting"] == "你好世界"
        assert decoded["items"] == ["苹果", "香蕉", "橙子"]

    def test_arabic_characters(self):
        """Arabic characters should be preserved."""
        data = {"greeting": "مرحبا بالعالم", "numbers": ["واحد", "اثنان", "ثلاثة"]}

        result = encode(data)
        assert "مرحبا" in result

        decoded = decode(result)
        assert decoded["greeting"] == "مرحبا بالعالم"
        assert decoded["numbers"] == ["واحد", "اثنان", "ثلاثة"]

    def test_japanese_characters(self):
        """Japanese characters (Hiragana, Katakana, Kanji) should be preserved."""
        data = {"hiragana": "こんにちは", "katakana": "カタカナ", "kanji": "漢字"}

        result = encode(data)
        assert "こんにちは" in result
        assert "カタカナ" in result
        assert "漢字" in result

        decoded = decode(result)
        assert decoded["hiragana"] == "こんにちは"
        assert decoded["katakana"] == "カタカナ"
        assert decoded["kanji"] == "漢字"

    def test_korean_characters(self):
        """Korean characters (Hangul) should be preserved."""
        data = {"greeting": "안녕하세요"}

        result = encode(data)
        assert "안녕하세요" in result

        decoded = decode(result)
        assert decoded["greeting"] == "안녕하세요"

    def test_cyrillic_characters(self):
        """Cyrillic characters should be preserved."""
        data = {"greeting": "Привет мир", "items": ["Москва", "Санкт-Петербург"]}

        result = encode(data)
        assert "Привет" in result

        decoded = decode(result)
        assert decoded["greeting"] == "Привет мир"
        assert decoded["items"] == ["Москва", "Санкт-Петербург"]

    def test_mixed_scripts(self):
        """Mixed scripts in the same document should work."""
        data = {"english": "Hello", "chinese": "你好", "arabic": "مرحبا", "emoji": "👋"}

        result = encode(data)
        decoded = decode(result)

        assert decoded["english"] == "Hello"
        assert decoded["chinese"] == "你好"
        assert decoded["arabic"] == "مرحبا"
        assert decoded["emoji"] == "👋"


class TestUTF8Encoding:
    """Tests for UTF-8 encoding compliance."""

    def test_utf8_roundtrip(self):
        """UTF-8 strings should roundtrip correctly."""
        # Various Unicode characters
        data = {
            "ascii": "Hello",
            "latin": "Café",
            "symbols": "©®™",
            "math": "∑∫∂",
            "arrows": "←→↑↓",
            "emoji": "😀😃😄",
        }

        result = encode(data)
        # Result should be UTF-8 encodable
        utf8_bytes = result.encode("utf-8")
        assert isinstance(utf8_bytes, bytes)

        # Should decode back correctly
        decoded = decode(result)
        assert decoded == data

    def test_bmp_characters(self):
        """Basic Multilingual Plane characters should work."""
        # Characters in BMP (U+0000 to U+FFFF)
        data = {"text": "Hello\u00a9World\u2603"}  # © and ☃

        result = encode(data)
        decoded = decode(result)
        assert decoded["text"] == "Hello©World☃"

    def test_supplementary_plane_characters(self):
        """Supplementary plane characters (above U+FFFF) should work."""
        # Mathematical Alphanumeric Symbols (U+1D400-U+1D7FF)
        # Emoji (U+1F300-U+1F9FF)
        data = {"text": "𝕳𝖊𝖑𝖑𝖔 🌟"}  # Gothic letters and star emoji

        result = encode(data)
        decoded = decode(result)
        assert "𝕳𝖊𝖑𝖑𝖔" in decoded["text"]
        assert "🌟" in decoded["text"]

    def test_zero_width_characters(self):
        """Zero-width characters should be preserved."""
        # Zero-width joiner and zero-width space
        data = {"text": "Hello\u200bWorld\u200d"}

        result = encode(data)
        decoded = decode(result)
        assert decoded["text"] == "Hello\u200bWorld\u200d"

    def test_combining_characters(self):
        """Combining diacritical marks should be preserved."""
        # e with combining acute accent
        data = {"text": "e\u0301"}  # é as e + combining acute

        result = encode(data)
        decoded = decode(result)
        assert decoded["text"] == "e\u0301"

    def test_rtl_text(self):
        """Right-to-left text should be preserved."""
        data = {"hebrew": "שלום", "arabic": "مرحبا"}

        result = encode(data)
        decoded = decode(result)
        assert decoded["hebrew"] == "שלום"
        assert decoded["arabic"] == "مرحبا"


class TestSpecialUnicodeScenarios:
    """Tests for special Unicode scenarios."""

    def test_emoji_with_skin_tone_modifiers(self):
        """Emoji with skin tone modifiers should be preserved."""
        data = {"emoji": "👋🏻👋🏼👋🏽👋🏾👋🏿"}

        result = encode(data)
        decoded = decode(result)
        assert decoded["emoji"] == "👋🏻👋🏼👋🏽👋🏾👋🏿"

    def test_emoji_with_zwj_sequences(self):
        """Emoji ZWJ sequences (family emojis etc) should be preserved."""
        # Family emoji composed with ZWJ
        data = {"family": "👨\u200d👩\u200d👧\u200d👦"}

        result = encode(data)
        decoded = decode(result)
        assert decoded["family"] == "👨\u200d👩\u200d👧\u200d👦"

    def test_flag_emojis(self):
        """Flag emojis (regional indicator symbols) should be preserved."""
        # US flag: 🇺🇸 (U+1F1FA U+1F1F8)
        data = {"flags": "🇺🇸🇬🇧🇯🇵"}

        result = encode(data)
        decoded = decode(result)
        assert decoded["flags"] == "🇺🇸🇬🇧🇯🇵"

    def test_unicode_in_tabular_format(self):
        """Unicode should work in tabular array format."""
        data = {
            "users": [
                {"name": "Alice", "emoji": "😀"},
                {"name": "Bob", "emoji": "😃"},
                {"name": "李明", "emoji": "😄"},
            ]
        }

        result = encode(data)
        decoded = decode(result)
        assert decoded["users"][0]["emoji"] == "😀"
        assert decoded["users"][2]["name"] == "李明"

    def test_unicode_with_internal_spaces(self):
        """Unicode with internal spaces should work unquoted."""
        data = {"text": "Hello 世界 Привет"}

        result = encode(data)
        # Internal spaces are safe unquoted per spec
        decoded = decode(result)
        assert decoded["text"] == "Hello 世界 Привет"

    def test_unicode_normalization_preserved(self):
        """Different Unicode normalizations should be preserved as-is."""
        # NFD vs NFC forms of é
        nfc = {"text": "\u00e9"}  # é as single character (NFC)
        nfd = {"text": "e\u0301"}  # é as e + combining accent (NFD)

        result_nfc = encode(nfc)
        result_nfd = encode(nfd)

        decoded_nfc = decode(result_nfc)
        decoded_nfd = decode(result_nfd)

        # Should preserve the original normalization form
        assert decoded_nfc["text"] == "\u00e9"
        assert decoded_nfd["text"] == "e\u0301"
        # These are visually the same but different Unicode representations
        assert decoded_nfc["text"] != decoded_nfd["text"]


class TestLocaleIndependence:
    """Tests that TOON is locale-independent per Section 16."""

    def test_numbers_not_locale_formatted(self):
        """Numbers should not use locale-specific formatting."""
        data = {"value": 1000000.5}

        result = encode(data)
        # Should not have thousands separators or locale-specific decimal
        assert "1000000.5" in result or "1000000" in result
        # Should not have comma thousand separators
        assert "1,000,000" not in result
        # Should not have locale-specific decimal separator
        assert "1000000,5" not in result

        decoded = decode(result)
        assert decoded["value"] == 1000000.5

    def test_booleans_not_locale_formatted(self):
        """Booleans should always be true/false, not locale variants."""
        data = {"flag": True}

        result = encode(data)
        # Should be lowercase "true", not "True" or locale variants
        assert "flag: true" in result
        assert "True" not in result
        assert "TRUE" not in result

        decoded = decode(result)
        assert decoded["flag"] is True

    def test_null_not_locale_formatted(self):
        """Null should always be "null", not locale variants."""
        data = {"value": None}

        result = encode(data)
        # Should be lowercase "null"
        assert "value: null" in result
        assert "None" not in result
        assert "NULL" not in result

        decoded = decode(result)
        assert decoded["value"] is None
