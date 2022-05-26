"""
Provide the meta model for Asset Administration Shell V3.0 Release Candidate 2.

The following constraints apply to the meta-model in general:

:constraint AASd-120:

    :attr:`Referable.id_short` of non-identifiable referables shall be unique in its
    namespace.

:constraint AASd-003:

    :attr:`Referable.id_short` of :class:`.Referable`'s shall be matched case-sensitive.

We could not implement the following constraints since they depend on registry
and can not be verified without it:

* :constraintref:`AASd-006`
* :constraintref:`AASd-007`

Some of the constraints are not enforceable as they depend on the wider context
such as language understanding, so we could not formalize them:

* :constraintref:`AASd-012`

We could not formalize the constraints which prescribed how to deal with
the default values as these are not really constraints in the strict sense, but more
a guideline on how to resolve default values:

* :constraintref:`AASd-115`
"""

from enum import Enum
from re import match
from typing import List, Optional

from icontract import invariant, DBC, ensure

from aas_core_meta.marker import (
    abstract,
    serialization,
    implementation_specific,
    reference_in_the_book,
    is_superset_of,
    verification,
)

__book_url__ = (
    "https://plattform-i40.coyocloud.com/files/"
    "442df5bf-72e7-4ad4-ade1-4ddee70dd392/4d299251-a723-4858-afe7-9f656af07bcb/"
    "DetailsOfTheAssetAdministrationShell_Part1_"
    "V3%200RC02_EN%20Working%20Version%20docx"
)
__book_version__ = "V3.0RC02"


# region Verification


@verification
def matches_id_short(text: str) -> bool:
    """
    Check that :paramref:`text` is a valid short ID.
    """
    pattern = f"^[a-zA-Z][a-zA-Z0-9_]+$"

    return match(pattern, text) is not None


