"""Test the functions and assertions of v3_2.py meta-model."""

import pathlib
import unittest
from unittest import mock
from typing import List, Set, Optional, Tuple

import aas_core_codegen.common
import icontract
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier
from aas_core_codegen.infer_for_schema import match as infer_for_schema_match

from aas_core_meta import v3_2
import tests.common

# pylint: disable=missing-docstring


class Test_matches_XML_serializable_string(unittest.TestCase):
    def test_free_form_text(self) -> None:
        assert v3_2.matches_XML_serializable_string(
            "some free & <free> \u1984 form text"
        )

    def test_fffe(self) -> None:
        assert not v3_2.matches_XML_serializable_string("\ufffe")

    def test_ffff(self) -> None:
        assert not v3_2.matches_XML_serializable_string("\uffff")

    # noinspection SpellCheckingInspection
    def test_surrogate_characters(self) -> None:
        assert not v3_2.matches_XML_serializable_string("\ud800")
        assert not v3_2.matches_XML_serializable_string("\udfff")

    def test_nul(self) -> None:
        assert not v3_2.matches_XML_serializable_string("\x00")


class Test_matches_xs_date_time_utc(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_date_time_UTC("")

    def test_date(self) -> None:
        assert not v3_2.matches_xs_date_time_UTC("2022-04-01")

    def test_date_with_time_zone(self) -> None:
        assert not v3_2.matches_xs_date_time_UTC("2022-04-01Z")

    def test_date_time_without_zone(self) -> None:
        assert not v3_2.matches_xs_date_time_UTC("2022-04-01T01:02:03")

    def test_date_time_with_offset(self) -> None:
        assert not v3_2.matches_xs_date_time_UTC("2022-04-01T01:02:03+02:00")

    def test_date_time_with_UTC(self) -> None:
        assert v3_2.matches_xs_date_time_UTC("2022-04-01T01:02:03Z")

    def test_date_time_without_seconds(self) -> None:
        assert not v3_2.matches_xs_date_time_UTC("2022-04-01T01:02Z")

    def test_date_time_without_minutes(self) -> None:
        assert not v3_2.matches_xs_date_time_UTC("2022-04-01T01Z")

    def test_date_time_with_UTC_and_suffix(self) -> None:
        assert not v3_2.matches_xs_date_time_UTC(
            "2022-04-01T01:02:03Z-unexpected-suffix"
        )


class Test_matches_MIME_type(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_MIME_type("")

    def test_integer(self) -> None:
        assert not v3_2.matches_MIME_type("1234")

    def test_common(self) -> None:
        assert v3_2.matches_MIME_type("audio/aac")

    def test_dash(self) -> None:
        assert v3_2.matches_MIME_type("application/x-abiword")

    def test_dot(self) -> None:
        assert v3_2.matches_MIME_type("application/vnd.amazon.ebook")

    def test_plus(self) -> None:
        assert v3_2.matches_MIME_type("application/vnd.apple.installer+xml")

    def test_number_in_suffix(self) -> None:
        assert v3_2.matches_MIME_type("audio/3gpp2")


class Test_matches_RFC_2396_path(unittest.TestCase):
    def test_empty(self) -> None:
        assert v3_2.matches_RFC_2396("")

    def test_integer(self) -> None:
        assert v3_2.matches_RFC_2396("1234")

    def test_absolute_without_scheme(self) -> None:
        assert v3_2.matches_RFC_2396("/path/to/somewhere")

    def test_relative_without_scheme(self) -> None:
        assert v3_2.matches_RFC_2396("path/to/somewhere")

    def test_local_absolute_with_scheme(self) -> None:
        assert v3_2.matches_RFC_2396("file:/path/to/somewhere")

    def test_local_relative_path_with_scheme(self) -> None:
        assert v3_2.matches_RFC_2396("file:path/to/somewhere")

    def test_absolute_path_without_scheme(self) -> None:
        assert v3_2.matches_RFC_2396("/path/to/somewhere")

    def test_relative_path_without_scheme(self) -> None:
        assert v3_2.matches_RFC_2396("path/to/somewhere")

    def test_URI(self) -> None:
        assert v3_2.matches_RFC_2396(
            "https://github.com/aas-core-works/aas-core-codegen"
        )

    def test_too_many_fragments(self) -> None:
        assert not v3_2.matches_RFC_2396("http://datypic.com#frag1#frag2")

    def test_percentage_followed_by_non_two_hexadecimal_digits(self) -> None:
        assert not v3_2.matches_RFC_2396("http://datypic.com#f% rag")


class Test_matches_BCP_47(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_BCP_47("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_BCP_47("some free form text")

    def test_valid(self) -> None:
        for text in ["de", "de-CH", "zh-cmn-Hans-CN"]:
            self.assertTrue(v3_2.matches_BCP_47(text), text)


class Test_matches_xs_any_URI(unittest.TestCase):
    # See: http://www.datypic.com/sc/xsd/t-xsd_anyURI.html

    def test_empty(self) -> None:
        # NOTE (mristin):
        # An empty string is a valid ``xs:anyURI``,
        # see https://lists.w3.org/Archives/Public/xml-dist-app/2003Mar/0076.html and
        # https://lists.w3.org/Archives/Public/xml-dist-app/2003Mar/0078.html
        assert v3_2.matches_xs_any_URI("")

    def test_integer(self) -> None:
        assert v3_2.matches_xs_any_URI("1234")

    def test_absolute_path_without_scheme(self) -> None:
        assert v3_2.matches_xs_any_URI("/path/to/somewhere")

    def test_relative_path_without_scheme(self) -> None:
        assert v3_2.matches_xs_any_URI("path/to/somewhere")

    def test_URI(self) -> None:
        assert v3_2.matches_xs_any_URI(
            "https://github.com/aas-core-works/aas-core-codegen"
        )

    def test_too_many_fragments(self) -> None:
        assert not v3_2.matches_xs_any_URI("http://datypic.com#frag1#frag2")

    def test_percentage_followed_by_non_two_hexadecimal_digits(self) -> None:
        assert not v3_2.matches_xs_any_URI("http://datypic.com#f% rag")


class Test_matches_xs_base_64_binary(unittest.TestCase):
    # See http://www.datypic.com/sc/xsd/t-xsd_base64Binary.html

    def test_without_space_uppercase(self) -> None:
        assert v3_2.matches_xs_base_64_binary("0FB8")

    def test_without_space_lowercase(self) -> None:
        assert v3_2.matches_xs_base_64_binary("0fb8")

    def test_whitespace_is_allowed_anywhere_in_the_value(self) -> None:
        assert v3_2.matches_xs_base_64_binary("0 FB8 0F+9")

    def test_equals_signs_are_used_for_padding(self) -> None:
        assert v3_2.matches_xs_base_64_binary("0F+40A==")

    def test_an_empty_value_is_valid(self) -> None:
        assert v3_2.matches_xs_base_64_binary("")

    def test_an_odd_number_of_characters_is_not_valid(self) -> None:
        # Characters must appear in groups of four.
        assert not v3_2.matches_xs_base_64_binary("FB8")

    def test_equals_signs_may_only_appear_at_the_end(self) -> None:
        assert not v3_2.matches_xs_base_64_binary("==0F")


class Test_matches_xs_date(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_date("")

    def test_date(self) -> None:
        assert v3_2.matches_xs_date("2022-04-01")

    def test_date_with_utc(self) -> None:
        assert v3_2.matches_xs_date("2022-04-01Z")

    def test_date_with_offset(self) -> None:
        assert v3_2.matches_xs_date("2022-04-01+02:34")

    def test_date_with_invalid_offset(self) -> None:
        assert not v3_2.matches_xs_date("2022-04-01+15:00")

    def test_date_with_unexpected_suffix(self) -> None:
        assert not v3_2.matches_xs_date("2022-04-01unexpected")


class Test_matches_xs_date_time(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_date_time("")

    def test_date(self) -> None:
        assert not v3_2.matches_xs_date_time("2022-04-01")

    def test_date_with_time_zone(self) -> None:
        assert not v3_2.matches_xs_date_time("2022-04-01Z")

    def test_date_time_without_zone(self) -> None:
        assert v3_2.matches_xs_date_time("2022-04-01T01:02:03")

    def test_date_time_with_offset(self) -> None:
        assert v3_2.matches_xs_date_time("2022-04-01T01:02:03+02:00")

    def test_date_time_with_invalid_offset(self) -> None:
        assert not v3_2.matches_xs_date_time("2022-04-01T01:02:03+15:00")

    def test_date_time_with_UTC(self) -> None:
        assert v3_2.matches_xs_date_time("2022-04-01T01:02:03Z")

    def test_date_time_without_seconds(self) -> None:
        assert not v3_2.matches_xs_date_time("2022-04-01T01:02Z")

    def test_date_time_without_minutes(self) -> None:
        assert not v3_2.matches_xs_date_time("2022-04-01T01Z")

    def test_date_time_with_unexpected_suffix(self) -> None:
        assert not v3_2.matches_xs_date_time("2022-04-01T01:02:03Z-unexpected-suffix")

    def test_date_time_with_unexpected_prefix(self) -> None:
        assert not v3_2.matches_xs_date_time("unexpected-prefix-2022-04-01T01:02:03Z")


class Test_matches_xs_decimal(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_decimal("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_decimal("some free form text")

    def test_integer(self) -> None:
        assert v3_2.matches_xs_decimal("1234")

    def test_decimal(self) -> None:
        assert v3_2.matches_xs_decimal("1234.01234")

    def test_integer_with_preceding_zeros(self) -> None:
        assert v3_2.matches_xs_decimal("0001234")

    def test_decimal_with_preceding_zeros(self) -> None:
        assert v3_2.matches_xs_decimal("0001234.01234")

    def test_scientific_notation(self) -> None:
        assert not v3_2.matches_xs_decimal("12.123e123")


class Test_matches_xs_double(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_double("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_double("some free form text")

    def test_integer(self) -> None:
        assert v3_2.matches_xs_double("1234")

    def test_double(self) -> None:
        assert v3_2.matches_xs_double("1234.01234")

    def test_integer_with_preceding_zeros(self) -> None:
        assert v3_2.matches_xs_double("0001234")

    def test_double_with_preceding_zeros(self) -> None:
        assert v3_2.matches_xs_double("0001234.01234")

    def test_exponent_integer(self) -> None:
        assert v3_2.matches_xs_double("-12.34e5")
        assert v3_2.matches_xs_double("+12.34e5")
        assert v3_2.matches_xs_double("12.34e5")
        assert v3_2.matches_xs_double("12.34e+5")
        assert v3_2.matches_xs_double("12.34e-5")

    def test_exponent_float(self) -> None:
        assert not v3_2.matches_xs_double("-12.34e5.6")
        assert not v3_2.matches_xs_double("+12.34e5.6")
        assert not v3_2.matches_xs_double("12.34e5.6")
        assert not v3_2.matches_xs_double("12.34e+5.6")
        assert not v3_2.matches_xs_double("12.34e-5.6")

    def test_edge_cases(self) -> None:
        # NOTE (mristin):
        # See: https://www.oreilly.com/library/view/xml-schema/0596002521/re67.html
        assert not v3_2.matches_xs_double("+INF")
        assert v3_2.matches_xs_double("-INF")
        assert v3_2.matches_xs_double("INF")
        assert v3_2.matches_xs_double("NaN")

    def test_case_matters(self) -> None:
        assert not v3_2.matches_xs_double("inf")
        assert not v3_2.matches_xs_double("nan")


class Test_matches_xs_duration(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_duration("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_duration("some free form text")

    def test_integer(self) -> None:
        assert not v3_2.matches_xs_duration("1234")

    # NOTE (mristin):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-duration

    def test_valid_values(self) -> None:
        for text in [
            "PT1004199059S",
            "PT130S",
            "PT2M10S",
            "P1DT2S",
            "-P1Y",
            "P1Y2M3DT5H20M30.123S",
        ]:
            self.assertTrue(v3_2.matches_xs_duration(text), text)

    def test_leading_P_missing(self) -> None:
        assert not v3_2.matches_xs_duration("1Y")

    def test_separator_T_missing(self) -> None:
        assert not v3_2.matches_xs_duration("P1S")

    def test_not_all_parts_positive(self) -> None:
        assert not v3_2.matches_xs_duration("P-1Y")
        assert not v3_2.matches_xs_duration("P1Y-1M")

    def test_the_order_matters(self) -> None:
        assert not v3_2.matches_xs_duration("P1M2Y")


class Test_matches_xs_float(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_float("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_float("some free form text")

    def test_integer(self) -> None:
        assert v3_2.matches_xs_float("1234")

    def test_float(self) -> None:
        assert v3_2.matches_xs_float("1234.01234")

    def test_integer_with_preceding_zeros(self) -> None:
        assert v3_2.matches_xs_float("0001234")

    def test_float_with_preceding_zeros(self) -> None:
        assert v3_2.matches_xs_float("0001234.01234")

    def test_exponent_integer(self) -> None:
        assert v3_2.matches_xs_float("-12.34e5")
        assert v3_2.matches_xs_float("+12.34e5")
        assert v3_2.matches_xs_float("12.34e5")
        assert v3_2.matches_xs_float("12.34e+5")
        assert v3_2.matches_xs_float("12.34e-5")

    def test_exponent_float(self) -> None:
        assert not v3_2.matches_xs_float("-12.34e5.6")
        assert not v3_2.matches_xs_float("+12.34e5.6")
        assert not v3_2.matches_xs_float("12.34e5.6")
        assert not v3_2.matches_xs_float("12.34e+5.6")
        assert not v3_2.matches_xs_float("12.34e-5.6")

    def test_edge_cases(self) -> None:
        # NOTE (mristin):
        # See: https://www.oreilly.com/library/view/xml-schema/0596002521/re67.html
        assert not v3_2.matches_xs_float("+INF")
        assert v3_2.matches_xs_float("-INF")
        assert v3_2.matches_xs_float("INF")
        assert v3_2.matches_xs_float("NaN")

    def test_case_matters(self) -> None:
        assert not v3_2.matches_xs_float("inf")
        assert not v3_2.matches_xs_float("nan")


class Test_matches_xs_g_day(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_g_day("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_g_day("some free form text")

    # NOTE (mristin):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-gday

    def test_valid_values(self) -> None:
        for text in ["---01", "---01Z", "---01+02:00", "---01-04:00", "---15", "---31"]:
            self.assertTrue(v3_2.matches_xs_g_day(text), text)

    def test_unexpected_suffix(self) -> None:
        assert not v3_2.matches_xs_g_day("--30-")

    def test_day_outside_of_range(self) -> None:
        assert not v3_2.matches_xs_g_day("---35")

    def test_missing_leading_digit(self) -> None:
        assert not v3_2.matches_xs_g_day("---5")

    def test_missing_leading_dashes(self) -> None:
        assert not v3_2.matches_xs_g_day("15")


class Test_matches_xs_g_month(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_g_month("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_g_month("some free form text")

    # NOTE (mristin):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-gmonth

    def test_valid_values(self) -> None:
        for text in ["--05", "--11Z", "--11+02:00", "--11-04:00", "--02"]:
            self.assertTrue(v3_2.matches_xs_g_month(text), text)

    def test_unexpected_prefix_and_suffix(self) -> None:
        assert not v3_2.matches_xs_g_month("-01-")

    def test_month_outside_of_range(self) -> None:
        assert not v3_2.matches_xs_g_month("--13")

    def test_missing_leading_digit(self) -> None:
        assert not v3_2.matches_xs_g_month("--1")

    def test_missing_leading_dashes(self) -> None:
        assert not v3_2.matches_xs_g_month("01")


class Test_matches_xs_g_month_day(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_g_month_day("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_g_month_day("some free form text")

    # NOTE (mristin):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-gmonthday

    def test_valid_values(self) -> None:
        for text in [
            "--05-01",
            "--11-01Z",
            "--11-01+02:00",
            "--11-01-04:00",
            "--11-15",
            "--02-29",
        ]:
            self.assertTrue(v3_2.matches_xs_g_month_day(text), text)

    def test_unexpected_prefix_and_suffix(self) -> None:
        assert not v3_2.matches_xs_g_month_day("-01-30-")

    def test_day_outside_of_range(self) -> None:
        assert not v3_2.matches_xs_g_month_day("--01-35")

    def test_missing_leading_digit(self) -> None:
        assert not v3_2.matches_xs_g_month_day("--1-5")

    def test_missing_leading_dashes(self) -> None:
        assert not v3_2.matches_xs_g_month_day("01-15")


class Test_matches_xs_g_year(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_g_year("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_g_year("some free form text")

    # NOTE (mristin):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-gyear

    def test_valid_values(self) -> None:
        for text in ["2001", "2001+02:00", "2001Z", "2001+00:00", "-2001", "-20000"]:
            self.assertTrue(v3_2.matches_xs_g_year(text), text)

    def test_missing_century(self) -> None:
        assert not v3_2.matches_xs_g_year("01")

    def test_unexpected_month(self) -> None:
        assert not v3_2.matches_xs_g_year("2001-12")


class Test_matches_xs_g_year_month(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_g_year_month("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_g_year_month("some free form text")

    # NOTE (mristin):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-gyearmonth

    def test_valid_values(self) -> None:
        for text in [
            "2001-10",
            "2001-10+02:00",
            "2001-10Z",
            "2001-10+00:00",
            "-2001-10",
            "-20000-04",
        ]:
            self.assertTrue(v3_2.matches_xs_g_year_month(text), text)

    def test_missing_month(self) -> None:
        assert not v3_2.matches_xs_g_year_month("2001")

    def test_month_out_of_range(self) -> None:
        assert not v3_2.matches_xs_g_year_month("2001-13")

    def test_missing_century(self) -> None:
        assert not v3_2.matches_xs_g_year_month("01-13")


class Test_matches_xs_hex_binary(unittest.TestCase):
    def test_empty(self) -> None:
        assert v3_2.matches_xs_hex_binary("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_hex_binary("some free form text")

    # NOTE (mristin):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-hexbinary

    def test_valid_values(self) -> None:
        for text in [
            "11",
            "12",
            "1234",
            "3c3f786d6c2076657273696f6e3d22312e302220656e636f64696e67",
        ]:
            self.assertTrue(v3_2.matches_xs_hex_binary(text), text)

    def test_odd_number_of_digits(self) -> None:
        assert not v3_2.matches_xs_hex_binary("1")
        assert not v3_2.matches_xs_hex_binary("123")


class Test_matches_xs_time(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_time("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_time("some free form text")

    # NOTE (mristin):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-time

    def test_valid_values(self) -> None:
        for text in [
            "21:32:52",
            "21:32:52+02:00",
            "19:32:52Z",
            "19:32:52+00:00",
            "21:32:52.12679",
        ]:
            self.assertTrue(v3_2.matches_xs_time(text), text)

    def test_missing_seconds(self) -> None:
        assert not v3_2.matches_xs_time("21:32")

    def test_hour_out_of_range(self) -> None:
        assert not v3_2.matches_xs_time("25:25:10")

    def test_minute_out_of_range(self) -> None:
        assert not v3_2.matches_xs_time("01:61:10")

    def test_second_out_of_range(self) -> None:
        assert not v3_2.matches_xs_time("01:02:61")

    def test_negative(self) -> None:
        assert not v3_2.matches_xs_time("-10:00:00")

    def test_missing_padded_zeros(self) -> None:
        assert not v3_2.matches_xs_time("1:20:10")


class Test_matches_xs_integer(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_integer("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_integer("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "-1", "+1"]:
            self.assertTrue(v3_2.matches_xs_integer(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_integer("1.2")


class Test_matches_xs_long(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_long("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_long("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "-1", "+1"]:
            self.assertTrue(v3_2.matches_xs_long(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_long("1.2")


class Test_matches_xs_int(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_int("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_int("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "-1", "+1"]:
            self.assertTrue(v3_2.matches_xs_int(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_int("1.2")


class Test_matches_xs_short(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_short("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_short("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "-1", "+1"]:
            self.assertTrue(v3_2.matches_xs_short(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_short("1.2")


class Test_matches_xs_byte(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_byte("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_byte("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "-1", "+1"]:
            self.assertTrue(v3_2.matches_xs_byte(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_byte("1.2")


class Test_matches_xs_non_negative_integer(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_non_negative_integer("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_non_negative_integer("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-0", "1", "001", "+1", "+001"]:
            self.assertTrue(v3_2.matches_xs_non_negative_integer(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_non_negative_integer("1.2")

    def test_negative(self) -> None:
        assert not v3_2.matches_xs_non_negative_integer("-1")


class Test_matches_xs_positive_integer(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_positive_integer("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_positive_integer("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "+1", "+001", "100"]:
            self.assertTrue(v3_2.matches_xs_positive_integer(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_positive_integer("1.2")

    def test_negative(self) -> None:
        assert not v3_2.matches_xs_positive_integer("-1")

    def test_zero(self) -> None:
        assert not v3_2.matches_xs_positive_integer("0")


class Test_matches_xs_unsigned_long(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_unsigned_long("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_unsigned_long("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-0", "1", "001", "+1", "+001"]:
            self.assertTrue(v3_2.matches_xs_unsigned_long(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_unsigned_long("1.2")

    def test_negative(self) -> None:
        assert not v3_2.matches_xs_unsigned_long("-1")


class Test_matches_xs_unsigned_int(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_unsigned_int("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_unsigned_int("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-0", "1", "001", "+1", "+001"]:
            self.assertTrue(v3_2.matches_xs_unsigned_int(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_unsigned_int("1.2")

    def test_negative(self) -> None:
        assert not v3_2.matches_xs_unsigned_int("-1")


class Test_matches_xs_unsigned_short(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_unsigned_short("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_unsigned_short("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-0", "1", "001", "+1", "+001"]:
            self.assertTrue(v3_2.matches_xs_unsigned_short(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_unsigned_short("1.2")

    def test_negative(self) -> None:
        assert not v3_2.matches_xs_unsigned_short("-1")


class Test_matches_xs_unsigned_byte(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_unsigned_byte("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_unsigned_byte("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-0", "1", "001", "+1", "+001"]:
            self.assertTrue(v3_2.matches_xs_unsigned_byte(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_unsigned_byte("1.2")

    def test_negative(self) -> None:
        assert not v3_2.matches_xs_unsigned_byte("-1")


class Test_matches_xs_non_positive_integer(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_non_positive_integer("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_non_positive_integer("some free form text")

    def test_valid_values(self) -> None:
        for text in ["+0", "0", "-1", "-001"]:
            self.assertTrue(v3_2.matches_xs_non_positive_integer(text), text)

    def test_zero_prefixed_with_zeros(self) -> None:
        assert not v3_2.matches_xs_non_positive_integer("000")

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_non_positive_integer("1.2")

    def test_positive(self) -> None:
        assert not v3_2.matches_xs_non_positive_integer("1")
        assert not v3_2.matches_xs_non_positive_integer("+1")


class Test_matches_xs_negative_integer(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3_2.matches_xs_negative_integer("")

    def test_free_form_text(self) -> None:
        assert not v3_2.matches_xs_negative_integer("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-1", "-001", "-100"]:
            self.assertTrue(v3_2.matches_xs_negative_integer(text), text)

    def test_decimal(self) -> None:
        assert not v3_2.matches_xs_negative_integer("-1.2")

    def test_zero(self) -> None:
        assert not v3_2.matches_xs_negative_integer("0")
        assert not v3_2.matches_xs_negative_integer("+0")
        assert not v3_2.matches_xs_negative_integer("-0")

    def test_positive(self) -> None:
        assert not v3_2.matches_xs_negative_integer("1")
        assert not v3_2.matches_xs_negative_integer("+1")


class Test_matches_xs_string(unittest.TestCase):
    def test_empty(self) -> None:
        assert v3_2.matches_xs_string("")

    def test_free_form_text(self) -> None:
        assert v3_2.matches_xs_string("some free & <free> \u1984 form text")

    def test_fffe(self) -> None:
        assert not v3_2.matches_xs_string("\ufffe")

    def test_ffff(self) -> None:
        assert not v3_2.matches_xs_string("\uffff")

    # noinspection SpellCheckingInspection
    def test_surrogate_characters(self) -> None:
        assert not v3_2.matches_xs_string("\ud800")
        assert not v3_2.matches_xs_string("\udfff")

    def test_nul(self) -> None:
        assert not v3_2.matches_xs_string("\x00")


class Test_v3_2_runtime_behavior(unittest.TestCase):
    @staticmethod
    def _make_template_qualifier() -> v3_2.Qualifier:
        return v3_2.Qualifier(
            type=v3_2.Qualifier_type("qualifier1"),
            value_type=v3_2.Data_type_def_XSD.String,
            kind=v3_2.Qualifier_kind.Template_qualifier,
        )

    @staticmethod
    def _make_property(
        id_short: str, qualifiers: Optional[List[v3_2.Qualifier]] = None
    ) -> v3_2.Property:
        return v3_2.Property(
            value_type=v3_2.Data_type_def_XSD.String,
            ID_short=v3_2.ID_short_type(id_short),
            qualifiers=qualifiers,
        )

    @staticmethod
    def _make_collection(
        id_short: str, value: Optional[List[v3_2.Submodel_element]]
    ) -> v3_2.Submodel_element_collection:
        return v3_2.Submodel_element_collection(
            ID_short=v3_2.ID_short_type(id_short),
            value=value,
        )

    @staticmethod
    def _make_list(
        id_short: str, value: Optional[List[v3_2.Submodel_element]]
    ) -> v3_2.Submodel_element_list:
        return v3_2.Submodel_element_list(
            type_value_list_element=v3_2.AAS_submodel_elements.Submodel_element_collection,
            ID_short=v3_2.ID_short_type(id_short),
            value=value,
        )

    @staticmethod
    def _make_entity(
        id_short: str, statements: List[v3_2.Submodel_element]
    ) -> v3_2.Entity:
        return v3_2.Entity(
            ID_short=v3_2.ID_short_type(id_short),
            statements=statements,
        )

    @staticmethod
    def _make_annotated_relationship(
        id_short: str, annotations: List[v3_2.Data_element]
    ) -> v3_2.Annotated_relationship_element:
        return v3_2.Annotated_relationship_element(
            ID_short=v3_2.ID_short_type(id_short),
            annotations=annotations,
        )

    @mock.patch.object(v3_2, "submodel_element_is_of_type", return_value=True)
    def test_template_submodel_accepts_nested_singleton_lists(
        self, _mocked: mock.MagicMock
    ) -> None:
        prop = self._make_property("p1")
        inner_collection = self._make_collection("c1", [prop])
        inner_list = self._make_list("l2", [inner_collection])
        outer_collection = self._make_collection("c2", [inner_list])
        top_list = self._make_list("l1", [outer_collection])

        v3_2.Submodel(
            ID=v3_2.Identifier("submodel-1"),
            ID_short=v3_2.ID_short_type("sm1"),
            kind=v3_2.Modelling_kind.Template,
            submodel_elements=[top_list],
        )

    @mock.patch.object(v3_2, "submodel_element_is_of_type", return_value=True)
    def test_template_submodel_rejects_list_with_two_elements(
        self, _mocked: mock.MagicMock
    ) -> None:
        col1 = self._make_collection("c1", [self._make_property("p1")])
        col2 = self._make_collection("c2", [self._make_property("p2")])
        bad_list = self._make_list("l1", [col1, col2])

        with self.assertRaises(icontract.ViolationError):
            v3_2.Submodel(
                ID=v3_2.Identifier("submodel-2"),
                ID_short=v3_2.ID_short_type("sm2"),
                kind=v3_2.Modelling_kind.Template,
                submodel_elements=[bad_list],
            )

    @mock.patch.object(v3_2, "submodel_element_is_of_type", return_value=True)
    def test_template_submodel_rejects_list_without_value(
        self, _mocked: mock.MagicMock
    ) -> None:
        bad_list = self._make_list("l1", None)

        with self.assertRaises(icontract.ViolationError):
            v3_2.Submodel(
                ID=v3_2.Identifier("submodel-3"),
                ID_short=v3_2.ID_short_type("sm3"),
                kind=v3_2.Modelling_kind.Template,
                submodel_elements=[bad_list],
            )

    @mock.patch.object(v3_2, "submodel_element_is_of_type", return_value=True)
    def test_operation_rejects_variable_list_with_two_elements(
        self, _mocked: mock.MagicMock
    ) -> None:
        col1 = self._make_collection("c1", [self._make_property("p1")])
        col2 = self._make_collection("c2", [self._make_property("p2")])
        bad_list = self._make_list("l1", [col1, col2])

        with self.assertRaises(icontract.ViolationError):
            v3_2.Operation(
                ID_short=v3_2.ID_short_type("op1"),
                input_variables=[v3_2.Operation_variable(value=bad_list)],
            )

    @mock.patch.object(v3_2, "submodel_element_is_of_type", return_value=True)
    def test_operation_rejects_variable_list_without_value(
        self, _mocked: mock.MagicMock
    ) -> None:
        bad_list = self._make_list("l1", None)

        with self.assertRaises(icontract.ViolationError):
            v3_2.Operation(
                ID_short=v3_2.ID_short_type("op3"),
                input_variables=[v3_2.Operation_variable(value=bad_list)],
            )

    @mock.patch.object(v3_2, "submodel_element_is_of_type", return_value=True)
    def test_operation_accepts_nested_singleton_list_variable(
        self, _mocked: mock.MagicMock
    ) -> None:
        prop = self._make_property("p1")
        inner_collection = self._make_collection("c1", [prop])
        inner_list = self._make_list("l2", [inner_collection])
        outer_collection = self._make_collection("c2", [inner_list])
        top_list = self._make_list("l1", [outer_collection])

        v3_2.Operation(
            ID_short=v3_2.ID_short_type("op2"),
            input_variables=[v3_2.Operation_variable(value=top_list)],
        )

    @mock.patch.object(v3_2, "submodel_element_is_of_type", return_value=True)
    def test_template_submodel_rejects_list_with_two_elements_in_entity(
        self, _mocked: mock.MagicMock
    ) -> None:
        col1 = self._make_collection("c1", [self._make_property("p1")])
        col2 = self._make_collection("c2", [self._make_property("p2")])
        bad_list = self._make_list("l1", [col1, col2])
        entity = self._make_entity("e1", [bad_list])

        with self.assertRaises(icontract.ViolationError):
            v3_2.Submodel(
                ID=v3_2.Identifier("submodel-5"),
                ID_short=v3_2.ID_short_type("sm5"),
                kind=v3_2.Modelling_kind.Template,
                submodel_elements=[entity],
            )

    def test_asset_information_rejects_reserved_specific_asset_id_case_insensitive(
        self,
    ) -> None:
        with self.assertRaises(icontract.ViolationError):
            v3_2.Asset_information(
                asset_kind=v3_2.Asset_kind.Instance,
                global_asset_ID=v3_2.Identifier("asset-1"),
                specific_asset_IDs=[
                    v3_2.Specific_asset_ID(
                        name=v3_2.Label_type("globalassetid"),
                        value=v3_2.Identifier("asset-2"),
                    )
                ],
            )

    def test_asset_information_accepts_reserved_specific_asset_id_if_value_matches(
        self,
    ) -> None:
        v3_2.Asset_information(
            asset_kind=v3_2.Asset_kind.Instance,
            global_asset_ID=v3_2.Identifier("asset-1"),
            specific_asset_IDs=[
                v3_2.Specific_asset_ID(
                    name=v3_2.Label_type("GLOBALASSETID"),
                    value=v3_2.Identifier("asset-1"),
                )
            ],
        )

    def test_asset_information_allows_non_ascii_lookalike_specific_asset_id_name(
        self,
    ) -> None:
        v3_2.Asset_information(
            asset_kind=v3_2.Asset_kind.Instance,
            global_asset_ID=v3_2.Identifier("asset-1"),
            specific_asset_IDs=[
                v3_2.Specific_asset_ID(
                    name=v3_2.Label_type("globalAsset\u0130d"),
                    value=v3_2.Identifier("asset-2"),
                )
            ],
        )

    def test_instance_submodel_rejects_nested_template_qualifier(self) -> None:
        prop = self._make_property("p1", qualifiers=[self._make_template_qualifier()])
        collection = self._make_collection("c1", [prop])

        with self.assertRaises(icontract.ViolationError):
            v3_2.Submodel(
                ID=v3_2.Identifier("submodel-4"),
                ID_short=v3_2.ID_short_type("sm4"),
                submodel_elements=[collection],
            )

    def test_instance_submodel_rejects_template_qualifier_in_entity_statement(
        self,
    ) -> None:
        prop = self._make_property("p1", qualifiers=[self._make_template_qualifier()])
        entity = self._make_entity("e1", [prop])

        with self.assertRaises(icontract.ViolationError):
            v3_2.Submodel(
                ID=v3_2.Identifier("submodel-6"),
                ID_short=v3_2.ID_short_type("sm6"),
                submodel_elements=[entity],
            )

    def test_instance_submodel_rejects_template_qualifier_in_annotation(
        self,
    ) -> None:
        prop = self._make_property("p1", qualifiers=[self._make_template_qualifier()])
        annotated_relationship = self._make_annotated_relationship("rel1", [prop])

        with self.assertRaises(icontract.ViolationError):
            v3_2.Submodel(
                ID=v3_2.Identifier("submodel-7"),
                ID_short=v3_2.ID_short_type("sm7"),
                submodel_elements=[annotated_relationship],
            )

    def test_operation_variable_allows_template_qualifier_exception(self) -> None:
        prop = self._make_property("p1", qualifiers=[self._make_template_qualifier()])

        v3_2.Operation(
            ID_short=v3_2.ID_short_type("op4"),
            input_variables=[v3_2.Operation_variable(value=prop)],
        )

    def test_external_reference_rejects_aas_referable_in_inner_key(self) -> None:
        with self.assertRaises(icontract.ViolationError):
            v3_2.Reference(
                type=v3_2.Reference_types.External_reference,
                keys=[
                    v3_2.Key(
                        type=v3_2.Key_types.Global_reference,
                        value=v3_2.Identifier("urn:source"),
                    ),
                    v3_2.Key(
                        type=v3_2.Key_types.Property,
                        value=v3_2.Identifier("property1"),
                    ),
                    v3_2.Key(
                        type=v3_2.Key_types.Fragment_reference,
                        value=v3_2.Identifier("fragment1"),
                    ),
                ],
            )

    def test_external_reference_accepts_generic_global_and_fragment_keys(self) -> None:
        v3_2.Reference(
            type=v3_2.Reference_types.External_reference,
            keys=[
                v3_2.Key(
                    type=v3_2.Key_types.Global_reference,
                    value=v3_2.Identifier("urn:source"),
                ),
                v3_2.Key(
                    type=v3_2.Key_types.Fragment_reference,
                    value=v3_2.Identifier("fragment1"),
                ),
            ],
        )

    @mock.patch.object(v3_2, "is_xs_date_time_UTC", return_value=True)
    def test_administrative_information_sets_created_and_updated_at(
        self, _mocked: mock.MagicMock
    ) -> None:
        created_at = v3_2.Date_time_UTC("2022-04-01T01:02:03Z")
        updated_at = v3_2.Date_time_UTC("2022-04-02T01:02:03Z")

        administration = v3_2.Administrative_information(
            created_at=created_at, updated_at=updated_at
        )

        assert administration.created_at == created_at
        assert administration.updated_at == updated_at


_META_MODEL: tests.common.MetaModel = tests.common.load_meta_model(
    pathlib.Path(v3_2.__file__)
)


class Test_assertions(unittest.TestCase):
    # NOTE (mristin):
    # We do not state "ID" as an abbreviation (which might imply "Identity Document"),
    # but rather expect "Id" or "id", short for "identifier".
    #
    # See: https://english.stackexchange.com/questions/101248/how-should-the-abbreviation-for-identifier-be-capitalized
    LOWER_TO_ABBREVIATION = {
        "aas": "AAS",
        "bcp": "BCP",
        "did": "DID",
        "din": "DIN",
        "ece": "ECE",
        "html": "HTML",
        "id": "ID",
        "ids": "IDs",
        "iec": "IEC",
        "irdi": "IRDI",
        "iri": "IRI",
        "mime": "MIME",
        "nist": "NIST",
        "rfc": "RFC",
        "si": "SI",
        "tlsa": "TLSA",
        "uri": "URI",
        "url": "URL",
        "utc": "UTC",
        "w3c": "W3C",
        "xml": "XML",
        "xsd": "XSD",
    }

    ABBREVIATIONS = set(LOWER_TO_ABBREVIATION.values())

    @staticmethod
    def check_class_name(name: aas_core_codegen.common.Identifier) -> List[str]:
        errors = []  # type: List[str]

        parts = name.split("_")  # type: List[str]

        if parts[0] not in Test_assertions.ABBREVIATIONS:
            if parts[0] != parts[0].capitalize():
                errors.append(
                    f"Expected first part of a class name "
                    f"to be capitalized ({parts[0].capitalize()!r}), "
                    f"but it was not ({parts[0]!r}) for class {name!r}"
                )

        for part in parts:
            expected_part = Test_assertions.LOWER_TO_ABBREVIATION.get(
                part.lower(), None
            )

            if expected_part is not None and part != expected_part:
                errors.append(
                    f"Expected a part of a class name "
                    f"to be {expected_part!r} "
                    f"since it denotes an abbreviation, "
                    f"but got {part!r} for the class {name!r}"
                )

        for part in parts[1:]:
            if part not in Test_assertions.ABBREVIATIONS:
                if part.lower() != part:
                    errors.append(
                        f"Expected a non-first part of a class name "
                        f"to be lower-case ({part.lower()}) "
                        f"since it was not registered as an abbreviation, "
                        f"but it was not ({part!r}) "
                        f"for class {name!r}"
                    )

        return errors

    @staticmethod
    def check_enum_literal_name(name: aas_core_codegen.common.Identifier) -> List[str]:
        errors = []  # type: List[str]

        parts = name.split("_")  # type: List[str]

        if parts[0] not in Test_assertions.ABBREVIATIONS:
            if parts[0] != parts[0].capitalize():
                errors.append(
                    f"Expected first part of an enumeration literal name "
                    f"to be capitalized ({parts[0].capitalize()!r}), "
                    f"but it was not ({parts[0]!r}) for enumeration literal {name!r}"
                )

        for part in parts:
            expected_part = Test_assertions.LOWER_TO_ABBREVIATION.get(
                part.lower(), None
            )

            if expected_part is not None and part != expected_part:
                errors.append(
                    f"Expected a part of an enumeration literal name "
                    f"to be {expected_part!r} since it denotes an abbreviation, "
                    f"but got {part!r} for enumeration literal {name!r}"
                )

        for part in parts[1:]:
            if part not in Test_assertions.ABBREVIATIONS:
                if part.lower() != part:
                    errors.append(
                        f"Expected a non-first part of an enumeration literal name "
                        f"to be lower-case ({part.lower()}) "
                        f"since it was not registered as an abbreviation, "
                        f"but it was not ({part!r}) "
                        f"for enumeration literal {name!r}"
                    )

        return errors

    @staticmethod
    def check_property_name(name: aas_core_codegen.common.Identifier) -> List[str]:
        errors = []  # type: List[str]

        parts = name.split("_")  # type: List[str]

        for part in parts:
            expected_part = Test_assertions.LOWER_TO_ABBREVIATION.get(
                part.lower(), None
            )

            if expected_part is not None and part != expected_part:
                errors.append(
                    f"Expected a part of a property name "
                    f"to be {expected_part!r} "
                    f"since it denotes an abbreviation, "
                    f"but got {part!r} for the property {name!r}"
                )

        for part in parts:
            if part not in Test_assertions.ABBREVIATIONS:
                if part.lower() != part:
                    errors.append(
                        f"Expected a part of a property name "
                        f"to be lower-case ({part.lower()}) "
                        f"since it was not registered as an abbreviation, "
                        f"but it was not ({part!r}) "
                        f"for the property {name!r}"
                    )

        return errors

    @staticmethod
    def check_method_name(name: aas_core_codegen.common.Identifier) -> List[str]:
        errors = []  # type: List[str]

        parts = name.split("_")  # type: List[str]

        for part in parts:
            expected_part = Test_assertions.LOWER_TO_ABBREVIATION.get(
                part.lower(), None
            )

            if expected_part is not None and part != expected_part:
                errors.append(
                    f"Expected a part of a method name "
                    f"to be {expected_part!r} "
                    f"since it denotes an abbreviation, "
                    f"but got {part!r} for the method {name!r}"
                )

        for part in parts:
            if part not in Test_assertions.ABBREVIATIONS:
                if part.lower() != part:
                    errors.append(
                        f"Expected a part of a method name "
                        f"to be lower-case ({part.lower()}) "
                        f"since it was not registered as an abbreviation, "
                        f"but it was not ({part!r}) "
                        f"for the method {name!r}"
                    )

        return errors

    @staticmethod
    def check_function_name(name: aas_core_codegen.common.Identifier) -> List[str]:
        errors = []  # type: List[str]

        parts = name.split("_")  # type: List[str]

        for part in parts:
            expected_part = Test_assertions.LOWER_TO_ABBREVIATION.get(
                part.lower(), None
            )

            if expected_part is not None and part != expected_part:
                errors.append(
                    f"Expected a part of a function name "
                    f"to be {expected_part!r} "
                    f"since it denotes an abbreviation, "
                    f"but got {part!r} for the function {name!r}"
                )

        for part in parts:
            if part not in Test_assertions.ABBREVIATIONS:
                if part.lower() != part:
                    errors.append(
                        f"Expected a part of a function name "
                        f"to be lower-case ({part.lower()}) "
                        f"since it was not registered as an abbreviation, "
                        f"but it was not ({part!r}) "
                        f"for the function {name!r}"
                    )

        return errors

    @staticmethod
    def needs_plural(type_annotation: intermediate.TypeAnnotationUnion) -> bool:
        lang_string_cls = _META_MODEL.symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Abstract_lang_string")
        )

        type_anno = intermediate.beneath_optional(type_annotation)

        return isinstance(type_anno, intermediate.ListTypeAnnotation) and not (
            isinstance(type_anno.items, intermediate.OurTypeAnnotation)
            and type_anno.items.our_type.is_subclass_of(lang_string_cls)
        )

    def test_naming(self) -> None:
        errors = []  # type: List[str]

        hard_wired_plural_exceptions = {
            "Concept_description.is_case_of",
            "Submodel_element_collection.value",
            "Submodel_element_list.value",
            "Extension.refers_to",
        }

        symbol_table = _META_MODEL.symbol_table

        for our_type in symbol_table.our_types:
            errors.extend(Test_assertions.check_class_name(name=our_type.name))

            # We descend and check literals, properties *etc.*

            if isinstance(our_type, intermediate.Enumeration):
                for literal in our_type.literals:
                    errors.extend(
                        Test_assertions.check_enum_literal_name(name=literal.name)
                    )

            elif isinstance(our_type, intermediate.ConstrainedPrimitive):
                # NOTE (mristin):
                # There are no names to be checked beneath the constrained primitive.
                pass

            elif isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                for prop in our_type.properties:
                    errors.extend(Test_assertions.check_property_name(prop.name))

                    qualified_name = f"{our_type.name}.{prop.name}"

                    if (
                        Test_assertions.needs_plural(prop.type_annotation)
                        and qualified_name not in hard_wired_plural_exceptions
                        and not prop.name.endswith("s")
                    ):
                        errors.append(
                            f"Expected the property to have a suffix '-s', "
                            f"but it does not: {qualified_name}"
                        )

                for method in our_type.methods:
                    errors.extend(Test_assertions.check_method_name(method.name))

            else:
                aas_core_codegen.common.assert_never(our_type)

        for func in symbol_table.verification_functions:
            errors.extend(Test_assertions.check_function_name(func.name))

        if len(errors) != 0:
            raise AssertionError("\n".join(f"* {error}" for error in errors))

    def test_AAS_identifiables_correspond_to_classes(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        identifiable_cls = symbol_table.must_find_abstract_class(
            aas_core_codegen.common.Identifier("Identifiable")
        )

        aas_identifiables_set = symbol_table.constants_by_name.get(
            aas_core_codegen.common.Identifier("AAS_identifiables"), None
        )
        assert isinstance(
            aas_identifiables_set, intermediate.ConstantSetOfEnumerationLiterals
        )

        tests.common.assert_subclasses_correspond_to_enumeration_literals(
            symbol_table=symbol_table,
            cls=identifiable_cls,
            enumeration_or_set=aas_identifiables_set,
        )

    def test_AAS_submodel_elements_as_keys_corresponds_to_classes(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        submodel_element_cls = symbol_table.must_find_abstract_class(
            aas_core_codegen.common.Identifier("Submodel_element")
        )

        aas_submodel_elements_as_keys_set = symbol_table.constants_by_name.get(
            aas_core_codegen.common.Identifier("AAS_submodel_elements_as_keys"), None
        )

        assert isinstance(
            aas_submodel_elements_as_keys_set,
            intermediate.ConstantSetOfEnumerationLiterals,
        )

        tests.common.assert_subclasses_correspond_to_enumeration_literals(
            symbol_table=symbol_table,
            cls=submodel_element_cls,
            enumeration_or_set=aas_submodel_elements_as_keys_set,
        )

    def test_referable_non_identifiables_correspond_to_classes(self) -> None:
        errors = []  # type: List[str]

        symbol_table = _META_MODEL.symbol_table

        class_name_set = set()  # type: Set[aas_core_codegen.common.Identifier]

        identifiable_cls = symbol_table.must_find_abstract_class(
            aas_core_codegen.common.Identifier("Identifiable")
        )

        referable_cls = symbol_table.must_find_abstract_class(
            aas_core_codegen.common.Identifier("Referable")
        )

        for our_type in symbol_table.our_types:
            if not isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                continue

            if our_type in (referable_cls, identifiable_cls):
                continue

            if our_type.is_subclass_of(referable_cls) and not our_type.is_subclass_of(
                identifiable_cls
            ):
                class_name_set.add(our_type.name)

        aas_referable_non_identifiables_set = symbol_table.constants_by_name.get(
            aas_core_codegen.common.Identifier("AAS_referable_non_identifiables"), None
        )

        assert isinstance(
            aas_referable_non_identifiables_set,
            intermediate.ConstantSetOfEnumerationLiterals,
        )

        literal_set = {
            literal.name for literal in aas_referable_non_identifiables_set.literals
        }

        if class_name_set != literal_set:
            # pylint: disable=line-too-long
            errors.append(f"""\
The sub-classes of {referable_cls.name} which are not {identifiable_cls.name} do not correspond to {aas_referable_non_identifiables_set.name}.

Observed classes:  {sorted(class_name_set)!r}
Observed literals: {sorted(literal_set)!r}""")

        if len(errors) != 0:
            raise AssertionError("\n".join(f"* {error}" for error in errors))

    def test_AAS_referables_correspond_to_classes(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        referable_cls = symbol_table.must_find_abstract_class(
            aas_core_codegen.common.Identifier("Referable")
        )

        aas_submodel_elements_as_keys_set = symbol_table.constants_by_name.get(
            aas_core_codegen.common.Identifier("AAS_referables"), None
        )

        assert isinstance(
            aas_submodel_elements_as_keys_set,
            intermediate.ConstantSetOfEnumerationLiterals,
        )

        tests.common.assert_subclasses_correspond_to_enumeration_literals(
            symbol_table=symbol_table,
            cls=referable_cls,
            enumeration_or_set=aas_submodel_elements_as_keys_set,
        )

    def test_AAS_submodel_elements_corresponds_to_classes(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        submodel_element_cls = symbol_table.must_find_abstract_class(
            aas_core_codegen.common.Identifier("Submodel_element")
        )

        aas_submodel_elements_enum = symbol_table.must_find_enumeration(
            aas_core_codegen.common.Identifier("AAS_submodel_elements")
        )

        tests.common.assert_subclasses_correspond_to_enumeration_literals(
            symbol_table=symbol_table,
            cls=submodel_element_cls,
            enumeration_or_set=aas_submodel_elements_enum,
        )

    def test_administrative_information_has_created_and_updated_at(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        administrative_information_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Administrative_information")
        )

        assert (
            aas_core_codegen.common.Identifier("created_at")
            in administrative_information_cls.properties_by_name
        )
        assert (
            aas_core_codegen.common.Identifier("updated_at")
            in administrative_information_cls.properties_by_name
        )

        for prop_name in ("created_at", "updated_at"):
            prop = administrative_information_cls.properties_by_name[
                aas_core_codegen.common.Identifier(prop_name)
            ]

            assert isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)
            type_anno = intermediate.beneath_optional(prop.type_annotation)
            assert isinstance(type_anno, intermediate.OurTypeAnnotation)
            assert type_anno.our_type.name == aas_core_codegen.common.Identifier(
                "Date_time_UTC"
            )

    def test_asset_kind_includes_batch(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        asset_kind_enum = symbol_table.must_find_enumeration(
            aas_core_codegen.common.Identifier("Asset_kind")
        )

        literal_names = {literal.name for literal in asset_kind_enum.literals}
        assert aas_core_codegen.common.Identifier("Batch") in literal_names

    def test_constraint_137_on_reference(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        reference_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Reference")
        )

        expected_condition_str = """\
(
    not (self.type == Reference_types.External_reference)
    or (
        all(
            not (key.type in AAS_referables)
            for key in self.keys
        )
    )
)"""

        expected_description = (
            "Constraint AASd-137: For external references, i.e. References with "
            "Reference/type = ExternalReference, the value of Key/type of any key in "
            "Reference/keys shall not be one of AAS referables."
        )

        assert tests.common.has_invariant(
            expected_condition=tests.common.parse_condition(expected_condition_str),
            expected_description=expected_description,
            invariants=reference_cls.invariants,
        )

    def test_constraint_138_on_submodel(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        submodel_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Submodel")
        )

        expected_condition_str = """\
(
    not (
        self.kind_or_default() == Modelling_kind.Template
    )
    or (
        self.submodel_elements is not None
        and submodel_element_lists_in_submodel_elements_have_exactly_one_element(
            self.submodel_elements
        )
    )
)"""

        expected_description = (
            "Constraint AASd-138: A submodel element list within a submodel of kind "
            "Template or as part of an operation variable shall have exactly one "
            "element."
        )

        assert tests.common.has_invariant(
            expected_condition=tests.common.parse_condition(expected_condition_str),
            expected_description=expected_description,
            invariants=submodel_cls.invariants,
        )

    def test_constraint_138_on_operation(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        operation_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Operation")
        )

        expected_condition_str = """\
(
    submodel_element_lists_in_operation_variables_have_exactly_one_element(
        self.input_variables,
        self.output_variables,
        self.inoutput_variables,
    )
)"""

        expected_description = (
            "Constraint AASd-138: A submodel element list within a submodel of kind "
            "Template or as part of an operation variable shall have exactly one "
            "element."
        )

        assert tests.common.has_invariant(
            expected_condition=tests.common.parse_condition(expected_condition_str),
            expected_description=expected_description,
            invariants=operation_cls.invariants,
        )

    def test_constraint_119_in_all_qualifiable_with_has_kind(self) -> None:
        renegade_classes = []  # type: List[str]

        expected_condition_str = """\
(
    not (self.qualifiers is not None)
    or (
        not any(
            qualifier.kind_or_default() == Qualifier_kind.Template_qualifier
            for qualifier in self.qualifiers
        ) or (
            self.kind_or_default() == Modelling_kind.Template
        )
    )
)"""

        expected_condition = tests.common.parse_condition(expected_condition_str)

        expected_description = (
            "Constraint AASd-119: If any qualifier kind value of "
            "a qualifiable qualifier is equal to template qualifier and "
            "the qualified element has kind then the qualified element "
            "shall be of kind template."
        )

        symbol_table = _META_MODEL.symbol_table

        qualifiable_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Qualifiable")
        )

        has_kind_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Has_kind")
        )

        for our_type in symbol_table.our_types:
            if not isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                continue

            if our_type.is_subclass_of(qualifiable_cls) and our_type.is_subclass_of(
                has_kind_cls
            ):
                if not tests.common.has_invariant(
                    expected_condition=expected_condition,
                    expected_description=expected_description,
                    invariants=our_type.invariants,
                ):
                    renegade_classes.append(our_type.name)
                    continue

        if len(renegade_classes) > 0:
            raise AssertionError(
                f"The invariant corresponding to Constraint AASd-119 is "
                f"expected in the class(es):\n{renegade_classes!r}\n"
                f"which inherit both from {has_kind_cls.name} and {qualifiable_cls.name}, "
                f"but it could not be found.\n"
                f"\n"
                f"Expected condition of the invariant was:\n"
                f"{expected_condition_str}\n\n"
                f"Expected description was:\n"
                f"{expected_description}"
            )

    def test_all_lists_have_min_length_at_least_one(self) -> None:
        tests.common.assert_all_lists_have_min_length_at_least_one(
            symbol_table=_META_MODEL.symbol_table,
            constraints_by_class=_META_MODEL.constraints_by_class,
        )

    def test_that_all_list_of_lang_strings_are_lang_string_sets(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        abstract_lang_string_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Abstract_lang_string")
        )

        # List of (property reference, error message)
        errors = []  # type: List[Tuple[str, str]]

        for our_type in symbol_table.our_types:
            if not isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                continue

            lang_string_set_props_with_uniqueness_invariant = (
                set()
            )  # type: Set[aas_core_codegen.common.Identifier]

            for invariant in our_type.invariants:
                node = invariant.body
                expected_prop_name: Optional[aas_core_codegen.common.Identifier] = None

                conditional_on_prop = infer_for_schema_match.try_conditional_on_prop(
                    invariant.body
                )
                if conditional_on_prop is not None:
                    node = conditional_on_prop.consequent
                    expected_prop_name = conditional_on_prop.prop_name

                single_arg_function_on_member_or_name = (
                    infer_for_schema_match.try_single_arg_function_on_member_or_name(
                        node
                    )
                )
                if single_arg_function_on_member_or_name is None:
                    continue

                if single_arg_function_on_member_or_name.function_name != (
                    "lang_strings_have_unique_languages"
                ):
                    continue

                prop_name = infer_for_schema_match.try_property(
                    single_arg_function_on_member_or_name.member_or_name
                )
                if prop_name is None:
                    continue

                if expected_prop_name is not None and prop_name != expected_prop_name:
                    errors.append(
                        (
                            f"{our_type.name}.{prop_name}",
                            f"Unexpected invariant conditioned "
                            f"on the property {expected_prop_name!r} while "
                            f"the function call refers to the property {prop_name!r}",
                        )
                    )
                    continue

                # fmt: off
                human_readable_prop_name = (
                    tests.common.human_readable_property_name_capitalized(
                        prop_name
                    )
                )
                # fmt: on

                expected_description = (
                    f"{human_readable_prop_name} must specify unique languages."
                )

                if invariant.description is None:
                    errors.append(
                        (
                            f"{our_type.name}.{prop_name}",
                            f"Expected the description of the invariant "
                            f"to be {expected_description!r}, but got none",
                        )
                    )
                elif invariant.description != expected_description:
                    errors.append(
                        (
                            f"{our_type.name}.{prop_name}",
                            f"Expected the description of the invariant "
                            f"to be {expected_description!r}, "
                            f"but got {invariant.description!r}",
                        )
                    )
                else:
                    # Everything's OK.
                    pass

                lang_string_set_props_with_uniqueness_invariant.add(prop_name)

            for prop in our_type.properties:
                type_anno = intermediate.beneath_optional(prop.type_annotation)
                if (
                    isinstance(type_anno, intermediate.ListTypeAnnotation)
                    and isinstance(type_anno.items, intermediate.OurTypeAnnotation)
                    and type_anno.items.our_type.is_subclass_of(
                        abstract_lang_string_cls
                    )
                ):
                    if prop.name not in lang_string_set_props_with_uniqueness_invariant:
                        errors.append(
                            (
                                f"{our_type.name}.{prop.name}",
                                f"The invariant of no duplicate languages could not "
                                f"be inferred from the invariants of {our_type.name!r}",
                            )
                        )

        if len(errors) != 0:
            joined_errors = "\n".join(
                f"* {prop_ref}: {message}" for prop_ref, message in errors
            )
            raise AssertionError(
                f"Expected to the invariants for sets of language strings, "
                f"but:\n"
                f"{joined_errors}"
            )

    def test_constraint_117_on_non_submodel_element(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        referable_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Referable")
        )

        identifiable_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Identifiable")
        )

        submodel_element_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Submodel_element")
        )

        errors = []  # type: List[str]

        for our_type in symbol_table.our_types_topologically_sorted:
            if not isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                continue

            # NOTE (mristin):
            # We can not assert that ID-short is non-None in ``Submodel_element`` as
            # the submodel elements can be in the value of ``Submodel_element_list``.
            if our_type.is_subclass_of(submodel_element_cls):
                continue

            # NOTE (mristin):
            # We can not assert that ID-short is non-None in this class as
            # ``Submodel_element`` inherits from it, and the submodel elements can be
            # in the value of ``Submodel_element_list``.
            if id(submodel_element_cls) in our_type.descendant_id_set:
                continue

            # NOTE (mristin):
            # Identifiables are not affected by Constraint-117 so their ID-shorts remain
            # optional.
            if our_type.is_subclass_of(identifiable_cls):
                continue

            # NOTE (mristin):
            # Constraint AASd-117 considers only the class ``Referable``.
            if not our_type.is_subclass_of(referable_cls):
                continue

            # NOTE (mristin):
            # We use type strengthening to implement 117.
            if Identifier("ID_short") not in our_type.properties_by_name:
                errors.append(
                    f"Expected the referable class {our_type.name!r} to define "
                    f"the property ID_short, but it does not. See Constraint AASd-117."
                )
                continue

            id_short_prop = our_type.properties_by_name[Identifier("ID_short")]
            if isinstance(
                id_short_prop.type_annotation, intermediate.OptionalTypeAnnotation
            ):
                errors.append(
                    f"Expected the referable class {our_type.name!r} to define "
                    f"the property ID_short as required, but it defines it "
                    f"as {id_short_prop.type_annotation}. See Constraint AASd-117."
                )
                continue

        if len(errors) > 0:
            errors_joined = "\n".join(tests.common.make_bullet_points(errors))
            raise AssertionError(f"One or more errors:\n{errors_joined}")

    def test_constraint_117_on_properties_of_type_class(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        submodel_element_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Submodel_element")
        )

        errors = []  # type: List[str]

        for our_type in symbol_table.our_types:
            if not isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                continue

            # Check the invariants for properties which are submodel elements
            for prop in our_type.properties:
                if prop.specified_for is not our_type:
                    continue

                type_anno = intermediate.beneath_optional(prop.type_annotation)

                if not isinstance(type_anno, intermediate.OurTypeAnnotation):
                    continue

                if not isinstance(
                    type_anno.our_type,
                    (intermediate.AbstractClass, intermediate.ConcreteClass),
                ):
                    continue

                # NOTE (mristin):
                # All Referable classes already have to define the constraint as
                # their invariant (see the previous test), so we do not have to check
                # their ID-shorts here.
                if not type_anno.our_type.is_subclass_of(submodel_element_cls):
                    continue

                if isinstance(
                    prop.type_annotation, intermediate.OptionalTypeAnnotation
                ):
                    expected_condition_str = f"""\
(
    not ({prop.name} is not None)
    or (self.{prop.name}.ID_short is not None
)"""
                else:
                    expected_condition_str = f"self.{prop.name}.ID_short is not None"

                expected_condition = tests.common.parse_condition(
                    expected_condition_str
                )

                # fmt: off
                prop_name_readable = (
                    tests.common.human_readable_property_name_capitalized(
                        prop.name
                    )
                )
                # fmt: on

                expected_description = (
                    f"{prop_name_readable} must have the ID-short specified according "
                    f"to Constraint AASd-117 (ID-short of non-identifiable Referables "
                    f"not being a direct child of a Submodel element list shall be "
                    f"specified)."
                )

                if not tests.common.has_invariant(
                    expected_condition=expected_condition,
                    expected_description=expected_description,
                    invariants=our_type.invariants,
                ):
                    errors.append(
                        f"The invariant corresponding to Constraint AASd-117 is "
                        f"expected in the class {our_type.name!r} "
                        f"for the property {prop.name!r} "
                        f"of type {prop.type_annotation}, "
                        f"but it could not be found.\n"
                        f"\n"
                        f"Expected condition of the invariant was:\n"
                        f"{expected_condition_str}\n\n"
                        f"Expected description was:\n"
                        f"{expected_description}"
                    )

        if len(errors) > 0:
            errors_joined = "\n".join(tests.common.make_bullet_points(errors))
            raise AssertionError(f"One or more errors:\n{errors_joined}")

    def test_constraint_117_on_properties_of_type_list(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        submodel_element_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Submodel_element")
        )

        submodel_element_list_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Submodel_element_list")
        )

        assert Identifier("value") in submodel_element_list_cls.properties_by_name

        errors = []  # type: List[str]

        # Check the invariants for properties which are lists of submodel elements
        for our_type in symbol_table.our_types:
            if not isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                continue

            for prop in our_type.properties:
                if prop.specified_for is not our_type:
                    continue

                # The property Submodel_element_list.property is the only property
                # where ID-short can be ``None``.
                if prop.name == "value" and our_type is submodel_element_list_cls:
                    continue

                type_anno = intermediate.beneath_optional(prop.type_annotation)

                if not isinstance(type_anno, intermediate.ListTypeAnnotation):
                    continue

                assert isinstance(
                    type_anno.items, intermediate.OurTypeAnnotation
                ) and isinstance(
                    type_anno.items.our_type,
                    (intermediate.AbstractClass, intermediate.ConcreteClass),
                ), (
                    f"Expected only lists of class instances, "
                    f"but got: {type_anno.items}"
                )

                # NOTE (mristin):
                # All Referable classes already have to define the constraint as
                # their invariant (see the test above), so we do not have to check
                # their ID-shorts here.
                if not type_anno.items.our_type.is_subclass_of(submodel_element_cls):
                    continue

                if isinstance(
                    prop.type_annotation, intermediate.OptionalTypeAnnotation
                ):
                    expected_condition_str = f"""\
(
    not (self.{prop.name} is not None)
    or all(
        item.ID_short is not None
        for item in self.{prop.name}
    )
)"""
                else:
                    expected_condition_str = (
                        f"all(item.ID_short is not None for item in self.{prop.name})"
                    )

                expected_condition = tests.common.parse_condition(
                    expected_condition_str
                )

                prop_name_readable = tests.common.human_readable_property_name(
                    prop.name
                )

                expected_description = (
                    f"ID-shorts need to be defined for all the items of "
                    f"{prop_name_readable} according to AASd-117 (ID-short of "
                    f"non-identifiable Referables not being a direct child of a "
                    f"Submodel element list shall be specified)."
                )

                if not tests.common.has_invariant(
                    expected_condition=expected_condition,
                    expected_description=expected_description,
                    invariants=our_type.invariants,
                ):
                    errors.append(
                        f"The invariant corresponding to Constraint AASd-117 is "
                        f"expected in the class {our_type.name!r} "
                        f"for the property {prop.name!r} "
                        f"of type {prop.type_annotation}, "
                        f"but it could not be found.\n"
                        f"\n"
                        f"Expected condition of the invariant was:\n"
                        f"{expected_condition_str}\n\n"
                        f"Expected description was:\n"
                        f"{expected_description}"
                    )

        if len(errors) > 0:
            errors_joined = "\n".join(tests.common.make_bullet_points(errors))
            raise AssertionError(f"One or more errors:\n{errors_joined}")

    def test_dot_suffix_in_invariant_descriptions(self) -> None:
        symbol_table = _META_MODEL.symbol_table

        errors = []  # type: List[str]

        for our_type in symbol_table.our_types:
            if not isinstance(
                our_type,
                (
                    intermediate.ConstrainedPrimitive,
                    intermediate.AbstractClass,
                    intermediate.ConcreteClass,
                ),
            ):
                continue

            for invariant in our_type.invariants:
                if invariant.specified_for is not our_type:
                    continue

                if not invariant.description.endswith("."):
                    errors.append(
                        f"The invariant description in class {our_type.name!r} "
                        f"must end with a dot: "
                        f"{invariant.description!r}"
                    )

        if len(errors) > 0:
            errors_joined = "\n".join(tests.common.make_bullet_points(errors))
            raise AssertionError(f"One or more errors:\n{errors_joined}")

    def test_metadata_classes_exclude_only_the_value_related_properties(
        self,
    ) -> None:
        """
        Assert that every ``*_metadata`` class in the "Metadata And Value
        Views" region carries exactly the properties of its Part 1
        counterpart, minus the value-related properties it deliberately
        excludes, and that every property it does carry has *exactly* the
        same type as on the Part 1 counterpart (a ``*_metadata`` class only
        ever drops properties -- it never changes the type or the
        optionality of the ones it keeps).

        This keeps Part 1 and Part 2 in sync: if a property is added,
        renamed, removed or re-typed on the Part 1 class, this test will
        fail until the corresponding ``*_metadata`` class is updated to
        match.
        """
        symbol_table = _META_MODEL.symbol_table

        # fmt: off
        # Map the metadata class name to
        # (the Part 1 class name, the excluded property names)
        cases = [
            ("Property_metadata", "Property", {"value", "value_ID"}),
            ("Range_metadata", "Range", {"min", "max"}),
            ("Blob_metadata", "Blob", {"value", "content_type"}),
            ("File_metadata", "File", {"value", "content_type"}),
            (
                "Multi_language_property_metadata",
                "Multi_language_property",
                {"value", "value_ID"},
            ),
            ("Reference_element_metadata", "Reference_element", {"value"}),
            (
                "Relationship_element_metadata",
                "Relationship_element",
                {"first", "second"},
            ),
            (
                "Annotated_relationship_element_metadata",
                "Annotated_relationship_element",
                {"first", "second", "annotations"},
            ),
            (
                "Entity_metadata",
                "Entity",
                {
                    "statements",
                    "entity_type",
                    "global_asset_ID",
                    "specific_asset_IDs",
                },
            ),
            ("Capability_metadata", "Capability", set()),
            (
                "Operation_metadata",
                "Operation",
                {"input_variables", "output_variables", "inoutput_variables"},
            ),
            (
                "Submodel_element_collection_metadata",
                "Submodel_element_collection",
                {"value"},
            ),
            (
                "Submodel_element_list_metadata",
                "Submodel_element_list",
                {"value"},
            ),
            (
                "Basic_event_element_metadata",
                "Basic_event_element",
                {"observed"},
            ),
            ("Submodel_metadata", "Submodel", {"submodel_elements"}),
            (
                "Asset_administration_shell_metadata",
                "Asset_administration_shell",
                {"asset_information", "submodels"},
            ),
        ]
        # fmt: on

        errors = []  # type: List[str]

        for metadata_cls_name, full_cls_name, expected_excluded in cases:
            metadata_cls = symbol_table.must_find_class(
                aas_core_codegen.common.Identifier(metadata_cls_name)
            )
            full_cls = symbol_table.must_find_class(
                aas_core_codegen.common.Identifier(full_cls_name)
            )

            metadata_prop_names = set(metadata_cls.properties_by_name.keys())
            full_prop_names = set(full_cls.properties_by_name.keys())

            # NOTE (mristin):
            # This is a sanity-check that the excluded properties actually exist on the
            # full class; otherwise the exclusion set itself is stale.
            stale_exclusions = expected_excluded - full_prop_names
            if stale_exclusions:
                errors.append(
                    f"The excluded properties {sorted(stale_exclusions)!r} for "
                    f"{metadata_cls_name} no longer exist on {full_cls_name}; "
                    f"update the exclusion set in this test."
                )
                continue

            expected_metadata_prop_names = full_prop_names - expected_excluded

            missing = expected_metadata_prop_names - metadata_prop_names
            unexpected = metadata_prop_names - expected_metadata_prop_names

            if missing:
                errors.append(
                    f"{metadata_cls_name} is missing the propert(y/ies) present "
                    f"on {full_cls_name} and not in the excluded set: "
                    f"{sorted(missing)!r}"
                )

            if unexpected:
                errors.append(
                    f"{metadata_cls_name} has the unexpected propert(y/ies), not "
                    f"present on {full_cls_name} after excluding "
                    f"{sorted(expected_excluded)!r}: {sorted(unexpected)!r}"
                )

            # NOTE (mristin):
            # The retained properties must coincide in type (including
            # Optional-ness) with their Part 1 counterparts. This is exactly what
            # structural subtyping checks: every property of ``metadata_cls`` must
            # be matched on ``full_cls`` by a same-named property of the exact same
            # type.
            if (
                not missing
                and not unexpected
                and not full_cls.is_structural_subtype_of(metadata_cls)
            ):
                errors.append(
                    f"One or more of the propert(y/ies) shared between "
                    f"{metadata_cls_name} and {full_cls_name} do not coincide in "
                    f"type (including Optional-ness)."
                )

        if len(errors) > 0:
            errors_joined = "\n".join(tests.common.make_bullet_points(errors))
            raise AssertionError(f"One or more errors:\n{errors_joined}")

    def test_reference_element_value_mirrors_all_properties_of_reference(
        self,
    ) -> None:
        """
        Assert that ``Reference_element_value`` carries exactly the same
        properties as ``Reference``, each with exactly the same type.

        Unlike the ``*_metadata`` classes, ``Reference_element_value`` does
        not exclude any property: the Part 2 types ``ReferenceElementValue`` as
        a direct alias of ``Reference``, not an object wrapping one, so it must mirror
        *all* of ``Reference``'s properties. This keeps Part 1 and Part 2 in sync: if
        a property is added, renamed, removed or re-typed on ``Reference``, this test
        will fail until ``Reference_element_value`` is updated to match.
        """
        symbol_table = _META_MODEL.symbol_table

        reference_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Reference")
        )
        reference_element_value_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Reference_element_value")
        )

        # NOTE (mristin):
        # Two classes carry exactly the same properties, each with exactly the
        # same type, if and only if each is a structural subtype of the other.
        self.assertTrue(
            reference_element_value_cls.is_structural_subtype_of(reference_cls),
            "Reference_element_value is missing a propert(y/ies) present on "
            "Reference, or one of its shared properties is mistyped.",
        )
        self.assertTrue(
            reference_cls.is_structural_subtype_of(reference_element_value_cls),
            "Reference_element_value has (an) unexpected propert(y/ies), not "
            "present on Reference.",
        )

    def test_every_submodel_element_subclass_has_a_metadata_class(self) -> None:
        """
        Assert that every concrete subclass of ``Submodel_element`` in Part 1
        has a corresponding ``<ClassName>_metadata`` class in the "Metadata
        And Value Views" region.

        This keeps Part 1 and Part 2 in sync: if a new submodel element type
        is added to Part 1, this test will fail until a ``*_metadata`` class
        is added for it too.
        """
        symbol_table = _META_MODEL.symbol_table

        submodel_element_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Submodel_element")
        )

        errors = []  # type: List[str]

        for our_type in symbol_table.our_types:
            if not isinstance(our_type, intermediate.ConcreteClass):
                continue

            if our_type is submodel_element_cls:
                continue

            if not our_type.is_subclass_of(submodel_element_cls):
                continue

            expected_metadata_cls_name = aas_core_codegen.common.Identifier(
                f"{our_type.name}_metadata"
            )

            if symbol_table.find_our_type(expected_metadata_cls_name) is None:
                errors.append(
                    f"No {expected_metadata_cls_name!r} class found for the "
                    f"submodel element {our_type.name!r}"
                )

        if len(errors) > 0:
            errors_joined = "\n".join(tests.common.make_bullet_points(errors))
            raise AssertionError(f"One or more errors:\n{errors_joined}")

    def test_every_submodel_element_subclass_has_a_value_class_or_is_exempted(
        self,
    ) -> None:
        """
        Assert that every concrete subclass of ``Submodel_element`` in Part 1
        either has a corresponding ``<ClassName>_value`` class in the
        "Metadata And Value Views" region, or is explicitly exempted below
        with a reason.

        This keeps Part 1 and Part 2 in sync: if a new submodel element type
        is added to Part 1, this test will fail until either a ``*_value``
        class is added for it, or it is added to the exemptions with a
        reason (*e.g.*, because its value is ValueOnly-shaped/dynamic, or it
        has no value at all).
        """
        symbol_table = _META_MODEL.symbol_table

        submodel_element_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Submodel_element")
        )

        # fmt: off
        # Map the Part 1 class name to the reason why it has no *_value class.
        exemptions = {
            "Property": (
                "PropertyValue is a raw JSON string, number or boolean, not "
                "an object."
            ),
            "Multi_language_property": (
                "MultiLanguagePropertyValue is dynamic, ValueOnly-shaped JSON."
            ),
            "Annotated_relationship_element": (
                "Its only difference from Relationship_element is the "
                "annotations property, which is itself ValueOnly-shaped JSON."
            ),
            "Entity": (
                "specificAssetIds is an array of the already-exempted, "
                "dynamic SpecificAssetIdValue shape, and statements is "
                "itself ValueOnly-shaped JSON."
            ),
            "Capability": "Capability has no value at all; no Value schema exists.",
            "Operation": (
                "Operation has no simple value; invocation uses "
                "OperationRequest/OperationResult instead. No Value schema "
                "exists."
            ),
            "Submodel_element_collection": (
                "SubmodelElementCollectionValue is ValueOnly-shaped JSON."
            ),
            "Submodel_element_list": (
                "SubmodelElementListValue is a bare JSON array, not an "
                "object."
            ),
        }
        # fmt: on

        errors = []  # type: List[str]

        concrete_submodel_element_names = set()  # type: Set[str]

        for our_type in symbol_table.our_types:
            if not isinstance(our_type, intermediate.ConcreteClass):
                continue

            if our_type is submodel_element_cls:
                continue

            if not our_type.is_subclass_of(submodel_element_cls):
                continue

            concrete_submodel_element_names.add(our_type.name)

            expected_value_cls_name = aas_core_codegen.common.Identifier(
                f"{our_type.name}_value"
            )
            value_cls_exists = (
                symbol_table.find_our_type(expected_value_cls_name) is not None
            )
            is_exempted = our_type.name in exemptions

            if value_cls_exists and is_exempted:
                errors.append(
                    f"{our_type.name!r} has both a {expected_value_cls_name!r} "
                    f"class *and* an exemption entry; remove one of the two."
                )
            elif not value_cls_exists and not is_exempted:
                errors.append(
                    f"No {expected_value_cls_name!r} class found for the "
                    f"submodel element {our_type.name!r}, and it is not "
                    f"exempted either."
                )

        # NOTE (mristin):
        # Sanity-check that the exemptions do not refer to stale/renamed
        # submodel element classes.
        stale_exemptions = set(exemptions.keys()) - concrete_submodel_element_names
        if stale_exemptions:
            errors.append(
                f"The exemptions refer to classes which are no longer "
                f"concrete subclasses of Submodel_element: "
                f"{sorted(stale_exemptions)!r}"
            )

        if len(errors) > 0:
            errors_joined = "\n".join(tests.common.make_bullet_points(errors))
            raise AssertionError(f"One or more errors:\n{errors_joined}")

    def test_operation_request_async_has_the_expected_fields(self) -> None:
        """
        Assert that ``Operation_request_async`` has exactly the same fields
        as ``Operation_request`` -- ``input_arguments`` and
        ``inoutput_arguments`` with coinciding types, and
        ``client_timeout_duration`` present on both, but required (not
        ``Optional``) on ``Operation_request_async``.

        ``Operation_request_async`` is deliberately *not* a subclass of
        ``Operation_request`` (see the note on the class itself), so nothing
        keeps the two in sync automatically; this test is what does. If a
        field is added, renamed, removed or re-typed on ``Operation_request``,
        this test will fail until ``Operation_request_async`` is updated to
        match.
        """
        symbol_table = _META_MODEL.symbol_table

        operation_request_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Operation_request")
        )
        operation_request_async_cls = symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Operation_request_async")
        )

        operation_request_prop_names = set(
            operation_request_cls.properties_by_name.keys()
        )
        operation_request_async_prop_names = set(
            operation_request_async_cls.properties_by_name.keys()
        )

        errors = []  # type: List[str]

        missing = operation_request_prop_names - operation_request_async_prop_names
        unexpected = operation_request_async_prop_names - operation_request_prop_names

        if missing:
            errors.append(
                f"Operation_request_async is missing the propert(y/ies) "
                f"present on Operation_request: {sorted(missing)!r}"
            )

        if unexpected:
            errors.append(
                f"Operation_request_async has the unexpected propert(y/ies), "
                f"not present on Operation_request: {sorted(unexpected)!r}"
            )

        # NOTE (mristin):
        # client_timeout_duration is expected to differ: required (not
        # Optional) on Operation_request_async, Optional on Operation_request.
        # This is the one property that keeps the two classes from being
        # structural subtypes of each other (``Class.is_structural_subtype_of``
        # is invariant in Optional-ness), so we special-case it here and
        # compare the rest with ``intermediate.type_annotations_equal``.
        if not missing and not unexpected:
            client_timeout_duration_request = operation_request_cls.properties_by_name[
                "client_timeout_duration"
            ]
            client_timeout_duration_async = (
                operation_request_async_cls.properties_by_name[
                    "client_timeout_duration"
                ]
            )

            if isinstance(
                client_timeout_duration_async.type_annotation,
                intermediate.OptionalTypeAnnotation,
            ) or not intermediate.type_annotations_equal(
                intermediate.beneath_optional(
                    client_timeout_duration_request.type_annotation
                ),
                client_timeout_duration_async.type_annotation,
            ):
                errors.append(
                    "Operation_request_async.client_timeout_duration is "
                    "expected to be the required (non-Optional) form of "
                    "Operation_request.client_timeout_duration, but it is not."
                )

            for prop_name in sorted(
                operation_request_prop_names - {"client_timeout_duration"}
            ):
                request_prop = operation_request_cls.properties_by_name[prop_name]
                async_prop = operation_request_async_cls.properties_by_name[prop_name]

                if not intermediate.type_annotations_equal(
                    request_prop.type_annotation, async_prop.type_annotation
                ):
                    errors.append(
                        f"Operation_request_async.{prop_name} is typed "
                        f"{async_prop.type_annotation}, but "
                        f"Operation_request.{prop_name} is typed "
                        f"{request_prop.type_annotation}; the types (including "
                        f"Optional-ness) must coincide."
                    )

        if len(errors) > 0:
            errors_joined = "\n".join(tests.common.make_bullet_points(errors))
            raise AssertionError(f"One or more errors:\n{errors_joined}")

    def test_result_base_operation_result_operation_result_share_coinciding_fields(
        self,
    ) -> None:
        """
        Assert that the fields shared among ``Result``, ``Base_operation_result``
        and ``Operation_result`` coincide in type wherever they overlap.

        These three classes are deliberately *not* related by inheritance
        (see the note on ``Base_operation_result``): aas-core-codegen
        refuses to generate a schema for a concrete class with concrete
        descendants unless it is marked
        ``@serialization(with_model_type=True)``, which would introduce a
        ``modelType`` discriminator that the official schema does not have
        for this hierarchy. Flattening avoids that mismatch, but it means
        ``messages`` (all three classes) and ``execution_state``/``success``
        (``Base_operation_result`` and ``Operation_result``) are duplicated
        by hand. This test is what keeps those duplicates in sync: if one
        copy is changed without the other, this test will fail.
        """
        symbol_table = _META_MODEL.symbol_table

        class_names = ["Result", "Base_operation_result", "Operation_result"]
        props_by_class = {
            name: {
                prop.name: str(prop.type_annotation)
                for prop in symbol_table.must_find_class(
                    aas_core_codegen.common.Identifier(name)
                ).properties
            }
            for name in class_names
        }

        errors = []  # type: List[str]

        for i, first_name in enumerate(class_names):
            for second_name in class_names[i + 1 :]:
                first_props = props_by_class[first_name]
                second_props = props_by_class[second_name]

                shared_prop_names = set(first_props.keys()) & set(second_props.keys())

                for prop_name in sorted(shared_prop_names):
                    first_type_str = first_props[prop_name]
                    second_type_str = second_props[prop_name]

                    if first_type_str != second_type_str:
                        errors.append(
                            f"{first_name}.{prop_name} is typed "
                            f"{first_type_str!r}, but {second_name}.{prop_name} "
                            f"is typed {second_type_str!r}; the types "
                            f"(including Optional-ness) must coincide."
                        )

        if len(errors) > 0:
            errors_joined = "\n".join(tests.common.make_bullet_points(errors))
            raise AssertionError(f"One or more errors:\n{errors_joined}")

    def test_get_xxx_result_envelopes_have_the_expected_fields(self) -> None:
        """
        Assert that every ``Get_*_result`` class in the "GetXxxResult
        Envelopes" region has exactly ``paging_metadata`` (required, typed
        ``Paging_metadata``) and ``result`` (``Optional[List[...]]`` of the
        expected item type), and nothing else.

        These classes are deliberately standalone (not related by
        inheritance to ``Paged_result`` or to each other; see the note at
        the top of the region), so nothing keeps their shape in sync
        automatically. This test is what does: if a class is mistyped
        (*e.g.*, a stale or misspelled item type) or gains/loses a field,
        this test will fail.
        """
        symbol_table = _META_MODEL.symbol_table

        # fmt: off
        # Map the class name to the expected item type of its "result" list.
        cases = [
            (
                "Get_all_asset_administration_shells_recent_changes_result",
                "Asset_administration_shell_recent_change",
            ),
            (
                "Get_all_concept_descriptions_recent_changes_result",
                "Concept_description_recent_change",
            ),
            ("Get_all_submodels_recent_changes_result", "Submodel_recent_change"),
            (
                "Get_asset_administration_shell_descriptors_result",
                "Asset_administration_shell_descriptor",
            ),
            (
                "Get_asset_administration_shells_metadata_result",
                "Asset_administration_shell_metadata",
            ),
            ("Get_asset_administration_shells_result", "Asset_administration_shell"),
            ("Get_concept_descriptions_result", "Concept_description"),
            ("Get_package_descriptions_result", "Package_description"),
            ("Get_path_items_result", "Path_item"),
            ("Get_references_result", "Reference"),
            ("Get_submodel_descriptors_result", "Submodel_descriptor"),
            ("Get_submodel_elements_metadata_result", "Submodel_element_metadata"),
            ("Get_submodel_elements_result", "Submodel_element"),
            ("Get_submodels_metadata_result", "Submodel_metadata"),
            ("Get_submodels_result", "Submodel"),
        ]
        # fmt: on

        errors = []  # type: List[str]

        for cls_name, item_type_name in cases:
            cls = symbol_table.must_find_class(
                aas_core_codegen.common.Identifier(cls_name)
            )

            props_by_name = {prop.name: prop for prop in cls.properties}
            prop_names = set(props_by_name.keys())

            expected_prop_names = {"paging_metadata", "result"}

            missing = expected_prop_names - prop_names
            unexpected = prop_names - expected_prop_names

            if missing:
                errors.append(
                    f"{cls_name} is missing the expected propert(y/ies): "
                    f"{sorted(missing)!r}"
                )

            if unexpected:
                errors.append(
                    f"{cls_name} has the unexpected propert(y/ies): "
                    f"{sorted(unexpected)!r}"
                )

            if "paging_metadata" in props_by_name:
                paging_metadata_type_str = str(
                    props_by_name["paging_metadata"].type_annotation
                )
                if paging_metadata_type_str != "Paging_metadata":
                    errors.append(
                        f"{cls_name}.paging_metadata is typed "
                        f"{paging_metadata_type_str!r}, expected "
                        f"'Paging_metadata' (required)."
                    )

            if "result" in props_by_name:
                result_type_str = str(props_by_name["result"].type_annotation)
                expected_result_type_str = f"Optional[List[{item_type_name}]]"
                if result_type_str != expected_result_type_str:
                    errors.append(
                        f"{cls_name}.result is typed {result_type_str!r}, "
                        f"expected {expected_result_type_str!r}."
                    )

        if len(errors) > 0:
            errors_joined = "\n".join(tests.common.make_bullet_points(errors))
            raise AssertionError(f"One or more errors:\n{errors_joined}")


if __name__ == "__main__":
    unittest.main()
