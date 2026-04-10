# test_braille_map.py
# Day 2 — Unit tests for braille_map.py
# Run with:  pytest test_braille_map.py -v

import pytest
from braille_map import (
    ENGLISH_BRAILLE,
    TAMIL_BRAILLE,
    TAMIL_VOWELS,
    TAMIL_CONSONANTS,
    PUNCTUATION,
    DIGIT_MAP,
    BRAILLE_MAP,
    CAPITAL_MARKER,
    NUMBER_MARKER,
    encode_text,
)


# -------------------------------------------------------
# Test 1: Every value must be exactly 5 ints
# -------------------------------------------------------
class TestBrailleMapStructure:
    """All maps must have values that are lists of exactly 5 elements."""

    def test_english_braille_length(self):
        assert all(len(v) == 5 for v in ENGLISH_BRAILLE.values()), \
            "Every English Braille value must be exactly 5 ints"

    def test_tamil_braille_length(self):
        assert all(len(v) == 5 for v in TAMIL_BRAILLE.values()), \
            "Every Tamil Braille value must be exactly 5 ints"

    def test_punctuation_length(self):
        assert all(len(v) == 5 for v in PUNCTUATION.values()), \
            "Every punctuation value must be exactly 5 ints"

    def test_digit_map_length(self):
        assert all(len(v) == 5 for v in DIGIT_MAP.values()), \
            "Every digit value must be exactly 5 ints"

    def test_capital_marker_length(self):
        assert len(CAPITAL_MARKER) == 5

    def test_number_marker_length(self):
        assert len(NUMBER_MARKER) == 5

    def test_full_braille_map_length(self):
        assert all(len(v) == 5 for v in BRAILLE_MAP.values()), \
            "Every BRAILLE_MAP value must be exactly 5 ints"


# -------------------------------------------------------
# Test 2: Every element must be 0 or 1
# -------------------------------------------------------
class TestBrailleMapValues:
    """All map values must contain only 0 or 1."""

    def test_english_braille_binary(self):
        assert all(
            b in (0, 1)
            for v in ENGLISH_BRAILLE.values()
            for b in v
        ), "English Braille values must only contain 0 or 1"

    def test_tamil_braille_binary(self):
        assert all(
            b in (0, 1)
            for v in TAMIL_BRAILLE.values()
            for b in v
        ), "Tamil Braille values must only contain 0 or 1"

    def test_punctuation_binary(self):
        assert all(
            b in (0, 1)
            for v in PUNCTUATION.values()
            for b in v
        ), "Punctuation values must only contain 0 or 1"

    def test_digit_map_binary(self):
        assert all(
            b in (0, 1)
            for v in DIGIT_MAP.values()
            for b in v
        ), "Digit map values must only contain 0 or 1"

    def test_capital_marker_binary(self):
        assert all(b in (0, 1) for b in CAPITAL_MARKER)

    def test_number_marker_binary(self):
        assert all(b in (0, 1) for b in NUMBER_MARKER)


# -------------------------------------------------------
# Test 3: Coverage checks
# -------------------------------------------------------
class TestCoverage:
    """Ensure full coverage of expected character sets."""

    def test_english_covers_a_to_z(self):
        for ch in "abcdefghijklmnopqrstuvwxyz":
            assert ch in ENGLISH_BRAILLE, f"Missing English letter: {ch}"

    def test_english_count(self):
        assert len(ENGLISH_BRAILLE) == 26

    def test_digits_0_to_9(self):
        for d in "0123456789":
            assert d in DIGIT_MAP, f"Missing digit: {d}"

    def test_digit_count(self):
        assert len(DIGIT_MAP) == 10

    def test_tamil_vowels_count(self):
        assert len(TAMIL_VOWELS) == 12, "Expected 12 Tamil vowels"

    def test_tamil_consonants_count(self):
        assert len(TAMIL_CONSONANTS) == 10, "Expected 10 Tamil consonants"

    def test_space_is_all_zeros(self):
        assert PUNCTUATION[' '] == [0, 0, 0, 0, 0]