@verification
def matches_xs_date_time_stamp_utc(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:dateTimeStamp``.

    The time zone must be fixed to UTC. We verify only that the ``text`` matches
    a pre-defined pattern. We *do not* verify that the day of month is
    correct nor do we check for leap seconds.

    See: https://www.w3.org/TR/xmlschema11-2/#dateTimeStamp

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    digit = "[0-9]"
    year_frag = f"-?(([1-9]{digit}{digit}{digit}+)|(0{digit}{digit}{digit}))"
    month_frag = f"((0[1-9])|(1[0-2]))"
    day_frag = f"((0[1-9])|([12]{digit})|(3[01]))"
    hour_frag = f"(([01]{digit})|(2[0-3]))"
    minute_frag = f"[0-5]{digit}"
    second_frag = f"([0-5]{digit})(\\.{digit}+)?"
    end_of_day_frag = "24:00:00(\\.0+)?"
    timezone_frag = "Z"
    date_time_stamp_lexical_rep = (
        f"{year_frag}-{month_frag}-{day_frag}"
        f"T"
        f"(({hour_frag}:{minute_frag}:{second_frag})|{end_of_day_frag})"
        f"{timezone_frag}"
    )
    pattern = f"^{date_time_stamp_lexical_rep}$"

    return match(pattern, text) is not None


# noinspection PyUnusedLocal
@verification
@implementation_specific
def is_xs_date_time_stamp_utc(text: str) -> bool:
    """
    Check that :paramref:`text` is a ``xs:dateTimeStamp`` with time zone set to UTC.

    The ``text`` is assumed to match a pre-defined pattern for ``xs:dateTimeStamp`` with
    the time zone set to UTC. In this function, we check for days of month (e.g.,
    February 29th).

    See: https://www.w3.org/TR/xmlschema11-2/#dateTimeStamp

    :param text: Text to be checked
    :returns: True if the :paramref:`text` is a valid ``xs:dateTimeStamp`` in UTC
    """
    raise NotImplementedError()


@verification
def matches_MIME_type(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of MIME type.

    The definition has been taken from:
    https://www.rfc-editor.org/rfc/rfc7231#section-3.1.1.1,
    https://www.rfc-editor.org/rfc/rfc7230#section-3.2.3 and
    https://www.rfc-editor.org/rfc/rfc7230#section-3.2.6.

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    tchar = "[!#$%&'*+\\-.^_`|~0-9a-zA-Z]"
    token = f"({tchar})+"
    type = f"{token}"
    subtype = f"{token}"
    ows = "[ \t]*"
    obs_text = "[\\x80-\\xff]"
    qd_text = f"([\t !#-\\[\\]-~]|{obs_text})"
    quoted_pair = f"\\\\([\t !-~]|{obs_text})"
    quoted_string = f'"({qd_text}|{quoted_pair})*"'
    parameter = f"{token}=({token}|{quoted_string})"
    media_type = f"^{type}/{subtype}({ows};{ows}{parameter})*$"

    return match(media_type, text) is not None


# noinspection SpellCheckingInspection
@verification
def matches_RFC_8089_path(text: str) -> bool:
    """
    Check that :paramref:`text` is a path conforming to the pattern of RFC 8089.

    The definition has been taken from:
    https://datatracker.ietf.org/doc/html/rfc8089

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern

    """
    h16 = "[0-9A-Fa-f]{1,4}"
    dec_octet = "([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"
    ipv4address = f"{dec_octet}\\.{dec_octet}\\.{dec_octet}\\.{dec_octet}"
    ls32 = f"({h16}:{h16}|{ipv4address})"
    ipv6address = (
        f"(({h16}:){{6}}{ls32}|::({h16}:){{5}}{ls32}|({h16})?::({h16}:){{4}}"
        f"{ls32}|(({h16}:)?{h16})?::({h16}:){{3}}{ls32}|(({h16}:){{2}}{h16})?::"
        f"({h16}:){{2}}{ls32}|(({h16}:){{3}}{h16})?::{h16}:{ls32}|(({h16}:){{4}}"
        f"{h16})?::{ls32}|(({h16}:){{5}}{h16})?::{h16}|(({h16}:){{6}}{h16})?::)"
    )
    unreserved = "[a-zA-Z0-9\\-._~]"
    sub_delims = "[!$&'()*+,;=]"
    ipvfuture = f"[vV][0-9A-Fa-f]+\\.({unreserved}|{sub_delims}|:)+"
    ip_literal = f"\\[({ipv6address}|{ipvfuture})\\]"
    pct_encoded = "%[0-9A-Fa-f][0-9A-Fa-f]"
    reg_name = f"({unreserved}|{pct_encoded}|{sub_delims})*"
    host = f"({ip_literal}|{ipv4address}|{reg_name})"
    file_auth = f"(localhost|{host})"
    pchar = f"({unreserved}|{pct_encoded}|{sub_delims}|[:@])"
    segment_nz = f"({pchar})+"
    segment = f"({pchar})*"
    path_absolute = f"/({segment_nz}(/{segment})*)?"
    auth_path = f"({file_auth})?{path_absolute}"
    local_path = f"{path_absolute}"
    file_hier_part = f"(//{auth_path}|{local_path})"
    file_scheme = "file"
    file_uri = f"{file_scheme}:{file_hier_part}"

    pattern = f"^{file_uri}$"
    return match(pattern, text) is not None


# noinspection SpellCheckingInspection
@verification
def matches_BCP_47(text: str) -> bool:
    """
    Check that :paramref:`text` is a valid BCP 47 language tag.

    See: https://en.wikipedia.org/wiki/IETF_language_tag
    """
    alphanum = "[a-zA-Z0-9]"
    singleton = "[0-9A-WY-Za-wy-z]"
    extension = f"{singleton}(-({alphanum}){{2,8}})+"
    extlang = "[a-zA-Z]{3}(-[a-zA-Z]{3}){2}"
    irregular = (
        "(en-GB-oed|i-ami|i-bnn|i-default|i-enochian|i-hak|"
        "i-klingon|i-lux|i-mingo|i-navajo|i-pwn|i-tao|i-tay|"
        "i-tsu|sgn-BE-FR|sgn-BE-NL|sgn-CH-DE)"
    )
    regular = (
        "(art-lojban|cel-gaulish|no-bok|no-nyn|zh-guoyu|zh-hakka|"
        "zh-min|zh-min-nan|zh-xiang)"
    )
    grandfathered = f"({irregular}|{regular})"
    language = f"([a-zA-Z]{{2,3}}(-{extlang})?|[a-zA-Z]{{4}}|[a-zA-Z]{{5,8}})"
    script = "[a-zA-Z]{4}"
    region = "([a-zA-Z]{2}|[0-9]{3})"
    variant = f"(({alphanum}){{5,8}}|[0-9]({alphanum}){{3}})"
    privateuse = f"[xX](-({alphanum}){{1,8}})+"
    langtag = (
        f"{language}(-{script})?(-{region})?(-{variant})*(-{extension})*(-"
        f"{privateuse})?"
    )
    language_tag = f"({langtag}|{privateuse}|{grandfathered})"

    pattern = f"^{language_tag}$"
    return match(pattern, text) is not None


@verification
@implementation_specific
def lang_strings_have_unique_languages(lang_strings: List["Lang_string"]) -> bool:
    """
    Check that the :paramref:`lang_strings` do not have overlapping
    :attr:`~Lang_string.language`'s
    """
    # NOTE (mristin, 2022-04-7):
    # This implementation will not be transpiled, but is given here as reference.
    language_set = set()
    for lang_string in lang_strings:
        if lang_string.language in language_set:
            return False
        language_set.add(lang_string.language)

    return True


@verification
@implementation_specific
def qualifier_types_are_unique(qualifiers: List["Qualifier"]) -> bool:
    """
    Check that :attr:`~Qualifier.type`'s of :paramref:`qualifiers` are unique.

    :param qualifiers: to be checked
    :return: True if all :attr:`~Qualifier.type`'s are unique
    """
    # NOTE (mristin, 2022-04-1):
    # This implementation is given here only as reference. It needs to be adapted
    # for each implementation separately.
    observed_types = set()
    for qualifier in qualifiers:
        if qualifier.type in observed_types:
            return False

        observed_types.add(qualifier.type)

    return True


# noinspection SpellCheckingInspection
@verification
def matches_xs_any_URI(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:anyURI``.

    See: https://www.w3.org/TR/xmlschema11-2/#anyURI and
    https://datatracker.ietf.org/doc/html/rfc3987

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    scheme = "[a-zA-Z][a-zA-Z0-9+\\-.]*"
    ucschar = (
        "[\\xa0-\\ud7ff\\uf900-\\ufdcf\\ufdf0-\\uffef\\u10000-\\u1fffd"
        "\\u20000-\\u2fffd\\u30000-\\u3fffd\\u40000-\\u4fffd"
        "\\u50000-\\u5fffd\\u60000-\\u6fffd\\u70000-\\u7fffd"
        "\\u80000-\\u8fffd\\u90000-\\u9fffd\\ua0000-\\uafffd"
        "\\ub0000-\\ubfffd\\uc0000-\\ucfffd\\ud0000-\\udfffd"
        "\\ue1000-\\uefffd]"
    )
    iunreserved = f"([a-zA-Z0-9\\-._~]|{ucschar})"
    pct_encoded = "%[0-9A-Fa-f][0-9A-Fa-f]"
    sub_delims = "[!$&'()*+,;=]"
    iuserinfo = f"({iunreserved}|{pct_encoded}|{sub_delims}|:)*"
    h16 = "[0-9A-Fa-f]{1,4}"
    dec_octet = "([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"
    ipv4address = f"{dec_octet}\\.{dec_octet}\\.{dec_octet}\\.{dec_octet}"
    ls32 = f"({h16}:{h16}|{ipv4address})"
    ipv6address = (
        f"(({h16}:){{6}}{ls32}|::({h16}:){{5}}{ls32}|({h16})?::({h16}:){{4}}"
        f"{ls32}|(({h16}:)?{h16})?::({h16}:){{3}}{ls32}|(({h16}:){{2}}{h16})?::"
        f"({h16}:){{2}}{ls32}|(({h16}:){{3}}{h16})?::{h16}:{ls32}|(({h16}:){{4}}"
        f"{h16})?::{ls32}|(({h16}:){{5}}{h16})?::{h16}|(({h16}:){{6}}{h16})?::)"
    )
    unreserved = "[a-zA-Z0-9\\-._~]"
    ipvfuture = f"[vV][0-9A-Fa-f]+\\.({unreserved}|{sub_delims}|:)+"
    ip_literal = f"\\[({ipv6address}|{ipvfuture})\\]"
    ireg_name = f"({iunreserved}|{pct_encoded}|{sub_delims})*"
    ihost = f"({ip_literal}|{ipv4address}|{ireg_name})"
    port = "[0-9]*"
    iauthority = f"({iuserinfo}@)?{ihost}(:{port})?"
    ipchar = f"({iunreserved}|{pct_encoded}|{sub_delims}|[:@])"
    isegment = f"({ipchar})*"
    ipath_abempty = f"(/{isegment})*"
    isegment_nz = f"({ipchar})+"
    ipath_absolute = f"/({isegment_nz}(/{isegment})*)?"
    ipath_rootless = f"{isegment_nz}(/{isegment})*"
    ipath_empty = f"({ipchar}){{0}}"
    ihier_part = (
        f"(//{iauthority}{ipath_abempty}|{ipath_absolute}|"
        f"{ipath_rootless}|{ipath_empty})"
    )
    iprivate = "[\\ue000-\\uf8ff\\uf0000-\\uffffd\\u100000-\\u10fffd]"
    iquery = f"({ipchar}|{iprivate}|[/?])*"
    ifragment = f"({ipchar}|[/?])*"
    isegment_nz_nc = f"({iunreserved}|{pct_encoded}|{sub_delims}|@)+"
    ipath_noscheme = f"{isegment_nz_nc}(/{isegment})*"
    irelative_part = (
        f"(//{iauthority}{ipath_abempty}|{ipath_absolute}|"
        f"{ipath_noscheme}|{ipath_empty})"
    )
    irelative_ref = f"{irelative_part}(\\?{iquery})?(\\#{ifragment})?"
    iri = f"{scheme}:{ihier_part}(\\?{iquery})?(\\#{ifragment})?"
    iri_reference = f"({iri}|{irelative_ref})"

    pattern = f"^{iri_reference}$"
    return match(pattern, text) is not None


# noinspection SpellCheckingInspection
@verification
def matches_xs_base_64_binary(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:base64Binary``.

    See: https://www.w3.org/TR/xmlschema11-2/#base64Binary

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # Base64 characters whose bit-string value ends in '0000'
    b04_char = "[AQgw]"
    b04 = f"{b04_char}\\x20?"

    # Base64 characters whose bit-string value ends in '00'
    b16_char = "[AEIMQUYcgkosw048]"
    b16 = f"{b16_char}\\x20?"

    b64_char = "[A-Za-z0-9+/]"
    b64 = f"{b64_char}\\x20?"

    b64quad = f"({b64}{b64}{b64}{b64})"

    # b64_final_quad represents three octets of binary data without trailing space.
    b64_final_quad = f"({b64}{b64}{b64}{b64_char})"

    # padded_8 represents a single octet at the end of the data.
    padded_8 = f"{b64}{b04}=\x20?="

    # padded_16 represents a two-octet at the end of the data.
    padded_16 = f"{b64}{b64}{b16}="

    b64final = f"({b64_final_quad}|{padded_16}|{padded_8})"

    base64_binary = f"({b64quad}*{b64final})?"

    pattern = f"^{base64_binary}$"
    return match(pattern, text) is not None


@verification
def matches_xs_boolean(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:boolean``.

    See: https://www.w3.org/TR/xmlschema11-2/#boolean

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    pattern = "^(true|false|1|0)$"
    return match(pattern, text) is not None


@verification
def matches_xs_date(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:date``.

    See: https://www.w3.org/TR/xmlschema11-2/#date

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    digit = "[0-9]"
    year_frag = f"-?(([1-9]{digit}{digit}{digit}+)|(0{digit}{digit}{digit}))"
    month_frag = f"((0[1-9])|(1[0-2]))"
    day_frag = f"((0[1-9])|([12]{digit})|(3[01]))"
    minute_frag = f"[0-5]{digit}"
    timezone_frag = rf"(Z|(\+|-)(0{digit}|1[0-3]):{minute_frag}|14:00)"
    date_lexical_rep = f"{year_frag}-{month_frag}-{day_frag}{timezone_frag}?"

    pattern = f"^{date_lexical_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_date_time(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:dateTime``.

    See: https://www.w3.org/TR/xmlschema11-2/#dateTime

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    digit = "[0-9]"
    year_frag = f"-?(([1-9]{digit}{digit}{digit}+)|(0{digit}{digit}{digit}))"
    month_frag = f"((0[1-9])|(1[0-2]))"
    day_frag = f"((0[1-9])|([12]{digit})|(3[01]))"
    hour_frag = f"(([01]{digit})|(2[0-3]))"
    minute_frag = f"[0-5]{digit}"
    second_frag = f"([0-5]{digit})(\\.{digit}+)?"
    end_of_day_frag = "24:00:00(\\.0+)?"
    timezone_frag = rf"(Z|(\+|-)(0{digit}|1[0-3]):{minute_frag}|14:00)"
    date_time_lexical_rep = (
        f"{year_frag}-{month_frag}-{day_frag}"
        f"T"
        f"(({hour_frag}:{minute_frag}:{second_frag})|{end_of_day_frag})"
        f"{timezone_frag}?"
    )

    pattern = f"^{date_time_lexical_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_date_time_stamp(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:dateTimeStamp``.

    See: https://www.w3.org/TR/xmlschema11-2/#dateTimeStamp

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    digit = "[0-9]"
    year_frag = f"-?(([1-9]{digit}{digit}{digit}+)|(0{digit}{digit}{digit}))"
    month_frag = f"((0[1-9])|(1[0-2]))"
    day_frag = f"((0[1-9])|([12]{digit})|(3[01]))"
    hour_frag = f"(([01]{digit})|(2[0-3]))"
    minute_frag = f"[0-5]{digit}"
    second_frag = f"([0-5]{digit})(\\.{digit}+)?"
    end_of_day_frag = "24:00:00(\\.0+)?"
    timezone_frag = rf"(Z|(\+|-)(0{digit}|1[0-3]):{minute_frag}|14:00)"
    date_time_stamp_lexical_rep = (
        f"{year_frag}-{month_frag}-{day_frag}"
        f"T"
        f"(({hour_frag}:{minute_frag}:{second_frag})|{end_of_day_frag})"
        f"{timezone_frag}"
    )

    pattern = f"^{date_time_stamp_lexical_rep}$"
    return match(pattern, text) is not None


# noinspection SpellCheckingInspection
@verification
def matches_xs_decimal(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:decimal``.

    See: https://www.w3.org/TR/xmlschema11-2/#decimal

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    digit = "[0-9]"
    unsigned_no_decimal_pt_numeral = f"{digit}+"
    no_decimal_pt_numeral = rf"(\+|-)?{unsigned_no_decimal_pt_numeral}"
    frac_frag = f"{digit}+"
    unsigned_decimal_pt_numeral = (
        rf"({unsigned_no_decimal_pt_numeral}\.{frac_frag}|\.{frac_frag})"
    )
    decimal_pt_numeral = rf"(\+|-)?{unsigned_decimal_pt_numeral}"
    decimal_lexical_rep = f"({decimal_pt_numeral}|{no_decimal_pt_numeral})"

    pattern = f"^{decimal_lexical_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_double(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:double``.

    See: https://www.w3.org/TR/xmlschema11-2/#double

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin, 2022-04-6):
    # See: https://www.w3.org/TR/xmlschema11-2/#nt-doubleRep
    double_rep = (
        r"(\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([Ee](\+|-)?[0-9]+)?|(\+|-)?INF|NaN"
    )

    pattern = f"^{double_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_duration(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:duration``.

    See: https://www.w3.org/TR/xmlschema11-2/#duration

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin, 2022-04-6):
    # See https://www.w3.org/TR/xmlschema11-2/#nt-durationRep

    # fmt: off
    duration_rep = (
r"-?P((([0-9]+Y([0-9]+M)?([0-9]+D)?"
      r"|([0-9]+M)([0-9]+D)?"
      r"|([0-9]+D)"
      r")"
      r"(T(([0-9]+H)([0-9]+M)?([0-9]+(\.[0-9]+)?S)?"
         r"|([0-9]+M)([0-9]+(\.[0-9]+)?S)?"
         r"|([0-9]+(\.[0-9]+)?S)"
         r")"
      r")?"
   r")"
 r"|(T(([0-9]+H)([0-9]+M)?([0-9]+(\.[0-9]+)?S)?"
      r"|([0-9]+M)([0-9]+(\.[0-9]+)?S)?"
      r"|([0-9]+(\.[0-9]+)?S)"
      r")"
   r")"
 r")"
    )
    # fmt: on

    pattern = f"^{duration_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_float(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:float``.

    See: https://www.w3.org/TR/xmlschema11-2/#float

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    float_rep = (
        r"(\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([Ee](\+|-)?[0-9]+)?" r"|(\+|-)?INF|NaN"
    )

    pattern = f"^{float_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_g_day(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:gDay``.

    See: https://www.w3.org/TR/xmlschema11-2/#gDay

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin, 2022-04-6):
    # See https://www.w3.org/TR/xmlschema11-2/#nt-gDayRep
    g_day_lexical_rep = (
        r"---(0[1-9]|[12][0-9]|3[01])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    )

    pattern = f"^{g_day_lexical_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_g_month(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:gMonth``.

    See: https://www.w3.org/TR/xmlschema11-2/#gMonth

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin, 2022-04-6):
    # See https://www.w3.org/TR/xmlschema11-2/#nt-gMonthRep
    g_month_lexical_rep = (
        r"--(0[1-9]|1[0-2])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    )

    pattern = f"^{g_month_lexical_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_g_month_day(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:gMonthDay``.

    See: https://www.w3.org/TR/xmlschema11-2/#gMonthDay

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin, 2022-04-6):
    # See https://www.w3.org/TR/xmlschema11-2/#nt-gMonthDayRep
    g_month_day_rep = (
        r"--(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])"
        r"(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    )

    pattern = f"^{g_month_day_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_g_year(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:gYear``.

    See: https://www.w3.org/TR/xmlschema11-2/#gYear

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin, 2022-04-6):
    # See https://www.w3.org/TR/xmlschema11-2/#nt-gYearRep
    g_year_rep = (
        r"-?([1-9][0-9]{3,}|0[0-9]{3})(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    )

    pattern = f"^{g_year_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_g_year_month(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:gYearMonth``.

    See: https://www.w3.org/TR/xmlschema11-2/#gYearMonth

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin, 2022-04-6):
    # See https://www.w3.org/TR/xmlschema11-2/#nt-gYearMonthRep

    g_year_month_rep = (
        r"-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])"
        r"(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    )

    pattern = f"^{g_year_month_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_hex_binary(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:hexBinary``.

    See: https://www.w3.org/TR/xmlschema11-2/#hexBinary

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin, 2022-04-6):
    # See https://www.w3.org/TR/xmlschema11-2/#nt-hexBinary
    hex_binary = r"([0-9a-fA-F]{2})*"

    pattern = f"^{hex_binary}$"
    return match(pattern, text) is not None


@verification
def matches_xs_time(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:time``.

    See: https://www.w3.org/TR/xmlschema11-2/#time

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin, 2022-04-6):
    # See https://www.w3.org/TR/xmlschema11-2/#nt-timeRep
    time_rep = (
        r"(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))"
        r"(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    )

    pattern = f"^{time_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_day_time_duration(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:dayTimeDuration``.

    See: https://www.w3.org/TR/xmlschema11-2/#dayTimeDuration

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin, 2022-04-6):
    # See https://www.w3.org/TR/xmlschema11-2/#nt-durationRep and
    # https://www.w3.org/TR/xmlschema11-2/#dayTimeDuration related to pattern
    # intersection

    # fmt: off
    day_time_duration_rep = (
        r"-?P(("
        r"([0-9]+D)"
        r"(T(([0-9]+H)([0-9]+M)?([0-9]+(\.[0-9]+)?S)?"
        r"|([0-9]+M)([0-9]+(\.[0-9]+)?S)?"
        r"|([0-9]+(\.[0-9]+)?S)"
        r")"
        r")?"
        r")"
        r"|(T(([0-9]+H)([0-9]+M)?([0-9]+(\.[0-9]+)?S)?"
        r"|([0-9]+M)([0-9]+(\.[0-9]+)?S)?"
        r"|([0-9]+(\.[0-9]+)?S)"
        r")"
        r")"
        r")"
    )
    # fmt: on

    pattern = f"^{day_time_duration_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_year_month_duration(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:yearMonthDuration``.

    See: https://www.w3.org/TR/xmlschema11-2/#yearMonthDuration

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    year_month_duration_rep = r"-?P((([0-9]+Y)([0-9]+M)?)|([0-9]+M))"

    pattern = f"^{year_month_duration_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_integer(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:integer``.

    See: https://www.w3.org/TR/xmlschema11-2/#integer

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    integer_rep = r"[\-+]?[0-9]+"

    pattern = f"^{integer_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_long(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:long``.

    See: https://www.w3.org/TR/xmlschema11-2/#long

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    long_rep = r"[\-+]?0*[0-9]{1,20}"

    pattern = f"^{long_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_int(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:int``.

    See: https://www.w3.org/TR/xmlschema11-2/#int

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    int_rep = r"[\-+]?0*[0-9]{1,10}"

    pattern = f"^{int_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_short(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:short``.

    See: https://www.w3.org/TR/xmlschema11-2/#short

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    short_rep = r"[\-+]?0*[0-9]{1,5}"

    pattern = f"^{short_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_byte(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:byte``.

    See: https://www.w3.org/TR/xmlschema11-2/#byte

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    byte_rep = r"[\-+]?0*[0-9]{1,3}"

    pattern = f"^{byte_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_non_negative_integer(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:nonNegativeInteger``.

    See: https://www.w3.org/TR/xmlschema11-2/#nonNegativeInteger

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    non_negative_integer_rep = r"(-0|\+?[0-9]+)"

    pattern = f"^{non_negative_integer_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_positive_integer(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:positiveInteger``.

    See: https://www.w3.org/TR/xmlschema11-2/#positiveInteger

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    positive_integer_rep = r"\+?0*[1-9][0-9]*"

    pattern = f"^{positive_integer_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_unsigned_long(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:unsignedLong``.

    See: https://www.w3.org/TR/xmlschema11-2/#unsignedLong

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    unsigned_long_rep = r"(-0|\+?0*[0-9]{1,20})"

    pattern = f"^{unsigned_long_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_unsigned_int(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:unsignedInt``.

    See: https://www.w3.org/TR/xmlschema11-2/#unsignedInt

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    unsigned_int_rep = r"(-0|\+?0*[0-9]{1,10})"

    pattern = f"^{unsigned_int_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_unsigned_short(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:unsignedShort``.

    See: https://www.w3.org/TR/xmlschema11-2/#unsignedShort

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    unsigned_short_rep = r"(-0|\+?0*[0-9]{1,5})"

    pattern = f"^{unsigned_short_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_unsigned_byte(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:unsignedByte``.

    See: https://www.w3.org/TR/xmlschema11-2/#unsignedByte

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    unsigned_byte_rep = r"(-0|\+?0*[0-9]{1,3})"

    pattern = f"^{unsigned_byte_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_non_positive_integer(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:nonPositiveInteger``.

    See: https://www.w3.org/TR/xmlschema11-2/#nonPositiveInteger

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    non_positive_integer_rep = r"(\+0|0|-[0-9]+)"

    pattern = f"^{non_positive_integer_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_negative_integer(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:negativeInteger``.

    See: https://www.w3.org/TR/xmlschema11-2/#negativeInteger

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    negative_integer_rep = r"(-0*[1-9][0-9]*)"

    pattern = f"^{negative_integer_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_string(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:string``.

    See: https://www.w3.org/TR/xmlschema11-2/#string

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # From: https://www.w3.org/TR/xml11/#NT-Char
    # Any Unicode character, excluding the surrogate blocks, FFFE, and FFFF.
    pattern = r"^[^\x00]*$"
    return match(pattern, text) is not None


# noinspection PyUnusedLocal
@verification
@implementation_specific
def value_consistent_with_xsd_type(value: str, value_type: "Data_type_def_XSD") -> bool:
    """
    Check that the :paramref:`value` conforms to its :paramref:`value_type`.

    :param value: which needs to conform
    :param value_type: pre-defined value type
    :return: True if the :paramref:`value` conforms
    """
    # NOTE (mristin, 2022-04-1):
    # We specify the pattern-matching functions above, and they should be handy to check
    # for most obvious pattern mismatches.
    #
    # However, bear in mind that the pattern checks are not enough! For example,
    # consider a ``xs:dateTimeStamp``. You need to check not only that the value
    # follows the pattern, but also that the day-of-month and leap seconds are taken
    # into account.


@verification
@implementation_specific
def is_model_reference_to(reference: "Reference", expected_type: "Key_types") -> bool:
    """Check that the target of the model reference matches the expected ``target``."""
    # NOTE (mristin, 2022-03-28):
    # This implementation is given here only as reference. It needs to be adapted
    # for each implementation separately.
    return reference.type == Reference_types.Model_reference and (
        len(reference.keys) != 0 or reference.keys[-1].type == expected_type
    )


@verification
@implementation_specific
def id_shorts_are_unique(referables: List["Referable"]) -> bool:
    """
    Check that the :attr:`~Referable.id_short`'s among the :paramref:`referables` are
    unique.
    """
    # NOTE (mristin, 2022-04-7):
    # This implementation will not be transpiled, but is given here as reference.
    id_short_set = set()
    for referable in referables:
        if referable.id_short is not None:
            if referable.id_short in id_short_set:
                return False

            id_short_set.add(referable.id_short)

    return True


@verification
@implementation_specific
def extension_names_are_unique(extensions: List["Extension"]) -> bool:
    """Check that the extension names are unique."""
    # NOTE (mristin, 2022-04-7):
    # This implementation will not be transpiled, but is given here as reference.
    name_set = set()
    for extension in extensions:
        if extension.name in name_set:
            return False
        name_set.add(extension.name)

    return True


@verification
@implementation_specific
def submodel_elements_have_identical_semantic_ids(
    elements: List["Submodel_element"],
) -> bool:
    """Check that all semantic IDs are identical, if specified."""
    # NOTE (mristin, 2022-04-7):
    # This implementation will not be transpiled, but is given here as a reference.
    semantic_id = None
    for element in elements:
        if element.semantic_id is not None:
            if semantic_id is None:
                semantic_id = element.semantic_id
            else:
                if semantic_id != element.semantic_id:
                    return False
    return True


# noinspection PyUnusedLocal
@verification
@implementation_specific
def submodel_element_is_of_type(
    element: "Submodel_element", element_type: "AAS_submodel_elements"
) -> bool:
    """
    Check that the run-time type of the :paramref:`element` coincides with
    :paramref:`element_type`.
    """
    raise NotImplementedError()


@verification
@implementation_specific
def properties_or_ranges_have_value_type(
    elements: List["Submodel_element"], value_type: "Data_type_def_XSD"
) -> bool:
    """Check that all the :paramref:`elements` have the :paramref:`value_type`."""
    # NOTE (mristin, 2022-04-7):
    # This implementation will not be transpiled, but is given here as reference.
    for element in elements:
        if isinstance(element, (Property, Range)):
            if element.value_type != value_type:
                return False

    return True


@verification
@implementation_specific
def concept_description_category_is_valid(category: str) -> bool:
    """
    Check that the :paramref:`category` is a valid category for
    a :class:`.Concept_description`.
    """
    # NOTE (mristin, 2022-04-7):
    # This implementation will not be transpiled, but is given here as reference.
    # Notably, the specific implementation should use a hash set or a trie for efficient
    # lookups.
    return category in (
        "VALUE",
        "PROPERTY",
        "REFERENCE",
        "DOCUMENT",
        "CAPABILITY",
        "RELATIONSHIP",
        "COLLECTION",
        "FUNCTION",
        "EVENT",
        "ENTITY",
        "APPLICATION_CLASS",
        "QUALIFIER",
        "VIEW",
    )


# endregion


@invariant(lambda self: len(self) >= 1)
class Non_empty_string(str, DBC):
    """Represent a string with at least one character."""


@invariant(lambda self: is_xs_date_time_stamp_utc(self))
@invariant(lambda self: matches_xs_date_time_stamp_utc(self))
class Date_time_stamp_UTC(str, DBC):
    """Represent an ``xs:dateTimeStamp`` with the time zone fixed to UTC."""


@reference_in_the_book(section=(5, 7, 12, 2))
class Blob_type(bytearray, DBC):
    """Group of bytes to represent file content (binaries and non-binaries)"""


@reference_in_the_book(section=(5, 7, 12, 2))
class Identifier(Non_empty_string, DBC):
    """
    string
    """


# noinspection SpellCheckingInspection
@invariant(lambda self: matches_BCP_47(self))
class BCP_47_language_tag(str, DBC):
    """
    Represent a language tag conformant to BCP 47.

    See: https://en.wikipedia.org/wiki/IETF_language_tag
    """


@reference_in_the_book(section=(5, 7, 12, 2))
@invariant(lambda self: matches_MIME_type(self))
class Content_type(Non_empty_string, DBC):
    """
    string

    .. note::

        Any content type as in RFC2046.

    A media type (also MIME type and content type) […] is a two-part
    identifier for file formats and format contents transmitted on
    the Internet. The Internet Assigned Numbers Authority (IANA) is
    the official authority for the standardization and publication of
    these classifications. Media types were originally defined in
    Request for Comments 2045 in November 1996 as a part of MIME
    (Multipurpose Internet Mail Extensions) specification, for denoting
    type of email message content and attachments.
    """


@invariant(lambda self: matches_RFC_8089_path(self))
@reference_in_the_book(section=(5, 7, 12, 2))
class Path_type(Non_empty_string, DBC):
    """
    string

    .. note::

        Any string conformant to RFC8089 , the “file” URI scheme (for
        relative and absolute file paths)
    """

    pass


@reference_in_the_book(section=(5, 7, 12, 2))
class Qualifier_type(Non_empty_string, DBC):
    """
    string
    """


class Value_data_type(str, DBC):
    """
    any xsd atomic type as specified via :class:`.Data_type_def_XSD`
    """


@invariant(
    lambda self: matches_id_short(self),
    "ID-short of Referables shall only feature letters, digits, underscore (``_``); "
    "starting mandatory with a letter. *I.e.* ``[a-zA-Z][a-zA-Z0-9_]+``.",
)
@invariant(
    lambda self: not (self.id_short is not None) or len(self.id_short) <= 128,
    "Constraint AASd-027: ID-short shall have a maximum length of 128 characters.",
)
class Id_short(str, DBC):
    """
    Represent a short ID of an :class:`.Referable`.

    :constraint AASd-002:

        ID-short of :class:`.Referable`'s shall only feature letters, digits,
        underscore (``_``); starting mandatory with a letter.
        *I.e.* ``[a-zA-Z][a-zA-Z0-9_]+``.

    :constraint AASd-027:

        ID-short of :class:`.Referable`'s shall have a maximum length
        of 128 characters.
    """


@abstract
# fmt: off
@invariant(
    lambda self:
    not (self.supplemental_semantic_ids is not None)
    or (
        self.semantic_id is not None
    ),
    "Constraint AASd-118: If there are supplemental semantic IDs defined "
    "then there shall be also a main semantic ID."
)
# fmt: on
@reference_in_the_book(section=(5, 7, 2, 6))
class Has_semantics(DBC):
    """
    Element that can have a semantic definition plus some supplemental semantic
    definitions.

    :constraint AASd-118:

        If there are ID :attr:`~Has_semantics.supplemental_semantic_ids` defined
        then there shall be also a main semantic ID :attr:`~Has_semantics.semantic_id`.
    """

    semantic_id: Optional["Reference"]
    """
    Identifier of the semantic definition of the element. It is called semantic ID
    of the element or also main semantic ID of the element.
    
    .. note::
    
        It is recommended to use a global reference.
    """

    supplemental_semantic_ids: Optional[List["Reference"]]
    """
    Identifier of a supplemental semantic definition of the element. 
    It is called supplemental semantic ID of the element.
    
    .. note::
    
        It is recommended to use a global reference.
    """

    def __init__(
        self,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
    ) -> None:
        self.semantic_id = semantic_id
        self.supplemental_semantic_ids = supplemental_semantic_ids


@reference_in_the_book(section=(5, 7, 2, 1), index=1)
class Extension(Has_semantics):
    """
    Single extension of an element.
    """

    name: Non_empty_string
    """
    Name of the extension.

    :constraint AASd-077:

        The name of an extension within :class:`.Has_extensions` needs to be unique.
    """

    value_type: Optional["Data_type_def_XSD"]
    """
    Type of the value of the extension.

    Default: :attr:`~Data_type_def_XSD.String`
    """

    @implementation_specific
    def value_type_or_default(self) -> "Data_type_def_XSD":
        # NOTE (mristin, 2022-04-7):
        # This implementation will not be transpiled, but is given here as reference.
        return (
            self.value_type if self.value_type is not None else Data_type_def_XSD.String
        )

    value: Optional["Value_data_type"]
    """
    Value of the extension
    """

    refers_to: Optional["Reference"]
    """
    Reference to an element the extension refers to.
    """

    def __init__(
        self,
        name: Non_empty_string,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        value_type: Optional["Data_type_def_XSD"] = None,
        value: Optional["Value_data_type"] = None,
        refers_to: Optional["Reference"] = None,
    ) -> None:
        Has_semantics.__init__(
            self,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
        )

        self.name = name
        self.value_type = value_type
        self.value = value
        self.refers_to = refers_to


# fmt: off
@abstract
@reference_in_the_book(section=(5, 7, 2, 1))
@invariant(
    lambda self:
    not (self.extensions is not None) or extension_names_are_unique(self.extensions),
    "Constraint AASd-077: The name of an extension within Has-Extensions "
    "needs to be unique."
)
# fmt: on
class Has_extensions(DBC):
    """
    Element that can be extended by proprietary extensions.

    .. note::

        Extensions are proprietary, i.e. they do not support global interoperability.
    """

    extensions: Optional[List["Extension"]]
    """
    An extension of the element.
    """

    def __init__(self, extensions: Optional[List["Extension"]] = None) -> None:
        self.extensions = extensions


# fmt: off
@abstract
@reference_in_the_book(section=(5, 7, 2, 2))
@serialization(with_model_type=True)
# fmt: on
class Referable(Has_extensions):
    """
    An element that is referable by its :attr:`~id_short`.

    This ID is not globally unique.
    This ID is unique within the name space of the element.
    """

    category: Optional[Non_empty_string]
    """
    The category is a value that gives further meta information
    w.r.t. to the class of the element.
    It affects the expected existence of attributes and the applicability of
    constraints.

    .. note::

        The category is not identical to the semantic definition
        (:class:`.Has_semantics`) of an element. The category e.g. could denote that
        the element is a measurement value whereas the semantic definition of
        the element would denote that it is the measured temperature.
    """

    id_short: Optional[Id_short]
    """
    In case of identifiables this attribute is a short name of the element.
    In case of referable this ID is an identifying string of the element within
    its name space.

    .. note::

        In case the element is a property and the property has a semantic definition
        (:attr:`~Has_semantics.semantic_id`) conformant to IEC61360
        the :attr:`~id_short` is typically identical to the short name in English.
    """

    display_name: Optional["Lang_string_set"]
    """
    Display name. Can be provided in several languages.

    If no display name is defined in the language requested by the application,
    then the display name is selected in the following order if available:

    * the preferred name in the requested language of the concept description defining
      the semantics of the element
    * If there is a default language list defined in the application,
      then the corresponding preferred name in the language is chosen
      according to this order.
    * the English preferred name of the concept description defining
      the semantics of the element
    * the short name of the concept description
    * the :attr:`~id_short` of the element
    """

    description: Optional["Lang_string_set"]
    """
    Description or comments on the element.

    The description can be provided in several languages.

    If no description is defined, then the definition of the concept
    description that defines the semantics of the element is used.

    Additional information can be provided, e.g., if the element is
    qualified and which qualifier types can be expected in which
    context or which additional data specification templates are
    provided.
    """

    checksum: Optional["Non_empty_string"]
    """
    Checksum to be used to determine if an Referable (including its
    aggregated child elements) has changed.

    The checksum is calculated by the user's tool environment.
    The checksum has no semantic meaning for an asset administration
    shell model and there is no requirement for asset administration
    shell tools to manage the checksum

    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
    ) -> None:
        Has_extensions.__init__(self, extensions=extensions)

        self.id_short = id_short
        self.display_name = display_name
        self.category = category
        self.description = description
        self.checksum = checksum


@abstract
@reference_in_the_book(section=(5, 7, 2, 3))
class Identifiable(Referable):
    """An element that has a globally unique identifier."""

    administration: Optional["Administrative_information"]
    """
    Administrative information of an identifiable element.

    .. note::

        Some of the administrative information like the version number might need to
        be part of the identification.
    """

    id: "Identifier"
    """The globally unique identification of the element."""

    def __init__(
        self,
        id: "Identifier",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        administration: Optional["Administrative_information"] = None,
    ) -> None:
        Referable.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
        )

        self.id = id
        self.administration = administration


@reference_in_the_book(section=(5, 7, 2, 4), index=1)
class Modeling_kind(Enum):
    """Enumeration for denoting whether an element is a template or an instance."""

    Template = "Template"
    """
    Software element which specifies the common attributes shared by all instances of
    the template.

    [SOURCE: IEC TR 62390:2005-01, 3.1.25] modified
    """

    Instance = "Instance"
    """
    Concrete, clearly identifiable component of a certain template.

    .. note::

        It becomes an individual entity of a  template,  for example a
        device model, by defining specific property values.

    .. note::

        In an object oriented view,  an instance denotes an object of a
        template (class).

    [SOURCE: IEC 62890:2016, 3.1.16 65/617/CDV]  modified
    """


@abstract
@reference_in_the_book(section=(5, 7, 2, 4))
class Has_kind(DBC):
    """
    An element with a kind is an element that can either represent a template or an
    instance.

    Default for an element is that it is representing an instance.
    """

    kind: Optional["Modeling_kind"]
    """
    Kind of the element: either type or instance.

    Default: :attr:`~Modeling_kind.Instance`
    """

    @implementation_specific
    def kind_or_default(self) -> "Modeling_kind":
        # NOTE (mristin, 2022-04-7):
        # This implementation will not be transpiled, but is given here as reference.
        return self.kind if self.kind is not None else Modeling_kind.Instance

    def __init__(self, kind: Optional["Modeling_kind"] = None) -> None:
        self.kind = kind


@abstract
@reference_in_the_book(section=(5, 7, 2, 9))
class Has_data_specification(DBC):
    """
    Element that can be extended by using data specification templates.

    A data specification template defines a named set of additional attributes an
    element may or shall have. The data specifications used are explicitly specified
    with their global ID.
    """

    data_specifications: Optional[List["Reference"]]
    """
    Global reference to the data specification template used by the element.
    
    .. note::
    
        This is a global reference.
    """

    def __init__(self, data_specifications: Optional[List["Reference"]] = None) -> None:
        self.data_specifications = data_specifications


# fmt: off
@invariant(
    lambda self:
    not (self.revision is not None) or self.version is not None,
    "Constraint AASd-005: If version is not specified then also revision shall "
    "be unspecified. This means, a revision requires a version. If there is "
    "no version there is no revision either. Revision is optional."
)
@reference_in_the_book(section=(5, 7, 2, 5))
# fmt: on
class Administrative_information(Has_data_specification):
    """
    Administrative meta-information for an element like version
    information.

    :constraint AASd-005:

        If :attr:`~version` is not specified then also :attr:`~revision` shall be
        unspecified. This means, a revision requires a version. If there is no version
        there is no revision neither. Revision is optional.
    """

    version: Optional[Non_empty_string]
    """Version of the element."""

    revision: Optional[Non_empty_string]
    """Revision of the element."""

    def __init__(
        self,
        data_specifications: Optional[List["Reference"]] = None,
        version: Optional[Non_empty_string] = None,
        revision: Optional[Non_empty_string] = None,
    ) -> None:
        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.version = version
        self.revision = revision


# fmt: off
@abstract
@invariant(
    lambda self:
    not (self.qualifiers is not None)
    or qualifier_types_are_unique(self.qualifiers),
    "Constraint AASd-021: Every qualifiable can only have one qualifier with "
    "the same type."
)
@reference_in_the_book(section=(5, 7, 2, 7))
@serialization(with_model_type=True)
# fmt: on
class Qualifiable(DBC):
    """
    The value of a qualifiable element may be further qualified by one or more
    qualifiers.

    :constraint AASd-119:

        If any :attr:`~Qualifier.kind` value of :attr:`~Qualifiable.qualifiers` is
        equal to :attr:`~Qualifier_kind.Template_qualifier` and the qualified element
        inherits from :class:`.Has_kind` then the qualified element shell be of
        kind Template (:attr:`Has_kind.kind` = :attr:`Modeling_kind.Template`).
    """

    qualifiers: Optional[List["Qualifier"]]
    """
    Additional qualification of a qualifiable element.

    :constraint AASd-021:

        Every qualifiable can only have one qualifier with the same
        :attr:`~Qualifier.type`.
    """

    def __init__(self, qualifiers: Optional[List["Qualifier"]] = None) -> None:
        self.qualifiers = qualifiers


@reference_in_the_book(section=(5, 7, 2, 8), index=1)
class Qualifier_kind(Enum):
    """
    Enumeration for kinds of qualifiers.
    """

    Value_qualifier = "ValueQualifier"
    """
    qualifies the value of the element and can change during run-time.
    
    Value qualifiers are only applicable to elements with kind
    :attr:`~Modeling_kind.Instance`.
    """

    Concept_qualifier = "ConceptQualifier"
    """
    qualifies the semantic definition the element is referring to
    (:attr:`~Has_semantics.semantic_id`)
    """

    Template_qualifier = "TemplateQualifier"
    """
    qualifies the elements within a specific submodel on concept level.
    
    Template qualifiers are only applicable to elements with kind
    :attr:`~Modeling_kind.Template`.
    """


@invariant(
    lambda self: not (self.value is not None)
    or value_consistent_with_xsd_type(self.value, self.value_type),
    "Constraint AASd-020: The value shall be consistent to the data type as defined "
    "in value type.",
)
@reference_in_the_book(section=(5, 7, 2, 8))
@serialization(with_model_type=True)
# fmt: on
class Qualifier(Has_semantics):
    """
    A qualifier is a type-value-pair that makes additional statements w.r.t. the value
    of the element.

    :constraint AASd-006:

        If both the :attr:`~value` and the :attr:`~value_id` of
        a :class:`.Qualifier` are present then the :attr:`~value` needs
        to be identical to the value of the referenced coded value
        in :attr:`~value_id`.

    :constraint AASd-020:

        The value of :attr:`~value` shall be consistent to the data type as
        defined in :attr:`~value_type`.
    """

    kind: Optional["Qualifier_kind"]
    """
    The qualifier kind describes the kind of the qualifier that is applied to the
    element.

    Default: :attr:`~Qualifier_kind.Concept_qualifier`
    """

    @implementation_specific
    def kind_or_default(self) -> "Qualifier_kind":
        # NOTE (mristin, 2022-05-24):
        # This implementation will not be transpiled, but is given here as reference.
        return self.kind if self.kind is not None else Qualifier_kind.Concept_qualifier

    type: "Qualifier_type"
    """
    The qualifier *type* describes the type of the qualifier that is applied to
    the element.
    """

    value_type: "Data_type_def_XSD"
    """
    Data type of the qualifier value.
    """

    value: Optional["Value_data_type"]
    """
    The qualifier value is the value of the qualifier.
    """

    value_id: Optional["Reference"]
    """
    Reference to the global unique ID of a coded value.
    
    .. note::
    
        It is recommended to use a global reference.
    """

    def __init__(
        self,
        type: "Qualifier_type",
        value_type: "Data_type_def_XSD",
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        kind: Optional["Qualifier_kind"] = None,
        value: Optional["Value_data_type"] = None,
        value_id: Optional["Reference"] = None,
    ) -> None:
        Has_semantics.__init__(
            self,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
        )

        self.type = type
        self.value_type = value_type
        self.kind = kind
        self.value = value
        self.value_id = value_id


# fmt: off
@reference_in_the_book(section=(5, 7, 3))
@serialization(with_model_type=True)
@invariant(
    lambda self:
    not (self.submodels is not None)
    or (
        all(
            is_model_reference_to(reference, Key_types.Submodel)
            for reference in self.submodels
        )
    )
)
@invariant(
    lambda self:
    not (self.derived_from is not None)
    or (
        is_model_reference_to(
            self.derived_from,
            Key_types.Asset_administration_shell
        )
    )
)
# fmt: on
class Asset_administration_shell(Identifiable, Has_data_specification):
    """An asset administration shell."""

    derived_from: Optional["Reference"]
    """The reference to the AAS the AAS was derived from."""

    asset_information: "Asset_information"
    """Meta-information about the asset the AAS is representing."""

    submodels: Optional[List["Reference"]]
    """
    References to submodels of the AAS.

    A submodel is a description of an aspect of the asset the AAS is representing.
    
    The asset of an AAS is typically described by one or more submodels.
    
    Temporarily no submodel might be assigned to the AAS.
    """

    def __init__(
        self,
        id: Identifier,
        asset_information: "Asset_information",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        administration: Optional["Administrative_information"] = None,
        data_specifications: Optional[List["Reference"]] = None,
        derived_from: Optional["Reference"] = None,
        submodels: Optional[List["Reference"]] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            id=id,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            administration=administration,
        )

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.derived_from = derived_from
        self.asset_information = asset_information
        self.submodels = submodels


@invariant(
    lambda self: not (self.specific_asset_id is not None)
    or (
        not (self.specific_asset_id.name.lower() == "globalassetid")
        or (
            self.global_asset_id is not None
            and self.specific_asset_id.value == self.global_asset_id
        )
    ),
    "Constraint AASd-116: ``globalAssetId`` (case-insensitive) is a reserved key. "
    "If used as value for name of the specific asset ID then "
    "the value of the specific asset ID shall be identical to the global asset ID.",
)
@reference_in_the_book(section=(5, 7, 4), index=0)
class Asset_information(DBC):
    """
    In :class:`.Asset_information` identifying meta data of the asset that is
    represented by an AAS is defined.

    The asset may either represent an asset type or an asset instance.

    The asset has a globally unique identifier plus – if needed – additional domain
    specific (proprietary) identifiers. However, to support the corner case of very
    first phase of lifecycle where a stabilised/constant global asset identifier does
    not already exist, the corresponding attribute :attr:`~global_asset_id` is optional.

    :constraint AASd-116:

        ``globalAssetId`` (case-insensitive) is a reserved key. If used as value for
        :attr:`~Specific_asset_id.name` then :attr:`~Specific_asset_id.value` shall be
        identical to :attr:`~global_asset_id`.
    """

    asset_kind: "Asset_kind"
    """
    Denotes whether the Asset is of kind :attr:`~Asset_kind.Type` or
    :attr:`~Asset_kind.Instance`.
    """

    global_asset_id: Optional["Reference"]
    """
    Global identifier of the asset the AAS is representing.

    This attribute is required as soon as the AAS is exchanged via partners in the life
    cycle of the asset. In a first phase of the life cycle the asset might not yet have
    a global ID but already an internal identifier. The internal identifier would be
    modelled via :attr:`~specific_asset_id`.
    
    .. note::
    
        This is a global reference.
    """

    specific_asset_id: Optional["Specific_asset_id"]
    """
    Additional domain-specific, typically proprietary identifier for the asset like
    e.g., serial number etc.
    """

    default_thumbnail: Optional["Resource"]
    """
    Thumbnail of the asset represented by the Asset Administration Shell.

    Used as default.
    """

    def __init__(
        self,
        asset_kind: "Asset_kind",
        global_asset_id: Optional["Reference"] = None,
        specific_asset_id: Optional["Specific_asset_id"] = None,
        default_thumbnail: Optional["Resource"] = None,
    ) -> None:
        self.asset_kind = asset_kind
        self.global_asset_id = global_asset_id
        self.specific_asset_id = specific_asset_id
        self.default_thumbnail = default_thumbnail


@reference_in_the_book(section=(5, 7, 4), index=1)
class Resource(DBC):
    """
    Resource represents an address to a file (a locator). The value is an URI that
    can represent an absolute or relative path
    """

    path: "Path_type"
    """
    Path and name of the resource (with file extension).

    The path can be absolute or relative.
    """

    content_type: Optional["Content_type"]
    """
    Content type of the content of the file.

    The content type states which file extensions the file can have.
    """

    def __init__(
        self,
        path: "Path_type",
        content_type: Optional["Content_type"] = None,
    ) -> None:
        self.path = path
        self.content_type = content_type


@reference_in_the_book(section=(5, 7, 4), index=2)
class Asset_kind(Enum):
    """
    Enumeration for denoting whether an asset is a type asset or an instance asset.
    """

    Type = "Type"
    """
    hardware or software element which specifies the common attributes shared by all
    instances of the type

    [SOURCE: IEC TR 62390:2005-01, 3.1.25]
    """

    Instance = "Instance"
    """
    concrete, clearly identifiable component of a certain type

    .. note::

        It becomes an individual entity of a type, for example a device, by defining
        specific property values.

    .. note::

        In an object oriented view, an instance denotes an object of a class
        (of a type).

    [SOURCE: IEC 62890:2016, 3.1.16] 65/617/CDV
    """


@reference_in_the_book(section=(5, 7, 4), index=3)
class Specific_asset_id(Has_semantics):
    """
    A specific asset ID describes a generic supplementary identifying attribute of the
    asset.

    The specific asset ID is not necessarily globally unique.
    """

    name: Non_empty_string
    """Name of the identifier"""

    value: Non_empty_string
    """The value of the specific asset identifier with the corresponding name."""

    external_subject_id: "Reference"
    """
    The (external) subject the key belongs to or has meaning to.

    .. note::
    
        This is a global reference.
    """

    def __init__(
        self,
        name: Non_empty_string,
        value: Non_empty_string,
        external_subject_id: "Reference",
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
    ) -> None:
        Has_semantics.__init__(
            self,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
        )
        self.name = name
        self.value = value
        self.external_subject_id = external_subject_id


# fmt: off
@reference_in_the_book(section=(5, 7, 5))
@invariant(
    lambda self:
    not any(
        qualifier.kind == Qualifier_kind.Template_qualifier
        for qualifier in self.qualifiers
    ) or (
        self.kind_or_default() == Modeling_kind.Template
    ),
    "Constraint AASd-119: If any qualifier kind value of a qualifiable qualifier is "
    "equal to template qualifier and the qualified element has kind then the qualified "
    "element shall be of kind template."
)
@invariant(
    lambda self:
    not (self.submodel_elements is not None)
    or (id_shorts_are_unique(self.submodel_elements)),
    "Constraint AASd-120: ID-short of non-identifiable referables shall be unique "
    "in its namespace."
)
@invariant(
    lambda self:
    not (self.submodel_elements is not None)
    or all(
        element.id_short is not None
        for element in self.submodel_elements
    ),
    "ID-shorts need to be defined for all the submodel elements."
)
# fmt: on
class Submodel(
    Identifiable, Has_kind, Has_semantics, Qualifiable, Has_data_specification
):
    """
    A submodel defines a specific aspect of the asset represented by the AAS.

    A submodel is used to structure the digital representation and technical
    functionality of an Administration Shell into distinguishable parts. Each submodel
    refers to a well-defined domain or subject matter. Submodels can become
    standardized and, thus, become submodels templates.
    """

    submodel_elements: Optional[List["Submodel_element"]]
    """A submodel consists of zero or more submodel elements."""

    def __init__(
        self,
        id: Identifier,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        administration: Optional["Administrative_information"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        submodel_elements: Optional[List["Submodel_element"]] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            id=id,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            administration=administration,
        )

        Has_kind.__init__(self, kind=kind)

        Has_semantics.__init__(
            self,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
        )

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.submodel_elements = submodel_elements


# fmt: off
@abstract
@invariant(
    lambda self:
    not any(
        qualifier.kind == Qualifier_kind.Template_qualifier
        for qualifier in self.qualifiers
    ) or (
        self.kind_or_default() == Modeling_kind.Template
    ),
    "Constraint AASd-119: If any qualifier kind value of a qualifiable qualifier is "
    "equal to template qualifier and the qualified element has kind then the qualified "
    "element shall be of kind template."
)
@reference_in_the_book(section=(5, 7, 6))
# fmt: on
class Submodel_element(
    Referable, Has_kind, Has_semantics, Qualifiable, Has_data_specification
):
    """
    A submodel element is an element suitable for the description and differentiation of
    assets.

    It is recommended to add a :attr:`~Has_semantics.semantic_id` to a submodel element.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Referable.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
        )

        Has_kind.__init__(self, kind=kind)

        Has_semantics.__init__(
            self,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
        )

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(self, data_specifications=data_specifications)


@reference_in_the_book(section=(5, 7, 7, 14))
@abstract
class Relationship_element(Submodel_element):
    """
    A relationship element is used to define a relationship between two elements
    being either referable (model reference) or external (global reference).
    """

    first: "Reference"
    """
    Reference to the first element in the relationship taking the role of the subject.
    """

    second: "Reference"
    """
    Reference to the second element in the relationship taking the role of the object.
    """

    def __init__(
        self,
        first: "Reference",
        second: "Reference",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.first = first
        self.second = second


# fmt: off
@reference_in_the_book(section=(5, 7, 7, 16))
@invariant(
    lambda self:
    not (self.value is not None)
    or id_shorts_are_unique(self.value)
)
@invariant(
    lambda self:
    not (self.value is not None)
    or all(
        element.id_short is None
        for element in self.value
    ),
    "Constraint AASd-120: ID-shorts of submodel elements within a SubmodelElementList "
    "shall not be specified."
)
@invariant(
    lambda self:
    not (
            self.value is not None
            and (
                    self.type_value_list_element == AAS_submodel_elements.Property
                    or self.type_value_list_element == AAS_submodel_elements.Range
            )
    ) or (
        self.value_type_list_element is not None
        and properties_or_ranges_have_value_type(
            self.value,
            self.value_type_list_element
        )
    ),
    "Constraint AASd-109: If type value list element is equal to "
    "Property or Range value type list element shall be set "
    "and all first level child elements shall have the value type as specified in "
    "value type list element.")
@invariant(
    lambda self:
    not (self.value is not None)
    or all(
        submodel_element_is_of_type(element, self.type_value_list_element)
        for element in self.value
    ),
    "Constraint AASd-108: All first level child elements shall have "
    "the same submodel element type as specified in type value list element."
)
@invariant(
    lambda self:
    not (self.value is not None)
    or submodel_elements_have_identical_semantic_ids(self.value),
    "Constraint AASd-114: If two first level child elements "
    "have a semantic ID then they shall be identical."
)
@invariant(
    lambda self:
    not (
            self.value is not None
            and self.semantic_id_list_element is not None
    ) or (
        all(
            not (child.semantic_id is not None)
            or child.semantic_id == self.semantic_id_list_element
            for child in self.value
        )
    ),
    "Constraint AASd-107: If a first level child element has a semantic ID "
    "it shall be identical to semantic ID list element."
)
# fmt: on
class Submodel_element_list(Submodel_element):
    """
    A submodel element list is an ordered list of submodel elements.

    The numbering starts with zero (0).

    :constraint AASd-107:

        If a first level child element in a :class:`.Submodel_element_list` has
        a :attr:`~Submodel_element.semantic_id` it
        shall be identical to :attr:`~Submodel_element_list.semantic_id_list_element`.

    :constraint AASd-114:

        If two first level child elements in a :class:`.Submodel_element_list` have
        a :attr:`~Submodel_element.semantic_id` then they shall be identical.

    :constraint AASd-115:

        If a first level child element in a :class:`.Submodel_element_list` does not
        specify a :attr:`~Submodel_element.semantic_id` then the value is assumed to be
        identical to :attr:`~Submodel_element_list.semantic_id_list_element`.

    :constraint AASd-108:

        All first level child elements in a :class:`.Submodel_element_list` shall have
        the same submodel element type as specified in :attr:`~type_value_list_element`.

    :constraint AASd-109:

        If :attr:`~type_value_list_element` is equal to
        :attr:`AAS_submodel_elements.Property` or
        :attr:`AAS_submodel_elements.Range`
        :attr:`~value_type_list_element` shall be set and all first
        level child elements in the :class:`.Submodel_element_list` shall have
        the value type as specified in :attr:`~value_type_list_element`.
    """

    order_relevant: Optional["bool"]
    """
    Defines whether order in list is relevant. If :attr:`~order_relevant` = ``False``
    then the list is representing a set or a bag.

    Default: ``True``
    """

    @implementation_specific
    def order_relevant_or_default(self) -> bool:
        # NOTE (mristin, 2022-04-7):
        # This implementation will not be transpiled, but is given here as reference.
        return self.order_relevant if self.order_relevant is not None else True

    value: Optional[List["Submodel_element"]]
    """
    Submodel element contained in the list.

    The list is ordered.
    """

    semantic_id_list_element: Optional["Reference"]
    """
    Semantic ID the submodel elements contained in the list match to.
    
    .. note::

        It is recommended to use a global reference.
    """

    type_value_list_element: "AAS_submodel_elements"
    """
    The submodel element type of the submodel elements contained in the list.
    """

    value_type_list_element: Optional["Data_type_def_XSD"]
    """
    The value type of the submodel element contained in the list.
    """

    def __init__(
        self,
        type_value_list_element: "AAS_submodel_elements",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        order_relevant: Optional["bool"] = None,
        value: Optional[List["Submodel_element"]] = None,
        semantic_id_list_element: Optional["Reference"] = None,
        value_type_list_element: Optional["Data_type_def_XSD"] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.type_value_list_element = type_value_list_element
        self.order_relevant = order_relevant
        self.value = value
        self.semantic_id_list_element = semantic_id_list_element
        self.value_type_list_element = value_type_list_element


# fmt: off
@reference_in_the_book(section=(5, 7, 7, 15))
@invariant(
    lambda self:
    not (self.value is not None)
    or id_shorts_are_unique(self.value)
)
@invariant(
    lambda self:
    not (self.value is not None)
    or all(
        element.id_short is not None
        for element in self.value
    ),
    "ID-shorts need to be defined for all the elements."
)
# fmt: on
class Submodel_element_collection(Submodel_element):
    """
    A submodel element collection is a kind of struct, i.e. a a logical encapsulation
    of multiple named values. It has a fixed number of submodel elements.
    """

    value: Optional[List["Submodel_element"]]
    """
    Submodel element contained in the collection.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional[List["Submodel_element"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value = value


@abstract
@invariant(
    lambda self: not (self.category is not None)
    or (
        self.category == "CONSTANT"
        or self.category == "PARAMETER"
        or self.category == "VARIABLE"
    ),
    "Constraint AASd-090: For data elements category shall be one "
    "of the following values: CONSTANT, PARAMETER or VARIABLE",
)
@reference_in_the_book(section=(5, 7, 7, 5))
class Data_element(Submodel_element):
    """
    A data element is a submodel element that is not further composed out of
    other submodel elements.

    A data element is a submodel element that has a value. The type of value differs
    for different subtypes of data elements.

    :constraint AASd-090:

        For data elements :attr:`~category` (inherited by :class:`.Referable`) shall be
        one of the following values: ``CONSTANT``, ``PARAMETER`` or ``VARIABLE``.

        Default: ``VARIABLE``
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

    @implementation_specific
    def category_or_default(self) -> str:
        # NOTE (mristin, 2022-04-7):
        # This implementation will not be transpiled, but is given here as reference.
        return self.category if self.category is not None else "VARIABLE"


# fmt: off
@reference_in_the_book(section=(5, 7, 7, 11))
@invariant(
    lambda self:
    not (self.value is not None)
    or value_consistent_with_xsd_type(self.value, self.value_type)
)
# fmt: on
class Property(Data_element):
    """
    A property is a data element that has a single value.

    :constraint AASd-007:

        If both, the :attr:`~value` and the :attr:`~value_id` are
        present then the value of :attr:`~value` needs to be identical to
        the value of the referenced coded value in :attr:`~value_id`.
    """

    value_type: "Data_type_def_XSD"
    """
    Data type of the value
    """

    value: Optional["Value_data_type"]
    """
    The value of the property instance.
    """

    value_id: Optional["Reference"]
    """
    Reference to the global unique ID of a coded value.

    .. note::
    
        It is recommended to use a global reference.
    """

    def __init__(
        self,
        value_type: "Data_type_def_XSD",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional["Value_data_type"] = None,
        value_id: Optional["Reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value_type = value_type
        self.value = value
        self.value_id = value_id


@reference_in_the_book(section=(5, 7, 7, 9))
class Multi_language_property(Data_element):
    """
    A property is a data element that has a multi-language value.

    :constraint AASd-012:
        If both the :attr:`~value` and the :attr:`~value_id` are present then for each
        string in a specific language the meaning must be the same as specified in
        :attr:`~value_id`.
    """

    value: Optional["Lang_string_set"]
    """
    The value of the property instance.
    """

    value_id: Optional["Reference"]
    """
    Reference to the global unique ID of a coded value.

    .. note::
    
        It is recommended to use a global reference.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional["Lang_string_set"] = None,
        value_id: Optional["Reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value = value
        self.value_id = value_id


# fmt: off
@reference_in_the_book(section=(5, 7, 7, 12))
@invariant(
    lambda self:
    not (self.min is not None)
    or value_consistent_with_xsd_type(self.min, self.value_type)
)
@invariant(
    lambda self:
    not (self.max is not None)
    or value_consistent_with_xsd_type(self.max, self.value_type)
)
# fmt: on
class Range(Data_element):
    """
    A range data element is a data element that defines a range with min and max.
    """

    value_type: "Data_type_def_XSD"
    """
    Data type of the min und max
    """

    min: Optional["Value_data_type"]
    """
    The minimum value of the range.

    If the min value is missing, then the value is assumed to be negative infinite.
    """

    max: Optional["Value_data_type"]
    """
    The maximum value of the range.

    If the max value is missing,  then the value is assumed to be positive infinite.
    """

    def __init__(
        self,
        value_type: "Data_type_def_XSD",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        min: Optional["Value_data_type"] = None,
        max: Optional["Value_data_type"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value_type = value_type
        self.min = min
        self.max = max


@reference_in_the_book(section=(5, 7, 7, 15))
class Reference_element(Data_element):
    """
    A reference element is a data element that defines a logical reference to another
    element within the same or another AAS or a reference to an external object or
    entity.
    """

    value: Optional["Reference"]
    """
    Global reference to an external object or entity or a logical reference to
    another element within the same or another AAS (i.e. a model reference to
    a Referable).
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional["Reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value = value


@reference_in_the_book(section=(5, 7, 7, 3))
class Blob(Data_element):
    """
    A :class:`.Blob` is a data element that represents a file that is contained with its
    source code in the value attribute.
    """

    value: Optional["Blob_type"]
    """
    The value of the :class:`.Blob` instance of a blob data element.

    .. note::

        In contrast to the file property the file content is stored directly as value
        in the :class:`.Blob` data element.
    """

    content_type: Content_type
    """
    Content type of the content of the :class:`.Blob`.

    The content type (MIME type) states which file extensions the file can have.

    Valid values are content types like e.g. ``application/json``, ``application/xls``,
    ``image/jpg``.

    The allowed values are defined as in RFC2046.
    """

    def __init__(
        self,
        content_type: Content_type,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional["Blob_type"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.content_type = content_type
        self.value = value


@reference_in_the_book(section=(5, 7, 7, 8))
class File(Data_element):
    """
    A File is a data element that represents an address to a file (a locator).

    The value is an URI that can represent an absolute or relative path.
    """

    value: Optional["Path_type"]
    """
    Path and name of the referenced file (with file extension).

    The path can be absolute or relative.
    """

    content_type: "Content_type"
    """
    Content type of the content of the file.

    The content type states which file extensions the file can have.
    """

    def __init__(
        self,
        content_type: "Content_type",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional["Path_type"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.content_type = content_type
        self.value = value


@reference_in_the_book(section=(5, 7, 7, 1))
class Annotated_relationship_element(Relationship_element):
    """
    An annotated relationship element is a relationship element that can be annotated
    with additional data elements.
    """

    annotations: Optional[List[Data_element]]
    """
    A data element that represents an annotation that holds for the relationship
    between the two elements
    """

    def __init__(
        self,
        first: "Reference",
        second: "Reference",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        annotations: Optional[List[Data_element]] = None,
    ) -> None:
        Relationship_element.__init__(
            self,
            first=first,
            second=second,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.annotations = annotations


@reference_in_the_book(section=(5, 7, 7, 6), index=1)
class Entity_type(Enum):
    """
    Enumeration for denoting whether an entity is a self-managed entity or a co-managed
    entity.
    """

    Co_managed_entity = "CoManagedEntity"
    """
    For co-managed entities there is no separate AAS. Co-managed entities need to be
    part of a self-managed entity.
    """

    Self_managed_entity = "SelfManagedEntity"
    """
    Self-Managed Entities have their own AAS but can be part of the bill of material of
    a composite self-managed entity. 
    
    The asset of an I4.0 Component is a self-managed entity per definition."
    """


# fmt: off
@reference_in_the_book(section=(5, 7, 7, 6))
@invariant(
    lambda self:
    (
        self.entity_type == Entity_type.Self_managed_entity
        and (
            (
                self.global_asset_id is not None
                and self.specific_asset_id is None
            ) or (
                self.global_asset_id is None
                and self.specific_asset_id is not None
            )
        )
    ) or (
        self.global_asset_id is None
        and self.specific_asset_id is None
    ),
    "Constraint AASd-014: Either the attribute global asset ID or "
    "specific asset ID must be set if entity type is set to 'SelfManagedEntity'. "
    "They are not existing otherwise."
)
# fmt: on
class Entity(Submodel_element):
    """
    An entity is a submodel element that is used to model entities.

    :constraint AASd-014:

        Either the attribute :attr:`~global_asset_id` or :attr:`~specific_asset_id`
        of an :class:`.Entity` must be set if :attr:`~entity_type` is set to
        :attr:`~Entity_type.Self_managed_entity`. They are not existing otherwise.
    """

    statements: Optional[List["Submodel_element"]]
    """
    Describes statements applicable to the entity by a set of submodel elements,
    typically with a qualified value.
    """

    entity_type: "Entity_type"
    """
    Describes whether the entity is a co-managed entity or a self-managed entity.
    """

    global_asset_id: Optional["Reference"]
    """
    Global identifier of the asset the entity is representing.

    .. note::

        This is a global reference.
    """

    specific_asset_id: Optional["Specific_asset_id"]
    """
    Reference to a specific asset ID representing a supplementary identifier
    of the asset represented by the Asset Administration Shell.
    """

    def __init__(
        self,
        entity_type: "Entity_type",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        statements: Optional[List["Submodel_element"]] = None,
        global_asset_id: Optional["Reference"] = None,
        specific_asset_id: Optional["Specific_asset_id"] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.statements = statements
        self.entity_type = entity_type
        self.global_asset_id = global_asset_id
        self.specific_asset_id = specific_asset_id


@reference_in_the_book(section=(5, 7, 7, 2), index=1)
class Direction(Enum):
    """
    Direction
    """

    Input = "INPUT"
    """
    Input direction.
    """

    Output = "OUTPUT"
    """
    Output direction
    """


@reference_in_the_book(section=(5, 7, 7, 2), index=2)
class State_of_event(Enum):
    """
    State of an event
    """

    On = "ON"
    """
    Event is on
    """

    Off = "OFF"
    """
    Event is off.
    """


# fmt: off
@invariant(
    lambda self:
    is_model_reference_to(self.observable_reference, Key_types.Referable)
)
@invariant(
    lambda self:
    is_model_reference_to(self.source, Key_types.Referable)
)
@reference_in_the_book(section=(5, 7, 7, 2), index=3)
# fmt: on
class Event_payload(DBC):
    """Defines the necessary information of an event instance sent out or received."""

    source: "Reference"
    """
    Reference to the source event element, including identification of
    :class:`.Asset_administration_shell`, :class:`.Submodel`,
    :class:`.Submodel_element`'s.
    """

    source_semantic_id: Optional["Reference"]
    """
    :attr:`~Has_semantics.semantic_id` of the source event element, if available
    
    .. note::
    
        It is recommended to use a global reference.
    """

    observable_reference: "Reference"
    """
    Reference to the referable, which defines the scope of the event.

    Can be :class:`.Asset_administration_shell`, :class:`.Submodel` or
    :class:`.Submodel_element`.
    """

    observable_semantic_id: Optional["Reference"]
    """
    :attr:`~Has_semantics.semantic_id` of the referable which defines the scope of
    the event, if available.
    
    .. note::
    
        It is recommended to use a global reference.
    """

    topic: Optional["Non_empty_string"]
    """
    Information for the outer message infrastructure for scheduling the event to
    the respective communication channel.
    """

    subject_id: Optional["Reference"]
    """
    Subject, who/which initiated the creation.
    
    .. note::
    
        This is a global reference.
    """

    time_stamp: "Date_time_stamp_UTC"
    """
    Timestamp in UTC, when this event was triggered.
    """

    payload: Optional["Non_empty_string"]
    """
    Event specific payload.
    """

    def __init__(
        self,
        source: "Reference",
        observable_reference: "Reference",
        time_stamp: "Date_time_stamp_UTC",
        source_semantic_id: Optional["Reference"] = None,
        observable_semantic_id: Optional["Reference"] = None,
        topic: Optional["Non_empty_string"] = None,
        subject_id: Optional["Reference"] = None,
        payload: Optional["Non_empty_string"] = None,
    ) -> None:
        self.source = source
        self.observable_reference = observable_reference
        self.time_stamp = time_stamp
        self.source_semantic_id = source_semantic_id
        self.observable_semantic_id = observable_semantic_id
        self.topic = topic
        self.subject_id = subject_id
        self.payload = payload


@abstract
@reference_in_the_book(section=(5, 7, 7, 7))
class Event_element(Submodel_element):
    """
    An event element.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )


# fmt: off
@reference_in_the_book(section=(5, 7, 7, 2))
@invariant(
    lambda self:
    is_model_reference_to(self.message_broker, Key_types.Referable)
)
@invariant(
    lambda self:
    is_model_reference_to(self.observed, Key_types.Referable)
)
@invariant(
    lambda self:
    not (self.direction == Direction.Input)
    or self.max_interval is None,
    "Max. interval is not applicable for input direction"
)
# fmt: on
class Basic_event_element(Event_element):
    """
    A basic event element.
    """

    observed: "Reference"
    """
    Reference to the :class:`.Referable`, which defines the scope of the event.
    Can be :class:`.Asset_administration_shell`, :class:`.Submodel`, or
    :class:`.Submodel_element`.
    
    Reference to a referable, e.g., a data element or
    a submodel, that is being observed.
    """

    direction: "Direction"
    """
    Direction of event.

    Can be ``{ Input, Output }``.
    """

    state: "State_of_event"
    """
    State of event.

    Can be ``{ On, Off }``.
    """

    message_topic: Optional["Non_empty_string"]
    """
    Information for the outer message infrastructure for scheduling the event to the
    respective communication channel.
    """

    message_broker: Optional["Reference"]
    """
    Information, which outer message infrastructure shall handle messages for
    the :class:`.Event_element`. Refers to a :class:`.Submodel`, 
    :class:`.Submodel_element_list`, :class:`.Submodel_element_collection` or 
    :class:`.Entity`, which contains :class:`.Data_element`'s describing 
    the proprietary specification for the message broker.

    .. note::

        For different message infrastructure, e.g., OPC UA or MQTT or AMQP, this
        proprietary specification could be standardized by having respective Submodels.
    """

    last_update: Optional["Date_time_stamp_UTC"]
    """
    Timestamp in UTC, when the last event was received (input direction) or sent
    (output direction).
    """

    min_interval: Optional["Date_time_stamp_UTC"]
    """
    For input direction, reports on the maximum frequency, the software entity behind
    the respective Referable can handle input events.
    
    For output events, specifies the maximum frequency of outputting this event to 
    an outer infrastructure.
    
    Might be not specified, that is, there is no minimum interval.
    """

    max_interval: Optional["Date_time_stamp_UTC"]
    """
    For input direction: not applicable.

    For output direction: maximum interval in time, the respective Referable shall send
    an update of the status of the event, even if no other trigger condition for
    the event was not met.
    
    Might be not specified, that is, there is no maximum interval
    """

    def __init__(
        self,
        observed: "Reference",
        direction: "Direction",
        state: "State_of_event",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        message_topic: Optional["Non_empty_string"] = None,
        message_broker: Optional["Reference"] = None,
        last_update: Optional["Date_time_stamp_UTC"] = None,
        min_interval: Optional["Date_time_stamp_UTC"] = None,
        max_interval: Optional["Date_time_stamp_UTC"] = None,
    ) -> None:
        Event_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.observed = observed
        self.direction = direction
        self.state = state
        self.message_topic = message_topic
        self.message_broker = message_broker
        self.last_update = last_update
        self.min_interval = min_interval
        self.max_interval = max_interval


@reference_in_the_book(section=(5, 7, 7, 10))
class Operation(Submodel_element):
    """
    An operation is a submodel element with input and output variables.
    """

    input_variables: Optional[List["Operation_variable"]]
    """
    Input parameter of the operation.
    """

    output_variables: Optional[List["Operation_variable"]]
    """
    Output parameter of the operation.
    """

    inoutput_variables: Optional[List["Operation_variable"]]
    """
    Parameter that is input and output of the operation.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        input_variables: Optional[List["Operation_variable"]] = None,
        output_variables: Optional[List["Operation_variable"]] = None,
        inoutput_variables: Optional[List["Operation_variable"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.input_variables = input_variables
        self.output_variables = output_variables
        self.inoutput_variables = inoutput_variables


@reference_in_the_book(section=(5, 7, 7, 10), index=1)
class Operation_variable(DBC):
    """
    The value of an operation variable is a submodel element that is used as input
    and/or output variable of an operation.
    """

    value: "Submodel_element"
    """
    Describes an argument or result of an operation via a submodel element
    """

    def __init__(self, value: "Submodel_element") -> None:
        self.value = value


@reference_in_the_book(section=(5, 7, 7, 4))
class Capability(Submodel_element):
    """
    A capability is the implementation-independent description of the potential of an
    asset to achieve a certain effect in the physical or virtual world.

    .. note::

        The :attr:`~semantic_id` of a capability is typically an ontology.
        Thus, reasoning on capabilities is enabled.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_id: Optional["Reference"] = None,
        supplemental_semantic_ids: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_id=semantic_id,
            supplemental_semantic_ids=supplemental_semantic_ids,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )


# fmt: off
@reference_in_the_book(section=(5, 7, 8))
@serialization(with_model_type=True)
@invariant(
    lambda self:
    not (self.category is not None)
    or concept_description_category_is_valid(self.category),
    "Constraint AASd-051: A concept description shall have one of "
    "the following categories: 'VALUE', 'PROPERTY', 'REFERENCE', 'DOCUMENT', "
    "'CAPABILITY',; 'RELATIONSHIP', 'COLLECTION', 'FUNCTION', 'EVENT', 'ENTITY', "
    "'APPLICATION_CLASS', 'QUALIFIER', 'VIEW'.")
# fmt: on
class Concept_description(Identifiable, Has_data_specification):
    """
    The semantics of a property or other elements that may have a semantic description
    is defined by a concept description.

    The description of the concept should follow a standardized schema (realized as
    data specification template).

    :constraint AASd-051:

        A :class:`.Concept_description` shall have one of the following categories
        ``VALUE``, ``PROPERTY``, ``REFERENCE``, ``DOCUMENT``, ``CAPABILITY``,
        ``RELATIONSHIP``, ``COLLECTION``, ``FUNCTION``, ``EVENT``, ``ENTITY``,
        ``APPLICATION_CLASS``, ``QUALIFIER``, ``VIEW``.

        Default: ``PROPERTY``.
    """

    @implementation_specific
    @ensure(lambda result: concept_description_category_is_valid(result))
    def category_or_default(self) -> str:
        # NOTE (mristin, 2022-04-7):
        # This implementation will not be transpiled, but is given here as reference.
        return self.category if self.category is not None else "PROPERTY"

    is_case_of: Optional[List["Reference"]]
    """
    Reference to an external definition the concept is compatible to or was derived 
    from.

    .. note::

       It is recommended to use a global reference.

    .. note::

       Compare to is-case-of relationship in ISO 13584-32 & IEC EN 61360"
    """

    def __init__(
        self,
        id: Identifier,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Non_empty_string] = None,
        id_short: Optional[Id_short] = None,
        display_name: Optional["Lang_string_set"] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        administration: Optional["Administrative_information"] = None,
        data_specifications: Optional[List["Reference"]] = None,
        is_case_of: Optional[List["Reference"]] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            id=id,
            extensions=extensions,
            category=category,
            id_short=id_short,
            display_name=display_name,
            description=description,
            checksum=checksum,
            administration=administration,
        )

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.is_case_of = is_case_of


@reference_in_the_book(section=(5, 7, 10, 2), index=1)
class Reference_types(Enum):
    """
    ReferenceTypes
    """

    Global_reference = "GlobalReference"
    """
    GlobalReference.
    """

    Model_reference = "ModelReference"
    """
    ModelReference
    """


# TODO (mristin, 2022-05-25): put aasd-122 in text
# TODO (mristin, 2022-05-25): put aasd-123 in text
# TODO (mristin, 2022-05-25): put aasd-123 in tests

# TODO (mristin, 2022-05-25): write out aasd-124 description, in text and tests

# fmt: off
@invariant(lambda self: len(self.keys) >= 1)
@reference_in_the_book(section=(5, 7, 10, 2))
@serialization(with_model_type=True)
# fmt: on
class Reference(DBC):
    """
    Reference to either a model element of the same or another AAS or to an external
    entity.

    A reference is an ordered list of keys.

    A model reference is an ordered list of keys, each key referencing an element. The
    complete list of keys may for example be concatenated to a path that then gives
    unique access to an element.

    A global reference is a reference to an external entity.

    :constraint AASd-121:

        For :class:`.Reference`'s the :attr:`~Key.type` of the first key of
        :attr:`~keys` shall be one of :class:`.Globally_identifiables`.

    :constraint AASd-122:

        For global references, i.e. :class:`.Reference`'s with
        :attr:`~Reference.type` = :attr:`~Reference_types.Global_reference`, the type
        of the first key of :attr:`~Reference.keys` shall be one of
        :class:`.Generic_globally_identifiables`.

    :constraint AASd-123:

        For model references, i.e. :class:`.Reference`'s with
        :attr:`~Reference.type` = :attr:`~Reference_types.Model_reference`, the type
        of the first key of :attr:`~Reference.keys` shall be one of
        :class:`.AAS_identifiables`.

    :constraint AASd-124:

        For global references, i.e. :class:`.Reference`'s with
        :attr:`~Reference.type` = :attr:`~Reference_types.Global_reference`, the last
        key of :attr:`~Reference.keys` shall be either one of
        :class:`.Generic_globally_identifiables` or one of
        :class:`.Generic_fragment_keys`.

    :constraint AASd-125:

        For model references, i.e. :class:`.Reference`'s with
        :attr:`~Reference.type` = :attr:`~Reference_types.Model_reference`, with more
        than one key in :attr:`~Reference.keys` the type of the keys following the first
        key of  :attr:`~Reference.keys` shall be one of :class:`.Fragment_keys`.

        .. note::

            :constraintref:`AASd-125` ensures that the shortest path is used.

    :constraint AASd-126:

        For model references, i.e. :class:`.Reference`'s with
        :attr:`~Reference.type` = :attr:`~Reference_types.Model_reference`, with more
        than one key in :attr:`~Reference.keys` the type of the last key in the
        reference key chain may be one of :class:`.Generic_fragment_keys` or no key
        at all shall have a value out of :class:`.Generic_fragment_keys`.

    :constraint AASd-127:

        For model references, i.e. :class:`.Reference`'s with
        :attr:`~Reference.type` = :attr:`~Reference_types.Model_reference`, with more
        than one key in :attr:`~Reference.keys` a key with :attr:`~Key.type`
        :attr:`~Key_types.Fragment_reference` shall be preceded by a key with
        :attr:`~Key.type` :attr:`~Key_types.File` or :attr:`~Key_types.Blob`. All other
        AAS fragments, i.e. type values out of :class:`.AAS_submodel_elements`, do not
        support fragments.

        .. note::

            Which kind of fragments are supported depends on the content type and the
            specification of allowed fragment identifiers for the corrsponding resource
            being referenced via the reference.

    :constraint AASd-128:

        For model references, i.e. :class:`.Reference`'s with
        :attr:`~Reference.type` = :attr:`~Reference_types.Model_reference`, the
        :attr:`~Key.value` of a :class:`.Key` preceded by a :class:`.Key` with
        :attr:`~Key.type` = :attr:`~Key_types.Submodel_element_list` is an integer
        number denoting the position in the array of the submodel element list.
    """

    type: "Reference_types"
    """
    Type of the reference.

    Denotes, whether reference is a global reference or a model reference.
    """

    referred_semantic_id: Optional["Reference"]
    """
    :attr:`Has_semantics.semantic_id` of the referenced model element 
    (:attr:`~Reference.type` = :attr:`~Reference_types.Model_reference`).
    
    For global references there typically is no semantic ID.
    
    .. note::
    
        It is recommended to use a global reference.
    """

    keys: List["Key"]
    """
    Unique references in their name space.
    """

    def __init__(
        self,
        type: Reference_types,
        keys: List["Key"],
        referred_semantic_id: Optional["Reference"] = None,
    ) -> None:
        self.type = type
        self.keys = keys
        self.referred_semantic_id = referred_semantic_id


@reference_in_the_book(section=(5, 7, 10, 3), index=1)
class Key(DBC):
    """A key is a reference to an element by its ID."""

    type: "Key_types"
    """
    Denotes which kind of entity is referenced.

    In case :attr:`~type` = :attr:`~Key_types.Fragment_reference` the key represents 
    a bookmark or a similar local identifier within its parent element as specified 
    by the key that precedes this key.

    In all other cases the key references a model element of the same or of another AAS.
    The name of the model element is explicitly listed.
    """

    value: Non_empty_string
    """The key value, for example an IRDI or an URI"""

    def __init__(self, type: "Key_types", value: Non_empty_string) -> None:
        self.type = type
        self.value = value


@reference_in_the_book(section=(5, 7, 10, 3), index=6)
class Generic_fragment_keys(Enum):
    """
    Enumeration of all identifiable elements within an asset administration shell.
    """

    Fragment_reference = "FragmentReference"
    """
    Bookmark or a similar local identifier of a subordinate part of a primary resource
    """


@reference_in_the_book(section=(5, 7, 10, 3), index=8)
class Generic_globally_identifiables(Enum):
    """
    Enumeration of different key value types within a key.
    """

    Global_reference = "GlobalReference"


@reference_in_the_book(section=(5, 7, 10, 3), index=7)
class AAS_identifiables(Enum):
    """
    Enumeration of different key value types within a key.
    """

    Asset_administration_shell = "AssetAdministrationShell"
    Concept_description = "ConceptDescription"
    Submodel = "Submodel"


@reference_in_the_book(section=(5, 7, 10, 3), index=5)
class AAS_submodel_elements(Enum):
    """
    Enumeration of all referable elements within an asset administration shell.
    """

    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Basic_event_element = "BasicEventElement"
    Blob = "Blob"
    Capability = "Capability"
    Data_element = "DataElement"
    """
    Data Element.

    .. note::

        Data Element is abstract, *i.e.* if a key uses :attr:`~Data_element`
        the reference may be a :class:`.Property`, a :class:`.File` etc.
    """
    Entity = "Entity"
    Event_element = "EventElement"
    """
    Event element

    .. note::

        :class:`.Event_element` is abstract.
    """
    File = "File"

    Multi_language_property = "MultiLanguageProperty"
    """
    Property with a value that can be provided in multiple languages
    """
    Operation = "Operation"
    Property = "Property"
    Range = "Range"
    """
    Range with min and max
    """
    Reference_element = "ReferenceElement"
    """
    Reference
    """
    Relationship_element = "RelationshipElement"
    """
    Relationship
    """

    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, i.e. if a key uses
        :attr:`Submodel_element` the reference may be a :class:`.Property`,
        a :class:`.Submodel_element_list`, an :class:`.Operation` etc.
    """
    Submodel_element_list = "SubmodelElementList"
    """
    List of Submodel Elements
    """
    Submodel_element_collection = "SubmodelElementCollection"
    """
    Struct of Submodel Elements
    """


@reference_in_the_book(section=(5, 7, 10, 3), index=4)
@is_superset_of(enums=[AAS_submodel_elements])
class AAS_referable_non_identifiables(Enum):
    """
    Enumeration of all referable elements within an asset administration shell.
    """

    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Basic_event_element = "BasicEventElement"
    Blob = "Blob"
    Capability = "Capability"
    Data_element = "DataElement"
    """
    Data Element.

    .. note::

        Data Element is abstract, *i.e.* if a key uses :attr:`~Data_element`
        the reference may be a :class:`.Property`, a :class:`.File` etc.
    """
    Entity = "Entity"
    Event_element = "EventElement"
    """
    Event element

    .. note::

        :class:`.Event_element` is abstract.
    """
    File = "File"

    Multi_language_property = "MultiLanguageProperty"
    """
    Property with a value that can be provided in multiple languages
    """
    Operation = "Operation"
    Property = "Property"
    Range = "Range"
    """
    Range with min and max
    """
    Reference_element = "ReferenceElement"
    """
    Reference
    """
    Relationship_element = "RelationshipElement"
    """
    Relationship
    """

    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, i.e. if a key uses
        :attr:`Submodel_element` the reference may be a :class:`.Property`,
        a :class:`.Submodel_element_list`, an :class:`.Operation` etc.
    """
    Submodel_element_collection = "SubmodelElementCollection"
    """
    Struct of Submodel Elements
    """
    Submodel_element_list = "SubmodelElementList"
    """
    List of Submodel Elements
    """


@reference_in_the_book(section=(5, 7, 10, 3), index=3)
@is_superset_of(enums=[AAS_identifiables, Generic_globally_identifiables])
class Globally_identifiables(Enum):
    """
    Enumeration of all referable elements within an asset administration shell
    """

    Global_reference = "GlobalReference"

    Asset_administration_shell = "AssetAdministrationShell"
    Concept_description = "ConceptDescription"
    Submodel = "Submodel"


@reference_in_the_book(section=(5, 7, 10, 3), index=2)
@is_superset_of(enums=[AAS_referable_non_identifiables, Generic_fragment_keys])
class Fragment_keys(Enum):
    """Enumeration of different key value types within a key."""

    Fragment_reference = "FragmentReference"
    """
    Bookmark or a similar local identifier of a subordinate part of
    a primary resource
    """

    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Asset_administration_shell = "AssetAdministrationShell"
    Basic_event_element = "BasicEventElement"
    Blob = "Blob"
    Capability = "Capability"
    Concept_description = "ConceptDescription"
    Data_element = "DataElement"
    """
    Data element.

    .. note::

        Data Element is abstract, *i.e.* if a key uses :attr:`~Data_element`
        the reference may be a Property, a File etc.
    """

    Entity = "Entity"
    Event_element = "EventElement"
    """
    Event.

    .. note::

        :class:`.Event_element` is abstract.
    """

    File = "File"

    Multi_language_property = "MultiLanguageProperty"
    """Property with a value that can be provided in multiple languages"""

    Operation = "Operation"
    Property = "Property"
    Range = "Range"
    """Range with min and max"""

    Reference_element = "ReferenceElement"
    """
    Reference
    """
    Relationship_element = "RelationshipElement"
    """
    Relationship
    """
    Submodel = "Submodel"
    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, *i.e.* if a key uses :attr:`~Submodel_element`
        the reference may be a :class:`.Property`, an :class:`.Operation` etc.
    """

    Submodel_element_list = "SubmodelElementList"
    """
    List of Submodel Elements
    """
    Submodel_element_collection = "SubmodelElementCollection"
    """
    Struct of Submodel Elements
    """


@reference_in_the_book(section=(5, 7, 10, 3), index=1)
@is_superset_of(enums=[Fragment_keys, Globally_identifiables])
class Key_types(Enum):
    """Enumeration of different key value types within a key."""

    Fragment_reference = "FragmentReference"
    """
    Bookmark or a similar local identifier of a subordinate part of
    a primary resource
    """

    Global_reference = "GlobalReference"

    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Asset_administration_shell = "AssetAdministrationShell"
    Basic_event_element = "BasicEventElement"
    Blob = "Blob"
    Capability = "Capability"
    Concept_description = "ConceptDescription"
    Data_element = "DataElement"
    """
    Data element.

    .. note::

        Data Element is abstract, *i.e.* if a key uses :attr:`~Data_element`
        the reference may be a Property, a File etc.
    """

    Entity = "Entity"
    Event_element = "EventElement"
    """
    Event.

    .. note::

        :class:`.Event_element` is abstract.
    """

    File = "File"

    Multi_language_property = "MultiLanguageProperty"
    """Property with a value that can be provided in multiple languages"""

    Operation = "Operation"
    Property = "Property"
    Range = "Range"
    """Range with min and max"""
    Referable = "Referable"
    Reference_element = "ReferenceElement"
    """
    Reference
    """
    Relationship_element = "RelationshipElement"
    """
    Relationship
    """
    Submodel = "Submodel"
    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, *i.e.* if a key uses :attr:`~Submodel_element`
        the reference may be a :class:`.Property`, an :class:`.Operation` etc.
    """

    Submodel_element_list = "SubmodelElementList"
    """
    List of Submodel Elements
    """
    Submodel_element_collection = "SubmodelElementCollection"
    """
    Struct of Submodel Elements
    """


@reference_in_the_book(section=(5, 7, 11, 3))
class Data_type_def_XSD(Enum):
    """
    Enumeration listing all xsd anySimpleTypes
    """

    Any_URI = "xs:anyURI"
    Base_64_binary = "xs:base64Binary"
    Boolean = "xs:boolean"
    Date = "xs:date"
    Date_time = "xs:dateTime"
    Date_time_stamp = "xs:dateTimeStamp"
    Decimal = "xs:decimal"
    Double = "xs:double"
    Duration = "xs:duration"
    Float = "xs:float"
    G_day = "xs:gDay"
    G_month = "xs:gMonth"
    G_month_day = "xs:gMonthDay"
    G_year = "xs:gYear"
    G_year_month = "xs:gYearMonth"
    Hex_binary = "xs:hexBinary"
    String = "xs:string"
    Time = "xs:time"
    Day_time_duration = "xs:dayTimeDuration"
    Year_month_duration = "xs:yearMonthDuration"
    Integer = "xs:integer"
    Long = "xs:long"
    Int = "xs:int"
    Short = "xs:short"
    Byte = "xs:byte"
    Non_negative_integer = "xs:NonNegativeInteger"
    Positive_integer = "xs:positiveInteger"
    Unsigned_long = "xs:unsignedLong"
    Unsigned_int = "xs:unsignedInt"
    Unsigned_short = "xs:unsignedShort"
    Unsigned_byte = "xs:unsignedByte"
    Non_positive_integer = "xs:nonPositiveInteger"
    Negative_integer = "xs:negativeInteger"


@reference_in_the_book(section=(5, 7, 12, 3), index=4)
class Data_type_def_RDF(Enum):
    """
    Enumeration listing all RDF types
    """

    Lang_string = "rdf:langString"
    """
    String with a language tag

    .. note::

        RDF requires IETF BCP 47  language tags, i.e. simple two-letter language tags
        for Locales like “de” conformant to ISO 639-1 are allowed as well as language
        tags plus extension like “de-DE” for country code, dialect etc. like in “en-US”
        or “en-GB” for English (United Kingdom) and English (United States).
        IETF language tags are referencing ISO 639, ISO 3166 and ISO 15924.

    """


@reference_in_the_book(section=(5, 7, 12, 2))
@is_superset_of(enums=[Data_type_def_XSD, Data_type_def_RDF])
class Data_type_def(Enum):
    """
    string with values of enumerations :class:`.Data_type_def_XSD`,
    :class:`.Data_type_def_RDF`
    """

    Any_URI = "xs:anyURI"
    Base_64_binary = "xs:base64Binary"
    Boolean = "xs:boolean"
    Date = "xs:date"
    Date_time = "xs:dateTime"
    Date_time_stamp = "xs:dateTimeStamp"
    Decimal = "xs:decimal"
    Double = "xs:double"
    Duration = "xs:duration"
    Float = "xs:float"
    G_day = "xs:gDay"
    G_month = "xs:gMonth"
    G_month_day = "xs:gMonthDay"
    G_year = "xs:gYear"
    G_year_month = "xs:gYearMonth"
    Hex_binary = "xs:hexBinary"
    String = "xs:string"
    Time = "xs:time"
    Day_time_duration = "xs:dayTimeDuration"
    Year_month_duration = "xs:yearMonthDuration"
    Integer = "xs:integer"
    Long = "xs:long"
    Int = "xs:int"
    Short = "xs:short"
    Byte = "xs:byte"
    Non_negative_integer = "xs:NonNegativeInteger"
    Positive_integer = "xs:positiveInteger"
    Unsigned_long = "xs:unsignedLong"
    Unsigned_int = "xs:unsignedInt"
    Unsigned_short = "xs:unsignedShort"
    Unsigned_byte = "xs:unsignedByte"
    Non_positive_integer = "xs:nonPositiveInteger"
    Negative_integer = "xs:negativeInteger"
    Lang_string = "rdf:langString"


@reference_in_the_book(section=(5, 7, 12, 1))
class Lang_string(DBC):
    """Strings with language tags"""

    language: BCP_47_language_tag
    """Language tag conforming to BCP 47"""

    text: str
    """Text in the :attr:`~language`"""

    def __init__(self, language: BCP_47_language_tag, text: str) -> None:
        self.language = language
        self.text = text


@reference_in_the_book(section=(5, 7, 12, 2))
@invariant(lambda self: lang_strings_have_unique_languages(self.lang_strings))
@invariant(lambda self: len(self.lang_strings) >= 1)
class Lang_string_set(DBC):
    """
    Array of elements of type langString

    .. note::

        langString is a RDF data type.

    A langString is a string value tagged with a language code.
    It depends on the serialization rules for a technology how
    this is realized.
    """

    lang_strings: List[Lang_string]
    """Strings in different languages"""

    def __init__(self, lang_strings: List[Lang_string]) -> None:
        self.lang_strings = lang_strings


@abstract
@reference_in_the_book(section=(6, 2, 1, 1), index=1)
class Data_specification_content:
    """
    Data specification content is part of a data specification template and defines
    which additional attributes shall be added to the element instance that references
    the data specification template and meta information about the template itself.
    """


@abstract
@reference_in_the_book(section=(6, 2, 1, 1))
class Data_specification:
    """
    Data Specification Template
    """

    id: Identifier
    """
    The globally unique identification of the element.
    """

    data_specification_content: Data_specification_content
    """
    The content of the template without meta data
    """

    administration: Optional[Administrative_information]
    """
    Administrative information of an identifiable element.

    .. note::

        Some of the administrative information like the version number might need to
        be part of the identification.
    """

    description: Optional[Lang_string_set]
    """
    Description how and in which context the data specification template is applicable.
    The description can be provided in several languages.
    """

    def __init__(
        self,
        id: Identifier,
        data_specification_content: Data_specification_content,
        administration: Optional[Administrative_information],
        description: Optional[Lang_string_set],
    ) -> None:
        self.id = id
        self.data_specification_content = data_specification_content
        self.administration = administration
        self.description = description


@reference_in_the_book(section=(5, 7, 9))
class Environment:
    """
    Container for the sets of different identifiables.

    .. note::

        w.r.t. file exchange: There is exactly one environment independent on how many
        files the contained elements are split. If the file is split then there
        shall be no element with the same identifier in two different files.
    """

    asset_administration_shells: Optional[List[Asset_administration_shell]]
    """
    Asset administration shell
    """

    submodels: Optional[List[Submodel]]
    """
    Submodel
    """

    concept_descriptions: Optional[List[Concept_description]]
    """
    Concept description
    """

    data_specifications: Optional[List[Data_specification]]
    """
    Data specification
    """

    def __init__(
        self,
        asset_administration_shells: Optional[List[Asset_administration_shell]] = None,
        submodels: Optional[List[Submodel]] = None,
        concept_descriptions: Optional[List[Concept_description]] = None,
        data_specifications: Optional[List[Data_specification]] = None,
    ) -> None:
        self.asset_administration_shells = asset_administration_shells
        self.submodels = submodels
        self.concept_descriptions = concept_descriptions
        self.data_specifications = data_specifications
