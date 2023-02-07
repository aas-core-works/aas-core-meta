import pathlib
import unittest
from typing import List, Set, Optional, Union, Tuple

from aas_core_codegen import intermediate
import aas_core_codegen.common
from aas_core_codegen.infer_for_schema import match as infer_for_schema_match
import aas_core_meta.v3 as v3

import tests.common


class Test_matches_XML_serializable_string(unittest.TestCase):
    def test_free_form_text(self) -> None:
        assert v3.matches_XML_serializable_string("some free & <free> \u1984 form text")

    def test_fffe(self) -> None:
        assert not v3.matches_XML_serializable_string("\uFFFE")

    def test_ffff(self) -> None:
        assert not v3.matches_XML_serializable_string("\uFFFF")

    # noinspection SpellCheckingInspection
    def test_surrogate_characters(self) -> None:
        assert not v3.matches_XML_serializable_string("\uD800")
        assert not v3.matches_XML_serializable_string("\uDFFF")

    def test_nul(self) -> None:
        assert not v3.matches_XML_serializable_string("\x00")


class Test_matches_xs_date_time_utc(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_date_time_UTC("")

    def test_date(self) -> None:
        assert not v3.matches_xs_date_time_UTC("2022-04-01")

    def test_date_with_time_zone(self) -> None:
        assert not v3.matches_xs_date_time_UTC("2022-04-01Z")

    def test_date_time_without_zone(self) -> None:
        assert not v3.matches_xs_date_time_UTC("2022-04-01T01:02:03")

    def test_date_time_with_offset(self) -> None:
        assert not v3.matches_xs_date_time_UTC("2022-04-01T01:02:03+02:00")

    def test_date_time_with_UTC(self) -> None:
        assert v3.matches_xs_date_time_UTC("2022-04-01T01:02:03Z")

    def test_date_time_without_seconds(self) -> None:
        assert not v3.matches_xs_date_time_UTC("2022-04-01T01:02Z")

    def test_date_time_without_minutes(self) -> None:
        assert not v3.matches_xs_date_time_UTC("2022-04-01T01Z")

    def test_date_time_with_UTC_and_suffix(self) -> None:
        assert not v3.matches_xs_date_time_UTC("2022-04-01T01:02:03Z-unexpected-suffix")


class Test_matches_MIME_type(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_MIME_type("")

    def test_integer(self) -> None:
        assert not v3.matches_MIME_type("1234")

    def test_common(self) -> None:
        assert v3.matches_MIME_type("audio/aac")

    def test_dash(self) -> None:
        assert v3.matches_MIME_type("application/x-abiword")

    def test_dot(self) -> None:
        assert v3.matches_MIME_type("application/vnd.amazon.ebook")

    def test_plus(self) -> None:
        assert v3.matches_MIME_type("application/vnd.apple.installer+xml")

    def test_number_in_suffix(self) -> None:
        assert v3.matches_MIME_type("audio/3gpp2")


class Test_matches_RFC_8089_path(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_RFC_8089_path("")

    def test_integer(self) -> None:
        assert not v3.matches_RFC_8089_path("1234")

    def test_absolute_path_without_scheme(self) -> None:
        assert not v3.matches_RFC_8089_path("/path/to/somewhere")

    def test_relative_path_without_scheme(self) -> None:
        assert not v3.matches_RFC_8089_path("path/to/somewhere")

    def test_local_absolute_path_with_scheme(self) -> None:
        assert v3.matches_RFC_8089_path("file:/path/to/somewhere")

    def test_non_local_file_with_an_explicit_authority(self) -> None:
        # See https://datatracker.ietf.org/doc/html/rfc8089#appendix-B
        assert v3.matches_RFC_8089_path("file://host.example.com/path/to/file")

    def test_local_relative_path_with_scheme(self) -> None:
        assert not v3.matches_RFC_8089_path("file:path/to/somewhere")


class Test_matches_BCP_47(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_BCP_47("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_BCP_47("some free form text")

    def test_valid(self) -> None:
        for text in ["de", "de-CH"]:
            self.assertTrue(v3.matches_BCP_47(text), text)


class Test_matches_xs_any_URI(unittest.TestCase):
    # See: http://www.datypic.com/sc/xsd/t-xsd_anyURI.html

    def test_empty(self) -> None:
        # NOTE (mristin, 2022-04-1):
        # An empty string is a valid ``xs:anyURI``,
        # see https://lists.w3.org/Archives/Public/xml-dist-app/2003Mar/0076.html and
        # https://lists.w3.org/Archives/Public/xml-dist-app/2003Mar/0078.html
        assert v3.matches_xs_any_URI("")

    def test_integer(self) -> None:
        assert v3.matches_xs_any_URI("1234")

    def test_absolute_path_without_scheme(self) -> None:
        assert v3.matches_xs_any_URI("/path/to/somewhere")

    def test_relative_path_without_scheme(self) -> None:
        assert v3.matches_xs_any_URI("path/to/somewhere")

    def test_URI(self) -> None:
        assert v3.matches_xs_any_URI(
            "https://github.com/aas-core-works/aas-core-codegen"
        )

    def test_too_many_fragments(self) -> None:
        assert not v3.matches_xs_any_URI("http://datypic.com#frag1#frag2")

    def test_percentage_followed_by_non_two_hexadecimal_digits(self) -> None:
        assert not v3.matches_xs_any_URI("http://datypic.com#f% rag")


class Test_matches_xs_base_64_binary(unittest.TestCase):
    # See http://www.datypic.com/sc/xsd/t-xsd_base64Binary.html

    def test_without_space_uppercase(self) -> None:
        assert v3.matches_xs_base_64_binary("0FB8")

    def test_without_space_lowercase(self) -> None:
        assert v3.matches_xs_base_64_binary("0fb8")

    def test_whitespace_is_allowed_anywhere_in_the_value(self) -> None:
        assert v3.matches_xs_base_64_binary("0 FB8 0F+9")

    def test_equals_signs_are_used_for_padding(self) -> None:
        assert v3.matches_xs_base_64_binary("0F+40A==")

    def test_an_empty_value_is_valid(self) -> None:
        assert v3.matches_xs_base_64_binary("")

    def test_an_odd_number_of_characters_is_not_valid(self) -> None:
        # Characters must appear in groups of four.
        assert not v3.matches_xs_base_64_binary("FB8")

    def test_equals_signs_may_only_appear_at_the_end(self) -> None:
        assert not v3.matches_xs_base_64_binary("==0F")


class Test_matches_xs_date(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_date("")

    def test_date(self) -> None:
        assert v3.matches_xs_date("2022-04-01")

    def test_date_with_utc(self) -> None:
        assert v3.matches_xs_date("2022-04-01Z")

    def test_date_with_offset(self) -> None:
        assert v3.matches_xs_date("2022-04-01+02:34")

    def test_date_with_invalid_offset(self) -> None:
        assert not v3.matches_xs_date("2022-04-01+15:00")

    def test_date_with_unexpected_suffix(self) -> None:
        assert not v3.matches_xs_date("2022-04-01unexpected")


class Test_matches_xs_date_time(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_date_time("")

    def test_date(self) -> None:
        assert not v3.matches_xs_date_time("2022-04-01")

    def test_date_with_time_zone(self) -> None:
        assert not v3.matches_xs_date_time("2022-04-01Z")

    def test_date_time_without_zone(self) -> None:
        assert v3.matches_xs_date_time("2022-04-01T01:02:03")

    def test_date_time_with_offset(self) -> None:
        assert v3.matches_xs_date_time("2022-04-01T01:02:03+02:00")

    def test_date_time_with_invalid_offset(self) -> None:
        assert not v3.matches_xs_date_time("2022-04-01T01:02:03+15:00")

    def test_date_time_with_UTC(self) -> None:
        assert v3.matches_xs_date_time("2022-04-01T01:02:03Z")

    def test_date_time_without_seconds(self) -> None:
        assert not v3.matches_xs_date_time("2022-04-01T01:02Z")

    def test_date_time_without_minutes(self) -> None:
        assert not v3.matches_xs_date_time("2022-04-01T01Z")

    def test_date_time_with_unexpected_suffix(self) -> None:
        assert not v3.matches_xs_date_time("2022-04-01T01:02:03Z-unexpected-suffix")

    def test_date_time_with_unexpected_prefix(self) -> None:
        assert not v3.matches_xs_date_time("unexpected-prefix-2022-04-01T01:02:03Z")


class Test_matches_xs_decimal(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_decimal("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_decimal("some free form text")

    def test_integer(self) -> None:
        assert v3.matches_xs_decimal("1234")

    def test_decimal(self) -> None:
        assert v3.matches_xs_decimal("1234.01234")

    def test_integer_with_preceding_zeros(self) -> None:
        assert v3.matches_xs_decimal("0001234")

    def test_decimal_with_preceding_zeros(self) -> None:
        assert v3.matches_xs_decimal("0001234.01234")

    def test_scientific_notation(self) -> None:
        assert not v3.matches_xs_decimal("12.123e123")


class Test_matches_xs_double(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_double("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_double("some free form text")

    def test_integer(self) -> None:
        assert v3.matches_xs_double("1234")

    def test_double(self) -> None:
        assert v3.matches_xs_double("1234.01234")

    def test_integer_with_preceding_zeros(self) -> None:
        assert v3.matches_xs_double("0001234")

    def test_double_with_preceding_zeros(self) -> None:
        assert v3.matches_xs_double("0001234.01234")

    def test_exponent_integer(self) -> None:
        assert v3.matches_xs_double("-12.34e5")
        assert v3.matches_xs_double("+12.34e5")
        assert v3.matches_xs_double("12.34e5")
        assert v3.matches_xs_double("12.34e+5")
        assert v3.matches_xs_double("12.34e-5")

    def test_exponent_float(self) -> None:
        assert not v3.matches_xs_double("-12.34e5.6")
        assert not v3.matches_xs_double("+12.34e5.6")
        assert not v3.matches_xs_double("12.34e5.6")
        assert not v3.matches_xs_double("12.34e+5.6")
        assert not v3.matches_xs_double("12.34e-5.6")

    def test_edge_cases(self) -> None:
        # NOTE (mristin, 2022-10-30):
        # See: https://www.oreilly.com/library/view/xml-schema/0596002521/re67.html
        assert not v3.matches_xs_double("+INF")
        assert v3.matches_xs_double("-INF")
        assert v3.matches_xs_double("INF")
        assert v3.matches_xs_double("NaN")

    def test_case_matters(self) -> None:
        assert not v3.matches_xs_double("inf")
        assert not v3.matches_xs_double("nan")


class Test_matches_xs_duration(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_duration("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_duration("some free form text")

    def test_integer(self) -> None:
        assert not v3.matches_xs_duration("1234")

    # NOTE (mristin, 2022-04-6):
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
            self.assertTrue(v3.matches_xs_duration(text), text)

    def test_leading_P_missing(self) -> None:
        assert not v3.matches_xs_duration("1Y")

    def test_separator_T_missing(self) -> None:
        assert not v3.matches_xs_duration("P1S")

    def test_not_all_parts_positive(self) -> None:
        assert not v3.matches_xs_duration("P-1Y")
        assert not v3.matches_xs_duration("P1Y-1M")

    def test_the_order_matters(self) -> None:
        assert not v3.matches_xs_duration("P1M2Y")


class Test_matches_xs_float(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_float("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_float("some free form text")

    def test_integer(self) -> None:
        assert v3.matches_xs_float("1234")

    def test_float(self) -> None:
        assert v3.matches_xs_float("1234.01234")

    def test_integer_with_preceding_zeros(self) -> None:
        assert v3.matches_xs_float("0001234")

    def test_float_with_preceding_zeros(self) -> None:
        assert v3.matches_xs_float("0001234.01234")

    def test_exponent_integer(self) -> None:
        assert v3.matches_xs_float("-12.34e5")
        assert v3.matches_xs_float("+12.34e5")
        assert v3.matches_xs_float("12.34e5")
        assert v3.matches_xs_float("12.34e+5")
        assert v3.matches_xs_float("12.34e-5")

    def test_exponent_float(self) -> None:
        assert not v3.matches_xs_float("-12.34e5.6")
        assert not v3.matches_xs_float("+12.34e5.6")
        assert not v3.matches_xs_float("12.34e5.6")
        assert not v3.matches_xs_float("12.34e+5.6")
        assert not v3.matches_xs_float("12.34e-5.6")

    def test_edge_cases(self) -> None:
        # NOTE (mristin, 2022-10-30):
        # See: https://www.oreilly.com/library/view/xml-schema/0596002521/re67.html
        assert not v3.matches_xs_float("+INF")
        assert v3.matches_xs_float("-INF")
        assert v3.matches_xs_float("INF")
        assert v3.matches_xs_float("NaN")

    def test_case_matters(self) -> None:
        assert not v3.matches_xs_float("inf")
        assert not v3.matches_xs_float("nan")


class Test_matches_xs_g_day(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_g_day("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_g_day("some free form text")

    # NOTE (mristin, 2022-04-6):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-gday

    def test_valid_values(self) -> None:
        for text in ["---01", "---01Z", "---01+02:00", "---01-04:00", "---15", "---31"]:
            self.assertTrue(v3.matches_xs_g_day(text), text)

    def test_unexpected_suffix(self) -> None:
        assert not v3.matches_xs_g_day("--30-")

    def test_day_outside_of_range(self) -> None:
        assert not v3.matches_xs_g_day("---35")

    def test_missing_leading_digit(self) -> None:
        assert not v3.matches_xs_g_day("---5")

    def test_missing_leading_dashes(self) -> None:
        assert not v3.matches_xs_g_day("15")


class Test_matches_xs_g_month(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_g_month("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_g_month("some free form text")

    # NOTE (mristin, 2022-04-6):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-gmonth

    def test_valid_values(self) -> None:
        for text in ["--05", "--11Z", "--11+02:00", "--11-04:00", "--02"]:
            self.assertTrue(v3.matches_xs_g_month(text), text)

    def test_unexpected_prefix_and_suffix(self) -> None:
        assert not v3.matches_xs_g_month("-01-")

    def test_month_outside_of_range(self) -> None:
        assert not v3.matches_xs_g_month("--13")

    def test_missing_leading_digit(self) -> None:
        assert not v3.matches_xs_g_month("--1")

    def test_missing_leading_dashes(self) -> None:
        assert not v3.matches_xs_g_month("01")


class Test_matches_xs_g_month_day(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_g_month_day("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_g_month_day("some free form text")

    # NOTE (mristin, 2022-04-6):
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
            self.assertTrue(v3.matches_xs_g_month_day(text), text)

    def test_unexpected_prefix_and_suffix(self) -> None:
        assert not v3.matches_xs_g_month_day("-01-30-")

    def test_day_outside_of_range(self) -> None:
        assert not v3.matches_xs_g_month_day("--01-35")

    def test_missing_leading_digit(self) -> None:
        assert not v3.matches_xs_g_month_day("--1-5")

    def test_missing_leading_dashes(self) -> None:
        assert not v3.matches_xs_g_month_day("01-15")


class Test_matches_xs_g_year(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_g_year("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_g_year("some free form text")

    # NOTE (mristin, 2022-04-6):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-gyear

    def test_valid_values(self) -> None:
        for text in ["2001", "2001+02:00", "2001Z", "2001+00:00", "-2001", "-20000"]:
            self.assertTrue(v3.matches_xs_g_year(text), text)

    def test_missing_century(self) -> None:
        assert not v3.matches_xs_g_year("01")

    def test_unexpected_month(self) -> None:
        assert not v3.matches_xs_g_year("2001-12")


class Test_matches_xs_g_year_month(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_g_year_month("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_g_year_month("some free form text")

    # NOTE (mristin, 2022-04-6):
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
            self.assertTrue(v3.matches_xs_g_year_month(text), text)

    def test_missing_month(self) -> None:
        assert not v3.matches_xs_g_year_month("2001")

    def test_month_out_of_range(self) -> None:
        assert not v3.matches_xs_g_year_month("2001-13")

    def test_missing_century(self) -> None:
        assert not v3.matches_xs_g_year_month("01-13")


class Test_matches_xs_hex_binary(unittest.TestCase):
    def test_empty(self) -> None:
        assert v3.matches_xs_hex_binary("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_hex_binary("some free form text")

    # NOTE (mristin, 2022-04-6):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-hexbinary

    def test_valid_values(self) -> None:
        for text in [
            "11",
            "12",
            "1234",
            "3c3f786d6c2076657273696f6e3d22312e302220656e636f64696e67",
        ]:
            self.assertTrue(v3.matches_xs_hex_binary(text), text)

    def test_odd_number_of_digits(self) -> None:
        assert not v3.matches_xs_hex_binary("1")
        assert not v3.matches_xs_hex_binary("123")


class Test_matches_xs_time(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_time("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_time("some free form text")

    # NOTE (mristin, 2022-04-6):
    # See https://www.data2type.de/xml-xslt-xslfo/xml-schema/datentypen-referenz/xs-time

    def test_valid_values(self) -> None:
        for text in [
            "21:32:52",
            "21:32:52+02:00",
            "19:32:52Z",
            "19:32:52+00:00",
            "21:32:52.12679",
        ]:
            self.assertTrue(v3.matches_xs_time(text), text)

    def test_missing_seconds(self) -> None:
        assert not v3.matches_xs_time("21:32")

    def test_hour_out_of_range(self) -> None:
        assert not v3.matches_xs_time("25:25:10")

    def test_minute_out_of_range(self) -> None:
        assert not v3.matches_xs_time("01:61:10")

    def test_second_out_of_range(self) -> None:
        assert not v3.matches_xs_time("01:02:61")

    def test_negative(self) -> None:
        assert not v3.matches_xs_time("-10:00:00")

    def test_missing_padded_zeros(self) -> None:
        assert not v3.matches_xs_time("1:20:10")


class Test_matches_xs_integer(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_integer("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_integer("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "-1", "+1"]:
            self.assertTrue(v3.matches_xs_integer(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_integer("1.2")


class Test_matches_xs_long(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_long("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_long("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "-1", "+1"]:
            self.assertTrue(v3.matches_xs_long(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_long("1.2")


class Test_matches_xs_int(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_int("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_int("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "-1", "+1"]:
            self.assertTrue(v3.matches_xs_int(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_int("1.2")


class Test_matches_xs_short(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_short("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_short("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "-1", "+1"]:
            self.assertTrue(v3.matches_xs_short(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_short("1.2")


class Test_matches_xs_byte(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_byte("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_byte("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "-1", "+1"]:
            self.assertTrue(v3.matches_xs_byte(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_byte("1.2")


class Test_matches_xs_non_negative_integer(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_non_negative_integer("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_non_negative_integer("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-0", "1", "001", "+1", "+001"]:
            self.assertTrue(v3.matches_xs_non_negative_integer(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_non_negative_integer("1.2")

    def test_negative(self) -> None:
        assert not v3.matches_xs_non_negative_integer("-1")


class Test_matches_xs_positive_integer(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_positive_integer("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_positive_integer("some free form text")

    def test_valid_values(self) -> None:
        for text in ["1", "001", "+1", "+001", "100"]:
            self.assertTrue(v3.matches_xs_positive_integer(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_positive_integer("1.2")

    def test_negative(self) -> None:
        assert not v3.matches_xs_positive_integer("-1")

    def test_zero(self) -> None:
        assert not v3.matches_xs_positive_integer("0")


class Test_matches_xs_unsigned_long(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_unsigned_long("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_unsigned_long("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-0", "1", "001", "+1", "+001"]:
            self.assertTrue(v3.matches_xs_unsigned_long(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_unsigned_long("1.2")

    def test_negative(self) -> None:
        assert not v3.matches_xs_unsigned_long("-1")


class Test_matches_xs_unsigned_int(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_unsigned_int("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_unsigned_int("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-0", "1", "001", "+1", "+001"]:
            self.assertTrue(v3.matches_xs_unsigned_int(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_unsigned_int("1.2")

    def test_negative(self) -> None:
        assert not v3.matches_xs_unsigned_int("-1")


class Test_matches_xs_unsigned_short(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_unsigned_short("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_unsigned_short("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-0", "1", "001", "+1", "+001"]:
            self.assertTrue(v3.matches_xs_unsigned_short(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_unsigned_short("1.2")

    def test_negative(self) -> None:
        assert not v3.matches_xs_unsigned_short("-1")


class Test_matches_xs_unsigned_byte(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_unsigned_byte("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_unsigned_byte("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-0", "1", "001", "+1", "+001"]:
            self.assertTrue(v3.matches_xs_unsigned_byte(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_unsigned_byte("1.2")

    def test_negative(self) -> None:
        assert not v3.matches_xs_unsigned_byte("-1")


class Test_matches_xs_non_positive_integer(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_non_positive_integer("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_non_positive_integer("some free form text")

    def test_valid_values(self) -> None:
        for text in ["+0", "0", "-1", "-001"]:
            self.assertTrue(v3.matches_xs_non_positive_integer(text), text)

    def test_zero_prefixed_with_zeros(self) -> None:
        assert not v3.matches_xs_non_positive_integer("000")

    def test_decimal(self) -> None:
        assert not v3.matches_xs_non_positive_integer("1.2")

    def test_positive(self) -> None:
        assert not v3.matches_xs_non_positive_integer("1")
        assert not v3.matches_xs_non_positive_integer("+1")


class Test_matches_xs_negative_integer(unittest.TestCase):
    def test_empty(self) -> None:
        assert not v3.matches_xs_negative_integer("")

    def test_free_form_text(self) -> None:
        assert not v3.matches_xs_negative_integer("some free form text")

    def test_valid_values(self) -> None:
        for text in ["-1", "-001", "-100"]:
            self.assertTrue(v3.matches_xs_negative_integer(text), text)

    def test_decimal(self) -> None:
        assert not v3.matches_xs_negative_integer("-1.2")

    def test_zero(self) -> None:
        assert not v3.matches_xs_negative_integer("0")
        assert not v3.matches_xs_negative_integer("+0")
        assert not v3.matches_xs_negative_integer("-0")

    def test_positive(self) -> None:
        assert not v3.matches_xs_negative_integer("1")
        assert not v3.matches_xs_negative_integer("+1")


class Test_matches_xs_string(unittest.TestCase):
    def test_empty(self) -> None:
        assert v3.matches_xs_string("")

    def test_free_form_text(self) -> None:
        assert v3.matches_xs_string("some free & <free> \u1984 form text")

    def test_fffe(self) -> None:
        assert not v3.matches_xs_string("\uFFFE")

    def test_ffff(self) -> None:
        assert not v3.matches_xs_string("\uFFFF")

    # noinspection SpellCheckingInspection
    def test_surrogate_characters(self) -> None:
        assert not v3.matches_xs_string("\uD800")
        assert not v3.matches_xs_string("\uDFFF")

    def test_nul(self) -> None:
        assert not v3.matches_xs_string("\x00")


_META_MODEL: tests.common.MetaModel = tests.common.load_meta_model(
    pathlib.Path(v3.__file__)
)


class Test_assertions(unittest.TestCase):
    # NOTE (mristin, 2023-01-25):
    # We do not state "ID" as an abbreviation (which might imply "Identity Document"),
    # but rather expect "Id" or "id", short for "identifier".
    #
    # See: https://english.stackexchange.com/questions/101248/how-should-the-abbreviation-for-identifier-be-capitalized
    ABBREVIATIONS = {
        "AAS",
        "BCP",
        "DIN",
        "ECE",
        "HTML",
        "IEC",
        "IRDI",
        "IRI",
        "MIME",
        "NIST",
        "RFC",
        "SI",
        "URI",
        "URL",
        "UTC",
        "XML",
        "XSD",
    }

    @staticmethod
    def check_class_name(name: aas_core_codegen.common.Identifier) -> List[str]:
        errors = []  # type: List[str]

        parts = name.split("_")  # type: List[str]

        if parts[0].upper() not in Test_assertions.ABBREVIATIONS:
            if parts[0] != parts[0].capitalize():
                errors.append(
                    f"Expected first part of a class name "
                    f"to be capitalized ({parts[0].capitalize()!r}), "
                    f"but it was not ({parts[0]!r}) for class {name!r}"
                )

        for part in parts:
            if part.upper() in Test_assertions.ABBREVIATIONS and part.upper() != part:
                errors.append(
                    f"Expected a part of a class name "
                    f"to be uppercase ({part.upper()!r})"
                    f"since it denotes an abbreviation, "
                    f"but it was not ({part!r}) for class {name!r}"
                )

        for part in parts[1:]:
            if part.upper() not in Test_assertions.ABBREVIATIONS:
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

        if parts[0].upper() not in Test_assertions.ABBREVIATIONS:
            if parts[0] != parts[0].capitalize():
                errors.append(
                    f"Expected first part of an enumeration literal name "
                    f"to be capitalized ({parts[0].capitalize()!r}), "
                    f"but it was not ({parts[0]!r}) for enumeration literal {name!r}"
                )

        for part in parts:
            if part.upper() in Test_assertions.ABBREVIATIONS and part.upper() != part:
                errors.append(
                    f"Expected a part of a enumeration literal name to be uppercase "
                    f"since it denotes an abbreviation, "
                    f"but it was not ({part!r}) for enumeration literal {name!r}"
                )

        for part in parts[1:]:
            if part.upper() not in Test_assertions.ABBREVIATIONS:
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
            if part.upper() in Test_assertions.ABBREVIATIONS and part.upper() != part:
                errors.append(
                    f"Expected a part of a property name to be uppercase "
                    f"since it denotes an abbreviation, "
                    f"but it was not ({part!r}) for the property {name!r}"
                )

        for part in parts:
            if part.upper() not in Test_assertions.ABBREVIATIONS:
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
            if part.upper() in Test_assertions.ABBREVIATIONS and part.upper() != part:
                errors.append(
                    f"Expected a part of a method name to be uppercase "
                    f"since it denotes an abbreviation, "
                    f"but it was not ({part!r}) for the method {name!r}"
                )

        for part in parts:
            if part.upper() not in Test_assertions.ABBREVIATIONS:
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
            if part.upper() in Test_assertions.ABBREVIATIONS and part.upper() != part:
                errors.append(
                    f"Expected a part of a function name to be uppercase "
                    f"since it denotes an abbreviation, "
                    f"but it was not ({part!r}) for the function {name!r}"
                )

        for part in parts:
            if part.upper() not in Test_assertions.ABBREVIATIONS:
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
            aas_core_codegen.common.Identifier("Lang_string")
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
                # NOTE (mristin, 2022-08-19):
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
            errors.append(
                f"""\
The sub-classes of {referable_cls.name} which are not {identifiable_cls.name} do not correspond to {aas_referable_non_identifiables_set.name}.

Observed classes:  {sorted(class_name_set)!r}
Observed literals: {sorted(literal_set)!r}"""
            )

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
            aas_core_codegen.common.Identifier("Aas_submodel_elements")
        )

        tests.common.assert_subclasses_correspond_to_enumeration_literals(
            symbol_table=symbol_table,
            cls=submodel_element_cls,
            enumeration_or_set=aas_submodel_elements_enum,
        )

    def test_constraint_119_in_all_qualifiable_with_has_kind(self) -> None:
        renegade_classes = []  # type: List[str]

        expected_condition_str = f"""\
not (self.qualifiers is not None)
    or (
        not any(
            qualifier.kind == Qualifier_kind.Template_qualifier
            for qualifier in self.qualifiers
        ) or (
            self.kind_or_default() == Modelling_kind.Template
        )
    )"""

        expected_description = (
            "Constraint AASd-119: If any qualifier kind value of "
            "a qualifiable qualifier is equal to template qualifier and "
            "the qualified element has kind then the qualified element "
            "shall be of kind template."
        )

        atok = _META_MODEL.atok
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
                found_invariant = False
                for invariant in our_type.invariants:
                    condition_str = atok.get_text(invariant.body.original_node)

                    if (
                        condition_str == expected_condition_str
                        and invariant.description == expected_description
                    ):
                        found_invariant = True
                        break

                if not found_invariant:
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
                f"{expected_description}\n\n"
                f"The expected condition and description need to be "
                f"literally the same for this test to pass."
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

                human_readable_prop_name = tests.common.human_readable_property_name(
                    prop_name
                )

                expected_description = (
                    f"{human_readable_prop_name.capitalize()} specifies no duplicate "
                    f"languages"
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
                    and type_anno.items.our_type.is_subclass_of(abstract_lang_string_cls)
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


if __name__ == "__main__":
    unittest.main()
