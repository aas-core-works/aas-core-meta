"""
--- WORK IN PROGRESS ---
Provide an implementation of the Asset Administration Shell (AAS) V3.2.

The presented version of the Metamodel is related to the work of
aas-core-works, which can be found here: https://github.com/aas-core-works.

The presented content is neither related to the IDTA nor
Plattform Industrie 4.0 and does not represent an official publication.

We diverge from the book in the following points.

We did not implement the following constraints as they are too general and can not
be formalized as part of the core library, but affects external components such as
AAS registry or AAS server:

* :constraintref:`AASd-022`

We did not implement the following constraints since they depend on registry and
de-referencing of :class:`Reference` objects:

* :constraintref:`AASd-006`
* :constraintref:`AASd-007`
* :constraintref:`AASc-3a-003`

Some constraints are not enforceable as they depend on the wider context
such as language understanding, so we could not formalize them:

* :constraintref:`AASd-012`: This constraint requires that the texts inside
  ``Multi_language_property`` shall have the same meanings in the separate languages.
  This cannot be tested.

Furthermore, we diverge from the book in the following points regarding
the enumerations. We have to implement subsets of enumerations as sets as common
programming languages do not support inheritance of enumerations. The relationship
between the properties and the sets is defined through invariants. This causes
the following divergences:

* We decided therefore to remove the enumeration ``DataTypeDefRDF``
  and keep only :class:`Data_type_def_XSD` as enumeration. Otherwise, we would have
  to write redundant invariants all over the meta-model because ``DataTypeDefRDF``
  is actually never used in any type definition.

* The enumeration :class:`AAS_submodel_elements` is used in two different contexts.
  One context is the definition of key types in a reference. Another context is
  the definition of element types in a :class:`Submodel_element_list`.

  To avoid confusion, we introduce two separate enumerations for the separate contexts.
  Firstly, a set of :class:`Key_types`, :const:`AAS_submodel_elements_as_keys` to
  represent the first context (key type in a reference).
  Secondly, the enumeration :class:`AAS_submodel_elements` is kept as designator
  for :attr:`Submodel_element_list.type_value_list_element`.

* The specification introduces several types of ``Lang_string_set``.
  These types differ between the allowed length of their text inside the singular
  ``Lang_string`` objects. Since the native representation of ``Lang_string_set`` as
  ``List`` of ``Lang_string`` is required by specification, it is impossible to
  introduce separate ``Lang_string_set`` types. Therefore, the distinction is drawn here
  between the ``Lang_string`` types.

  ``DefinitionTypeIEC61360`` is represented as a
  ``List`` of :class:`Lang_string_definition_type_IEC_61360`

  ``MultiLanguageNameType`` is represented as a
  ``List`` of :class:`Lang_string_name_type`

  ``PreferredNameTypeIEC61360`` is represented as a
  ``List`` of :class:`Lang_string_preferred_name_type_IEC_61360`

  ``ShortNameTypeIEC61360`` is represented as a
  ``List`` of :class:`Lang_string_short_name_type_IEC_61360`

  ``MultiLanguageTextType`` is represented as a
  ``List`` of :class:`Lang_string_text_type`

  Furthermore, since ``Lang_string`` is not used anywhere, we rename it to
  :class:`Abstract_lang_string`.

Concerning the data specifications, we embed them within
:class:`Has_data_specification` instead of referencing them *via* an external reference.
The working group decided to change the rules for serialization *after* the book was
published. The data specifications are critical in applications, but there is no
possibility to access them through a data channel as they are not part of
an environment.
"""

from enum import Enum
from re import match
from typing import List, Optional, Set

from icontract import invariant, DBC, ensure

from aas_core_meta.marker import (
    abstract,
    serialization,
    implementation_specific,
    verification,
    constant_set,
    non_mutating,
)

__version__ = "V3.2"

__xml_namespace__ = "https://admin-shell.io/aas/3/2"


# region Verification


@verification
def matches_ID_short(text: str) -> bool:
    """
    Check that :paramref:`text` is a valid short ID.
    """
    pattern = f"^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9_]+$"

    return match(pattern, text) is not None


@verification
def matches_version_type(text: str) -> bool:
    """
    Check that :paramref:`text` is a valid version string.
    """
    pattern = f"^(0|[1-9][0-9]*)$"

    return match(pattern, text) is not None


@verification
def matches_revision_type(text: str) -> bool:
    """
    Check that :paramref:`text` is a valid revision string.
    """
    pattern = f"^(0|[1-9][0-9]*)$"

    return match(pattern, text) is not None


@verification
def matches_xs_date_time_UTC(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:dateTime``.

    The time zone must be fixed to UTC. We verify only that the ``text`` matches
    a pre-defined pattern. We *do not* verify that the day of month is
    correct nor do we check for leap seconds.

    See: https://www.w3.org/TR/xmlschema-2/#dateTime

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
    timezone_frag = r"(Z|\+00:00|-00:00)"
    date_time_lexical_rep = (
        f"{year_frag}-{month_frag}-{day_frag}"
        f"T"
        f"(({hour_frag}:{minute_frag}:{second_frag})|{end_of_day_frag})"
        f"{timezone_frag}"
    )
    pattern = f"^{date_time_lexical_rep}$"

    return match(pattern, text) is not None


# noinspection PyUnusedLocal
@verification
@implementation_specific
def is_xs_date_time_UTC(text: str) -> bool:
    """
    Check that :paramref:`text` is a ``xs:dateTime`` with time zone set to UTC.

    The ``text`` is assumed to match a pre-defined pattern for ``xs:dateTime`` with
    the time zone set to UTC. In this function, we check for days of month (e.g.,
    February 29th).

    See: https://www.w3.org/TR/xmlschema-2/#dateTime

    :param text: Text to be checked
    :returns: True if the :paramref:`text` is a valid ``xs:dateTime`` in UTC
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


@verification
def matches_RFC_2396(text: str) -> bool:
    """
    Check that :paramref:`text` matches to the URI pattern defined in RFC 2396

    The definition has been taken from:
    https://datatracker.ietf.org/doc/html/rfc2396

    Note that RFX 2396 alone is not enough for specifying ``xs:anyURI`` for
    XSD version 1.0, as that specifies URI together with the amendment of
    RFC 2732.

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    alphanum = "[a-zA-Z0-9]"
    mark = "[\\-_.!~*'()]"
    unreserved = f"({alphanum}|{mark})"
    hex = "([0-9]|[aA]|[bB]|[cC]|[dD]|[eE]|[fF]|[aA]|[bB]|[cC]|[dD]|[eE]|[fF])"
    escaped = f"%{hex}{hex}"
    pchar = f"({unreserved}|{escaped}|[:@&=+$,])"
    param = f"({pchar})*"
    segment = f"({pchar})*(;{param})*"
    path_segments = f"{segment}(/{segment})*"
    abs_path = f"/{path_segments}"
    scheme = "[a-zA-Z][a-zA-Z0-9+\\-.]*"
    userinfo = f"({unreserved}|{escaped}|[;:&=+$,])*"
    domainlabel = f"({alphanum}|{alphanum}({alphanum}|-)*{alphanum})"
    toplabel = f"([a-zA-Z]|[a-zA-Z]({alphanum}|-)*{alphanum})"
    hostname = f"({domainlabel}\\.)*{toplabel}(\\.)?"
    ipv4address = "[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+"
    host = f"({hostname}|{ipv4address})"
    port = "[0-9]*"
    hostport = f"{host}(:{port})?"
    server = f"(({userinfo}@)?{hostport})?"
    reg_name = f"({unreserved}|{escaped}|[$,;:@&=+])+"
    authority = f"({server}|{reg_name})"
    net_path = f"//{authority}({abs_path})?"
    reserved = "[;/?:@&=+$,]"
    uric = f"({reserved}|{unreserved}|{escaped})"
    query = f"({uric})*"
    hier_part = f"({net_path}|{abs_path})(\\?{query})?"
    uric_no_slash = f"({unreserved}|{escaped}|[;?:@&=+$,])"
    opaque_part = f"{uric_no_slash}({uric})*"
    absoluteuri = f"{scheme}:({hier_part}|{opaque_part})"
    fragment = f"({uric})*"
    rel_segment = f"({unreserved}|{escaped}|[;@&=+$,])+"
    rel_path = f"{rel_segment}({abs_path})?"
    relativeuri = f"({net_path}|{abs_path}|{rel_path})(\\?{query})?"
    uri_reference = f"^({absoluteuri}|{relativeuri})?(\\#{fragment})?$"
    return match(uri_reference, text) is not None


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
    extlang = "[a-zA-Z]{3}(-[a-zA-Z]{3}){,2}"
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
def lang_strings_have_unique_languages(
    lang_strings: List["Abstract_lang_string"],
) -> bool:
    """
    Check that the :paramref:`lang_strings` do not have overlapping
    :attr:`Abstract_lang_string.language`'s
    """
    # NOTE (mristin):
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
    Check that :attr:`Qualifier.type`'s of :paramref:`qualifiers` are unique.

    :param qualifiers: to be checked
    :return: True if all :attr:`Qualifier.type`'s are unique
    """
    # NOTE (mristin):
    # This implementation is given here only as reference. It needs to be adapted
    # for each implementation separately.
    observed_types = set()
    for qualifier in qualifiers:
        if qualifier.type in observed_types:
            return False

        observed_types.add(qualifier.type)

    return True


@verification
def matches_XML_serializable_string(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of the Constraint AASd-130.

    Ensures that encoding is possible and interoperability between different
    serializations is possible.

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # noinspection SpellCheckingInspection
    pattern = r"^[\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]*$"
    return match(pattern, text) is not None


# noinspection SpellCheckingInspection
@verification
def matches_xs_any_URI(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:anyURI``.

    See: https://www.w3.org/TR/xmlschema-2/#anyURI and
    https://datatracker.ietf.org/doc/html/rfc2396 and
    https://datatracker.ietf.org/doc/html/rfc2732

    Note, that version 1.0 of the XSD specification defines ``xs:anyURI`` as
    "defined by RFC 2396, as amended by RFC 2732". Therefore, we use a
    pattern here that implements the amendments of RFC 2732. This should not
    be confused with ``matches_RFC_2396``, which does not include those
    amendments and is used in different parts of the specification.

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    alphanum = "[a-zA-Z0-9]"
    mark = "[\\-_.!~*'()]"
    unreserved = f"({alphanum}|{mark})"
    hex = "([0-9]|[aA]|[bB]|[cC]|[dD]|[eE]|[fF]|[aA]|[bB]|[cC]|[dD]|[eE]|[fF])"
    escaped = f"%{hex}{hex}"
    pchar = f"({unreserved}|{escaped}|[:@&=+$,])"
    param = f"({pchar})*"
    segment = f"({pchar})*(;{param})*"
    path_segments = f"{segment}(/{segment})*"
    abs_path = f"/{path_segments}"
    scheme = "[a-zA-Z][a-zA-Z0-9+\\-.]*"
    userinfo = f"({unreserved}|{escaped}|[;:&=+$,])*"
    domainlabel = f"({alphanum}|{alphanum}({alphanum}|-)*{alphanum})"
    toplabel = f"([a-zA-Z]|[a-zA-Z]({alphanum}|-)*{alphanum})"
    hostname = f"({domainlabel}\\.)*{toplabel}(\\.)?"
    ipv4address = "[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}"
    hex4 = "[0-9A-Fa-f]{1,4}"
    hexseq = f"{hex4}(:{hex4})*"
    hexpart = f"({hexseq}|{hexseq}::({hexseq})?|::({hexseq})?)"
    ipv6address = f"{hexpart}(:{ipv4address})?"
    ipv6reference = f"\\[{ipv6address}\\]"
    host = f"({hostname}|{ipv4address}|{ipv6reference})"
    port = "[0-9]*"
    hostport = f"{host}(:{port})?"
    server = f"(({userinfo}@)?{hostport})?"
    reg_name = f"({unreserved}|{escaped}|[$,;:@&=+])+"
    authority = f"({server}|{reg_name})"
    net_path = f"//{authority}({abs_path})?"
    reserved = "[;/?:@&=+$,\\[\\]]"
    uric = f"({reserved}|{unreserved}|{escaped})"
    query = f"({uric})*"
    hier_part = f"({net_path}|{abs_path})(\\?{query})?"
    uric_no_slash = f"({unreserved}|{escaped}|[;?:@&=+$,])"
    opaque_part = f"{uric_no_slash}({uric})*"
    absoluteuri = f"{scheme}:({hier_part}|{opaque_part})"
    fragment = f"({uric})*"
    rel_segment = f"({unreserved}|{escaped}|[;@&=+$,])+"
    rel_path = f"{rel_segment}({abs_path})?"
    relativeuri = f"({net_path}|{abs_path}|{rel_path})(\\?{query})?"
    uri_reference = f"^({absoluteuri}|{relativeuri})?(\\#{fragment})?$"
    return match(uri_reference, text) is not None


# noinspection SpellCheckingInspection
@verification
def matches_xs_base_64_binary(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:base64Binary``.

    See: https://www.w3.org/TR/xmlschema-2/#base64Binary

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

    See: https://www.w3.org/TR/xmlschema-2/#boolean

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    pattern = "^(true|false|1|0)$"
    return match(pattern, text) is not None


@verification
def matches_xs_date(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:date``.

    See: https://www.w3.org/TR/xmlschema-2/#date

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    digit = "[0-9]"
    year_frag = f"-?(([1-9]{digit}{digit}{digit}+)|(0{digit}{digit}{digit}))"
    month_frag = f"((0[1-9])|(1[0-2]))"
    day_frag = f"((0[1-9])|([12]{digit})|(3[01]))"
    minute_frag = f"[0-5]{digit}"
    timezone_frag = rf"(Z|(\+|-)((0{digit}|1[0-3]):{minute_frag}|14:00))"
    date_lexical_rep = f"{year_frag}-{month_frag}-{day_frag}{timezone_frag}?"

    pattern = f"^{date_lexical_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_date_time(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:dateTime``.

    See: https://www.w3.org/TR/xmlschema-2/#dateTime

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
    timezone_frag = rf"(Z|(\+|-)((0{digit}|1[0-3]):{minute_frag}|14:00))"
    date_time_lexical_rep = (
        f"{year_frag}-{month_frag}-{day_frag}"
        f"T"
        f"(({hour_frag}:{minute_frag}:{second_frag})|{end_of_day_frag})"
        f"{timezone_frag}?"
    )

    pattern = f"^{date_time_lexical_rep}$"
    return match(pattern, text) is not None


# noinspection PyUnusedLocal
@verification
@implementation_specific
def is_xs_date_time(text: str) -> bool:
    """
    Check that :paramref:`text` is a ``xs:dateTime``.

    The ``text`` is assumed to match a pre-defined pattern for ``xs:dateTime``.
    In this function, we check for days of month (e.g., February 29th).

    See: https://www.w3.org/TR/xmlschema-2/#dateTime

    :param text: Text to be checked
    :returns: True if the :paramref:`text` is a valid ``xs:dateTime``
    """
    raise NotImplementedError()


# noinspection SpellCheckingInspection
@verification
def matches_xs_decimal(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:decimal``.

    See: https://www.w3.org/TR/xmlschema-2/#decimal

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

    See: https://www.w3.org/TR/xmlschema-2/#double

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin):
    # See: https://www.w3.org/TR/xmlschema-2/#nt-doubleRep
    double_rep = r"((\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([Ee](\+|-)?[0-9]+)?|-?INF|NaN)"

    pattern = f"^{double_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_duration(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:duration``.

    See: https://www.w3.org/TR/xmlschema-2/#duration

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin):
    # See https://www.w3.org/TR/xmlschema-2/#nt-durationRep

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

    See: https://www.w3.org/TR/xmlschema-2/#float

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    float_rep = (
        r"((\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([Ee](\+|-)?[0-9]+)?" r"|-?INF|NaN)"
    )

    pattern = f"^{float_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_g_day(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:gDay``.

    See: https://www.w3.org/TR/xmlschema-2/#gDay

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin):
    # See https://www.w3.org/TR/xmlschema-2/#nt-gDayRep
    g_day_lexical_rep = (
        r"---(0[1-9]|[12][0-9]|3[01])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    )

    pattern = f"^{g_day_lexical_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_g_month(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:gMonth``.

    See: https://www.w3.org/TR/xmlschema-2/#gMonth

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin):
    # See https://www.w3.org/TR/xmlschema-2/#nt-gMonthRep
    g_month_lexical_rep = (
        r"--(0[1-9]|1[0-2])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    )

    pattern = f"^{g_month_lexical_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_g_month_day(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:gMonthDay``.

    See: https://www.w3.org/TR/xmlschema-2/#gMonthDay

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin):
    # See https://www.w3.org/TR/xmlschema-2/#nt-gMonthDayRep
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

    See: https://www.w3.org/TR/xmlschema-2/#gYear

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin):
    # See https://www.w3.org/TR/xmlschema-2/#nt-gYearRep
    g_year_rep = (
        r"-?([1-9][0-9]{3,}|0[0-9]{3})(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    )

    pattern = f"^{g_year_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_g_year_month(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:gYearMonth``.

    See: https://www.w3.org/TR/xmlschema-2/#gYearMonth

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin):
    # See https://www.w3.org/TR/xmlschema-2/#nt-gYearMonthRep

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

    See: https://www.w3.org/TR/xmlschema-2/#hexBinary

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin):
    # See https://www.w3.org/TR/xmlschema-2/#nt-hexBinary
    hex_binary = r"([0-9a-fA-F]{2})*"

    pattern = f"^{hex_binary}$"
    return match(pattern, text) is not None


@verification
def matches_xs_time(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:time``.

    See: https://www.w3.org/TR/xmlschema-2/#time

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # NOTE (mristin):
    # See https://www.w3.org/TR/xmlschema-2/#nt-timeRep
    time_rep = (
        r"(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))"
        r"(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    )

    pattern = f"^{time_rep}$"
    return match(pattern, text) is not None


@verification
def matches_xs_integer(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:integer``.

    See: https://www.w3.org/TR/xmlschema-2/#integer

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

    See: https://www.w3.org/TR/xmlschema-2/#long

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

    See: https://www.w3.org/TR/xmlschema-2/#int

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

    See: https://www.w3.org/TR/xmlschema-2/#short

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

    See: https://www.w3.org/TR/xmlschema-2/#byte

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

    See: https://www.w3.org/TR/xmlschema-2/#nonNegativeInteger

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    non_negative_integer_rep = r"(-0|\+?[0-9]+)"

    pattern = f"^{non_negative_integer_rep}$"
    return match(pattern, text) is not None


# noinspection PyUnusedLocal
@verification
@implementation_specific
def is_xs_non_negative_integer(text: str) -> bool:
    """
    Check that :paramref:`text` is a valid ``xs:nonNegativeInteger``.

    The ``text`` is assumed to match a pre-defined pattern for
    ``xs:nonNegativeInteger``. In this function, we check that the represented
    number fits within the value range supported by the target implementation.

    See: https://www.w3.org/TR/xmlschema-2/#nonNegativeInteger

    :param text: Text to be checked
    :returns: True if the :paramref:`text` is a valid ``xs:nonNegativeInteger``
    """
    raise NotImplementedError()


@verification
def matches_xs_positive_integer(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of an ``xs:positiveInteger``.

    See: https://www.w3.org/TR/xmlschema-2/#positiveInteger

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

    See: https://www.w3.org/TR/xmlschema-2/#unsignedLong

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

    See: https://www.w3.org/TR/xmlschema-2/#unsignedInt

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

    See: https://www.w3.org/TR/xmlschema-2/#unsignedShort

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

    See: https://www.w3.org/TR/xmlschema-2/#unsignedByte

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

    See: https://www.w3.org/TR/xmlschema-2/#nonPositiveInteger

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

    See: https://www.w3.org/TR/xmlschema-2/#negativeInteger

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

    See: https://www.w3.org/TR/xmlschema-2/#string

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    # From: https://www.w3.org/TR/xml11/#NT-Char
    # Any Unicode character, excluding the surrogate blocks, FFFE, and FFFF.
    # noinspection SpellCheckingInspection
    pattern = r"^[\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]*$"
    return match(pattern, text) is not None


# noinspection PyUnusedLocal
@verification
@implementation_specific
def value_consistent_with_XSD_type(value: str, value_type: "Data_type_def_XSD") -> bool:
    """
    Check that the :paramref:`value` conforms to its :paramref:`value_type`.

    :param value: which needs to conform
    :param value_type: pre-defined value type
    :return: True if the :paramref:`value` conforms
    """
    # NOTE (mristin):
    # We specify the pattern-matching functions above, and they should be handy to check
    # for most obvious pattern mismatches.
    #
    # However, bear in mind that the pattern checks are not enough! For example,
    # consider a ``xs:dateTime``. You need to check not only that the value
    # follows the pattern, but also that the day-of-month and leap seconds are taken
    # into account.

    raise NotImplementedError()


@verification
def is_model_reference_to(reference: "Reference", expected_type: "Key_types") -> bool:
    """
    Check that the target of the model reference matches the :paramref:`expected_type`.
    """
    # fmt: off
    return (
        reference.type == Reference_types.Model_reference
        and len(reference.keys) != 0
        and reference.keys[-1].type == expected_type
    )
    # fmt: on


@verification
def is_model_reference_to_referable(reference: "Reference") -> bool:
    """Check that the target of the reference matches a :const:`AAS_referables`."""
    # fmt: off
    return (
        reference.type == Reference_types.Model_reference
        and len(reference.keys) != 0
        and reference.keys[-1].type in AAS_referables
    )
    # fmt: on


@verification
@implementation_specific
def ID_shorts_are_unique(referables: List["Referable"]) -> bool:
    """
    Check that the :attr:`Referable.ID_short`'s among the :paramref:`referables` are
    unique in their namespace.
    """
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as reference.
    id_short_set = set()
    for referable in referables:
        if referable.ID_short is not None:
            if referable.ID_short in id_short_set:
                return False

            id_short_set.add(referable.ID_short)

    return True


@verification
@implementation_specific
def ID_shorts_of_variables_are_unique(
    input_variables: Optional[List["Operation_variable"]],
    output_variables: Optional[List["Operation_variable"]],
    inoutput_variables: Optional[List["Operation_variable"]],
) -> bool:
    """
    Check that the :attr:`Referable.ID_short`'s among all the
    :paramref:`input_variables`, :paramref:`output_variables`
    and :paramref:`inoutput_variables` are unique.
    """
    # NOTE (s-heppner):
    # This implementation will not be transpiled, but is given here as reference.
    id_short_set = set()
    if input_variables is not None:
        for variable in input_variables:
            if variable.value.ID_short is not None:
                if variable.value.ID_short in id_short_set:
                    return False

                id_short_set.add(variable.value.ID_short)
    if output_variables is not None:
        for variable in output_variables:
            if variable.value.ID_short is not None:
                if variable.value.ID_short in id_short_set:
                    return False

                id_short_set.add(variable.value.ID_short)
    if inoutput_variables is not None:
        for variable in inoutput_variables:
            if variable.value.ID_short is not None:
                if variable.value.ID_short in id_short_set:
                    return False

                id_short_set.add(variable.value.ID_short)
    return True


@verification
def specific_asset_ID_name_matches_global_asset_ID(name: str) -> bool:
    """Check whether :paramref:`name` is the reserved global asset ID key."""
    pattern = "^[gG][lL][oO][bB][aA][lL][aA][sS][sS][eE][tT][iI][dD]$"
    return match(pattern, name) is not None


@verification
@implementation_specific
def submodel_element_has_template_qualifier_in_tree(
    element: "Submodel_element",
) -> bool:
    """Check whether :paramref:`element` or its descendants have template qualifiers."""
    # NOTE (aaronzi):
    # This implementation will not be transpiled, but is given here as reference.
    if element.qualifiers is not None and any(
        qualifier.kind_or_default() == Qualifier_kind.Template_qualifier
        for qualifier in element.qualifiers
    ):
        return True

    if isinstance(element, Submodel_element_list):
        return element.value is not None and any(
            submodel_element_has_template_qualifier_in_tree(child)
            for child in element.value
        )

    if isinstance(element, Submodel_element_collection):
        return element.value is not None and any(
            submodel_element_has_template_qualifier_in_tree(child)
            for child in element.value
        )

    if isinstance(element, Entity):
        return element.statements is not None and any(
            submodel_element_has_template_qualifier_in_tree(child)
            for child in element.statements
        )

    if isinstance(element, Annotated_relationship_element):
        return element.annotations is not None and any(
            submodel_element_has_template_qualifier_in_tree(child)
            for child in element.annotations
        )

    return False


@verification
@implementation_specific
def submodel_elements_have_no_template_qualifiers(
    elements: List["Submodel_element"],
) -> bool:
    """Check that :paramref:`elements` have no template qualifiers in their trees."""
    # NOTE (aaronzi):
    # This implementation will not be transpiled, but is given here as reference.
    return all(
        not submodel_element_has_template_qualifier_in_tree(element)
        for element in elements
    )


@verification
@implementation_specific
def submodel_element_lists_have_exactly_one_element_in_tree(
    element: "Submodel_element",
) -> bool:
    """Recursively check that submodel element lists have exactly one child."""
    # NOTE (aaronzi):
    # This implementation will not be transpiled, but is given here as reference.
    if isinstance(element, Submodel_element_list):
        return (
            element.value is not None
            and len(element.value) == 1
            and all(
                submodel_element_lists_have_exactly_one_element_in_tree(child)
                for child in element.value
            )
        )

    if isinstance(element, Submodel_element_collection):
        return element.value is None or all(
            submodel_element_lists_have_exactly_one_element_in_tree(child)
            for child in element.value
        )

    if isinstance(element, Entity):
        return element.statements is None or all(
            submodel_element_lists_have_exactly_one_element_in_tree(child)
            for child in element.statements
        )

    if isinstance(element, Annotated_relationship_element):
        return element.annotations is None or all(
            submodel_element_lists_have_exactly_one_element_in_tree(child)
            for child in element.annotations
        )

    return True


@verification
@implementation_specific
def submodel_element_lists_in_submodel_elements_have_exactly_one_element(
    elements: List["Submodel_element"],
) -> bool:
    """Check that all submodel element lists among :paramref:`elements` have one item."""
    # NOTE (aaronzi):
    # This implementation will not be transpiled, but is given here as reference.
    return all(
        submodel_element_lists_have_exactly_one_element_in_tree(element)
        for element in elements
    )


@verification
@implementation_specific
def submodel_element_lists_in_operation_variables_have_exactly_one_element(
    input_variables: Optional[List["Operation_variable"]],
    output_variables: Optional[List["Operation_variable"]],
    inoutput_variables: Optional[List["Operation_variable"]],
) -> bool:
    """Check that submodel element lists in operation variables have one item."""
    # NOTE (aaronzi):
    # This implementation will not be transpiled, but is given here as reference.
    for variable_list in (input_variables, output_variables, inoutput_variables):
        if variable_list is None:
            continue

        for variable in variable_list:
            if not submodel_element_lists_have_exactly_one_element_in_tree(
                variable.value
            ):
                return False

    return True


@verification
@implementation_specific
def extension_names_are_unique(extensions: List["Extension"]) -> bool:
    """Check that the extension names are unique."""
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as reference.
    name_set = set()
    for extension in extensions:
        if extension.name in name_set:
            return False
        name_set.add(extension.name)

    return True


@verification
@implementation_specific
def submodel_elements_have_identical_semantic_IDs(
    elements: List["Submodel_element"],
) -> bool:
    """Check that all semantic IDs are identical, if specified."""
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as a reference.
    semantic_ID = None
    for element in elements:
        if element.semantic_ID is not None:
            if semantic_ID is None:
                semantic_ID = element.semantic_ID
            else:
                if semantic_ID != element.semantic_ID:
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
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as reference.
    for element in elements:
        if isinstance(element, (Property, Range)):
            if element.value_type != value_type:
                return False

    return True


@verification
@implementation_specific
def reference_key_values_equal(that: "Reference", other: "Reference") -> bool:
    """Check that the two references are equal by comparing their key values."""
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as reference.
    if len(that.keys) != len(other.keys):
        return False

    for that_key, other_key in zip(that.keys, other.keys):
        if that_key.value != other_key.value:
            return False

    return True


# endregion


@invariant(
    lambda self: matches_XML_serializable_string(self),
    "Constraint AASd-130: An attribute with data type 'string' shall consist "
    "of these characters only: "
    r"^[\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]*$.",
)
class XML_serializable_string(str, DBC):
    r"""
    Represent a string which must be serializable to XML.

    :constraint AASd-130:

        An attribute with data type "string" shall consist of these characters only:
        ``^[\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\u00010000-\u0010FFFF]*$``.
    """


# fmt: off
@invariant(
    lambda self: len(self) >= 1,
    "The value must not be empty."
)
# fmt: on
class Non_empty_XML_serializable_string(XML_serializable_string, DBC):
    """Represent an XML-serializable string with at least one character."""


@invariant(
    lambda self: is_xs_date_time_UTC(self),
    "The value must represent a valid xs:dateTime with the time zone fixed to UTC.",
)
@invariant(
    lambda self: matches_xs_date_time_UTC(self),
    "The value must match the pattern of xs:dateTime with the time zone fixed to UTC.",
)
class Date_time_UTC(str, DBC):
    """Represent an ``xs:dateTime`` with the time zone fixed to UTC."""


@invariant(
    lambda self: is_xs_date_time(self),
    "The value must represent a valid xs:dateTime.",
)
@invariant(
    lambda self: matches_xs_date_time(self),
    "The value must match the pattern of xs:dateTime.",
)
class Date_time(str, DBC):
    """Represent an ``xs:dateTime``."""


@invariant(
    lambda self: matches_xs_duration(self),
    "The value must match the pattern of xs:duration.",
)
class Duration(str, DBC):
    """Represent an ``xs:duration``."""


class Blob_type(bytearray, DBC):
    """Group of bytes to represent file content (binaries and non-binaries)"""


@invariant(
    lambda self: len(self) <= 2048,
    "Identifier shall have a maximum length of 2048 characters.",
)
class Identifier(Non_empty_XML_serializable_string, DBC):
    """
    string

    .. note::

        It is recommended to use existing standards, for example ID-Link
        (IEC 61406) may be used for :attr:`Asset_information.global_asset_ID`.

        Typically, identifier strings do not contain blanks, emoticons or
        carriage returns because they are not representable in existing systems.
    """


@invariant(
    lambda self: len(self) <= 2048,
    "Value type IEC 61360 shall have a maximum length of 2048 characters.",
)
class Value_type_IEC_61360(Non_empty_XML_serializable_string):
    """
    string
    """


@invariant(
    lambda self: len(self) <= 128,
    "Name type shall have a maximum length of 128 characters.",
)
class Name_type(Non_empty_XML_serializable_string, DBC):
    """
    string with length 128 maximum and 1 minimum
    """


@invariant(
    lambda self: len(self) <= 4,
    "Version type shall have a maximum length of 4 characters.",
)
@invariant(
    lambda self: matches_version_type(self),
    "Version type shall match the version pattern.",
)
class Version_type(Non_empty_XML_serializable_string):
    """
    string with max 4 and min 1 characters
    following the following regular expression: ``^([0-9]|[1-9][0-9]*)$``
    """


@invariant(
    lambda self: len(self) <= 4,
    "Revision type shall have a maximum length of 4 characters.",
)
@invariant(
    lambda self: matches_revision_type(self),
    "Revision type shall match the revision pattern.",
)
class Revision_type(Non_empty_XML_serializable_string):
    """
    string with max 4 and min 1 characters
    following the following regular expression: ``^([0-9]|[1-9][0-9]*)$``
    """


@invariant(
    lambda self: len(self) <= 64,
    "Label type shall have a maximum length of 64 characters.",
)
class Label_type(Non_empty_XML_serializable_string, DBC):
    """
    string with max 64 and min 1 characters
    """


@invariant(
    lambda self: len(self) <= 255,
    "Message topic type shall have a maximum length of 255 characters.",
)
class Message_topic_type(Non_empty_XML_serializable_string, DBC):
    """
    string with max 255 and min 1 characters
    """


# noinspection SpellCheckingInspection
@invariant(
    lambda self: matches_BCP_47(self),
    "The value must represent a value language tag conformant to BCP 47.",
)
class BCP_47_language_tag(str, DBC):
    """
    Represent a language tag conformant to BCP 47.

    See: https://tools.ietf.org/rfc/bcp/bcp47.txt
    """


@invariant(
    lambda self: matches_MIME_type(self),
    "The value must represent a valid content MIME type according to RFC 2046.",
)
@invariant(
    lambda self: len(self) <= 128,
    "Content type shall have a maximum length of 128 characters.",
)
class Content_type(Non_empty_XML_serializable_string, DBC):
    """
    string with max 128 and min 1 characters

    Any content type as specified in RFC2046.

    The content type should be registered by the Internet Assigned Numbers
    Authority (IANA) as specified in RFC2048.
    """


@invariant(
    lambda self: matches_RFC_2396(self),
    "String with max 2048 and min 1 characters conformant to a URI as per RFC 2396.",
)
class Path_type(Identifier, DBC):
    """
    Identifier

    string with max 2048 and min 1 characters

    conformant to a URI as per RFC 2396

    .. note::

        Values with this restriction are also conformant to the xsd datatype
        anyURI.

        "A wide range of internationalized resource identifiers can be
        specified when an anyURI is called for, and still be understood as
        URIs per RFC 2396 and its successor(s)."

        Source: W3C XML Schema Definition Language (XSD) 1.0 Part 2: Datatypes
    """

    pass


class Qualifier_type(Name_type, DBC):
    """
    NameType
    """


class Value_data_type(XML_serializable_string, DBC):
    """
    any XSD atomic type as specified via :class:`Data_type_def_XSD`
    """


@invariant(
    lambda self: matches_ID_short(self),
    "AASd-002: ID-short of Referables shall consist of at least two characters "
    "and shall only feature letters, digits, hyphen (``-``) and underscore (``_``); "
    "starting mandatory with a letter, and not ending with a hyphen, "
    "*I.e.* ``^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9_]+$``.",
)
class ID_short_type(Name_type, DBC):
    """
    Represent a short ID of an :class:`Referable`.

    :constraint AASd-002:

        ID-short of :class:`Referable`'s shall consist of at least two characters
        and shall only feature letters, digits, hyphen (``-``) and underscore
        (``_``); starting mandatory with a letter,
        and not ending with a hyphen, *I.e.* ``^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9_]+$``.

    :constraint AASd-117:

        :attr:`Referable.ID_short` of non-identifiable :class:`Referable`'s
        not being a direct child of a :class:`Submodel_element_list` shall
        be specified.
    """


@abstract
# fmt: off
@invariant(
    lambda self:
    not (self.supplemental_semantic_IDs is not None)
    or (
        self.semantic_ID is not None
    ),
    "Constraint AASd-118: If there are supplemental semantic IDs defined "
    "then there shall be also a main semantic ID."
)
@invariant(
    lambda self:
    not (self.supplemental_semantic_IDs is not None)
    or len(self.supplemental_semantic_IDs) >= 1,
    "Supplemental semantic IDs must be either not set or have at least one item."
)
# fmt: on
class Has_semantics(DBC):
    """
    Element that can have a semantic definition plus some supplemental semantic
    definitions.

    :constraint AASd-118:

        If there are ID :attr:`Has_semantics.supplemental_semantic_IDs` defined
        then there shall be also a main semantic ID :attr:`Has_semantics.semantic_ID`.
    """

    semantic_ID: Optional["Reference"]
    """
    Identifier of the semantic definition of the element. It is called semantic ID
    of the element or also main semantic ID of the element.
    """

    supplemental_semantic_IDs: Optional[List["Reference"]]
    """
    Identifier of a supplemental semantic definition of the element.
    It is called supplemental semantic ID of the element.
    """

    def __init__(
        self,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
    ) -> None:
        self.semantic_ID = semantic_ID
        self.supplemental_semantic_IDs = supplemental_semantic_IDs


# fmt: off
@invariant(
    lambda self:
    not (self.value is not None)
    or (
        value_consistent_with_XSD_type(self.value, self.value_type_or_default())
    ),
    "The value must match the value type."
)
@invariant(
    lambda self:
    not (self.refers_to is not None)
    or len(self.refers_to) >= 1,
    "Refers-to must be either not set or have at least one item."
)
# fmt: on
class Extension(Has_semantics):
    """
    Single extension of an element.
    """

    name: "Name_type"
    """
    Name of the extension.

    :constraint AASd-077:

        The name of an extension (Extension/name) within :class:`Has_extensions` needs
        to be unique.
    """

    value_type: Optional["Data_type_def_XSD"]
    """
    Data type of the :attr:`value` attribute of the extension.

    Default: :attr:`Data_type_def_XSD.String`
    """

    @implementation_specific
    @non_mutating
    def value_type_or_default(self) -> "Data_type_def_XSD":
        # NOTE (mristin):
        # This implementation will not be transpiled, but is given here as reference.
        return (
            self.value_type if self.value_type is not None else Data_type_def_XSD.String
        )

    value: Optional["Value_data_type"]
    """
    Value of the extension
    """

    refers_to: Optional[List["Reference"]]
    """
    Reference to an element the extension refers to.
    """

    def __init__(
        self,
        name: "Name_type",
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        value_type: Optional["Data_type_def_XSD"] = None,
        value: Optional["Value_data_type"] = None,
        refers_to: Optional[List["Reference"]] = None,
    ) -> None:
        Has_semantics.__init__(
            self,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
        )

        self.name = name
        self.value_type = value_type
        self.value = value
        self.refers_to = refers_to


# fmt: off
@abstract
@invariant(
    lambda self:
    not (self.extensions is not None) or extension_names_are_unique(self.extensions),
    "Constraint AASd-077: The name of an extension within "
    "Has-Extensions needs to be unique."
)
@invariant(
    lambda self:
    not (self.extensions is not None)
    or len(self.extensions) >= 1,
    "Extensions must be either not set or have at least one item."
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
@invariant(
    lambda self:
    not (self.display_name is not None)
    or lang_strings_have_unique_languages(self.display_name),
    "Display name must specify unique languages."
)
@invariant(
    lambda self:
    not (self.display_name is not None)
    or len(self.display_name) >= 1,
    "Display name must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.description is not None)
    or lang_strings_have_unique_languages(self.description),
    "Description must specify unique languages."
)
@invariant(
    lambda self:
    not (self.description is not None)
    or len(self.description) >= 1,
    "Description must be either not set or have at least one item."
)
@serialization(with_model_type=True)
# fmt: on
class Referable(Has_extensions):
    """
    Element that is referable by its :attr:`ID_short`.

    This ID is not globally unique.
    This ID is unique within the name space of the element.

    :constraint AASd-022:

        :attr:`Referable.ID_short` of non-identifiable referables
        within the same name space shall be unique (case-sensitive).
    """

    category: Optional[Name_type]
    """
    The category is a value that gives further meta information
    w.r.t. the class of the element.
    It affects the expected existence of attributes and the applicability of
    constraints.

    .. note::

        The category is not identical to the semantic definition
        (:class:`Has_semantics`) of an element. The category could e.g. denote that
        the element is a measurement value, whereas the semantic definition of
        the element would denote that it is the measured temperature.

    .. note::

        Deprecated.
    """

    ID_short: Optional["ID_short_type"]
    """
    In case of identifiables, this attribute is a short name of the element.
    In case of a referable, this ID is an identifying string of the element within
    its name space.

    .. note::

        In case the element is a property and the property has a semantic definition
        (:attr:`Has_semantics.semantic_ID`) conformant to IEC61360
        the :attr:`ID_short` is typically identical to the short name in English,
        if available.
    """

    display_name: Optional[List["Lang_string_name_type"]]
    """
    Display name. Can be provided in several languages.
    """

    description: Optional[List["Lang_string_text_type"]]
    """
    Description or comments on the element.

    The description can be provided in several languages.

    If no description is defined, the definition of the concept
    description that defines the semantics of the element is used.

    Additional information can be provided, e.g., if the element is
    qualified and which qualifier types can be expected in which
    context or which additional data specification templates.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional["ID_short_type"] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
    ) -> None:
        Has_extensions.__init__(self, extensions=extensions)

        self.ID_short = ID_short
        self.display_name = display_name
        self.category = category
        self.description = description