# -------------------------------------------------------
# Test 4: Uniqueness within each map
# -------------------------------------------------------
class TestUniqueness:
    """No two characters in the same language should share the same pattern."""

    def test_english_unique_patterns(self):
        patterns = [tuple(v) for v in ENGLISH_BRAILLE.values()]
        assert len(patterns) == len(set(patterns)), \
            "Duplicate patterns found in English Braille"

    def test_tamil_unique_patterns(self):
        patterns = [tuple(v) for v in TAMIL_BRAILLE.values()]
        assert len(patterns) == len(set(patterns)), \
            "Duplicate patterns found in Tamil Braille"


# -------------------------------------------------------
# Test 5: encode_text() function
# -------------------------------------------------------
class TestEncodeText:
    """Test the encode_text() helper function."""

    def test_simple_english(self):
        result = encode_text("abc")
        assert len(result) == 3
        assert result[0]['char'] == 'a'
        assert result[0]['dots'] == [1, 0, 0, 0, 0]
        assert result[1]['char'] == 'b'
        assert result[2]['char'] == 'c'

    def test_each_entry_has_required_keys(self):
        result = encode_text("hello")
        for entry in result:
            assert 'char' in entry
            assert 'dots' in entry
            assert 'on_ms' in entry
            assert 'off_ms' in entry

    def test_each_dots_is_5_binary(self):
        result = encode_text("hello world")
        for entry in result:
            assert len(entry['dots']) == 5
            assert all(b in (0, 1) for b in entry['dots'])

    def test_space_has_700ms_gap(self):
        result = encode_text("a b")
        space_entry = [e for e in result if e['char'] == ' ']
        assert len(space_entry) == 1
        assert space_entry[0]['off_ms'] == 700
        assert space_entry[0]['dots'] == [0, 0, 0, 0, 0]

    def test_uppercase_adds_capital_marker(self):
        result = encode_text("A")
        assert len(result) == 2  # capital marker + 'a'
        assert result[0]['char'] == '⇧'
        assert result[0]['dots'] == [0, 1, 0, 0, 0]
        assert result[1]['char'] == 'a'

    def test_digit_adds_number_marker(self):
        result = encode_text("5")
        assert len(result) == 2  # number marker + '5'
        assert result[0]['char'] == '#'
        assert result[0]['dots'] == [0, 0, 0, 0, 1]

    def test_consecutive_digits_single_marker(self):
        result = encode_text("123")
        # should be: # 1 2 3  (one number marker, then three digits)
        assert len(result) == 4
        assert result[0]['char'] == '#'

    def test_tamil_mode(self):
        result = encode_text("அ", lang="ta")
        assert len(result) == 1
        assert result[0]['char'] == 'அ'
        assert result[0]['dots'] == [1, 0, 0, 0, 0]

    def test_unmapped_char_double_buzz(self):
        result = encode_text("a@b")
        # '@' is unmapped, should produce [1, 0, 1, 0, 1]
        assert len(result) == 3
        assert result[0]['char'] == 'a'
        assert result[1]['char'] == '@'
        assert result[1]['dots'] == [1, 0, 1, 0, 1]
        assert result[2]['char'] == 'b'

    def test_empty_string(self):
        result = encode_text("")
        assert result == []

    def test_given_examples_match(self):
        """Verify the exact examples from the spec image."""
        assert ENGLISH_BRAILLE['a'] == [1, 0, 0, 0, 0]
        assert ENGLISH_BRAILLE['b'] == [1, 1, 0, 0, 0]
        assert ENGLISH_BRAILLE['c'] == [1, 0, 0, 1, 0]

    def test_day8_specific_assertions(self):
        assert len(encode_text('hello')) == 5
        assert len(encode_text('hi there')) == 8 # includes space
        assert all(len(d['dots']) == 5 for d in encode_text('test'))