@abstract
class Identifiable(Referable):
    """An element that has a globally unique identifier."""

    administration: Optional["Administrative_information"]
    """
    Administrative information of an identifiable element.

    .. note::

        Some of the administrative information like the version number might need to
        be part of the identification.
    """

    ID: "Identifier"
    """The globally unique identification of the element."""

    def __init__(
        self,
        ID: "Identifier",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        administration: Optional["Administrative_information"] = None,
    ) -> None:
        Referable.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
        )

        self.ID = ID
        self.administration = administration


class Modelling_kind(Enum):
    """Enumeration for denoting whether an element is a template or an instance."""

    Template = "Template"
    """
    Specification of the common features of a structured element in sufficient detail
    that such an instance can be instantiated using it
    """

    Instance = "Instance"
    """
    Concrete, clearly identifiable element instance. Its creation and validation
    may be guided by a corresponding element template.
    """


@abstract
class Has_kind(DBC):
    """
    An element with a kind is an element that can either represent a template or an
    instance.

    Default for an element is that it is representing an instance.
    """

    kind: Optional["Modelling_kind"]
    """
    Kind of the element: either template or instance.

    Default: :attr:`Modelling_kind.Instance`
    """

    @implementation_specific
    @non_mutating
    def kind_or_default(self) -> "Modelling_kind":
        # NOTE (mristin):
        # This implementation will not be transpiled, but is given here as reference.
        return self.kind if self.kind is not None else Modelling_kind.Instance

    def __init__(self, kind: Optional["Modelling_kind"] = None) -> None:
        self.kind = kind


# fmt: off
@abstract
@invariant(
    lambda self:
    not (self.embedded_data_specifications is not None)
    or len(self.embedded_data_specifications) >= 1,
    "Embedded data specifications must be either not set or have at least one item."
)
# fmt: on
class Has_data_specification(DBC):
    """
    Element that can be extended by using data specification templates.

    A data specification template defines a named set of additional attributes an
    element may or shall have. The data specifications used are explicitly specified
    with their global ID.
    """

    embedded_data_specifications: Optional[List["Embedded_data_specification"]]
    """Embedded data specification."""

    def __init__(
        self,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        self.embedded_data_specifications = embedded_data_specifications


# fmt: off
@invariant(
    lambda self:
    not (self.revision is not None) or self.version is not None,
    "Constraint AASd-005: If version is not specified, revision shall also be "
    "unspecified. This means that a revision requires a version. If there is "
    "no version, there is no revision. Revision is optional."
)
# fmt: on
class Administrative_information(Has_data_specification):
    """
    Administrative metainformation for an element.

    :constraint AASd-005:

        If :attr:`version` is not specified, :attr:`revision` shall also be
        unspecified. This means that a revision requires a version. If there is
        no version, there is no revision. Revision is optional.
    """

    version: Optional[Version_type]
    """Version of the element."""

    revision: Optional[Revision_type]
    """Revision of the element."""

    creator: Optional["Reference"]
    """The subject ID of the subject responsible for making the element."""

    created_at: Optional["Date_time_UTC"]
    """date of creation."""

    updated_at: Optional["Date_time_UTC"]
    """date of update."""

    template_ID: Optional["Identifier"]
    """
    Identifier of the template that guided the creation of the element.

    .. note::

       So far, :attr:`template_ID` is only applicable for :class:`Submodel`'s,
       since template specifications are standardized for Submodels only.

    .. note::

       In case of a submodel, the :attr:`template_ID` is the identifier
       of the submodel template that guided the creation of the submodel

    .. note::

       The :attr:`template_ID` is not relevant for validation in Submodels.
       For validation the :attr:`Submodel.semantic_ID` shall be used.

    .. note::

       Usage of :attr:`template_ID` is not restricted to submodel instances. So also
       the creation of submodel templates can be guided by another submodel template.
    """

    def __init__(
        self,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        version: Optional[Version_type] = None,
        revision: Optional[Revision_type] = None,
        creator: Optional["Reference"] = None,
        created_at: Optional["Date_time_UTC"] = None,
        updated_at: Optional["Date_time_UTC"] = None,
        template_ID: Optional["Identifier"] = None,
    ) -> None:
        Has_data_specification.__init__(
            self, embedded_data_specifications=embedded_data_specifications
        )

        self.version = version
        self.revision = revision
        self.creator = creator
        self.created_at = created_at
        self.updated_at = updated_at
        self.template_ID = template_ID


# fmt: off
@abstract
@invariant(
    lambda self:
    not (self.qualifiers is not None)
    or qualifier_types_are_unique(self.qualifiers),
    "Constraint AASd-021: Every qualifiable shall only have one qualifier with "
    "the same type."
)
@invariant(
    lambda self:
    not (self.qualifiers is not None)
    or len(self.qualifiers) >= 1,
    "Qualifiers must be either not set or have at least one item."
)
@serialization(with_model_type=True)
# fmt: on
class Qualifiable(DBC):
    """
    A qualifiable element may be further qualified by one or more
    qualifiers.

    :constraint AASd-119:

        If any :attr:`Qualifier.kind` value of :attr:`Qualifiable.qualifiers` is
        equal to :attr:`Qualifier_kind.Template_qualifier` and the qualified element
        inherits from :class:`Has_kind` then the qualified element shall be of
        kind Template (:attr:`Has_kind.kind` = :attr:`Modelling_kind.Template`).

        .. note::

            This constraint is checked at :class:`Submodel`.
    """

    qualifiers: Optional[List["Qualifier"]]
    """
    Additional qualification of a qualifiable element.

    :constraint AASd-021:

        Every qualifiable shall only have one qualifier with the same
        :attr:`Qualifier.type`.
    """

    def __init__(self, qualifiers: Optional[List["Qualifier"]] = None) -> None:
        self.qualifiers = qualifiers


class Qualifier_kind(Enum):
    """
    Enumeration for kinds of qualifiers.

    .. note::

        This element is experimental and therefore may be subject to change or may be
        removed completely in future versions of the meta-model.
    """

    Value_qualifier = "ValueQualifier"
    """
    qualifies the value of the element; the corresponding qualifier value can
    change over time.

    Value qualifiers are only applicable to elements with kind
    :attr:`Modelling_kind.Instance`.
    """

    Concept_qualifier = "ConceptQualifier"
    """
    qualifies the semantic definition (:attr:`Has_semantics.semantic_ID`) the
    element is referring to; the corresponding qualifier value is static.
    """

    Template_qualifier = "TemplateQualifier"
    """
    qualifies the elements within a specific submodel on concept level; the
    corresponding qualifier value is static.

    Template qualifiers are only applicable to elements with kind
    :attr:`Modelling_kind.Template`.
    """


# fmt: off
@invariant(
    lambda self:
    not (self.value is not None)
    or value_consistent_with_XSD_type(self.value, self.value_type),
    "Constraint AASd-020: The value shall be consistent with the data type as defined "
    "in value type.",
)
# fmt: on
class Qualifier(Has_semantics):
    """
    A qualifier is essentially a type-value-pair. Depending on the kind of
    qualifier, it makes additional statements:

    * w.r.t. the value of the qualified element,
    * w.r.t. the concept, i.e. semantic definition of the qualified element,
    * w.r.t. existence and other meta information of the qualified element type.

    :constraint AASd-006:

        If both the :attr:`value` and the :attr:`value_ID` of
        a :class:`Qualifier` are present then the :attr:`value` needs
        to be identical to the value of the referenced coded value
        in :attr:`value_ID`.

    :constraint AASd-020:

        The value of :attr:`value` shall be consistent with the data type as
        defined in :attr:`value_type`.
    """

    kind: Optional["Qualifier_kind"]
    """
    The qualifier kind describes the kind of qualifier that is applied to the
    element.

    Default: :attr:`Qualifier_kind.Concept_qualifier`
    """

    @implementation_specific
    @non_mutating
    def kind_or_default(self) -> "Qualifier_kind":
        # NOTE (mristin):
        # This implementation will not be transpiled, but is given here as reference.
        return self.kind if self.kind is not None else Qualifier_kind.Concept_qualifier

    type: "Qualifier_type"
    """
    The qualifier *type* describes the type of qualifier that is applied to
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

    value_ID: Optional["Reference"]
    """
    Reference to the global unique ID of a coded value.
    """

    def __init__(
        self,
        type: "Qualifier_type",
        value_type: "Data_type_def_XSD",
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        kind: Optional["Qualifier_kind"] = None,
        value: Optional["Value_data_type"] = None,
        value_ID: Optional["Reference"] = None,
    ) -> None:
        Has_semantics.__init__(
            self,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
        )

        self.type = type
        self.value_type = value_type
        self.kind = kind
        self.value = value
        self.value_ID = value_ID


# fmt: off
@invariant(
    lambda self:
    not (self.submodels is not None)
    or (
        all(
            is_model_reference_to(reference, Key_types.Submodel)
            for reference in self.submodels
        )
    ),
    "All submodels must be model references to a submodel."
)
@invariant(
    lambda self:
    not (self.derived_from is not None)
    or (
        is_model_reference_to(
            self.derived_from,
            Key_types.Asset_administration_shell
        )
    ),
    "Derived-from must be a model reference to an asset administration shell."
)
@invariant(
    lambda self:
    not (self.submodels is not None)
    or len(self.submodels) >= 1,
    "Submodels must be either not set or have at least one item."
)
# fmt: on
class Asset_administration_shell(Identifiable, Has_data_specification):
    """An Asset Administration Shell."""

    derived_from: Optional["Reference"]
    """
    The reference to the Asset Administration Shell, which the Asset
    Administration Shell was derived from.
    """

    asset_information: "Asset_information"
    """
    Meta information about the asset, the Asset Administration Shell is
    representing.
    """

    submodels: Optional[List["Reference"]]
    """
    References to submodels of the Asset Administration Shell.

    A submodel is a description of an aspect of the asset, the Asset
    Administration Shell is representing.

    The asset of an Asset Administration Shell is typically described by one or
    more submodels.

    Temporarily, no submodel might be assigned to the Asset Administration Shell.
    """

    def __init__(
        self,
        ID: Identifier,
        asset_information: "Asset_information",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        administration: Optional["Administrative_information"] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        derived_from: Optional["Reference"] = None,
        submodels: Optional[List["Reference"]] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            ID=ID,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            administration=administration,
        )

        Has_data_specification.__init__(
            self, embedded_data_specifications=embedded_data_specifications
        )

        self.derived_from = derived_from
        self.asset_information = asset_information
        self.submodels = submodels


# fmt: off
@invariant(
    lambda self:
    not (self.specific_asset_IDs is not None)
    or len(self.specific_asset_IDs) >= 1,
    "Specific asset IDs must be either not set or have at least one item."
)
@invariant(
    lambda self:
    (
            self.global_asset_ID is not None
            or self.specific_asset_IDs is not None
    ) and (
            not (self.specific_asset_IDs is not None)
            or len(self.specific_asset_IDs) >= 1
    ),
    "Constraint AASd-131: Either the global asset ID shall be defined or at least one "
    "specific asset ID."
)
@invariant(
    lambda self:
    not (self.specific_asset_IDs is not None)
    or (
        all(
            not (
                specific_asset_ID_name_matches_global_asset_ID(
                    specific_asset_ID.name
                )
            ) or (
                self.global_asset_ID is not None
                and specific_asset_ID.value == self.global_asset_ID
            )
            for specific_asset_ID in self.specific_asset_IDs
        )
    ),
    "Constraint AASd-116: ``globalAssetId`` (case-insensitive) is a reserved key. "
    "If used as value for the name of specific asset ID then the value of specific "
    "asset ID shall be identical to the global asset ID with semantics as defined in "
    "https://admin-shell.io/aas/3/x/AssetInformation/globalAssetId, "
    "x being the minor version of the used specification."
)
# fmt: on
class Asset_information(DBC):
    """
    In :class:`Asset_information` identifying metadata of the asset that is
    represented by an Asset Administration Shell is defined.

    Several asset kinds are distinguished like for example type assets and
    instance assets.

    The asset has a globally unique identifier, plus – if needed – additional
    domain-specific (proprietary) identifiers. However, to support the corner case
    of very first phase of life cycle where a stabilized/constant global asset
    identifier does not already exist, the corresponding attribute
    :attr:`global_asset_ID` is optional.

    :constraint AASd-116:

        ``globalAssetId`` (case-insensitive) is a reserved key for
        :attr:`Specific_asset_ID.name` with the semantics as defined in
        ``https://admin-shell.io/aas/3/x/AssetInformation/globalAssetId``
        where ``x`` is the minor version.

        .. note::

            :constraintref:`AASd-116` is important to enable a generic search across
            global and specific asset IDs (e.g. in IDTA-01002-3-0 discovery
            operations like GetAllAssetLinksById). In the future the constraint
            might become more strict in stating that the name ``globalAssetId``
            shall not be used as :attr:`Specific_asset_ID.name`.

        .. note::

            The comparison against ``globalAssetId`` is ASCII case-insensitive.

    :constraint AASd-131:

        For :class:`Asset_information` either the :attr:`global_asset_ID` shall be
        defined or at least one item in :attr:`specific_asset_IDs`.


    """

    asset_kind: "Asset_kind"
    """
    Denotes whether the Asset is of kind :attr:`Asset_kind.Type`,
    :attr:`Asset_kind.Instance`, :attr:`Asset_kind.Batch`, :attr:`Asset_kind.Role`,
    or :attr:`Asset_kind.Not_applicable`.
    """

    global_asset_ID: Optional["Identifier"]
    """
    Identifier of the asset, the Asset Administration Shell is representing.

    This attribute is required as soon as the Asset Administration Shell is
    exchanged via partners in the life cycle of the asset. In a first phase of the
    life cycle, the asset might not yet have a global asset ID but already an
    internal identifier. The internal identifier would be modelled via
    :attr:`specific_asset_IDs`.
    """

    specific_asset_IDs: Optional[List["Specific_asset_ID"]]
    """
    Additional domain-specific, typically proprietary identifier for the asset like
    serial number, manufacturer part ID, customer part IDs, etc.
    """

    asset_type: Optional["Identifier"]
    """
    In case :attr:`asset_kind` is not :attr:`Asset_kind.Not_applicable` the
    :attr:`asset_type` is the asset ID of the type asset of the asset under
    consideration as identified by :attr:`global_asset_ID`.

    .. note::

        In case :attr:`asset_kind` is "Instance" then the :attr:`asset_type` denotes
        which "Type" the asset is of. But it is also possible
        to have an :attr:`asset_type` of an asset of kind "Type".

    """

    default_thumbnail: Optional["Resource"]
    """
    Thumbnail of the asset represented by the Asset Administration Shell.

    Used as default.
    """

    def __init__(
        self,
        asset_kind: "Asset_kind",
        global_asset_ID: Optional["Identifier"] = None,
        specific_asset_IDs: Optional[List["Specific_asset_ID"]] = None,
        asset_type: Optional["Identifier"] = None,
        default_thumbnail: Optional["Resource"] = None,
    ) -> None:
        self.asset_kind = asset_kind
        self.global_asset_ID = global_asset_ID
        self.specific_asset_IDs = specific_asset_IDs
        self.asset_type = asset_type
        self.default_thumbnail = default_thumbnail


class Resource(DBC):
    """
    Resource represents an address to a file (a locator). The value is a URI that
    can represent an absolute or relative path.
    """

    path: "Path_type"
    """
    Path and name of the resource (with file extension).

    The path can be absolute or relative.
    """

    content_type: Optional["Content_type"]
    """
    Content type of the content of the file.

    A single content type (MIME type) can have multiple file extensions
    associated with it.
    """

    def __init__(
        self,
        path: "Path_type",
        content_type: Optional["Content_type"] = None,
    ) -> None:
        self.path = path
        self.content_type = content_type


class Asset_kind(Enum):
    """
    Enumeration for denoting whether an asset is a type asset or an instance
    asset or a batch asset or is a role or whether this kind of classification
    is not applicable.
    """

    Type = "Type"
    """
    Type asset
    """

    Instance = "Instance"
    """
    Instance asset
    """

    Batch = "Batch"
    """
    Batch asset
    """

    Role = "Role"
    """
    Role asset
    """

    Not_applicable = "NotApplicable"
    """
    None of the other asset kinds
    """


@invariant(
    lambda self: not (self.external_subject_ID is not None)
    or (self.external_subject_ID.type == Reference_types.External_reference),
    "Constraint AASd-133: External subject ID shall be an external reference.",
)
class Specific_asset_ID(Has_semantics):
    """
    A specific asset ID describes a generic supplementary identifying attribute of the
    asset.

    The specific asset ID is not necessarily globally unique.

    :constraint AASd-133:

        :attr:`external_subject_ID` shall be an external reference,
        i.e. :attr:`Reference.type` = :attr:`Reference_types.External_reference`.
    """

    name: Label_type
    """Name of the asset identifier."""

    value: Identifier
    """The value of the specific asset identifier with the corresponding name."""

    external_subject_ID: Optional["Reference"]
    """
    The unique ID of the (external) subject the specific asset ID value belongs
    to or has meaning to.

    .. note::

        This is an external reference.
    """

    def __init__(
        self,
        name: Label_type,
        value: Identifier,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        external_subject_ID: Optional["Reference"] = None,
    ) -> None:
        Has_semantics.__init__(
            self,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
        )
        self.name = name
        self.value = value
        self.external_subject_ID = external_subject_ID


# fmt: off
@invariant(
    lambda self:
    not (self.qualifiers is not None)
    or (
        not any(
            qualifier.kind_or_default() == Qualifier_kind.Template_qualifier
            for qualifier in self.qualifiers
        ) or (
            self.kind_or_default() == Modelling_kind.Template
        )
    ),
    "Constraint AASd-119: If any qualifier kind value of a qualifiable qualifier is "
    "equal to template qualifier and the qualified element has kind then the qualified "
    "element shall be of kind template."
)
@invariant(
    lambda self:
    not (self.submodel_elements is not None)
    or (
        not (self.kind_or_default() != Modelling_kind.Template)
        or (
            submodel_elements_have_no_template_qualifiers(
                self.submodel_elements
            )
        )
    ),
    "Constraint AASd-129: If any kind value of a qualifier "
    "(attribute qualifier inherited via Qualifiable) is equal to TemplateQualifier, "
    "the submodel element shall be part of a submodel template, i.e. a submodel with "
    "kind (attribute kind inherited via Has-Kind) value equal to Template. "
    "Exception: the submodel element is part of an operation variable."
)
@invariant(
    lambda self:
    not (
            self.kind_or_default() == Modelling_kind.Template
    )
    or (
            self.submodel_elements is not None
            and submodel_element_lists_in_submodel_elements_have_exactly_one_element(
                self.submodel_elements
            )
    ),
    "Constraint AASd-138: A submodel element list within a submodel of kind "
    "Template or as part of an operation variable shall have exactly one element."
)
@invariant(
    lambda self:
    not (self.submodel_elements is not None)
    or (ID_shorts_are_unique(self.submodel_elements)),
    "Constraint AASd-022: ID-short of non-identifiable referables "
    "within the same name space shall be unique (case-sensitive)."
)
@invariant(
    lambda self:
    not (self.submodel_elements is not None)
    or all(
        item.ID_short is not None
        for item in self.submodel_elements
    ),
    "ID-shorts need to be defined for all the items of submodel elements according to "
    "AASd-117 (ID-short of non-identifiable Referables not being a direct child of "
    "a Submodel element list shall be specified)."
)
@invariant(
    lambda self:
    not (self.submodel_elements is not None)
    or len(self.submodel_elements) >= 1,
    "Submodel elements must be either not set or have at least one item."
)
# fmt: on
class Submodel(
    Identifiable, Has_kind, Has_semantics, Qualifiable, Has_data_specification
):
    """
    A submodel defines a specific aspect of the asset represented by the Asset
    Administration Shell.

    A submodel is used to structure the digital representation and technical
    functionality of an Administration Shell into distinguishable parts. Each submodel
    refers to a well-defined domain or subject. Submodels can become standardized
    and, in turn, submodel templates.
    """

    submodel_elements: Optional[List["Submodel_element"]]
    """Submodel elements contained in the submodel."""

    def __init__(
        self,
        ID: Identifier,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        administration: Optional["Administrative_information"] = None,
        kind: Optional["Modelling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        submodel_elements: Optional[List["Submodel_element"]] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            ID=ID,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            administration=administration,
        )

        Has_kind.__init__(self, kind=kind)

        Has_semantics.__init__(
            self,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
        )

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(
            self, embedded_data_specifications=embedded_data_specifications
        )

        self.submodel_elements = submodel_elements


@abstract
class Submodel_element(Referable, Has_semantics, Qualifiable, Has_data_specification):
    """
    A submodel element is an element suitable for the description and differentiation of
    assets.

    It is recommended to add a :attr:`Has_semantics.semantic_ID` to a submodel element.

    :constraint AASd-129:

        If any :attr:`Qualifier.kind` value of :attr:`qualifiers` (attribute qualifier
        inherited via Qualifiable) is equal to :attr:`Qualifier_kind.Template_qualifier`,
        the submodel element shall be part of a submodel template, i.e.
        a submodel with :attr:`Submodel.kind` (attribute kind inherited via
        :class:`Has_kind`) value equal to :attr:`Modelling_kind.Template`.
        Exception: the submodel element is part of an :class:`Operation_variable`.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Referable.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
        )

        Has_semantics.__init__(
            self,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
        )

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(
            self, embedded_data_specifications=embedded_data_specifications
        )


class Relationship_element(Submodel_element):
    """
    A relationship element is used to define a relationship between two elements
    being either referable (model reference) or external (external reference).
    """

    first: Optional["Reference"]
    """
    Reference to the first element in the relationship taking the role of the subject.
    """

    second: Optional["Reference"]
    """
    Reference to the second element in the relationship taking the role of the object.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        first: Optional["Reference"] = None,
        second: Optional["Reference"] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.first = first
        self.second = second


class AAS_submodel_elements(Enum):
    """
    Enumeration of Submodel Element types including abstract Submodel Element types.
    """

    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Basic_event_element = "BasicEventElement"
    Blob = "Blob"
    Capability = "Capability"

    Data_element = "DataElement"
    """
    Data element.

    .. note::

        Data Element is abstract, *i.e.* if a key uses :attr:`Data_element`
        the reference may be a :class:`Property`, a :class:`File` etc.
    """

    Entity = "Entity"

    Event_element = "EventElement"
    """
    Event.

    .. note::

        :class:`Event_element` is abstract.
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

    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, *i.e.* if a key uses :attr:`Submodel_element`
        the reference may be a :class:`Property`, an :class:`Operation` etc.
    """

    Submodel_element_list = "SubmodelElementList"
    """
    List of Submodel Elements
    """

    Submodel_element_collection = "SubmodelElementCollection"
    """
    Struct of Submodel Elements
    """


# fmt: off
@invariant(
    lambda self:
    not (self.value is not None)
    or ID_shorts_are_unique(self.value),
    "ID-shorts of the value must be unique."
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
    "value type list element."
)
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
    or submodel_elements_have_identical_semantic_IDs(self.value),
    "Constraint AASd-114: If two first level child elements "
    "have a semantic ID then they shall be identical."
)
@invariant(
    lambda self:
    not (
            self.value is not None
            and self.semantic_ID_list_element is not None
    ) or (
        all(
            not (child.semantic_ID is not None)
            or reference_key_values_equal(
                child.semantic_ID,
                self.semantic_ID_list_element)
            for child in self.value
        )
    ),
    "Constraint AASd-107: If a first level child element has a semantic ID "
    "it shall be identical to semantic ID list element."
)
@invariant(
    lambda self:
    not (self.value is not None)
    or len(self.value) >= 1,
    "Value must be either not set or have at least one item."
)
# fmt: on
class Submodel_element_list(Submodel_element):
    """
    A submodel element list is an ordered list of submodel elements.

    .. note::

        The list is ordered although the ordering might not be relevant
        (see :attr:`order_relevant`).

    The numbering starts with zero (0).

    :constraint AASd-107:

        If a first level child element in a :class:`Submodel_element_list` has
        a :attr:`Has_semantics.semantic_ID` it
        shall be identical to :attr:`Submodel_element_list.semantic_ID_list_element`.

    :constraint AASd-114:

        If two first level child elements in a :class:`Submodel_element_list` have
        a :attr:`Has_semantics.semantic_ID` then they shall be identical.

    :constraint AASd-115:

        If a first level child element in a :class:`Submodel_element_list` does not
        specify a :attr:`Has_semantics.semantic_ID` then the value is assumed to be
        identical to :attr:`Submodel_element_list.semantic_ID_list_element`.

    :constraint AASd-108:

        All first level child elements in a :class:`Submodel_element_list` shall have
        the same submodel element type as specified in :attr:`type_value_list_element`.

    :constraint AASd-109:

        If :attr:`type_value_list_element` is equal to
        :attr:`AAS_submodel_elements.Property` or
        :attr:`AAS_submodel_elements.Range`
        :attr:`value_type_list_element` shall be set and all first
        level child elements in the :class:`Submodel_element_list` shall have
        the value type as specified in :attr:`value_type_list_element`.

    :constraint AASd-138:

        A :class:`Submodel_element_list` within a :class:`Submodel` of
        :attr:`Has_kind.kind` = :attr:`Modelling_kind.Template` or as part of
        an :class:`Operation_variable` shall have exactly one element.

        .. note::

            This constraint is checked at :class:`Submodel` and :class:`Operation`.
    """

    order_relevant: Optional["bool"]
    """
    Defines whether order in list is relevant. If :attr:`order_relevant` = ``False``
    then the list is representing a set or a bag.

    Default: ``True``
    """

    @implementation_specific
    @non_mutating
    def order_relevant_or_default(self) -> bool:
        # NOTE (mristin):
        # This implementation will not be transpiled, but is given here as reference.
        return self.order_relevant if self.order_relevant is not None else True

    semantic_ID_list_element: Optional["Reference"]
    """
    Semantic ID the submodel elements contained in the list match to.
    """

    type_value_list_element: "AAS_submodel_elements"
    """
    The submodel element type of the submodel elements contained in the list.
    """

    value_type_list_element: Optional["Data_type_def_XSD"]
    """
    The value type of the submodel element contained in the list.
    """

    value: Optional[List["Submodel_element"]]
    """
    Submodel element contained in the list.
    """

    def __init__(
        self,
        type_value_list_element: "AAS_submodel_elements",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        order_relevant: Optional["bool"] = None,
        semantic_ID_list_element: Optional["Reference"] = None,
        value_type_list_element: Optional["Data_type_def_XSD"] = None,
        value: Optional[List["Submodel_element"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.type_value_list_element = type_value_list_element
        self.order_relevant = order_relevant
        self.semantic_ID_list_element = semantic_ID_list_element
        self.value_type_list_element = value_type_list_element
        self.value = value


# fmt: off
@invariant(
    lambda self:
    not (self.value is not None)
    or ID_shorts_are_unique(self.value),
    "ID-shorts of the value must be unique."
)
@invariant(
    lambda self:
    not (self.value is not None)
    or all(
        item.ID_short is not None
        for item in self.value
    ),
    "ID-shorts need to be defined for all the items of value according to AASd-117 "
    "(ID-short of non-identifiable Referables not being a direct child of a Submodel "
    "element list shall be specified)."
)
@invariant(
    lambda self:
    not (self.value is not None)
    or len(self.value) >= 1,
    "Value must be either not set or have at least one item."
)
# fmt: on
class Submodel_element_collection(Submodel_element):
    """
    A submodel element collection is a kind of struct, i.e. a logical encapsulation
    of multiple named values.
    """

    value: Optional[List["Submodel_element"]]
    """
    Submodel element contained in the collection.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        value: Optional[List["Submodel_element"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.value = value


# fmt: off
@abstract
# fmt: on
class Data_element(Submodel_element):
    """
    A data element is a submodel element that is not further composed of
    other submodel elements.

    A data element is a submodel element that has a value. The type of value differs
    for different subtypes of data elements.

    .. note::

        Categories are deprecated and should no longer be used.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


# fmt: off
@invariant(
    lambda self:
    not (self.value is not None)
    or value_consistent_with_XSD_type(self.value, self.value_type),
    "Value must be consistent with the value type."
)
# fmt: on
class Property(Data_element):
    """
    A property is a data element that has a single value.

    :constraint AASd-007:

        If both, the :attr:`value` and the :attr:`value_ID` are
        present then the value of :attr:`value` needs to be identical to
        the value of the referenced coded value in :attr:`value_ID`.
    """

    value_type: "Data_type_def_XSD"
    """
    Data type of the :attr:`value` attribute.
    """

    value: Optional["Value_data_type"]
    """
    The value of the property instance.
    """

    value_ID: Optional["Reference"]
    """
    Reference to the global unique ID of a coded value.
    """

    def __init__(
        self,
        value_type: "Data_type_def_XSD",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        value: Optional["Value_data_type"] = None,
        value_ID: Optional["Reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.value_type = value_type
        self.value = value
        self.value_ID = value_ID


# fmt: off
@invariant(
    lambda self:
    not (self.value is not None)
    or len(self.value) >= 1,
    "Value must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.value is not None)
    or lang_strings_have_unique_languages(self.value),
    "Value must specify unique languages."
)
# fmt: on
class Multi_language_property(Data_element):
    """
    A property is a data element that has a multi-language value.

    :constraint AASd-012:
        If both the :attr:`value` and the :attr:`value_ID` are present then for each
        string in a specific language the meaning must be the same as specified in
        :attr:`value_ID`.
    """

    value: Optional[List["Lang_string_text_type"]]
    """
    The value of the property instance.
    """

    value_ID: Optional["Reference"]
    """
    Reference to the global unique ID of a coded value.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        value: Optional[List["Lang_string_text_type"]] = None,
        value_ID: Optional["Reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.value = value
        self.value_ID = value_ID


# fmt: off
@invariant(
    lambda self:
    not (self.min is not None)
    or value_consistent_with_XSD_type(self.min, self.value_type),
    "Min must be consistent with the value type."
)
@invariant(
    lambda self:
    not (self.max is not None)
    or value_consistent_with_XSD_type(self.max, self.value_type),
    "Max must be consistent with the value type."
)
# fmt: on
class Range(Data_element):
    """
    A range data element is a data element that defines a range with min and max.

    .. note::

        This element is experimental and therefore may be subject to change or may be
        removed completely in future versions of the meta-model.
    """

    value_type: "Data_type_def_XSD"
    """
    Data type of the :attr:`min` und :attr:`max` attributes
    """

    min: Optional["Value_data_type"]
    """
    The minimum value of the range.
    """

    max: Optional["Value_data_type"]
    """
    The maximum value of the range.
    """

    def __init__(
        self,
        value_type: "Data_type_def_XSD",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        min: Optional["Value_data_type"] = None,
        max: Optional["Value_data_type"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.value_type = value_type
        self.min = min
        self.max = max


class Reference_element(Data_element):
    """
    A reference element is a data element that defines a logical reference to another
    element within the same or another Asset Administration Shell or a reference to
    an external object or entity.
    """

    value: Optional["Reference"]
    """
    External reference to an external object or entity or a logical reference to
    another element within the same or another Asset Administration Shell (i.e. a
    model reference to a Referable).
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        value: Optional["Reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.value = value


class Blob(Data_element):
    """
    A :class:`Blob` is a data element that represents a file that is contained in the
    :attr:`value` attribute with its source code.
    """

    value: Optional["Blob_type"]
    """
    The value of the :class:`Blob` instance of a blob data element.

    .. note::

        In contrast to the file property the file content is stored directly as value
        in the :class:`Blob` data element.
    """

    content_type: Optional[Content_type]
    """
    Content type of the content of the :class:`Blob`.

    The content type (MIME type) states which file extensions the file can have.

    Valid values are content types like ``application/json``, ``application/xls``,
    ``image/jpg``.

    The allowed values are defined as in RFC2046.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        value: Optional["Blob_type"] = None,
        content_type: Optional[Content_type] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.content_type = content_type
        self.value = value


class File(Data_element):
    """
    A file is a data element that represents an address to a file (a locator).

    The value is a URI that can represent an absolute or relative path.
    """

    value: Optional["Path_type"]
    """
    Path and name of the file (with file extension).

    The path can be absolute or relative.
    """

    content_type: Optional["Content_type"]
    """
    Content type of the content of the file.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        value: Optional["Path_type"] = None,
        content_type: Optional["Content_type"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.content_type = content_type
        self.value = value


# fmt: off
@invariant(
    lambda self:
    not (self.annotations is not None)
    or all(
      item.ID_short is not None
      for item in self.annotations
    ),
    "ID-shorts need to be defined for all the items of annotations according to "
    "AASd-117 (ID-short of non-identifiable Referables not being a direct child of "
    "a Submodel element list shall be specified)."
)
@invariant(
    lambda self:
    not (self.annotations is not None)
    or len(self.annotations) >= 1,
    "Annotations must be either not set or have at least one item."
)
# fmt: on
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
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        first: Optional["Reference"] = None,
        second: Optional["Reference"] = None,
        annotations: Optional[List[Data_element]] = None,
    ) -> None:
        Relationship_element.__init__(
            self,
            first=first,
            second=second,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.annotations = annotations


# fmt: off
@invariant(
    lambda self:
    not (self.specific_asset_IDs is not None)
    or len(self.specific_asset_IDs) >= 1,
    "Specific asset IDs must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.entity_type is not None)
    or (
            not (self.entity_type == Entity_type.Self_managed_entity)
            or (
                    (
                            self.global_asset_ID is not None
                            and self.specific_asset_IDs is None
                    ) or (
                            self.global_asset_ID is None
                            and self.specific_asset_IDs is not None
                            and len(self.specific_asset_IDs) >= 1
                    )
            )
    ),
    "Constraint AASd-014: Either the attribute global asset ID or "
    "specific asset ID must be set if Entity/entityType is set to :attr:`Entity_type.Self_managed_entity`."
)
@invariant(
    lambda self:
    not (self.statements is not None)
    or all(
        item.ID_short is not None
        for item in self.statements
    ),
    "ID-shorts need to be defined for all the items of statements according to "
    "AASd-117 (ID-short of non-identifiable Referables not being a direct child of "
    "a Submodel element list shall be specified)."
)
@invariant(
    lambda self:
    not (self.statements is not None)
    or len(self.statements) >= 1,
    "Statements must be either not set or have at least one item."
)
# fmt: on
class Entity(Submodel_element):
    """
    An entity is a submodel element that is used to model entities.

    :constraint AASd-014:

        Either the attribute :attr:`global_asset_ID` or :attr:`specific_asset_IDs`
        of an :class:`Entity` must be set if Entity/entityType is set to :attr:`Entity_type.Self_managed_entity`.
    """

    statements: Optional[List["Submodel_element"]]
    """
    Statement applicable to the entity, each statement described by a
    :class:`Submodel_element` - typically with a qualified value.
    """

    entity_type: Optional["Entity_type"]
    """
    Describes whether the entity is a co-managed entity or a self-managed entity.
    """

    global_asset_ID: Optional["Identifier"]
    """
    Global identifier of the asset the entity is representing.
    """

    specific_asset_IDs: Optional[List["Specific_asset_ID"]]
    """
    Reference to a specific asset ID representing a supplementary identifier
    of the asset represented by the Asset Administration Shell.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        statements: Optional[List["Submodel_element"]] = None,
        entity_type: Optional["Entity_type"] = None,
        global_asset_ID: Optional["Identifier"] = None,
        specific_asset_IDs: Optional[List["Specific_asset_ID"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.statements = statements
        self.entity_type = entity_type
        self.global_asset_ID = global_asset_ID
        self.specific_asset_IDs = specific_asset_IDs


class Entity_type(Enum):
    """
    Enumeration for denoting whether an entity is a self-managed entity or a co-managed
    entity.
    """

    Co_managed_entity = "CoManagedEntity"
    """
    There is no separate Asset Administration Shell for co-managed entities.
    Co-managed entities need to be part of a self-managed entity.
    """

    Self_managed_entity = "SelfManagedEntity"
    """
    Self-managed entities have their own Asset Administration Shell but can be part
    of another composite self-managed entity.

    The asset represented by an Asset Administration Shell is a self-managed entity
    per definition.
    """


class Direction(Enum):
    """
    Direction

    .. note::

        This element is experimental and therefore may be subject to change or may be
        removed completely in future versions of the meta-model.
    """

    Input = "input"
    """
    Input direction
    """

    Output = "output"
    """
    Output direction
    """


class State_of_event(Enum):
    """
    State of an event

    .. note::

        This element is experimental and therefore may be subject to change or may be
        removed completely in future versions of the meta-model.
    """

    On = "on"
    """
    Event is on
    """

    Off = "off"
    """
    Event is off
    """


# fmt: off
@invariant(
    lambda self:
    is_model_reference_to_referable(self.observable_reference),
    "Observable reference must be a model reference to a referable."
)
@invariant(
    lambda self:
    (
        is_model_reference_to(self.source, Key_types.Event_element)
        or is_model_reference_to(self.source, Key_types.Basic_event_element)
    ),
    "Source must be a model reference to an Event element."
)
# fmt: on
class Event_payload(DBC):
    """
    Defines the necessary information of an event instance sent out or received.

    .. note::

        This element is experimental and therefore may be subject to change or may be
        removed completely in future versions of the meta-model.
    """

    source: "Reference"
    """
    Reference to the source event element.
    """

    source_semantic_ID: Optional["Reference"]
    """
    :attr:`Has_semantics.semantic_ID` of the source event element, if available

    .. note::

        It is recommended to use an external reference.
    """

    observable_reference: "Reference"
    """
    Reference to the referable, which defines the scope of the event.
    """

    observable_semantic_ID: Optional["Reference"]
    """
    :attr:`Has_semantics.semantic_ID` of the referable which defines the scope of
    the event, if available.

    .. note::

        It is recommended to use an external reference.
    """

    topic: Optional["Message_topic_type"]
    """
    Information for the outer message infrastructure to schedule the event for
    the respective communication channel.
    """

    subject_ID: Optional["Reference"]
    """
    Subject, who/which initiated the creation.

    .. note::

        This is an external reference.
    """

    time_stamp: "Date_time_UTC"
    """
    Timestamp in UTC, when this event was triggered.
    """

    payload: Optional["Blob_type"]
    """
    Event-specific payload.
    """

    def __init__(
        self,
        source: "Reference",
        observable_reference: "Reference",
        time_stamp: "Date_time_UTC",
        source_semantic_ID: Optional["Reference"] = None,
        observable_semantic_ID: Optional["Reference"] = None,
        topic: Optional["Message_topic_type"] = None,
        subject_ID: Optional["Reference"] = None,
        payload: Optional["Blob_type"] = None,
    ) -> None:
        self.source = source
        self.observable_reference = observable_reference
        self.time_stamp = time_stamp
        self.source_semantic_ID = source_semantic_ID
        self.observable_semantic_ID = observable_semantic_ID
        self.topic = topic
        self.subject_ID = subject_ID
        self.payload = payload


@abstract
class Event_element(Submodel_element):
    """
    An event element.

    .. note::

        This element is experimental and therefore may be subject to change or may be
        removed completely in future versions of the meta-model.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


# fmt: off
@invariant(
    lambda self:
    not (self.message_broker is not None)
    or is_model_reference_to_referable(self.message_broker),
    "Message broker must be a model reference to a referable."
)
@invariant(
    lambda self:
    is_model_reference_to_referable(self.observed),
    "Observed must be a model reference to a referable."
)
@invariant(
    lambda self:
    not (self.direction == Direction.Input)
    or self.max_interval is None,
    "Max. interval is not applicable for input direction."
)
# fmt: on
class Basic_event_element(Event_element):
    """
    A basic event element.

    .. note::

        This element is experimental and therefore may be subject to change or may be
        removed completely in future versions of the meta-model.
    """

    observed: "Reference"
    """
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

    message_topic: Optional["Message_topic_type"]
    """
    Information for the outer message infrastructure to schedule the event for the
    respective communication channel.
    """

    message_broker: Optional["Reference"]
    """
    Information about which outer message infrastructure shall handle messages for
    the :class:`Event_element`. Refers to a :class:`Submodel`,
    :class:`Submodel_element_list`, :class:`Submodel_element_collection` or
    :class:`Entity`, which contains :class:`Data_element`'s describing
    the proprietary specification for the message broker.

    .. note::

        This proprietary specification could be standardized by using respective
        :class:`Submodel`'s for different message infrastructure, e.g., OPC UA,
        MQTT or AMQP.
    """

    last_update: Optional["Date_time_UTC"]
    """
    Timestamp in UTC, when the last event was received (input direction) or sent
    (output direction).
    """

    min_interval: Optional["Duration"]
    """
    For input direction reports on the maximum frequency, the software entity behind
    the respective :class:`Referable` can handle input events.

    For output events, the maximum frequency of outputting this event to an outer
    infrastructure is specified.

    Might be not specified, i.e. if there is no minimum interval.
    """

    max_interval: Optional["Duration"]
    """
    Not applicable for input direction.

    For output direction: maximum interval in time, the respective :class:`Referable`
    shall send an update of the status of the event, even if no other trigger
    condition for the event was not met.

    Might not be specified, i.e. if there is no maximum interval.
    """

    def __init__(
        self,
        observed: "Reference",
        direction: "Direction",
        state: "State_of_event",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        message_topic: Optional["Message_topic_type"] = None,
        message_broker: Optional["Reference"] = None,
        last_update: Optional["Date_time_UTC"] = None,
        min_interval: Optional["Duration"] = None,
        max_interval: Optional["Duration"] = None,
    ) -> None:
        Event_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.observed = observed
        self.direction = direction
        self.state = state
        self.message_topic = message_topic
        self.message_broker = message_broker
        self.last_update = last_update
        self.min_interval = min_interval
        self.max_interval = max_interval


# fmt: off
@invariant(
    lambda self:
    not (self.inoutput_variables is not None)
    or len(self.inoutput_variables) >= 1,
    "Inoutput variables must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.output_variables is not None)
    or len(self.output_variables) >= 1,
    "Output variables must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.input_variables is not None)
    or len(self.input_variables) >= 1,
    "Input variables must be either not set or have at least one item."
)
@invariant(
    lambda self:
    ID_shorts_of_variables_are_unique(
        self.input_variables,
        self.output_variables,
        self.inoutput_variables
    ),
    "Constraint AASd-134: For an Operation the ID-short of all values of "
    "input, output and in/output variables shall be unique."
)
@invariant(
    lambda self:
    submodel_element_lists_in_operation_variables_have_exactly_one_element(
        self.input_variables,
        self.output_variables,
        self.inoutput_variables,
    ),
    "Constraint AASd-138: A submodel element list within a submodel of kind Template "
    "or as part of an operation variable shall have exactly one element."
)
# fmt: on
class Operation(Submodel_element):
    """
    An operation is a submodel element with input and output variables.

    :constraint AASd-134:
        For an :class:`Operation` the :attr:`Referable.ID_short` of all
        :attr:`Operation_variable.value`'s in
        :attr:`input_variables`, :attr:`output_variables`
        and :attr:`inoutput_variables` shall be unique.
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

    .. note::

        In embedded systems inoutput variables are variables that can be read but
        that are also written by the system. Typically, this is implemented via a
        pointer (i.e. 'by reference' instead of 'by value').
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        input_variables: Optional[List["Operation_variable"]] = None,
        output_variables: Optional[List["Operation_variable"]] = None,
        inoutput_variables: Optional[List["Operation_variable"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.input_variables = input_variables
        self.output_variables = output_variables
        self.inoutput_variables = inoutput_variables


# fmt: off
@invariant(
    lambda self:
    self.value.ID_short is not None,
    "Value must have the ID-short specified according to Constraint AASd-117 "
    "(ID-short of non-identifiable Referables not being a direct child of a Submodel "
    "element list shall be specified)."
)
# fmt: on
class Operation_variable(DBC):
    """
    The value of an operation variable is a submodel element that is used as input
    and/or output variable of an operation.

    Specification of operations in a :class:`Submodel` with
    :attr:`Has_kind.kind` = :attr:`Modelling_kind.Instance` are handled
    identical to operations in Submodel templates (:class:`Submodel` with
    :attr:`Has_kind.kind` = :attr:`Modelling_kind.Template`).

    .. note::

        An operation can be invoked via an API call (``InvokeOperationSync``
        and ``InvokeOperationAsync``). For further explanation see Part 2
        (IDTA-01002).

    .. note::

        :class:`Operation_variable` is introduced as a separate class to
        enable future extensions, *e.g.* for adding a default value or
        cardinality (optional/mandatory).
    """

    value: "Submodel_element"
    """
    Describes an argument or result of an operation via a submodel element
    """

    def __init__(self, value: "Submodel_element") -> None:
        self.value = value


class Capability(Submodel_element):
    """
    A capability is the implementation-independent description of the potential of an
    asset to achieve a certain effect in the physical or virtual world.

    .. note::

        The :attr:`semantic_ID` of a capability is typically an ontology, which
        enables reasoning on capabilities. The mapping to one or more skills
        implementing the capability is done via a relationship element with the
        corresponding semantics. A skill is typically a property or an operation.
        In more complex cases, the mapping can also be a collection or a complete
        submodel.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


# NOTE (mristin):
# We make the following verification functions implementation-specific since the casts
# are very clumsy to formalize and transpile in a readable way across languages.
# For example, since Python does not have a null-coalescing operator, formalizing
# the constraints such as :constraintref:`AASc-3a-004` would involve walrus operator and
# would result in an unreadable invariant.
#
# Therefore, we decided to encapsulate the logic in these few functions and estimate
# the maintenance effort to dwarf the effort needed to get this right in
# aas-core-codegen.


@verification
@implementation_specific
def data_specification_IEC_61360s_for_property_or_value_have_appropriate_data_type(
    embedded_data_specifications: List["Embedded_data_specification"],
) -> bool:
    """
    Check that the :attr:`Data_specification_IEC_61360.data_type` is defined
    appropriately for all data specifications whose content is given as IEC 61360.
    """
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as reference.
    return all(
        not (
            isinstance(
                data_specification.data_specification_content,
                Data_specification_IEC_61360,
            )
        )
        or (
            data_specification.data_specification_content.data_type is not None
            and (
                data_specification.data_specification_content.data_type
                in Data_type_IEC_61360_for_property_or_value
            )
        )
        for data_specification in embedded_data_specifications
    )


@verification
@implementation_specific
def data_specification_IEC_61360s_for_reference_have_appropriate_data_type(
    embedded_data_specifications: List["Embedded_data_specification"],
) -> bool:
    """
    Check that the :attr:`Data_specification_IEC_61360.data_type` is defined
    appropriately for all data specifications whose content is given as IEC 61360.
    """
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as reference.
    return all(
        not (
            isinstance(
                data_specification.data_specification_content,
                Data_specification_IEC_61360,
            )
        )
        or (
            data_specification.data_specification_content.data_type is not None
            and (
                data_specification.data_specification_content.data_type
                in Data_type_IEC_61360_for_reference
            )
        )
        for data_specification in embedded_data_specifications
    )


@verification
@implementation_specific
def data_specification_IEC_61360s_for_document_have_appropriate_data_type(
    embedded_data_specifications: List["Embedded_data_specification"],
) -> bool:
    """
    Check that the :attr:`Data_specification_IEC_61360.data_type` is defined
    appropriately for all data specifications whose content is given as IEC 61360.
    """
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as reference.
    return all(
        not (
            isinstance(
                data_specification.data_specification_content,
                Data_specification_IEC_61360,
            )
        )
        or (
            data_specification.data_specification_content.data_type is not None
            and (
                data_specification.data_specification_content.data_type
                in Data_type_IEC_61360_for_document
            )
        )
        for data_specification in embedded_data_specifications
    )


@verification
@implementation_specific
def data_specification_IEC_61360s_have_data_type(
    embedded_data_specifications: List["Embedded_data_specification"],
) -> bool:
    """
    Check that the :attr:`Data_specification_IEC_61360.data_type` is defined for all
    data specifications whose content is given as IEC 61360.
    """
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as reference.
    return all(
        not (
            isinstance(
                data_specification.data_specification_content,
                Data_specification_IEC_61360,
            )
        )
        or (data_specification.data_specification_content.data_type is not None)
        for data_specification in embedded_data_specifications
    )


@verification
@implementation_specific
def data_specification_IEC_61360s_have_value(
    embedded_data_specifications: List["Embedded_data_specification"],
) -> bool:
    """
    Check that the :attr:`Data_specification_IEC_61360.value` is defined
    for all data specifications whose content is given as IEC 61360.
    """
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as reference.
    return all(
        not (
            isinstance(
                data_specification.data_specification_content,
                Data_specification_IEC_61360,
            )
        )
        or (data_specification.data_specification_content.value is not None)
        for data_specification in embedded_data_specifications
    )


@verification
@implementation_specific
def data_specification_IEC_61360s_have_definition_at_least_in_english(
    embedded_data_specifications: List["Embedded_data_specification"],
) -> bool:
    """
    Check that the :attr:`Data_specification_IEC_61360.definition` is defined
    for all data specifications whose content is given as IEC 61360 at least in English.
    """
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as reference.

    for data_specification in embedded_data_specifications:
        if not isinstance(
            data_specification.data_specification_content, Data_specification_IEC_61360
        ):
            continue

        if data_specification.data_specification_content.definition is None:
            return False

        if not any(
            is_BCP_47_for_english(lang_string.language)
            for lang_string in (
                data_specification.data_specification_content.definition
            )
        ):
            return False

    return True


# fmt: off
@invariant(
    lambda self:
    not (
            self.category is not None
            and (self.category == "PROPERTY" or self.category == "VALUE")
            and self.embedded_data_specifications is not None
    ) or (
        data_specification_IEC_61360s_for_property_or_value_have_appropriate_data_type(
            self.embedded_data_specifications)
    ),
    "Constraint AASc-3a-004: For a concept description with category PROPERTY or VALUE "
    "using data specification IEC 61360, the data type of the data specification is "
    "mandatory and shall be one of: DATE, STRING, STRING_TRANSLATABLE, "
    "INTEGER_MEASURE, INTEGER_COUNT, INTEGER_CURRENCY, REAL_MEASURE, REAL_COUNT, "
    "REAL_CURRENCY, BOOLEAN, RATIONAL, RATIONAL_MEASURE, TIME, TIMESTAMP."
)
@invariant(
    lambda self:
    not (
            self.category is not None
            and (self.category == "REFERENCE")
            and self.embedded_data_specifications is not None
    ) or (
        data_specification_IEC_61360s_for_reference_have_appropriate_data_type(
            self.embedded_data_specifications)
    ),
    "Constraint AASc-3a-005: For a concept description with category REFERENCE "
    "using data specification IEC 61360, the data type of the data specification "
    "shall be one of: STRING, IRI, IRDI."
)
@invariant(
    lambda self:
    not (
            self.category is not None
            and (self.category == "DOCUMENT")
            and self.embedded_data_specifications is not None
    ) or (
        data_specification_IEC_61360s_for_document_have_appropriate_data_type(
            self.embedded_data_specifications
        )
    ),
    "Constraint AASc-3a-006: For a concept description with category DOCUMENT "
    "using data specification IEC 61360, the data type of the data specification "
    "shall be one of: FILE, BLOB, HTML."
)
@invariant(
    lambda self:
    not (
            self.category is not None
            and (self.category == "QUALIFIER_TYPE")
            and self.embedded_data_specifications is not None
    ) or (
        data_specification_IEC_61360s_have_data_type(self.embedded_data_specifications)
    ),
    "Constraint AASc-3a-007: For a concept description with category QUALIFIER_TYPE "
    "using data specification IEC 61360, the data type of the data specification is "
    "mandatory and shall be defined."
)
@invariant(
    lambda self:
    not (
        self.embedded_data_specifications is not None
    ) or (
        (
            data_specification_IEC_61360s_have_definition_at_least_in_english(
                self.embedded_data_specifications
            )
        ) or (
            data_specification_IEC_61360s_have_value(self.embedded_data_specifications)
        )
    ),
    "Constraint AASc-3a-008: For a concept description "
    "using data specification template IEC 61360, the definition "
    "is mandatory and shall be defined at least in English. "
    "Exception: The concept description describes a value."
)
@invariant(
    lambda self:
    not (self.is_case_of is not None)
    or len(self.is_case_of) >= 1,
    "Is-case-of must be either not set or have at least one item."
)
# fmt: on
class Concept_description(Identifiable, Has_data_specification):
    """
    The semantics of a property or other elements that may have a semantic description
    is defined by a concept description.

    The description of the concept should follow a standardized schema (realized as
    data specification template).

    :constraint AASc-3a-004:

        For a :class:`Concept_description` with :attr:`category` ``PROPERTY`` or
        ``VALUE`` using data specification IEC61360,
        the :attr:`Data_specification_IEC_61360.data_type` is mandatory and shall be
        one of: ``DATE``, ``STRING``, ``STRING_TRANSLATABLE``, ``INTEGER_MEASURE``,
        ``INTEGER_COUNT``, ``INTEGER_CURRENCY``, ``REAL_MEASURE``, ``REAL_COUNT``,
        ``REAL_CURRENCY``, ``BOOLEAN``, ``RATIONAL``, ``RATIONAL_MEASURE``,
        ``TIME``, ``TIMESTAMP``.

        .. note::

            Note: categories are deprecated since V3.0 of Part 1a of the document series
            "Details of the Asset Administration Shell".

    :constraint AASc-3a-005:
        For a :class:`Concept_description` with :attr:`category` ``REFERENCE``
        using data specification template IEC61360,
        the :attr:`Data_specification_IEC_61360.data_type` shall be
        one of: ``STRING``, ``IRI``, ``IRDI``.

        .. note::

            Note: categories are deprecated since V3.0 of Part 1a of the document series
            "Details of the Asset Administration Shell".

    :constraint AASc-3a-006:
        For a :class:`Concept_description` with :attr:`category` ``DOCUMENT``
        using data specification IEC61360,
        the :attr:`Data_specification_IEC_61360.data_type` shall be one of ``FILE``,
        ``BLOB``, ``HTML``

        .. note::

            Categories are deprecated since V3.0 of Part 1a of the document series
            "Details of the Asset Administration Shell".

    :constraint AASc-3a-007:
        For a :class:`Concept_description` with :attr:`category` ``QUALIFIER_TYPE``
        using data specification IEC61360,
        the :attr:`Data_specification_IEC_61360.data_type` is mandatory and shall be
        defined.

        .. note::

            Categories are deprecated since V3.0 of Part 1a of the document series
            "Details of the Asset Administration Shell".

    :constraint AASc-3a-008:
        For a :class:`Concept_description` using data specification template IEC61360,
        :attr:`Data_specification_IEC_61360.definition` is mandatory and shall be
        defined at least in English.

        Exception: The concept description describes a value, i.e.
        :attr:`Data_specification_IEC_61360.value` is defined.

    :constraint AASc-3a-003:
        For a :class:`Concept_description` using data specification template IEC61360,
        referenced via :attr:`Data_specification_IEC_61360.value_list`
        :attr:`Value_reference_pair.value_ID`
        the :attr:`Data_specification_IEC_61360.value` shall be set.
    """

    is_case_of: Optional[List["Reference"]]
    """
    Reference to an external definition the concept is compatible to or was derived
    from.

    .. note::

       Compare with is-case-of relationship in ISO 13584-32 & IEC EN 61360
    """

    def __init__(
        self,
        ID: Identifier,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        administration: Optional["Administrative_information"] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        is_case_of: Optional[List["Reference"]] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            ID=ID,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            administration=administration,
        )

        Has_data_specification.__init__(
            self, embedded_data_specifications=embedded_data_specifications
        )

        self.is_case_of = is_case_of


class Reference_types(Enum):
    """
    Enumeration for denoting whether an element is an external or model reference.
    """

    External_reference = "ExternalReference"
    """
    External reference.
    """

    Model_reference = "ModelReference"
    """
    Model reference.
    """


# fmt: off
@invariant(
    lambda self:
    not (
        self.type == Reference_types.Model_reference
        and len(self.keys) > 2
    ) or (
        all(
            not (self.keys[i].type == Key_types.Submodel_element_list)
            or matches_xs_non_negative_integer(self.keys[i + 1].value)
            for i in range(0, len(self.keys) - 1)
        )
    ),
    "Constraint AASd-128: For model references, the value of a key preceded by a key "
    "with type Submodel element list is an integer number denoting the position in "
    "the array of the submodel element list."
)
# NOTE (mristin):
# We can write AASd-127 in this simpler form assuming that AASd-126 ensures that
# only the last key can be a fragment reference.
@invariant(
    lambda self:
    not (
        self.type == Reference_types.Model_reference
        and len(self.keys) > 1
        and self.keys[-1].type == Key_types.Fragment_reference
    ) or (
      self.keys[-2].type == Key_types.File
      or self.keys[-2].type == Key_types.Blob
    ),
    "Constraint AASd-127: For model references, with more than one key "
    "in keys a key with type Fragment Reference shall be preceded "
    "by a key with type File or Blob."
)
@invariant(
    lambda self:
    not (
            self.type == Reference_types.Model_reference
            and len(self.keys) > 1
    )
    or (
        all(
            not (self.keys[i].type in Generic_fragment_keys)
            for i in range(0, len(self.keys) - 1)
        )
    ),
    "Constraint AASd-126: For model references with more than one key "
    "in keys the value of type of the last key "
    "in the reference key chain may be one of Generic Fragment Keys or "
    "no key at all shall have a value out of Generic Fragment Keys."
)
@invariant(
    lambda self:
    not (self.type == Reference_types.Model_reference and len(self.keys) > 1)
    or (
        all(
            self.keys[i].type in Fragment_keys
            for i in range(1, len(self.keys))
        )
    ),
    "Constraint AASd-125: For model references with more than one key in keys "
    "the value of type of each of the keys following the first key "
    "of keys shall be one of Fragment Keys."
)
@invariant(
    lambda self:
    not (
        self.type == Reference_types.External_reference
        and len(self.keys) >= 1
    )
    or (
        self.keys[-1].type in Generic_globally_identifiables
        or self.keys[-1].type in Generic_fragment_keys
    ),
    "Constraint AASd-124: For external references the last key of keys "
    "shall be either one of Generic Globally Identifiables or "
    "one of Generic Fragment Keys."
)
@invariant(
    lambda self:
    not (self.type == Reference_types.External_reference)
    or (
        all(
            not (key.type in AAS_referables)
            for key in self.keys
        )
    ),
    "Constraint AASd-137: For external references, i.e. References with "
    "Reference/type = ExternalReference, the value of Key/type of any key in "
    "Reference/keys shall not be one of AAS referables."
)
@invariant(
    lambda self:
    not (
        self.type == Reference_types.Model_reference
        and len(self.keys) >= 1
    )
    or self.keys[0].type in AAS_identifiables,
    "Constraint AASd-123: For model references the value of type of the first key "
    "of keys shall be one of AAS identifiables."
)
@invariant(
    lambda self:
    not (
        self.type == Reference_types.External_reference
        and len(self.keys) >= 1
    )
    or self.keys[0].type in Generic_globally_identifiables,
    "Constraint AASd-122: For external references the value of type "
    "of the first key of keys shall be one of Generic Globally Identifiables."
)
@invariant(
    lambda self:
    not (len(self.keys) >= 1)
    or self.keys[0].type in Globally_identifiables,
    "Constraint AASd-121: For References the value of type of the first key of "
    "keys shall be one of Globally Identifiables."
)
@invariant(
    lambda self: len(self.keys) >= 1,
    "Keys must contain at least one item."
)
# fmt: on
class Reference(DBC):
    """
    Reference to either a model element of the same or another Asset Administration
    Shell or to an external entity.

    A model reference is an ordered list of keys, each key referencing an element. The
    complete list of keys may for example be concatenated to a path that gives
    unique access to an element.

    An external reference is a reference to an external entity.

    :constraint AASd-121:

        For :class:`Reference`'s the value of :attr:`Key.type` of the first key of "
        :attr:`keys` shall be one of :const:`Globally_identifiables`.

    :constraint AASd-122:

        For external references, i.e. :class:`Reference`'s with
        :attr:`Reference.type` = :attr:`Reference_types.External_reference`, the value
        of :attr:`Key.type` of the first key of :attr:`Reference.keys` shall be one of
        :const:`Generic_globally_identifiables`.

    :constraint AASd-123:

        For model references, i.e. :class:`Reference`'s with
        :attr:`Reference.type` = :attr:`Reference_types.Model_reference`, the value
        of :attr:`Key.type` of the first key of :attr:`Reference.keys` shall be one of
        :const:`AAS_identifiables`.

    :constraint AASd-124:

        For external references, i.e. :class:`Reference`'s with
        :attr:`Reference.type` = :attr:`Reference_types.External_reference`, the last
        key of :attr:`Reference.keys` shall be either one of
        :const:`Generic_globally_identifiables` or one of
        :const:`Generic_fragment_keys`.

    :constraint AASd-137:

        For external references, i.e. :class:`Reference`'s with
        :attr:`Reference.type` = :attr:`Reference_types.External_reference`,
        the value of :attr:`Key.type` of any key in :attr:`Reference.keys`
        shall not be one of :const:`AAS_referables`.

    :constraint AASd-125:

        For model references, i.e. :class:`Reference`'s with
        :attr:`Reference.type` = :attr:`Reference_types.Model_reference`, with more
        than one key in :attr:`Reference.keys` the value of :attr:`Key.type`
        of each of the keys following the first
        key of :attr:`Reference.keys` shall be one of :const:`Fragment_keys`.

        .. note::

            :constraintref:`AASd-125` ensures that the shortest path is used.

    :constraint AASd-126:

        For model references, i.e. :class:`Reference`'s with
        :attr:`Reference.type` = :attr:`Reference_types.Model_reference`, with more
        than one key in :attr:`Reference.keys` the value of :attr:`Key.type`
        of the last key in the reference key chain may be
        one of :const:`Generic_fragment_keys` or no key at all
        shall have a value out of :const:`Generic_fragment_keys`.

    :constraint AASd-127:

        For model references, i.e. :class:`Reference`'s with
        :attr:`Reference.type` = :attr:`Reference_types.Model_reference`, with more
        than one key in :attr:`Reference.keys` a key with :attr:`Key.type`
        :attr:`Key_types.Fragment_reference` shall be preceded by a key with
        :attr:`Key.type` :attr:`Key_types.File` or :attr:`Key_types.Blob`. All other
        AAS fragments, i.e. :attr:`Key.type` values
        out of :const:`AAS_submodel_elements_as_keys`, do not support fragments.

        .. note::

            Which kind of fragments are supported depends on the content type and the
            specification of allowed fragment identifiers for the corresponding resource
            being referenced via the reference.

    :constraint AASd-128:

        For model references, i.e. :class:`Reference`'s with
        :attr:`Reference.type` = :attr:`Reference_types.Model_reference`, the
        :attr:`Key.value` of a :class:`Key` preceded by a :class:`Key` with
        :attr:`Key.type` = :attr:`Key_types.Submodel_element_list` is an integer
        number denoting the position in the array of the submodel element list.
    """

    type: "Reference_types"
    """
    Type of the reference.

    Denotes whether the reference is an external reference or a model reference.
    """

    referred_semantic_ID: Optional["Reference"]
    """
    Expected :attr:`Has_semantics.semantic_ID` of the referenced model element
    (:attr:`Reference.type` = :attr:`Reference_types.Model_reference`); there
    typically is no semantic ID for the referenced object of external references
    (:attr:`Reference.type` = :attr:`Reference_types.External_reference`).

    .. note::

        If :attr:`referred_semantic_ID` is defined, the
        :attr:`Has_semantics.semantic_ID` of the model element referenced should
        have a matching semantic ID. If this is not the case, a validator should
        raise a warning.
    """

    keys: List["Key"]
    """
    Unique references in their name space.
    """

    def __init__(
        self,
        type: Reference_types,
        keys: List["Key"],
        referred_semantic_ID: Optional["Reference"] = None,
    ) -> None:
        self.type = type
        self.keys = keys
        self.referred_semantic_ID = referred_semantic_ID


class Key(DBC):
    """A key is a reference to an element by its ID."""

    type: "Key_types"
    """
    Denotes which kind of entity is referenced.

    If :attr:`type` = :attr:`Key_types.Global_reference`,
    the key represents a reference to a source that can be globally identified.

    If :attr:`type` = :attr:`Key_types.Fragment_reference` the key represents
    a bookmark or a similar local identifier within its parent element as specified
    by the key that precedes this key.

    In all other cases, the key references a model element of the same or another
    Asset Administration Shell.
    The name of the model element is explicitly listed.
    """

    value: "Identifier"
    """
    The key value, for example an IRDI or a URI or the ID-short or any other 
    fragment value
    """

    def __init__(self, type: "Key_types", value: "Identifier") -> None:
        self.type = type
        self.value = value


class Key_types(Enum):
    """Enumeration of different key value types within a key."""

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

        Data elements are abstract, *i.e.* if a key uses :attr:`Data_element`
        the reference may be a property, file, etc.
    """

    Entity = "Entity"
    Event_element = "EventElement"
    """
    Event.

    .. note::

        :class:`Event_element` is abstract.
    """

    File = "File"

    Fragment_reference = "FragmentReference"
    """
    Bookmark or a similar local identifier of a subordinate part of
    a primary resource
    """

    Global_reference = "GlobalReference"

    Identifiable = "Identifiable"
    """
    Identifiable.

    .. note::

        Identifiable is abstract, i.e. if a key uses "Identifiable" the reference
        may be an :class:`Asset_administration_shell`, a :class:`Submodel` or
        a :class:`Concept_description`.
    """

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

        Submodel Element is abstract, *i.e.* if a key uses :attr:`Submodel_element`
        the reference may be a :class:`Property`, a :class:`Submodel_element_list`,
        an :class:`Operation` etc.
    """
    Submodel_element_collection = "SubmodelElementCollection"
    """
    Struct of :class:`Submodel_element`'s
    """

    Submodel_element_list = "SubmodelElementList"
    """
    List of :class:`Submodel_element`'s
    """


Generic_fragment_keys: Set[Key_types] = constant_set(
    values=[
        Key_types.Fragment_reference,
    ],
    description="""\
Enumeration of all identifiable elements within an asset administration shell.""",
)

assert Key_types.Fragment_reference in Generic_fragment_keys, (
    "We assume that fragment reference is in the generic fragment keys so that "
    "AASd-126 ensures that a key of type Fragment reference can only be the last key "
    "in the reference. This is necessary for our simpler formulation of AASd-127."
)

Generic_globally_identifiables: Set[Key_types] = constant_set(
    values=[
        Key_types.Global_reference,
    ],
    description="Enumeration of different key value types within a key.",
)

AAS_identifiables: Set[Key_types] = constant_set(
    values=[
        Key_types.Asset_administration_shell,
        Key_types.Concept_description,
        Key_types.Identifiable,
        Key_types.Submodel,
    ],
    description="Enumeration of different key value types within a key.",
)

AAS_submodel_elements_as_keys: Set[Key_types] = constant_set(
    values=[
        Key_types.Annotated_relationship_element,
        Key_types.Basic_event_element,
        Key_types.Blob,
        Key_types.Capability,
        Key_types.Data_element,
        Key_types.Entity,
        Key_types.Event_element,
        Key_types.File,
        Key_types.Multi_language_property,
        Key_types.Operation,
        Key_types.Property,
        Key_types.Range,
        Key_types.Reference_element,
        Key_types.Relationship_element,
        Key_types.Submodel_element,
        Key_types.Submodel_element_collection,
        Key_types.Submodel_element_list,
    ],
    description="""\
Enumeration of all submodel elements within an asset administration shell.""",
)

AAS_referable_non_identifiables: Set[Key_types] = constant_set(
    values=[
        Key_types.Annotated_relationship_element,
        Key_types.Basic_event_element,
        Key_types.Blob,
        Key_types.Capability,
        Key_types.Data_element,
        Key_types.Entity,
        Key_types.Event_element,
        Key_types.File,
        Key_types.Multi_language_property,
        Key_types.Operation,
        Key_types.Property,
        Key_types.Range,
        Key_types.Reference_element,
        Key_types.Relationship_element,
        Key_types.Submodel_element,
        Key_types.Submodel_element_collection,
        Key_types.Submodel_element_list,
    ],
    description="Enumeration of different fragment key value types within a key.",
    superset_of=[AAS_submodel_elements_as_keys],
)

AAS_referables: Set[Key_types] = constant_set(
    values=[
        Key_types.Asset_administration_shell,
        Key_types.Concept_description,
        Key_types.Identifiable,
        Key_types.Submodel,
        Key_types.Annotated_relationship_element,
        Key_types.Basic_event_element,
        Key_types.Blob,
        Key_types.Capability,
        Key_types.Data_element,
        Key_types.Entity,
        Key_types.Event_element,
        Key_types.File,
        Key_types.Multi_language_property,
        Key_types.Operation,
        Key_types.Property,
        Key_types.Range,
        Key_types.Reference_element,
        Key_types.Referable,
        Key_types.Relationship_element,
        Key_types.Submodel_element,
        Key_types.Submodel_element_collection,
        Key_types.Submodel_element_list,
    ],
    description="Enumeration of referables. "
    "We need this to check that model references refer to a Referable. "
    "For example, the observed attribute of the "
    "Basic Event Element object must be a model reference to a Referable.",
    superset_of=[AAS_referable_non_identifiables, AAS_identifiables],
)

Globally_identifiables: Set[Key_types] = constant_set(
    values=[
        Key_types.Global_reference,
        Key_types.Asset_administration_shell,
        Key_types.Concept_description,
        Key_types.Identifiable,
        Key_types.Submodel,
    ],
    description="""\
Enumeration of all referable elements within an asset administration shell""",
    superset_of=[AAS_identifiables, Generic_globally_identifiables],
)

Fragment_keys: Set[Key_types] = constant_set(
    values=[
        Key_types.Annotated_relationship_element,
        Key_types.Basic_event_element,
        Key_types.Blob,
        Key_types.Capability,
        Key_types.Data_element,
        Key_types.Entity,
        Key_types.Event_element,
        Key_types.File,
        Key_types.Fragment_reference,
        Key_types.Multi_language_property,
        Key_types.Operation,
        Key_types.Property,
        Key_types.Range,
        Key_types.Reference_element,
        Key_types.Relationship_element,
        Key_types.Submodel_element,
        Key_types.Submodel_element_collection,
        Key_types.Submodel_element_list,
    ],
    description="Enumeration of different key value types within a key.",
    superset_of=[AAS_referable_non_identifiables, Generic_fragment_keys],
)


class Data_type_def_XSD(Enum):
    """
    Enumeration listing selected XSD anySimpleTypes of XML Schema 1.0.

    See: https://www.w3.org/TR/xmlschema-2/#built-in-primitive-datatypes

    .. note::

        RDF uses XML Schema Built-in data types from Version 1.1 but recommends
        to use only a subset of XSD data types. That is why they are excluded
        from the allowed data types in :class:`Data_type_def_XSD`.

        * XSD BuildIn List types are not supported (``ENTITIES``, ``IDREFS``
          and ``NMTOKENS``).
        * XSD string BuildIn types are not supported (``normalizedString``,
          ``token``, ``language``, ``NCName``, ``ENTITY``, ``ID``, ``IDREF``).
        * The following XSD primitive types are not supported: ``NOTATION``,
          ``QName``.

    .. note::

        Additionally, the following RDF types are not supported in
        :class:`Data_type_def_XSD`: ``HTML`` and ``XMLLiteral``.

    .. note::

        Numeric data types in XML Schema are based on the definitions of
        IEEE 754 with slight adoptions. For instance, :attr:`Float` and
        :attr:`Double` use different exponent ranges. In any case, solely
        the XML Schema data type definitions are applicable for AAS values.
    """

    Any_URI = "xs:anyURI"
    Base_64_binary = "xs:base64Binary"
    Boolean = "xs:boolean"
    Byte = "xs:byte"
    Date = "xs:date"
    Date_time = "xs:dateTime"
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
    Int = "xs:int"
    Integer = "xs:integer"
    Long = "xs:long"
    Negative_integer = "xs:negativeInteger"
    Non_negative_integer = "xs:nonNegativeInteger"
    Non_positive_integer = "xs:nonPositiveInteger"
    Positive_integer = "xs:positiveInteger"
    Short = "xs:short"
    String = "xs:string"
    Time = "xs:time"
    Unsigned_byte = "xs:unsignedByte"
    Unsigned_int = "xs:unsignedInt"
    Unsigned_long = "xs:unsignedLong"
    Unsigned_short = "xs:unsignedShort"


@abstract
class Abstract_lang_string(DBC):
    """Strings with language tags"""

    language: BCP_47_language_tag
    """Language tag conforming to BCP 47"""

    text: Non_empty_XML_serializable_string
    """Text in the :attr:`language`"""

    def __init__(
        self, language: BCP_47_language_tag, text: Non_empty_XML_serializable_string
    ) -> None:
        self.language = language
        self.text = text


@invariant(
    lambda self: len(self.text) <= 128,
    "String shall have a maximum length of 128 characters.",
)
class Lang_string_name_type(Abstract_lang_string, DBC):
    """String with length 128 maximum and minimum 1 characters and with language tags"""

    def __init__(
        self, language: BCP_47_language_tag, text: Non_empty_XML_serializable_string
    ) -> None:
        Abstract_lang_string.__init__(self, language=language, text=text)


@invariant(
    lambda self: len(self.text) <= 1023,
    "String shall have a maximum length of 1023 characters.",
)
class Lang_string_text_type(Abstract_lang_string, DBC):
    """
    String with length 1023 maximum and minimum 1 characters and with language tags
    """

    def __init__(
        self, language: BCP_47_language_tag, text: Non_empty_XML_serializable_string
    ) -> None:
        Abstract_lang_string.__init__(self, language=language, text=text)


# fmt: off
@invariant(
    lambda self:
    not (self.asset_administration_shells is not None)
    or len(self.asset_administration_shells) >= 1,
    "Asset administration shells must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.submodels is not None)
    or len(self.submodels) >= 1,
    "Submodels must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.concept_descriptions is not None)
    or len(self.concept_descriptions) >= 1,
    "Concept descriptions must be either not set or have at least one item."
)
# fmt: on
class Environment:
    """
    Container for the sets of different identifiables.

    .. note::

        Environment is not an identifiable or referable element. It is introduced
        to enable file transfer as well as serialization.
    """

    asset_administration_shells: Optional[List[Asset_administration_shell]]
    """
    Asset Administration Shell
    """

    submodels: Optional[List[Submodel]]
    """
    Submodel
    """

    concept_descriptions: Optional[List[Concept_description]]
    """
    Concept description
    """

    def __init__(
        self,
        asset_administration_shells: Optional[List[Asset_administration_shell]] = None,
        submodels: Optional[List[Submodel]] = None,
        concept_descriptions: Optional[List[Concept_description]] = None,
    ) -> None:
        self.asset_administration_shells = asset_administration_shells
        self.submodels = submodels
        self.concept_descriptions = concept_descriptions


# region Data specifications


@abstract
@serialization(with_model_type=True)
class Data_specification_content:
    """
    Data specification content is part of a data specification template and defines
    which additional attributes shall be added to the element instance that references
    the data specification template and meta information about the template itself.

    :constraint AASc-3a-050:
        If the :class:`Data_specification_IEC_61360` is used
        for an element, the value of
        :attr:`Has_data_specification.embedded_data_specifications`
        shall contain the global reference to the IRI of the corresponding
        data specification template
        https://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/3/0

    """


class Embedded_data_specification:
    """Embed the content of a data specification."""

    data_specification: Reference
    """Reference to the data specification"""

    data_specification_content: Data_specification_content
    """Actual content of the data specification"""

    def __init__(
        self,
        data_specification: Reference,
        data_specification_content: Data_specification_content,
    ) -> None:
        self.data_specification = data_specification
        self.data_specification_content = data_specification_content


class Data_type_IEC_61360(Enum):
    Date = "DATE"
    """
    values containing a calendar date, conformant to ISO 8601:2004 Format yyyy-mm-dd
    Example from IEC 61360-1:2017: "1999-05-31" is the [DATE] representation of:
    "31 May 1999".
    """

    String = "STRING"
    """
    values consisting of sequence of characters but cannot be translated into other
    languages
    """

    String_translatable = "STRING_TRANSLATABLE"
    """
    values containing string but shall be represented as different string in different
    languages
    """

    Integer_measure = "INTEGER_MEASURE"
    """
    values containing values that are measure of type INTEGER. In addition such a value
    comes with a physical unit.
    """

    Integer_count = "INTEGER_COUNT"
    """
    values containing values of type INTEGER but are no currencies or measures
    """

    Integer_currency = "INTEGER_CURRENCY"
    """
    values containing values of type INTEGER that are currencies
    """

    Real_measure = "REAL_MEASURE"
    """
    values containing values that are measures of type REAL. In addition such a value
    comes with a physical unit.
    """

    Real_count = "REAL_COUNT"
    """
    values containing numbers that can be written as a terminating or non-terminating
    decimal; a rational or irrational number but are no currencies or measures
    """

    Real_currency = "REAL_CURRENCY"
    """
    values containing values of type REAL that are currencies
    """

    Boolean = "BOOLEAN"
    """
    values representing truth of logic or Boolean algebra (TRUE, FALSE)
    """

    IRI = "IRI"
    """
    values containing values of type STRING conformant to Rfc 3987

    .. note::

        In IEC61360-1 (2017) only URI is supported.
        An IRI type allows in particular to express an URL or an URI.
    """

    IRDI = "IRDI"
    """
    values conforming to ISO/IEC 11179 series global identifier sequences

    IRDI can be used instead of the more specific data types ICID or ISO29002_IRDI.

    ICID values are value conformant to an IRDI, where the delimiter between RAI and ID
    is “#” while the delimiter between DI and VI is confined to “##”

    ISO29002_IRDI values are values containing a global identifier that identifies an
    administrated item in a registry. The structure of this identifier complies with
    identifier syntax defined in ISO/TS 29002-5. The identifier shall fulfil the
    requirements specified in ISO/TS 29002-5 for an "international registration data
    identifier" (IRDI).
    """

    Rational = "RATIONAL"
    """
    values containing values of type rational
    """

    Rational_measure = "RATIONAL_MEASURE"
    """
    values containing values of type rational. In addition such a value comes with a
    physical unit.
    """

    Time = "TIME"
    """
    values containing a time, conformant to ISO 8601:2004 but restricted to what is
    allowed in the corresponding type in xml.

    Format hh:mm (ECLASS)

    Example from IEC 61360-1:2017: "13:20:00-05:00" is the [TIME] representation of:
    1.20 p.m. for Eastern Standard Time, which is 5 hours behind Coordinated
    Universal Time (UTC).
    """

    Timestamp = "TIMESTAMP"
    """
    values containing a time, conformant to ISO 8601:2004 but restricted to what is
    allowed in the corresponding type in xml.

    Format yyyy-mm-dd hh:mm (ECLASS)
    """

    File = "FILE"
    """
    values containing an address to a file. The values are of type URI and can represent
    an absolute or relative path.

    .. note::

        IEC61360 does not support the file type.
    """

    HTML = "HTML"
    """
    Values containing string with any sequence of characters, using the syntax of HTML5
    (see W3C Recommendation 28:2014)
    """

    Blob = "BLOB"
    """
    values containing the content of a file. Values may be binaries.

    HTML conformant to HTML5 is a special blob.

    In IEC61360 binary is for a sequence of bits, each bit being represented by “0” and
    “1” only. A binary is a blob but a blob may also contain other source code.
    """


Data_type_IEC_61360_for_property_or_value: Set[Data_type_IEC_61360] = constant_set(
    values=[
        Data_type_IEC_61360.Date,
        Data_type_IEC_61360.String,
        Data_type_IEC_61360.String_translatable,
        Data_type_IEC_61360.Integer_measure,
        Data_type_IEC_61360.Integer_count,
        Data_type_IEC_61360.Integer_currency,
        Data_type_IEC_61360.Real_measure,
        Data_type_IEC_61360.Real_count,
        Data_type_IEC_61360.Real_currency,
        Data_type_IEC_61360.Boolean,
        Data_type_IEC_61360.Rational,
        Data_type_IEC_61360.Rational_measure,
        Data_type_IEC_61360.Time,
        Data_type_IEC_61360.Timestamp,
    ],
    description=(
        "IEC 61360 data types for concept descriptions categorized "
        "with PROPERTY or VALUE."
    ),
)

Data_type_IEC_61360_for_reference: Set[Data_type_IEC_61360] = constant_set(
    values=[
        Data_type_IEC_61360.String,
        Data_type_IEC_61360.IRI,
        Data_type_IEC_61360.IRDI,
    ],
    description=(
        "IEC 61360 data types for concept descriptions categorized " "with REFERENCE."
    ),
)

Data_type_IEC_61360_for_document: Set[Data_type_IEC_61360] = constant_set(
    values=[
        Data_type_IEC_61360.File,
        Data_type_IEC_61360.Blob,
        Data_type_IEC_61360.HTML,
    ],
    description=(
        "IEC 61360 data types for concept descriptions categorized " "with DOCUMENT."
    ),
)


class Level_type(DBC):
    """
    Value represented by up to four variants of a numeric value in a specific role:
    ``MIN``, ``NOM``, ``TYP`` and ``MAX``. True means that the value is available,
    false means the value is not available.

    EXAMPLE from [IEC61360-1]: In the case of having a property which is
    of the LEVEL_TYPE min/max − expressing a range − only those two values
    need to be provided.

    .. note::

        This is how AAS deals with the following combinations of level types:

        - Either all attributes are false. In this case the concept is mapped
          to a :class:`Property` and level type is ignored.
        - At most one of the attributes is set to true. In this case
          the concept is mapped to a :class:`Property`.
        - Min and max are set to true. In this case the concept is mapped
          to a :class:`Range`.
        - More than one attribute is set to true but not min and max only
          (see second case). In this case the concept is mapped
          to a :class:`Submodel_element_collection` with the corresponding
          number of Properties.
          Example: If attribute :attr:`min` and :attr:`nom` are set to true
          then the concept is mapped to a :class:`Submodel_element_collection`
          with two Properties within: min and nom.
          The data type of both Properties is the same.

    .. note::

        In the cases 2. and 4. the :attr:`Property.semantic_ID` of the Property
        or Properties within the :class:`Submodel_element_collection` needs to include
        information about the level type. Otherwise, the semantics is not described
        in a unique way. Please refer to the specification.

    """

    min: "bool"
    """Minimum of the value"""

    nom: "bool"
    """Nominal value (value as designated)"""

    typ: "bool"
    """Value as typically present"""

    max: "bool"
    """Maximum of the value"""

    def __init__(
        self,
        min: "bool",
        nom: "bool",
        typ: "bool",
        max: "bool",
    ) -> None:
        self.min = min
        self.nom = nom
        self.typ = typ
        self.max = max


class Value_reference_pair(DBC):
    """
    A value reference pair within a value list. Each value has a global unique id
    defining its semantic.
    """

    value: Value_type_IEC_61360
    """
    The value of the referenced concept definition of the value in :attr:`value_ID`.
    """

    value_ID: Optional["Reference"]
    """
    Global unique id of the value.

    .. note::

        It is recommended to use a global reference.

    """

    def __init__(
        self,
        value: Value_type_IEC_61360,
        value_ID: Optional["Reference"] = None,
    ) -> None:
        self.value = value
        self.value_ID = value_ID


# fmt: off
@invariant(
    lambda self:
    len(self.value_reference_pairs) >= 1,
    "Value reference pair types must contain at least one item."
)
# fmt: on
class Value_list(DBC):
    """
    A set of value reference pairs.
    """

    value_reference_pairs: List["Value_reference_pair"]
    """
    A pair of a value together with its global unique id.
    """

    def __init__(self, value_reference_pairs: List["Value_reference_pair"]) -> None:
        self.value_reference_pairs = value_reference_pairs


# todo: Update Reference as it applies to Part 3b document
IEC_61360_data_types_with_unit: Set[Data_type_IEC_61360] = constant_set(
    values=[
        Data_type_IEC_61360.Integer_measure,
        Data_type_IEC_61360.Real_measure,
        Data_type_IEC_61360.Rational_measure,
        Data_type_IEC_61360.Integer_currency,
        Data_type_IEC_61360.Real_currency,
    ],
    description="""\
These data types imply that the unit is defined in the data specification.""",
)


@invariant(
    lambda self: len(self.text) <= 255,
    "String shall have a maximum length of 255 characters.",
)
class Lang_string_preferred_name_type_IEC_61360(Abstract_lang_string, DBC):
    """
    String with length 255 maximum and minimum 1 characters and with language tags

    .. note::

        It is advised to keep the length of the name limited to 35 characters.

    """

    def __init__(
        self, language: BCP_47_language_tag, text: Non_empty_XML_serializable_string
    ) -> None:
        Abstract_lang_string.__init__(self, language=language, text=text)


@invariant(
    lambda self: len(self.text) <= 18,
    "String shall have a maximum length of 18 characters.",
)
class Lang_string_short_name_type_IEC_61360(Abstract_lang_string, DBC):
    """
    String with length 18 maximum and minimum 1 characters and with language tags
    """

    def __init__(
        self, language: BCP_47_language_tag, text: Non_empty_XML_serializable_string
    ) -> None:
        Abstract_lang_string.__init__(self, language=language, text=text)


@invariant(
    lambda self: len(self.text) <= 1023,
    "String shall have a maximum length of 1023 characters.",
)
class Lang_string_definition_type_IEC_61360(Abstract_lang_string, DBC):
    """
    String with length 1023 maximum and minimum 1 characters and with language tags
    """

    def __init__(
        self, language: BCP_47_language_tag, text: Non_empty_XML_serializable_string
    ) -> None:
        Abstract_lang_string.__init__(self, language=language, text=text)


@verification
def is_BCP_47_for_english(text: str) -> bool:
    """Check that the :paramref:`text` corresponds to a BCP47 code for english."""
    pattern = f"^(en|EN)(-.*)?$"

    return match(pattern, text) is not None


# fmt: off
@invariant(
    lambda self:
    any(
        is_BCP_47_for_english(lang_string.language)
        for lang_string in self.preferred_name
    ),
    "Constraint AASc-002: preferred name shall be provided at least in English."
)
@invariant(
    lambda self:
    lang_strings_have_unique_languages(self.preferred_name),
    "Preferred name must specify unique languages."
)
@invariant(
    lambda self:
    len(self.preferred_name) >= 1,
    "Preferred name must have at least one item."
)
@invariant(
    lambda self:
    not (self.short_name is not None)
    or lang_strings_have_unique_languages(self.short_name),
    "Short name must specify unique languages."
)
@invariant(
    lambda self:
    not (self.short_name is not None)
    or len(self.short_name) >= 1,
    "Short name must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.definition is not None)
    or lang_strings_have_unique_languages(self.definition),
    "Definition must specify unique languages."
)
@invariant(
    lambda self:
    not (self.definition is not None)
    or len(self.definition) >= 1,
    "Definition must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (
            self.data_type is not None
            and self.data_type in IEC_61360_data_types_with_unit
    ) or (
            self.unit is not None or self.unit_ID is not None
    ),
    "Constraint AASc-3a-009: If data type is a an integer, real or rational with "
    "a measure or currency, unit or unit ID shall be defined."
)
@invariant(
    lambda self:
    not (
        self.value is not None
        and self.value_list is not None
    ),
    "Constraint AASc-3a-010: If value is not empty then value list shall be empty and "
    "vice versa."
)
@serialization(with_model_type=True)
# fmt: on
class Data_specification_IEC_61360(Data_specification_content):
    """
    Content of data specification template for concept descriptions for properties,
    values and value lists conformant to IEC 61360.

    .. note::

        IEC61360 requires also a globally unique identifier for a concept
        description. This ID is not part of the data specification template.
        Instead the :attr:`Concept_description.ID` as inherited via
        :class:`Identifiable` is used. Same holds for administrative
        information like the version and revision.

    .. note::

        :attr:`Concept_description.ID_short` and :attr:`short_name` are very
        similar. However, in this case the decision was to add
        :attr:`short_name` explicitly to the data specification. Same holds for
        :attr:`Concept_description.display_name` and
        :attr:`preferred_name`. Same holds for
        :attr:`Concept_description.description` and :attr:`definition`.

    :constraint AASc-3a-010:
        If :attr:`value` is not empty then :attr:`value_list` shall be empty
        and vice versa.

        .. note::

            It is also possible that both :attr:`value` and :attr:`value_list` are
            empty. This is the case for concept descriptions that define the semantics
            of a property but do not have an enumeration (:attr:`value_list`) as
            data type.

        .. note::

            Although it is possible to define a :class:`Concept_description` for a
            :attr:´value_list`,
            it is not possible to reuse this :attr:`value_list`.
            It is only possible to directly add a :attr:`value_list` as data type
            to a specific semantic definition of a property.

    :constraint AASc-3a-009:
        If :attr:`data_type` one of:
        :attr:`Data_type_IEC_61360.Integer_measure`,
        :attr:`Data_type_IEC_61360.Real_measure`,
        :attr:`Data_type_IEC_61360.Rational_measure`,
        :attr:`Data_type_IEC_61360.Integer_currency`,
        :attr:`Data_type_IEC_61360.Real_currency`, then :attr:`unit` or
        :attr:`unit_ID` shall be defined.
    """

    preferred_name: List["Lang_string_preferred_name_type_IEC_61360"]
    """
    Preferred name

    .. note::

        It is advised to keep the length of the name limited to 35 characters.

    :constraint AASc-3a-002:
        :attr:`preferred_name` shall be provided at least in English.
    """

    short_name: Optional[List["Lang_string_short_name_type_IEC_61360"]]
    """
    Short name
    """

    unit: Optional[Non_empty_XML_serializable_string]
    """
    Unit
    """

    unit_ID: Optional["Reference"]
    """
    Unique unit id

    :attr:`unit` and :attr:`unit_ID` need to be consistent if both attributes
    are set

    .. note::

        It is recommended to use an external reference ID.

    """

    source_of_definition: Optional[Non_empty_XML_serializable_string]
    """
    Source of definition
    """

    symbol: Optional[Non_empty_XML_serializable_string]
    """
    Symbol
    """

    data_type: Optional["Data_type_IEC_61360"]
    """
    Data Type
    """

    definition: Optional[List["Lang_string_definition_type_IEC_61360"]]
    """
    Definition in different languages
    """

    value_format: Optional[Non_empty_XML_serializable_string]
    """
    Value Format

    .. note::

        The value format is based on ISO 13584-42 and IEC 61360-2.

    """

    value_list: Optional["Value_list"]
    """
    List of allowed values
    """

    value: Optional[Value_type_IEC_61360]
    """
    Value
    """

    level_type: Optional["Level_type"]
    """
    Set of levels.
    """

    def __init__(
        self,
        preferred_name: List["Lang_string_preferred_name_type_IEC_61360"],
        short_name: Optional[List["Lang_string_short_name_type_IEC_61360"]] = None,
        unit: Optional[Non_empty_XML_serializable_string] = None,
        unit_ID: Optional["Reference"] = None,
        source_of_definition: Optional[Non_empty_XML_serializable_string] = None,
        symbol: Optional[Non_empty_XML_serializable_string] = None,
        data_type: Optional["Data_type_IEC_61360"] = None,
        definition: Optional[List["Lang_string_definition_type_IEC_61360"]] = None,
        value_format: Optional[Non_empty_XML_serializable_string] = None,
        value_list: Optional["Value_list"] = None,
        value: Optional[Value_type_IEC_61360] = None,
        level_type: Optional["Level_type"] = None,
    ) -> None:
        self.preferred_name = preferred_name
        self.short_name = short_name
        self.unit = unit
        self.unit_ID = unit_ID
        self.source_of_definition = source_of_definition
        self.symbol = symbol
        self.data_type = data_type
        self.definition = definition
        self.value_format = value_format
        self.value_list = value_list
        self.value = value
        self.level_type = level_type


# region Part 2


# region API Interfaces


class Serialization_format(Enum):
    """
    Determines the format of serialization, for example JSON or XML.

    The values are media types conformant to RFC 2046 and registered as
    described in RFC 6838 (IANA).

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces.html#SerializationFormat
    """

    JSON = "application/json"
    """
    JSON serialization of the requested data object inside an AAS
    Environment structure
    """

    XML = "application/xml"
    """
    XML serialization of the requested data object inside an AAS Environment
    structure.
    """

    AASX = "application/aasx+xml"
    """AASX-Package (binary data) containing the requested data object"""


# endregion API Interfaces


# region Data Types For Payload


@abstract
# fmt: off
@invariant(
    lambda self:
    not (self.extensions is not None)
    or extension_names_are_unique(self.extensions),
    "The name of an extension needs to be unique."
)
@invariant(
    lambda self:
    not (self.extensions is not None)
    or len(self.extensions) >= 1,
    "Extensions must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.display_name is not None)
    or lang_strings_have_unique_languages(self.display_name),
    "Display name must specify unique languages."
)
@invariant(
    lambda self:
    not (self.display_name is not None)
    or len(self.display_name) >= 1,
    "Display name must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.description is not None)
    or lang_strings_have_unique_languages(self.description),
    "Description must specify unique languages."
)
@invariant(
    lambda self:
    not (self.description is not None)
    or len(self.description) >= 1,
    "Description must be either not set or have at least one item."
)
# fmt: on
class Descriptor(DBC):
    """
    The self-describing information of a network resource.

    This class is not part of the metamodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#Descriptor
    """

    description: Optional[List["Lang_string_text_type"]]
    """
    Description or comments on the element.

    The description can be provided in several languages.
    """

    display_name: Optional[List["Lang_string_name_type"]]
    """Display name. Can be provided in several languages."""

    extensions: Optional[List["Extension"]]
    """
    An extension of the element.

    .. note::

        Extensions are proprietary, i.e. they do not support global interoperability.
    """

    def __init__(
        self,
        description: Optional[List["Lang_string_text_type"]] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        extensions: Optional[List["Extension"]] = None,
    ) -> None:
        self.description = description
        self.display_name = display_name
        self.extensions = extensions


# fmt: off
@invariant(
    lambda self:
    not (self.submodel_descriptors is not None)
    or len(self.submodel_descriptors) >= 1,
    "Submodel descriptors must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.specific_asset_IDs is not None)
    or len(self.specific_asset_IDs) >= 1,
    "Specific asset IDs must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.endpoints is not None)
    or len(self.endpoints) >= 1,
    "Endpoints must be either not set or have at least one item."
)
# fmt: on
class Asset_administration_shell_descriptor(Descriptor):
    """
    Descriptor of an Asset Administration Shell.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#AssetAdministrationShellDescriptor
    """

    ID: "Identifier"
    """Globally unique identification of the Asset Administration Shell."""

    administration: Optional["Administrative_information"]
    """Administrative information of the Asset Administration Shell."""

    asset_kind: Optional["Asset_kind"]
    """
    Denotes whether the asset of the described Asset Administration Shell is of
    kind :attr:`Asset_kind.Type`, :attr:`Asset_kind.Instance`,
    :attr:`Asset_kind.Role`, or :attr:`Asset_kind.Not_applicable`.
    """

    asset_type: Optional["Identifier"]
    """
    The type of the asset described by the Asset Administration Shell of this
    descriptor.

    See :attr:`Asset_information.asset_type` for further information.
    """

    endpoints: Optional[List["Endpoint"]]
    """
    Endpoint of the network resource.

    .. note::

        The cardinality restriction for :attr:`endpoints` allows a provider to skip
        the declaration of the location of an Asset Administration Shell and directly
        point to the endpoints of the contained submodels through 
        :attr:`submodel_descriptors`' :attr:`Submodel_descriptor.endpoints`.
        A client, therefore, might decide to skip the lookup on the Asset
        Administration Shell.
        Nevertheless, in case the information contained in the
        :class:`Asset_administration_shell_descriptor` deviates from the
        related :class:`Asset_administration_shell`, or attributes are missing,
        the :class:`Asset_administration_shell` is always the source of truth.
    """

    global_asset_ID: Optional["Identifier"]
    """Global reference to the asset the Asset Administration Shell is representing."""

    ID_short: Optional["Name_type"]
    """Short name of the Asset Administration Shell."""

    specific_asset_IDs: Optional[List["Specific_asset_ID"]]
    """Specific asset identifier."""

    submodel_descriptors: Optional[List["Submodel_descriptor"]]
    """Descriptor of a submodel of the Asset Administration Shell."""

    def __init__(
        self,
        ID: "Identifier",
        description: Optional[List["Lang_string_text_type"]] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        extensions: Optional[List["Extension"]] = None,
        administration: Optional["Administrative_information"] = None,
        asset_kind: Optional["Asset_kind"] = None,
        asset_type: Optional["Identifier"] = None,
        endpoints: Optional[List["Endpoint"]] = None,
        global_asset_ID: Optional["Identifier"] = None,
        ID_short: Optional["Name_type"] = None,
        specific_asset_IDs: Optional[List["Specific_asset_ID"]] = None,
        submodel_descriptors: Optional[List["Submodel_descriptor"]] = None,
    ) -> None:
        Descriptor.__init__(
            self,
            description=description,
            display_name=display_name,
            extensions=extensions,
        )

        self.ID = ID
        self.administration = administration
        self.asset_kind = asset_kind
        self.asset_type = asset_type
        self.endpoints = endpoints
        self.global_asset_ID = global_asset_ID
        self.ID_short = ID_short
        self.specific_asset_IDs = specific_asset_IDs
        self.submodel_descriptors = submodel_descriptors


# fmt: off
@invariant(
    lambda self: len(self.endpoints) >= 1,
    "Endpoints must contain at least one item.",
)
@invariant(
    lambda self:
    not (self.supplemental_semantic_IDs is not None)
    or (self.semantic_ID is not None),
    "If there are supplemental semantic IDs defined then there shall be also "
    "a main semantic ID."
)
@invariant(
    lambda self:
    not (self.supplemental_semantic_IDs is not None)
    or len(self.supplemental_semantic_IDs) >= 1,
    "Supplemental semantic IDs must be either not set or have at least one item."
)
# fmt: on
class Submodel_descriptor(Descriptor):
    """
    A descriptor of a submodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#SubmodelDescriptor
    """

    endpoints: List["Endpoint"]
    """Endpoint of the network resource."""

    ID: "Identifier"
    """Globally unique identification of the Submodel."""

    administration: Optional["Administrative_information"]
    """Administrative information of the Submodel."""

    ID_short: Optional["Name_type"]
    """Short name of the Submodel."""

    semantic_ID: Optional["Reference"]
    """
    Identifier of the semantic definition of the Submodel.
    """

    supplemental_semantic_IDs: Optional[List["Reference"]]
    """
    Identifier of a supplemental semantic definition of the element called supplemental
    semantic ID of the element.
    """

    def __init__(
        self,
        endpoints: List["Endpoint"],
        ID: "Identifier",
        description: Optional[List["Lang_string_text_type"]] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        extensions: Optional[List["Extension"]] = None,
        administration: Optional["Administrative_information"] = None,
        ID_short: Optional["Name_type"] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
    ) -> None:
        Descriptor.__init__(
            self,
            description=description,
            display_name=display_name,
            extensions=extensions,
        )

        self.endpoints = endpoints
        self.ID = ID
        self.administration = administration
        self.ID_short = ID_short
        self.semantic_ID = semantic_ID
        self.supplemental_semantic_IDs = supplemental_semantic_IDs


class Endpoint(DBC):
    """
    The endpoint description of a network resource.

    This class is not part of the metamodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#Endpoint
    """

    protocol_information: "Protocol_information"
    """Protocol information of the network resource endpoint."""

    interface: "Name_type"
    """Name of the offered interface at the endpoint."""

    def __init__(
        self,
        protocol_information: "Protocol_information",
        interface: "Name_type",
    ) -> None:
        self.protocol_information = protocol_information
        self.interface = interface


# fmt: off
@invariant(
    lambda self:
    not (self.security_attributes is not None)
    or len(self.security_attributes) >= 1,
    "Security attributes must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.endpoint_protocol_versions is not None)
    or len(self.endpoint_protocol_versions) >= 1,
    "Endpoint protocol versions must be either not set or have at least one item."
)
# fmt: on
class Protocol_information(DBC):
    """
    The protocol information of a network resource endpoint.

    .. note::

        The protocol information of a network resource endpoint is defined in
        DIN SPEC 16593-2. After the release of DIN SPEC 16593-2, any required
        updates will be made. This class is not part of the metamodel.

        The information in this class is a 1:1 copy from DIN SPEC 16593-2. Required
        changes need to be made by the related DIN working group.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#ProtocolInformation
    """

    href: "Locator_type"
    """The endpoint address as a URL."""

    endpoint_protocol: Optional["Scheme_type"]
    """
    Either scheme of :attr:`href` or scheme plus further information.

    The scheme denotes the highest level of doubtless transmission.
    """

    endpoint_protocol_versions: Optional[List["Name_type"]]
    """
    Each entry represents one supported version at this very endpoint, the entry shall
    be formatted according to the regulations of the protocol specified in
    the :attr:`href`
    """

    subprotocol: Optional["Short_ID_type"]
    """
    Allows for referencing sub-protocols that may be used in the context of that
    endpoint e.g. "OPC Basic SOAP" or UA Binary
    """

    subprotocol_body: Optional["Text_type"]
    """
    If the sub-protocol field is present, a subprotocol body might be given to hold
    extra information, e.g. node and namespace in an OPC UA server
    """

    subprotocol_body_encoding: Optional["Name_type"]
    """
    If :attr:`subprotocol_body` is present, the encoding might be explicitly defined,
    otherwise it shall default to subprotocols encoding scheme
    """

    security_attributes: Optional[List["Security_attribute_object"]]
    """
    Array of :class:`Security_attribute_object`'s. Each attribute has
    three properties:

    :attr:`~Security_attribute_object.type`: enum security type or standard:

    * ``NONE``;
    * ``RFC_TLSA``, TLSA according to RFC 6698; or
    * ``W3C_DID``, W3C DID document.

    :attr:`~Security_attribute_object.key`: security attribute key according to standard
    definitions of the security type.
    
    :attr:`~Security_attribute_object.value`: security attribute value, *e.g.*, DANE
    TLSA Resource Record.

    The :class:`Security_attribute_object`'s are treated as possible
    alternatives (logical "or").
    """

    def __init__(
        self,
        href: "Locator_type",
        endpoint_protocol: Optional["Scheme_type"] = None,
        endpoint_protocol_versions: Optional[List["Name_type"]] = None,
        subprotocol: Optional["Short_ID_type"] = None,
        subprotocol_body: Optional["Text_type"] = None,
        subprotocol_body_encoding: Optional["Name_type"] = None,
        security_attributes: Optional[List["Security_attribute_object"]] = None,
    ) -> None:
        self.href = href
        self.endpoint_protocol = endpoint_protocol
        self.endpoint_protocol_versions = endpoint_protocol_versions
        self.subprotocol = subprotocol
        self.subprotocol_body = subprotocol_body
        self.subprotocol_body_encoding = subprotocol_body_encoding
        self.security_attributes = security_attributes


class Security_attribute_object(DBC):
    """
    Security attributes as defined by DIN SPEC 16593-2. After the release of
    DIN SPEC 16593-2, any required updates will be made. This class is not part of
    the metamodel.

    The information in this table is derived from DIN SPEC 16593-2. Required changes
    need to be made by the related DIN working group.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#SecurityAttributeObject
    """

    type: "Security_type_enum"
    """Enum security type or standard."""

    key: str
    """Security attribute key according to standard definitions of the security type."""

    value: str
    """Security attribute value e.g. DANE TLSA Resource Record."""

    def __init__(self, type: "Security_type_enum", key: str, value: str) -> None:
        self.type = type
        self.key = key
        self.value = value


class Security_type_enum(Enum):
    """
    The security types as defined by DIN SPEC 16593-2. After the release of
    DIN SPEC 16593-2, any required updates will be made. This class is not part of
    the metamodel.

    The information in this table is derived from DIN SPEC 16593-2. Required changes
    need to be made by the related DIN working group.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#SecurityTypeEnum
    """

    # NOTE (mristin):
    # The literal ``NONE`` from the specification is named :attr:`No_security`
    # here since ``None`` is a reserved keyword in Python.
    No_security = "NONE"
    """No predefined security type available."""

    RFC_TLSA = "RFC_TLSA"
    """TLSA according to RFC 6698."""

    W3C_DID = "W3C_DID"
    """Decentralized Identifiers according to the W3C Recommendation."""


class Protocol_version(DBC):
    """
    A single protocol version supported at a network resource endpoint.

    This class is not part of the metamodel. It represents a single entry of
    :attr:`Protocol_information.endpoint_protocol_versions`, which is specified
    as an array of plain strings in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#ProtocolInformation
    """

    value: "Name_type"
    """
    The supported version.

    The entry shall be formatted according to the regulations of the protocol
    specified in :attr:`Protocol_information.href`.
    """

    def __init__(self, value: "Name_type") -> None:
        self.value = value


class Asset_link(DBC):
    """
    Asset identifier derived from either :class:`Specific_asset_ID` or
    :attr:`Asset_information.global_asset_ID`.

    This class is not part of the metamodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#AssetLink
    """

    name: "Label_type"
    """
    Name of the Asset identifier, *i.e.*, ``globalAssetId``, a serial number,
    manufacturer part ID, or customer part IDs.
    """

    value: "Identifier"
    """Value of the Asset Identifier."""

    def __init__(self, name: "Label_type", value: "Identifier") -> None:
        self.name = name
        self.value = value


@invariant(
    lambda self: len(self.profiles) >= 1,
    "Profiles must contain at least one item.",
)
class Service_description(DBC):
    """
    The self-describing information of an API Implementation. It enables
    servers to present their capabilities to the clients, in particular
    which profiles they implement. At least one defined profile is
    required. Additional, proprietary attributes might be included.
    Nevertheless, the server must not expect that a regular client
    understands them.

    This class is not part of the metamodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#ServiceDescription
    """

    profiles: List["Service_specification_profile_enum"]
    """List of implemented server specification profiles."""

    def __init__(self, profiles: List["Service_specification_profile_enum"]) -> None:
        self.profiles = profiles


class Service_specification_profile_enum(Enum):
    """
    The identifiers of the standardized service specification profiles.
    See also Clause Service Specifications and Profiles for further
    details.

    This class is not part of the metamodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#ServiceSpecificationProfileEnum

    See also Clause Service Specifications and Profiles:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/http-rest-api/service-specifications-and-profiles.html#service-specifications-and-profiles
    """

    AAS_service_specification_SSP_001_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "AssetAdministrationShellServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all features of the Asset Administration
    Shell Service Specification Full Profile in version 3.0.
    """

    AAS_service_specification_SSP_001_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AssetAdministrationShellServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all features of the Asset Administration
    Shell Service Specification Full Profile in version 3.1.
    """

    AAS_service_specification_SSP_001_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all features of the Asset Administration
    Shell Service Specification Full Profile in version 3.2.
    """

    AAS_service_specification_SSP_002_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "AssetAdministrationShellServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all features of the Asset Administration
    Shell Service Specification Read Profile in version 3.0.
    """

    AAS_service_specification_SSP_002_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AssetAdministrationShellServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all features of the Asset Administration
    Shell Service Specification Read Profile in version 3.1.
    """

    AAS_service_specification_SSP_002_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all features of the Asset Administration
    Shell Service Specification Read Profile in version 3.2.
    """

    Submodel_service_specification_SSP_001_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/SubmodelServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all features of the Submodel Service
    Specification Full Profile in version 3.0.
    """

    Submodel_service_specification_SSP_001_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/SubmodelServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all features of the Submodel Service
    Specification Full Profile in version 3.1.
    """

    Submodel_service_specification_SSP_001_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/SubmodelServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all features of the Submodel Service
    Specification Full Profile in version 3.2.
    """

    Submodel_service_specification_SSP_002_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/SubmodelServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all features of the Submodel Service
    Specification Value Profile in version 3.0.
    """

    Submodel_service_specification_SSP_002_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/SubmodelServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all features of the Submodel Service
    Specification Value Profile in version 3.1.
    """

    Submodel_service_specification_SSP_002_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/SubmodelServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all features of the Submodel Service
    Specification Value Profile in version 3.2.
    """

    Submodel_service_specification_SSP_003_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/SubmodelServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all features of the Submodel Service
    Specification Read Profile in version 3.0.
    """

    Submodel_service_specification_SSP_003_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/SubmodelServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all features of the Submodel Service
    Specification Read Profile in version 3.1.
    """

    Submodel_service_specification_SSP_003_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/SubmodelServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all features of the Submodel Service
    Specification Read Profile in version 3.2.
    """

    AASX_file_server_service_specification_SSP_001_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "AasxFileServerServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the AASX File Server
    Service Specification Full Profile in version 3.0.
    """

    AASX_file_server_service_specification_SSP_001_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AasxFileServerServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the AASX File Server
    Service Specification Full Profile in version 3.1.
    """

    AASX_file_server_service_specification_SSP_001_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AasxFileServerServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the AASX File Server
    Service Specification Full Profile in version 3.2.
    """

    AASX_file_server_service_specification_SSP_002_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AasxFileServerServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the AASX File Server
    Service Specification Read Profile in version 3.1.
    """

    AASX_file_server_service_specification_SSP_002_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AasxFileServerServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the AASX File Server
    Service Specification Read Profile in version 3.2.
    """

    AAS_registry_service_specification_SSP_001_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Full Profile in version 3.0.
    """

    AAS_registry_service_specification_SSP_001_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Full Profile in version 3.1.
    """

    AAS_registry_service_specification_SSP_001_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Full Profile in version 3.2.
    """

    AAS_registry_service_specification_SSP_002_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Read Profile in version 3.0.
    """

    AAS_registry_service_specification_SSP_002_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Read Profile in version 3.1.
    """

    AAS_registry_service_specification_SSP_002_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Read Profile in version 3.2.
    """

    AAS_registry_service_specification_SSP_003_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Bulk Profile in version 3.1.
    """

    AAS_registry_service_specification_SSP_003_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Bulk Profile in version 3.2.
    """

    AAS_registry_service_specification_SSP_004_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-004"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Query Profile in version 3.1.
    """

    AAS_registry_service_specification_SSP_004_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-004"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Query Profile in version 3.2.
    """

    AAS_registry_service_specification_SSP_005_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-005"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Minimal Read Profile in version 3.1.
    """

    AAS_registry_service_specification_SSP_005_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellRegistryServiceSpecification/SSP-005"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Registry Service Specification Minimal Read Profile in version 3.2.
    """

    Submodel_registry_service_specification_SSP_001_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "SubmodelRegistryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Submodel Registry
    Service Specification Full Profile in version 3.0.
    """

    Submodel_registry_service_specification_SSP_001_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "SubmodelRegistryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Submodel Registry
    Service Specification Full Profile in version 3.1.
    """

    Submodel_registry_service_specification_SSP_001_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "SubmodelRegistryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Submodel Registry
    Service Specification Full Profile in version 3.2.
    """

    Submodel_registry_service_specification_SSP_002_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "SubmodelRegistryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Submodel Registry
    Service Specification Read Profile in version 3.0.
    """

    Submodel_registry_service_specification_SSP_002_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "SubmodelRegistryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Submodel Registry
    Service Specification Read Profile in version 3.1.
    """

    Submodel_registry_service_specification_SSP_002_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "SubmodelRegistryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Submodel Registry
    Service Specification Read Profile in version 3.2.
    """

    Submodel_registry_service_specification_SSP_003_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "SubmodelRegistryServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all details of the Submodel Registry
    Service Specification Bulk Profile in version 3.1.
    """

    Submodel_registry_service_specification_SSP_003_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "SubmodelRegistryServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all details of the Submodel Registry
    Service Specification Bulk Profile in version 3.2.
    """

    Submodel_registry_service_specification_SSP_004_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "SubmodelRegistryServiceSpecification/SSP-004"
    )
    """
    Indicates that the server implemented all details of the Submodel Registry
    Service Specification Query Profile in version 3.1.
    """

    Submodel_registry_service_specification_SSP_004_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "SubmodelRegistryServiceSpecification/SSP-004"
    )
    """
    Indicates that the server implemented all details of the Submodel Registry
    Service Specification Query Profile in version 3.2.
    """

    Discovery_service_specification_SSP_001_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/" "DiscoveryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Discovery Service
    Specification Full Profile in version 3.0.
    """

    Discovery_service_specification_SSP_001_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/" "DiscoveryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Discovery Service
    Specification Full Profile in version 3.1.
    """

    Discovery_service_specification_SSP_001_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/" "DiscoveryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Discovery Service
    Specification Full Profile in version 3.2.
    """

    Discovery_service_specification_SSP_002_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/" "DiscoveryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Discovery Service
    Specification Read Profile in version 3.1.
    """

    AAS_repository_service_specification_SSP_001_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "AssetAdministrationShellRepositoryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Repository Service Specification Full Profile in version 3.0.
    """

    AAS_repository_service_specification_SSP_001_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AssetAdministrationShellRepositoryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Repository Service Specification Full Profile in version 3.1.
    """

    AAS_repository_service_specification_SSP_001_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellRepositoryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Repository Service Specification Read Profile in version 3.2.
    """

    AAS_repository_service_specification_SSP_002_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "AssetAdministrationShellRepositoryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Repository Service Specification Read Profile in version 3.0.
    """

    AAS_repository_service_specification_SSP_002_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AssetAdministrationShellRepositoryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Repository Service Specification Read Profile in version 3.1.
    """

    AAS_repository_service_specification_SSP_002_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellRepositoryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Repository Service Specification Read Profile in version 3.2.
    """

    AAS_repository_service_specification_SSP_003_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "AssetAdministrationShellRepositoryServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Repository Service Specification Query Profile in version 3.1.
    """

    AAS_repository_service_specification_SSP_003_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellRepositoryServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Repository Service Specification Query Profile in version 3.2.
    """

    AAS_repository_service_specification_SSP_004_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellRepositoryServiceSpecification/SSP-004"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Repository Service Specification Signature Profile in version 3.2.
    """

    AAS_repository_service_specification_SSP_005_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "AssetAdministrationShellRepositoryServiceSpecification/SSP-005"
    )
    """
    Indicates that the server implemented all details of the Asset Administration
    Shell Repository Service Specification Identifiable Profile in version 3.2.
    """

    Submodel_repository_service_specification_SSP_001_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "SubmodelRepositoryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Full Profile in version 3.0.
    """

    Submodel_repository_service_specification_SSP_001_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "SubmodelRepositoryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Full Profile in version 3.1.
    """

    Submodel_repository_service_specification_SSP_001_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "SubmodelRepositoryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Full Profile in version 3.2.
    """

    Submodel_repository_service_specification_SSP_002_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "SubmodelRepositoryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Read Profile in version 3.0.
    """

    Submodel_repository_service_specification_SSP_002_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "SubmodelRepositoryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Read Profile in version 3.1.
    """

    Submodel_repository_service_specification_SSP_002_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "SubmodelRepositoryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Read Profile in version 3.2.
    """

    Submodel_repository_service_specification_SSP_003_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "SubmodelRepositoryServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Template Profile in version 3.0.
    """

    Submodel_repository_service_specification_SSP_003_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "SubmodelRepositoryServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Template Profile in version 3.1.
    """

    Submodel_repository_service_specification_SSP_003_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "SubmodelRepositoryServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Template Profile in version 3.2.
    """

    Submodel_repository_service_specification_SSP_004_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "SubmodelRepositoryServiceSpecification/SSP-004"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Template Read Profile in version 3.0.
    """

    Submodel_repository_service_specification_SSP_004_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "SubmodelRepositoryServiceSpecification/SSP-004"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Template Read Profile in version 3.1.
    """

    Submodel_repository_service_specification_SSP_004_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "SubmodelRepositoryServiceSpecification/SSP-004"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Template Read Profile in version 3.2.
    """

    Submodel_repository_service_specification_SSP_005_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "SubmodelRepositoryServiceSpecification/SSP-005"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Query Profile in version 3.1.
    """

    Submodel_repository_service_specification_SSP_005_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "SubmodelRepositoryServiceSpecification/SSP-005"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Query Profile in version 3.2.
    """

    Submodel_repository_service_specification_SSP_006_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "SubmodelRepositoryServiceSpecification/SSP-006"
    )
    """
    Indicates that the server implemented all details of the Submodel Service
    Repository Specification Signature Profile in version 3.2.
    """

    Concept_description_repository_service_specification_SSP_001_V3_0 = (
        "https://admin-shell.io/aas/API/3/0/"
        "ConceptDescriptionRepositoryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Concept Description
    Repository Service Specification Profile in version 3.0.
    """

    Concept_description_repository_service_specification_SSP_001_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "ConceptDescriptionRepositoryServiceSpecification/SSP-001"
    )
    """
    Indicates that the server implemented all details of the Concept Description
    Repository Service Specification Profile in version 3.1.
    """

    Concept_description_repository_service_specification_SSP_002_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "ConceptDescriptionRepositoryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Concept Description
    Repository Service Specification Query Profile in version 3.2.
    """

    Concept_description_repository_service_specification_SSP_002_V3_1 = (
        "https://admin-shell.io/aas/API/3/1/"
        "ConceptDescriptionRepositoryServiceSpecification/SSP-002"
    )
    """
    Indicates that the server implemented all details of the Concept Description
    Repository Service Specification Query Profile in version 3.1.
    """

    Concept_description_repository_service_specification_SSP_003_V3_2 = (
        "https://admin-shell.io/aas/API/3/2/"
        "ConceptDescriptionRepositoryServiceSpecification/SSP-003"
    )
    """
    Indicates that the server implemented all details of the Concept Description
    Repository Service Specification Signature Profile in version 3.2.
    """


@abstract
class Recent_change(DBC):
    """
    This class is not part of the metamodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#RecentChange
    """

    created_at: "Date_time_UTC"
    """The point in time at which the Identifiable object was created"""

    updated_at: "Date_time_UTC"
    """
    The point in time at which the Identifiable object was recently updated
    """

    def __init__(
        self, created_at: "Date_time_UTC", updated_at: "Date_time_UTC"
    ) -> None:
        self.created_at = created_at
        self.updated_at = updated_at


# fmt: off
@invariant(
    lambda self:
    not (self.specific_asset_IDs is not None)
    or len(self.specific_asset_IDs) >= 1,
    "Specific asset IDs must be either not set or have at least one item."
)
# fmt: on
class Asset_administration_shell_recent_change(Recent_change):
    """
    This class is not part of the metamodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#AssetAdministrationShellRecentChange
    """

    ID: "Identifier"
    """Globally unique identification of the Asset Administration Shell"""

    global_asset_ID: Optional["Identifier"]
    """Global reference to the asset the AAS is representing"""

    specific_asset_IDs: Optional[List["Specific_asset_ID"]]
    """Specific asset identifier"""

    def __init__(
        self,
        created_at: "Date_time_UTC",
        updated_at: "Date_time_UTC",
        ID: "Identifier",
        global_asset_ID: Optional["Identifier"] = None,
        specific_asset_IDs: Optional[List["Specific_asset_ID"]] = None,
    ) -> None:
        Recent_change.__init__(self, created_at=created_at, updated_at=updated_at)

        self.ID = ID
        self.global_asset_ID = global_asset_ID
        self.specific_asset_IDs = specific_asset_IDs


class Concept_description_recent_change(Recent_change):
    """
    This class is not part of the metamodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#ConceptDescriptionRecentChange
    """

    ID: "Identifier"
    """Globally unique identification of the Submodel"""

    def __init__(
        self,
        created_at: "Date_time_UTC",
        updated_at: "Date_time_UTC",
        ID: "Identifier",
    ) -> None:
        Recent_change.__init__(self, created_at=created_at, updated_at=updated_at)

        self.ID = ID


# fmt: off
@invariant(
    lambda self:
    not (self.supplemental_semantic_IDs is not None)
    or (self.semantic_ID is not None),
    "If there are supplemental semantic IDs defined then there shall be also "
    "a main semantic ID."
)
@invariant(
    lambda self:
    not (self.supplemental_semantic_IDs is not None)
    or len(self.supplemental_semantic_IDs) >= 1,
    "Supplemental semantic IDs must be either not set or have at least one item."
)
# fmt: on
class Submodel_recent_change(Recent_change):
    """
    This class is not part of the metamodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#SubmodelRecentChange
    """

    ID: "Identifier"
    """Globally unique identification of the Submodel"""

    semantic_ID: Optional["Reference"]
    """Identifier of the semantic definition of the Submodel"""

    supplemental_semantic_IDs: Optional[List["Reference"]]
    """
    Identifier of a supplemental semantic definition of the element called
    supplemental semantic ID of the element
    """

    def __init__(
        self,
        created_at: "Date_time_UTC",
        updated_at: "Date_time_UTC",
        ID: "Identifier",
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
    ) -> None:
        Recent_change.__init__(self, created_at=created_at, updated_at=updated_at)

        self.ID = ID
        self.semantic_ID = semantic_ID
        self.supplemental_semantic_IDs = supplemental_semantic_IDs


@invariant(
    lambda self: self >= 0,
    "The value must be a non-negative integer.",
)
class Non_negative_integer(int, DBC):
    """
    The ``nonNegativeInteger`` datatype as defined by XML Schema Part 2 in
    version 1.0.

    This class is not part of the metamodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#_simple_data_types
    """


# region Primitive Data Types
#
# See:
# https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#_primitive_data_types


# fmt: off
@invariant(
    lambda self: len(self) >= 1,
    "The value must not be empty."
)
@invariant(
    lambda self: len(self) <= 32,
    "Code type shall have a maximum length of 32 characters.",
)
# fmt: on
class Code_type(str, DBC):
    """
    string with max 32 and min 1 characters

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#CodeType
    """


class Short_ID_type(Name_type, DBC):
    """
    same as :class:`Name_type` (string with max 128 and min 1 characters)

    .. note::

        :class:`Short_ID_type` is *not* the data type of :class:`ID_short_type`
        attributes, but for IDs which shall be shorter than the identifier type.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#ShortIdType
    """


# fmt: off
@invariant(
    lambda self: len(self) >= 1,
    "The value must not be empty."
)
@invariant(
    lambda self: len(self) <= 2048,
    "Locator type shall have a maximum length of 2048 characters.",
)
# fmt: on
class Locator_type(str, DBC):
    """
    string with max 2048 and min 1 characters

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#LocatorType
    """


# fmt: off
@invariant(
    lambda self: len(self) >= 1,
    "The value must not be empty."
)
@invariant(
    lambda self: len(self) <= 2048,
    "Text type shall have a maximum length of 2048 characters.",
)
# fmt: on
class Text_type(str, DBC):
    """
    string with max 2048 and min 1 characters

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#TextType
    """


class Scheme_type(Name_type, DBC):
    """
    same as NameType (string with max 128 and min 1 characters)

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#SchemeType
    """


# endregion Primitive Data Types


class Status_code(Enum):
    """
    Generic status codes.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#StatusCode
    """

    Success = "Success"
    """Success"""

    Success_created = "SuccessCreated"
    """Successful creation of a new resource"""

    Success_accepted = "SuccessAccepted"
    """The reception of the request was successful"""

    Success_no_content = "SuccessNoContent"
    """Success with explicitly no content in the payload"""

    Client_error_bad_request = "ClientErrorBadRequest"
    """Bad or malformed request"""

    Client_not_authorized = "ClientNotAuthorized"
    """Wrong or missing authorization credentials"""

    Client_forbidden = "ClientForbidden"
    """Authorization has been refused"""

    Client_method_not_allowed = "ClientMethodNotAllowed"
    """Operation request is not allowed"""

    Client_error_resource_not_found = "ClientErrorResourceNotFound"
    """Resource not found"""

    Client_resource_conflict = "ClientResourceConflict"
    """Conflict-creating resource (resource already exists)"""

    Server_internal_error = "ServerInternalError"
    """Unexpected error"""

    Server_not_implemented = "ServerNotImplemented"
    """
    The server has not implemented this API Operation. Intended for cases
    where API Operations beyond the supported service profiles are requested.
    """

    Server_error_bad_gateway = "ServerErrorBadGateway"
    """Bad gateway"""


# fmt: off
@invariant(
    lambda self:
    not (self.message is not None)
    or len(self.message) >= 1,
    "Message must be either not set or have at least one item."
)
# fmt: on
class Result(DBC):
    """
    The result object.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#Result
    """

    message: Optional[List["Message"]]
    """Additional message containing information for the requester"""

    def __init__(self, message: Optional[List["Message"]] = None) -> None:
        self.message = message


class Message(DBC):
    """
    A message containing more information for the requester about a certain
    happening in the backend.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#Message
    """

    message_type: "Message_type_enum"
    """The message type"""

    text: str
    """The message text"""

    code: Optional["Code_type"]
    """Technology-dependent status or error code"""

    correlation_ID: Optional["Short_ID_type"]
    """Identifier to relate several result messages throughout several systems"""

    timestamp: Optional["Date_time"]
    """Timestamp of the message"""

    def __init__(
        self,
        message_type: "Message_type_enum",
        text: str,
        code: Optional["Code_type"] = None,
        correlation_ID: Optional["Short_ID_type"] = None,
        timestamp: Optional["Date_time"] = None,
    ) -> None:
        self.message_type = message_type
        self.text = text
        self.code = code
        self.correlation_ID = correlation_ID
        self.timestamp = timestamp


class Message_type_enum(Enum):
    """
    The message type.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#MessageTypeEnum
    """

    Info = "Info"
    """Used to inform the user about a certain fact"""

    Warning = "Warning"
    """Used for warnings; warnings may lead to errors in the subsequent execution"""

    Error = "Error"
    """Used for handling errors"""

    Exception = "Exception"
    """Used in case of an internal and/or unhandled exception"""


# fmt: off
@invariant(
    lambda self:
    not (self.input_arguments is not None)
    or len(self.input_arguments) >= 1,
    "Input arguments must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.inoutput_arguments is not None)
    or len(self.inoutput_arguments) >= 1,
    "InOutput arguments must be either not set or have at least one item."
)
# fmt: on
class Operation_request(DBC):
    """
    The operation request object.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#OperationRequest
    """

    input_arguments: Optional[List["Operation_variable"]]
    """Input argument"""

    inoutput_arguments: Optional[List["Operation_variable"]]
    """InOutput argument"""

    client_timeout_duration: Optional["Duration"]
    """
    Duration indicating when the client suggests the server to have finished
    execution of the invoked operation. The server may take this value into account to
    decide on its effective timeout, however, the server may or may not use by its own
    discretion.
    """

    def __init__(
        self,
        input_arguments: Optional[List["Operation_variable"]] = None,
        inoutput_arguments: Optional[List["Operation_variable"]] = None,
        client_timeout_duration: Optional["Duration"] = None,
    ) -> None:
        self.input_arguments = input_arguments
        self.inoutput_arguments = inoutput_arguments
        self.client_timeout_duration = client_timeout_duration


@invariant(
    lambda self: self.client_timeout_duration is not None,
    "Client timeout duration must be set for asynchronous operation invocation.",
)
class Operation_request_async(Operation_request):
    """
    The operation request object for asynchronous invocation.

    This class is not part of the metamodel and is not itself a named class
    in the specification. It corresponds to the request body of the
    ``InvokeOperationAsync`` operation, which is :class:`Operation_request`
    with :attr:`~Operation_request.client_timeout_duration` made mandatory.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces.html#_operation_invokeoperationasync
    """

    def __init__(
        self,
        input_arguments: Optional[List["Operation_variable"]] = None,
        inoutput_arguments: Optional[List["Operation_variable"]] = None,
        client_timeout_duration: Optional["Duration"] = None,
    ) -> None:
        Operation_request.__init__(
            self,
            input_arguments=input_arguments,
            inoutput_arguments=inoutput_arguments,
            client_timeout_duration=client_timeout_duration,
        )


# NOTE (mristin):
# OperationRequestValueOnly is not formalized here. Its inputArguments/
# inoutputArguments are typed ValueOnly, which is not a metamodel class, but
# a dynamic JSON serialization mode defined in Part 1's mappings. Its shape mirrors
# the corresponding submodel element's own (recursive) structure and has no fixed
# set of attributes, so it does not fit this meta-model's static, attribute-typed
# class representation.
#
# See:
# https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#operation-request-value-only


class Base_operation_result(Result):
    """
    The object containing the intermediate state of an operation.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#BaseOperationResult
    """

    execution_state: "Execution_state"
    """Execution state"""

    success: Optional[bool]
    """
    Flag indicating whether the business operation behind the operation was
    successful (true) or not (false)
    """

    def __init__(
        self,
        execution_state: "Execution_state",
        message: Optional[List["Message"]] = None,
        success: Optional[bool] = None,
    ) -> None:
        Result.__init__(self, message=message)

        self.execution_state = execution_state
        self.success = success


# fmt: off
@invariant(
    lambda self:
    not (self.output_arguments is not None)
    or len(self.output_arguments) >= 1,
    "Output arguments must be either not set or have at least one item."
)
@invariant(
    lambda self:
    not (self.inoutput_arguments is not None)
    or len(self.inoutput_arguments) >= 1,
    "InOutput arguments must be either not set or have at least one item."
)
# fmt: on
class Operation_result(Base_operation_result):
    """
    The operation's invocation result object.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#OperationResult
    """

    output_arguments: Optional[List["Operation_variable"]]
    """Output argument"""

    inoutput_arguments: Optional[List["Operation_variable"]]
    """InOutput argument"""

    def __init__(
        self,
        execution_state: "Execution_state",
        message: Optional[List["Message"]] = None,
        success: Optional[bool] = None,
        output_arguments: Optional[List["Operation_variable"]] = None,
        inoutput_arguments: Optional[List["Operation_variable"]] = None,
    ) -> None:
        Base_operation_result.__init__(
            self,
            execution_state=execution_state,
            message=message,
            success=success,
        )

        self.output_arguments = output_arguments
        self.inoutput_arguments = inoutput_arguments


# NOTE (mristin):
# OperationResultValueOnly is not formalized here. Its outputArguments/
# inoutputArguments are typed ValueOnly, which is not a metamodel class, but
# a dynamic JSON serialization mode defined in Part 1's mappings. Its shape mirrors
# the corresponding submodel element's own (recursive) structure and has no fixed
# set of attributes, so it does not fit this meta-model's static, attribute-typed
# class representation.
#
# See:
# https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#operation-result-value-only


class Execution_state(Enum):
    """
    The operation's invocation result state.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#ExecutionState
    """

    Initiated = "Initiated"
    """The operation is ready to be executed (initial state)"""

    Running = "Running"
    """The operation is running"""

    Completed = "Completed"
    """The operation is completed"""

    Canceled = "Canceled"
    """The operation was cancelled externally"""

    Failed = "Failed"
    """The operation failed"""

    Timeout = "Timeout"
    """The operation has timed out due to given client or server timeout"""


class Operation_handle(DBC):
    """
    The returned handle of an operation's asynchronous invocation used to
    request the current state of the operation's execution.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-payload.html#OperationHandle
    """

    handle_ID: "Short_ID_type"
    """Handle ID"""

    def __init__(self, handle_ID: "Short_ID_type") -> None:
        self.handle_ID = handle_ID


# endregion Data Types For Payload

# region Basic Operation Parameters
#
# See:
# https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier


class Level(Enum):
    """
    Indicates the depth of the structure of the response or input content.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    Deep = "Deep"
    """
    All elements of a requested hierarchy level and all children on all
    sublevels are returned.

    Children in this sense are SubmodelElements which are contained at the
    'submodelElements' field of Submodels, the 'value' field of
    SubmodelElementCollections or SubmodelElementLists, the 'statements'
    field of Entities, or the 'annotations' field of
    AnnotatedRelationshipElements.
    """

    Core = "Core"
    """
    Only elements of a requested hierarchy level as well as direct children
    are returned. By this, a client can iterate the hierarchy step by step.
    """


class Content(Enum):
    """
    Content indicates the kind of serialization of the response or input content.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    Normal = "Normal"
    """
    The standard serialization of the model element or child elements is
    applied.
    """

    Metadata = "Metadata"
    """Only metadata of an element or child elements is returned; the value is not."""

    Value = "Value"
    """
    Only the raw value of the model element or child elements is returned;
    it is commonly referred to as ValueOnly-serialization.
    """

    Reference = "Reference"
    """
    Only applicable to Referables. Only the reference to the found element
    is returned; potential child elements are ignored.
    """

    Path = "Path"
    """
    Returns the ID-short of the requested element and a list of ID-short
    paths to child elements if the requested element is a Submodel,
    a SubmodelElementCollection, a SubmodelElementList, an
    AnnotatedRelationshipElement, or an Entity.
    """


class Extent(Enum):
    """
    Indicates to which extent the response or input content is being
    serialized.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    Without_BLOB_value = "WithoutBLOBValue"
    """
    Only applicable to BLOB-elements; the BLOB content is not returned.

    This is the default value.
    """

    With_BLOB_value = "WithBLOBValue"
    """
    Only applicable to BLOB-elements; the BLOB content is returned as
    base64-encoded string.
    """


# endregion Basic Operation Parameters


# region HTTP/REST API


# fmt: off
@invariant(
    lambda self:
    not (self.result is not None)
    or len(self.result) >= 1,
    "Result must be either not set or have at least one item."
)
# fmt: on
class Paged_result(DBC):
    """
    An object connecting the actual list of returned items with metadata
    information to, *e.g.*, fetch the next part of the result set.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/http-rest-api/http-rest-api.html#pagination
    """

    result: Optional[List["Referable"]]
    """
    List of returned items. Any kind of Referables is possible, depending on
    the endpoint which has been requested.
    """

    paging_metadata: "Paging_metadata"
    """
    Additional information for the client to, *e.g.*, fetch the next part of
    the result set.
    """

    def __init__(
        self,
        paging_metadata: "Paging_metadata",
        result: Optional[List["Referable"]] = None,
    ) -> None:
        self.paging_metadata = paging_metadata
        self.result = result


class Paging_metadata(DBC):
    """
    Additional information for the client to, *e.g.*, fetch the next part of
    the result set.

    .. note::

        More attributes may be added to this class in future versions.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/http-rest-api/http-rest-api.html#pagination
    """

    cursor: Optional[str]
    """
    The cursor for the next part of the result set. No cursor attribute means that
    the end of the result set has been reached.
    """

    def __init__(self, cursor: Optional[str] = None) -> None:
        self.cursor = cursor


# fmt: off
@invariant(
    lambda self:
    not (self.aas_IDs is not None)
    or len(self.aas_IDs) >= 1,
    "AAS IDs must be either not set or have at least one item."
)
# fmt: on
class Package_description(DBC):
    """
    The package description consists of a system-wide unique packageId and
    its corresponding Asset Administration Shell identifiers.

    The packageId is used to identify the AASX package at the AASX file
    server. The package description is used to list the Asset
    Administration Shells in a given AASX package.

    This class is not part of the metamodel.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/http-rest-api/http-rest-api.html#PackageDescription
    """

    package_ID: "Short_ID_type"
    """File server specific package id"""

    aas_IDs: Optional[List["Identifier"]]
    """Asset Administration Shell unique identifiers"""

    def __init__(
        self,
        package_ID: "Short_ID_type",
        aas_IDs: Optional[List["Identifier"]] = None,
    ) -> None:
        self.package_ID = package_ID
        self.aas_IDs = aas_IDs


@verification
def matches_path_item(text: str) -> bool:
    """
    Check that :paramref:`text` is a valid idShortPath.

    An idShortPath is a chain of idShorts or SubmodelElementList-indexes
    which points to an element within a hierarchy of elements, *e.g.*,
    ``sme1.sme2[0].p1``.
    """
    pattern = (
        r"^(([A-Za-z][A-Za-z0-9_]+)|(\[[0-9]+\]))"
        r"((\.[A-Za-z][A-Za-z0-9_]+)|(\[[0-9]+\])){0,}$"
    )

    return match(pattern, text) is not None


@invariant(
    lambda self: matches_path_item(self),
    "The value must match the pattern of a path item.",
)
class Path_item(str, DBC):
    """
    A chain of idShorts or SubmodelElementList-indexes, which points to an
    element within a hierarchy of elements, *e.g.*, ``sme1.sme2[0].p1``.

    The root of the path is always a submodel, and the first element is
    always the idShort of a first-level submodel element within it. idShorts
    are separated by a dot, while SubmodelElementList indices are written in
    brackets.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/http-rest-api/http-rest-api.html#_addressing_resources
    """


# endregion HTTP/REST API


# region Metadata And Value Views


# NOTE (mristin):
# This region formalizes the Content=Metadata and Content=Value serialization
# views referenced by SerializationModifier's Content enumeration (see class
# Content above), specified for the individual submodel element (and submodel /
# asset administration shell) types in Part 1's mappings document. These views
# are not part of the metamodel itself; they are payload shapes defined for the
# HTTP/REST API, mirrored here from the Part 2 OpenAPI schema
# (Part2-API-Schemas/openapi.yaml) rather than from book prose, since the book
# only describes the Content enumeration in general terms and does not spell
# out each view's attributes.
#
# The *_metadata classes carry every attribute of the corresponding submodel
# element *except* its value, mirroring the OpenAPI schema's
# SubmodelElementAttributes/SubmodelElementMetadata/*Metadata composition.
#
# The *_value classes carry only the value. Several Value variants from the
# OpenAPI schema are intentionally not formalized because their content is
# inherently dynamic (ValueOnly-shaped JSON with no fixed attributes, the same
# issue that already ruled out OperationRequestValueOnly/
# OperationResultValueOnly elsewhere in this file) or structurally mismatched
# with a static, attribute-typed class (a bare scalar or a bare array, not an
# object): PropertyValue, MultiLanguagePropertyValue,
# SubmodelElementCollectionValue, SubmodelElementListValue,
# ReferenceElementValue, SubmodelValue. Each omission is noted where it would
# otherwise be expected.
#
# See:
# https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier


@abstract
class Submodel_element_attributes(
    Referable, Has_semantics, Qualifiable, Has_data_specification
):
    """
    The attributes shared by all submodel elements, without their value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    # NOTE (mristin):
    # The OpenAPI schema also lists ``HasKind`` among the mixed-in classes. We
    # omit it here: in Part 1, Has_kind is only used by Submodel, never by an
    # individual submodel element, so including it here would introduce an
    # attribute (``kind``) that no submodel element actually carries. We treat
    # this as a mistake in the OpenAPI schema rather than a deliberate Part 2
    # addition.

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Referable.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
        )

        Has_semantics.__init__(
            self,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
        )

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(
            self, embedded_data_specifications=embedded_data_specifications
        )


@abstract
class Submodel_element_metadata(Submodel_element_attributes):
    """
    The metadata of a submodel element, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification. It is the polymorphic union of all the
    ``*Metadata`` classes below.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_attributes.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


class Property_metadata(Submodel_element_metadata):
    """
    The metadata of a :class:`Property`, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    value_type: "Data_type_def_XSD"
    """The value type of the property."""

    def __init__(
        self,
        value_type: "Data_type_def_XSD",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.value_type = value_type


class Range_metadata(Submodel_element_metadata):
    """
    The metadata of a :class:`Range`, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    value_type: "Data_type_def_XSD"
    """The value type of the range."""

    def __init__(
        self,
        value_type: "Data_type_def_XSD",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.value_type = value_type


class Blob_metadata(Submodel_element_metadata):
    """
    The metadata of a :class:`Blob`, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


class File_metadata(Submodel_element_metadata):
    """
    The metadata of a :class:`File`, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


class Multi_language_property_metadata(Submodel_element_metadata):
    """
    The metadata of a :class:`Multi_language_property`, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


class Reference_element_metadata(Submodel_element_metadata):
    """
    The metadata of a :class:`Reference_element`, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


class Relationship_element_metadata(Submodel_element_metadata):
    """
    The metadata of a :class:`Relationship_element`, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


class Annotated_relationship_element_metadata(Submodel_element_metadata):
    """
    The metadata of an :class:`Annotated_relationship_element`, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


class Entity_metadata(Submodel_element_metadata):
    """
    The metadata of an :class:`Entity`, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


class Capability_metadata(Submodel_element_metadata):
    """
    The metadata of a :class:`Capability`.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


class Operation_metadata(Submodel_element_metadata):
    """
    The metadata of an :class:`Operation`, without its input/output/inoutput variables.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


class Submodel_element_collection_metadata(Submodel_element_metadata):
    """
    The metadata of a :class:`Submodel_element_collection`, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )


class Basic_event_element_metadata(Submodel_element_metadata):
    """
    The metadata of a :class:`Basic_event_element`.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    direction: "Direction"
    """Direction of event."""

    state: "State_of_event"
    """State of event."""

    message_topic: Optional["Message_topic_type"]
    """Topic, to which the event's message is published."""

    message_broker: Optional["Reference"]
    """Reference to a broker where the event's message is published."""

    last_update: Optional["Date_time_UTC"]
    """Timestamp of the last update of the event."""

    min_interval: Optional["Duration"]
    """For continuous signalling, the minimum interval between two consecutive events."""

    max_interval: Optional["Duration"]
    """For continuous signalling, the maximum interval between two consecutive events."""

    def __init__(
        self,
        direction: "Direction",
        state: "State_of_event",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        message_topic: Optional["Message_topic_type"] = None,
        message_broker: Optional["Reference"] = None,
        last_update: Optional["Date_time_UTC"] = None,
        min_interval: Optional["Duration"] = None,
        max_interval: Optional["Duration"] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.direction = direction
        self.state = state
        self.message_topic = message_topic
        self.message_broker = message_broker
        self.last_update = last_update
        self.min_interval = min_interval
        self.max_interval = max_interval


class Submodel_element_list_metadata(Submodel_element_metadata):
    """
    The metadata of a :class:`Submodel_element_list`, without its value.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    order_relevant: Optional[bool]
    """Defines whether order in the list is relevant."""

    semantic_ID_list_element: Optional["Reference"]
    """Semantic ID the submodel elements contained in the list match to."""

    type_value_list_element: "AAS_submodel_elements"
    """The submodel element type of the submodel elements contained in the list."""

    value_type_list_element: Optional["Data_type_def_XSD"]
    """The value type of the submodel elements contained in the list."""

    def __init__(
        self,
        type_value_list_element: "AAS_submodel_elements",
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        order_relevant: Optional[bool] = None,
        semantic_ID_list_element: Optional["Reference"] = None,
        value_type_list_element: Optional["Data_type_def_XSD"] = None,
    ) -> None:
        Submodel_element_metadata.__init__(
            self,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
            qualifiers=qualifiers,
            embedded_data_specifications=embedded_data_specifications,
        )

        self.order_relevant = order_relevant
        self.semantic_ID_list_element = semantic_ID_list_element
        self.type_value_list_element = type_value_list_element
        self.value_type_list_element = value_type_list_element


class Submodel_metadata(
    Identifiable, Has_kind, Has_semantics, Qualifiable, Has_data_specification
):
    """
    The metadata of a :class:`Submodel`, without its submodel elements.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    def __init__(
        self,
        ID: Identifier,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        administration: Optional["Administrative_information"] = None,
        kind: Optional["Modelling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        supplemental_semantic_IDs: Optional[List["Reference"]] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            ID=ID,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            administration=administration,
        )

        Has_kind.__init__(self, kind=kind)

        Has_semantics.__init__(
            self,
            semantic_ID=semantic_ID,
            supplemental_semantic_IDs=supplemental_semantic_IDs,
        )

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(
            self, embedded_data_specifications=embedded_data_specifications
        )


class Asset_administration_shell_metadata(Identifiable, Has_data_specification):
    """
    The metadata of an :class:`Asset_administration_shell`, without its
    asset information and submodel references.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    derived_from: Optional["Reference"]
    """
    The reference to the Asset Administration Shell, which the Asset
    Administration Shell was derived from.
    """

    def __init__(
        self,
        ID: Identifier,
        extensions: Optional[List["Extension"]] = None,
        category: Optional[Name_type] = None,
        ID_short: Optional[ID_short_type] = None,
        display_name: Optional[List["Lang_string_name_type"]] = None,
        description: Optional[List["Lang_string_text_type"]] = None,
        administration: Optional["Administrative_information"] = None,
        embedded_data_specifications: Optional[
            List["Embedded_data_specification"]
        ] = None,
        derived_from: Optional["Reference"] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            ID=ID,
            extensions=extensions,
            category=category,
            ID_short=ID_short,
            display_name=display_name,
            description=description,
            administration=administration,
        )

        Has_data_specification.__init__(
            self, embedded_data_specifications=embedded_data_specifications
        )

        self.derived_from = derived_from


# NOTE (mristin):
# The *_value classes below are deliberately *not* related by inheritance,
# and none of them is used as a base class. Each stands alone as a plain
# DBC.
#
# Consequently, each is marked with @serialization(with_model_type=False):
# since none of them is part of a polymorphic hierarchy here, no "modelType"
# discriminator should be emitted for them on serialization.
#
# Several variants from the HTTP schema have no class here at all, since
# they do not fit this meta-model's static, attribute-typed class
# representation:
#
# * ``PropertyValue`` is a raw JSON string, number or boolean, not an
#   object -- use a plain scalar directly where needed.
# * ``MultiLanguagePropertyValue`` and ``SubmodelElementCollectionValue``
#   are dynamic, ValueOnly-shaped JSON (see the ValueOnly note earlier in
#   this region).
# * ``SubmodelElementListValue`` is a bare JSON array of values, not an
#   object.
# * ``SubmodelValue`` is, like ``SubmodelElementCollectionValue``,
#   ValueOnly-shaped JSON.
# * ``AnnotatedRelationshipElementValue`` has ``annotations`` attribute,
#   which is itself ValueOnly-shaped JSON, so we cannot represent it.
# * ``EntityValue`` has ``specificAssetIds`` as an array of dynamic
#   ``SpecificAssetIdValue`` shape, and ``statements`` as ValueOnly-shaped JSON.


@serialization(with_model_type=False)
class Reference_element_value(DBC):
    """
    The value of a :class:`Reference_element`.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    type: "Reference_types"
    """
    Type of the reference.

    Denotes whether the reference is an external reference or a model
    reference.
    """

    keys: List["Key"]
    """Unique references in their name space."""

    referred_semantic_ID: Optional["Reference"]
    """
    Expected :attr:`Has_semantics.semantic_ID` of the referenced model
    element.
    """

    def __init__(
        self,
        type: "Reference_types",
        keys: List["Key"],
        referred_semantic_ID: Optional["Reference"] = None,
    ) -> None:
        self.type = type
        self.keys = keys
        self.referred_semantic_ID = referred_semantic_ID


@serialization(with_model_type=False)
class Blob_value(DBC):
    """
    The value of a :class:`Blob`.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    content_type: Optional["Content_type"]
    """The content type of the BLOB, *e.g.*, ``application/pdf``."""

    value: Optional["Blob_type"]
    """The BLOB content."""

    def __init__(
        self,
        content_type: Optional["Content_type"] = None,
        value: Optional["Blob_type"] = None,
    ) -> None:
        self.content_type = content_type
        self.value = value


@serialization(with_model_type=False)
class File_value(DBC):
    """
    The value of a :class:`File`.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    content_type: Optional["Content_type"]
    """The content type of the file, *e.g.*, ``application/pdf``."""

    value: Optional["Path_type"]
    """The path or URL to the file content."""

    def __init__(
        self,
        content_type: Optional["Content_type"] = None,
        value: Optional["Path_type"] = None,
    ) -> None:
        self.content_type = content_type
        self.value = value


@serialization(with_model_type=False)
class Range_value(DBC):
    """
    The value of a :class:`Range`.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    min: float
    """The minimum value of the range."""

    max: float
    """The maximum value of the range."""

    def __init__(self, min: float, max: float) -> None:
        self.min = min
        self.max = max


@serialization(with_model_type=False)
class Relationship_element_value(DBC):
    """
    The value of a :class:`Relationship_element`.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    first: Optional["Reference"]
    """Reference to the first element in the relationship."""

    second: Optional["Reference"]
    """Reference to the second element in the relationship."""

    def __init__(
        self,
        first: Optional["Reference"] = None,
        second: Optional["Reference"] = None,
    ) -> None:
        self.first = first
        self.second = second


@serialization(with_model_type=False)
class Basic_event_element_value(DBC):
    """
    The value of a :class:`Basic_event_element`.

    This class is not part of the metamodel and is not itself a named class
    in the specification.

    See:
    https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.2/specification/interfaces-operation-parameters.html#SerializationModifier
    """

    observed: "Reference"
    """Reference to the :class:`Referable`, which defines the scope of the event."""

    def __init__(self, observed: "Reference") -> None:
        self.observed = observed


# endregion Metadata And Value Views


# endregion Part 2
