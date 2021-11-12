"""Provide the meta model for Asset Administration Shell V3 Release Candidate 1."""

from enum import Enum
from typing import List, Optional

from icontract import invariant, ensure, DBC

from aas_core3_meta.marker import (
    abstract,
    implementation_specific,
    reference_in_the_book
)
from aas_core3_meta.verification import (
    is_IRI, is_IRDI, is_ID_short, are_unique, is_of_type
)

__book_url__ = "https://www.plattform-i40.de/IP/Redaktion/DE/Downloads/Publikation/Details_of_the_Asset_Administration_Shell_Part1_V3.pdf?__blob=publicationFile&v=5"
__book_version__ = "V3.0RC1"


# TODO (mristin, 2021-10-27): check the order of properties in the constructor
#  🠒 first the concrete, then the more abstract/inherited

@abstract
@reference_in_the_book(section=(4, 7, 2, 1))
class Has_extensions(DBC):
    """
    Element that can be extended by proprietary extensions.
    """
    # NOTE (mristin, 2021-05-28):
    # We do not implement extensions at the moment.
    # This needs to be further discussed.
    pass


@abstract
@invariant(lambda self: is_ID_short(self.ID_short), "Constraint AASd-002")
@reference_in_the_book(section=(4, 7, 2, 2))
class Referable(Has_extensions):
    """
    An element that is referable by its :attr:`~ID_short`.

    This identifier is not globally unique.
    This identifier is unique within the name space of the element.
    """

    ID_short: str
    """
    In case of identifiables this attribute is a short name of the element.
    In case of referable this ID is an identifying string of
    the element within its name space.
    
    .. note::
    
        In case the element is a property and the property has a semantic definition 
        (:class:`.Has_semantics`) conformant to IEC61360 the idShort is typically 
        identical to the short name in English.
    """

    display_name: Optional['Lang_string_set']
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
    * the short name of the concept description-the idShort of the element
    """

    category: Optional[str]
    """
    The category is a value that gives further meta information
    w.r.t. to the class of the element.
    It affects the expected existence of attributes and the applicability of
    constraints.
    
    .. note::
    
        The category is not identical to the semantic definition 
        (:class:`.Has_semantics`) of an element. The category 
        *e.g.* could denote that the element is a measurement value whereas the 
        semantic definition of the element would 
        denote that it is the measured temperature.
    """

    description: Optional['Lang_string_set']
    """
    Description or comments on the element.

    The description can be provided in several languages. If no description is defined,
    then the definition of the concept description that defines the semantics
    of the element is used. Additional information can be provided,
    *e.g.*, if the element is qualified and which qualifier types can be expected
    in which context or which additional data specification templates are provided.
    """

    def __init__(
            self,
            ID_short: str,
            display_name: Optional['Lang_string_set'] = None,
            category: Optional[str] = None,
            description: Optional['Lang_string_set'] = None
    ) -> None:
        self.ID_short = ID_short
        self.display_name = display_name
        self.category = category
        self.description = description


@abstract
@reference_in_the_book(section=(4, 7, 2, 3))
class Identifiable(Referable):
    """An element that has a globally unique identifier."""

    administration: Optional['Administrative_information']
    """
    Administrative information of an identifiable element.

    .. note::

        Some of the administrative information like the version number might need to
        be part of the identification.
    """

    identification: 'Identifier'
    """The globally unique identification of the element."""

    def __init__(
            self,
            identification: 'Identifier',
            ID_short: str,
            display_name: Optional['Lang_string_set'] = None,
            category: Optional[str] = None,
            description: Optional['Lang_string_set'] = None,
            administration: Optional['Administrative_information'] = None
    ) -> None:
        Referable.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description)

        self.identification = identification
        self.administration = administration


# fmt: off
@invariant(
    lambda self:
    not (self.ID_type == Identifier_type.IRDI) or is_IRDI(self.ID)
)
@invariant(
    lambda self:
    not (self.ID_type == Identifier_type.IRI) or is_IRI(self.ID)
)
@reference_in_the_book(section=(4, 7, 2, 4), index=0)
# fmt: on
class Identifier(DBC):
    """
    Used to uniquely identify an entity by using an identifier.
    """

    ID_type: 'Identifier_type'
    """
    Type  of  the  Identifier, e.g. IRI, IRDI *etc.* The supported Identifier types are
    defined in the enumeration :class:`.Identifier_type`.
    """

    ID: 'ID'
    """
    Globally unique identifier of the element.

    Its type is defined in :attr:`~ID_type`.
    """

    def __init__(
            self,
            ID: 'ID',
            ID_type: 'Identifier_type',

    ) -> None:
        self.ID = ID
        self.ID_type = ID_type


@reference_in_the_book(section=(4, 7, 2, 4), index=1)
class Identifier_type(Enum):
    """Enumeration of different types of Identifiersfor global identification"""

    IRDI = "IRDI"
    """
    IRDI according to ISO29002-5 as an Identifier scheme for properties
    and classifications.
    """

    IRI = "IRI"
    """IRI according to Rfc 3987. Every URIis an IRI"""

    Custom = "Custom"
    """Custom identifiers like GUIDs (globally unique identifiers)"""


@reference_in_the_book(section=(4, 7, 2, 5), index=1)
class Modeling_kind(Enum):
    """ Enumeration for denoting whether an element is a template or an instance. """

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

        It  becomes  an  individual  entity  of  a  template,  for  example  a
        device model, by defining specific property  values.

    .. note::

        In  an  object  oriented  view,  an  instance  denotes  an  object  of  a
        template (class).

    [SOURCE: IEC 62890:2016, 3.1.16 65/617/CDV]  modified
    """


@abstract
@reference_in_the_book(section=(4, 7, 2, 5), index=0)
class Has_kind(DBC):
    """
    An element with a kind is an element that can either represent a template or an
    instance.

    Default for an element is that it is representing an instance.
    """

    kind: Optional['Modeling_kind']
    """
    Kind of the element: either type or instance.
    
    Default Value = Instance
    """

    # TODO (all, 2021-05-28): how can ``kind`` be optional
    #  and have a default value?
    #  (See page 54 in the book V3RC1, kind has the cardinality ``0..1``.)
    def __init__(
            self,
            kind: Optional['Modeling_kind'] = None
    ) -> None:
        self.kind = kind if kind is not None else Modeling_kind.Instance


# fmt: off
@invariant(
    lambda self:
    not (self.revision is not None) or self.version is not None,
    "Constraint AASd-005"
)
@reference_in_the_book(section=(4, 7, 2, 6))
# fmt: on
class Administrative_information(DBC):
    """
    Administrative meta-information for an element like version information.
    """

    version: Optional[str]
    """Version of the element."""

    revision: Optional[str]
    """Revision of the element."""

    def __init__(
            self,
            version: Optional[str] = None,
            revision: Optional[str] = None
    ) -> None:
        self.version = version
        self.revision = revision


@abstract
@reference_in_the_book(section=(4, 7, 2, 7))
class Has_semantics(DBC):
    """
    Element that can have a semantic definition.
    """

    semantic_id: Optional['Reference']
    """
    Identifier of the semantic definition of the element. It is called semantic ID
    of the element.
    """

    def __init__(
            self,
            semantic_id: Optional['Reference'] = None
    ) -> None:
        self.semantic_id = semantic_id


# fmt: off
@invariant(
    lambda self:
    are_unique(
        constraint.qualifier_type
        for constraint in self.qualifiers
        if isinstance(constraint, Qualifier)
    ),
    "Constraint AASd-021"
)
@abstract
@reference_in_the_book(section=(4, 7, 2, 8))
# fmt: on
class Qualifiable(DBC):
    """
    The value of a qualifiable element may be further qualified by one or more
    qualifiers or complex formulas.
    """

    qualifiers: Optional[List['Constraint']]
    """Additional qualification of a qualifiable element."""

    def __init__(
            self,
            qualifiers: Optional[List['Constraint']] = None
    ) -> None:
        self.qualifiers = qualifiers


@abstract
@reference_in_the_book(section=(4, 7, 2, 9))
class Constraint(DBC):
    """A constraint is used to further qualify or restrict an element."""


# fmt: off
@invariant(
    lambda self:
    not (self.value is not None) or is_of_type(self.value, self.value_type),
    "Constraint AASd-020"
)
@reference_in_the_book(section=(4, 7, 2, 11))
# fmt: on
class Qualifier(Constraint, Has_semantics):
    """
    A qualifier is a  type-value-pair that makes additional statements w.r.t.  the value
    of the element.
    """

    type: 'Qualifier_type'
    """
    The qualifier type describes the type of the qualifier that is applied to
    the element.
    """

    value_type: 'Data_type_def'
    """
    Data type of the qualifier value.
    """

    value: Optional['Value_data_type']
    """
    The qualifier value is the value of the qualifier.
    """

    value_id: Optional['Reference']
    """
    Reference to the global unique ID of a coded value.
    """

    def __init__(
            self,
            type: 'Qualifier_type',
            value_type: 'Data_type_def',
            value: Optional['Value_data_type'] = None,
            value_id: Optional['Reference'] = None,
            semantic_id: Optional['Reference'] = None
    ) -> None:
        Has_semantics.__init__(self, semantic_id=semantic_id)

        self.type = type
        self.value_type = value_type
        self.value = value
        self.value_id = value_id


@reference_in_the_book(section=(4, 7, 2, 12))
class Formula(Constraint):
    """
    A formula is used to describe constraints by a logical expression.
    """

    depends_on: Optional[List['Reference']]
    """
    A formula may depend on referable or even external global elements that are used in
    the logical expression.

    The value of the referenced elements needs to be accessible so that it can be
    evaluated in the formula to true or false in the corresponding logical expression
    it is used in.
    """

    def __init__(
            self,
            depends_on: Optional[List['Reference']]
    ) -> None:
        self.depends_on = depends_on


@abstract
@reference_in_the_book(section=(4, 7, 2, 13))
class Has_data_specification(DBC):
    """
    Element that can be extended by using data specification templates.

    A data specification template defines a  named set of additional attributes an
    element may or shall have. The data specifications used are explicitly specified
    with their global ID.
    """

    data_specifications: Optional[List['Reference']]
    """
    Global reference to the data specification template used by the element.
    """

    # TODO (all, 2021-09-24): need to implement the constraint:
    #  page 60 in V3RC1
    #  Constraint AASd-050:  If the DataSpecificationContent
    #  DataSpecificationIEC61360 is used for an element then the value of
    #  hasDataSpecification/dataSpecification shall contain the global reference to the
    #  IRI of the corresponding data specification template https://admin-
    #  shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0.

    def __init__(
            self,
            data_specifications: Optional[List['Reference']] = None
    ) -> None:
        self.data_specifications = (
            data_specifications if data_specifications is not None else []
        )


@reference_in_the_book(section=(4, 7, 3))
class Asset_administration_shell(Identifiable, Has_data_specification):
    """Structure a digital representation of an :class:`.Asset`."""
    derived_from: Optional['Asset_administration_shell']
    """The reference to the AAS the AAS was derived from."""

    security: Optional['Security']
    """Definition of the security relevant aspects of the AAS."""

    asset_information: 'Asset_information'
    """Meta-information about the asset the AAS is representing."""

    submodels: Optional[List['Submodel']]
    """
    References to submodels of the AAS.

    A submodel is a  description of an aspect of the asset the AAS is representing.
    The asset of an AAS is typically described by one or more submodels. Temporarily
    no submodel might be assigned to the AAS.
    """

    views: Optional[List['View']]
    """
    Stakeholder-specific views defined for the AAS.

    If needed, stakeholder specific views can be defined on the elements of the AAS.
    """

    def __init__(
            self,
            identification: 'Identifier',
            ID_short: str,
            asset_information: 'Asset_information',
            display_name: Optional['Lang_string_set'] = None,
            category: Optional[str] = None,
            description: Optional['Lang_string_set'] = None,
            administration: Optional['Administrative_information'] = None,
            data_specifications: Optional[List['Reference']] = None,
            derived_from: Optional['Asset_administration_shell'] = None,
            security: Optional['Security'] = None,
            submodels: Optional[List['Submodel']] = None,
            views: Optional[List['View']] = None
    ) -> None:
        Identifiable.__init__(
            self,
            identification=identification,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            administration=administration
        )

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.derived_from = derived_from
        self.asset_information = asset_information
        self.security = security
        self.submodels = [] if submodels is None else submodels
        self.views = [] if views is None else views


@reference_in_the_book(section=(4, 7, 4))
class Asset(DBC, Identifiable, Has_data_specification):
    """
    An Asset describes meta data of an asset that is represented by an AAS and is
    identical for all AAS representing this asset.

    The asset has a globally unique identifier.
    """

    def __init__(
            self,
            identification: 'Identifier',
            ID_short: str,
            display_name: Optional['Lang_string_set'] = None,
            category: Optional[str] = None,
            description: Optional['Lang_string_set'] = None,
            administration: Optional['Administrative_information'] = None,
            data_specifications: Optional[List['Reference']] = None
    ):
        Identifiable.__init__(
            self,
            identification=identification,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            administration=administration)

        Has_data_specification.__init__(
            self,
            data_specifications=data_specifications)


@reference_in_the_book(section=(4, 7, 5), index=0)
class Asset_information:
    """
    Identifying meta data of the asset that is represented by an AAS.

    The asset may either represent an asset type or an asset instance. The asset has
    a globally unique identifier plus – if needed – additional domain-specific
    (proprietary) identifiers. However, to support the corner case of very first
    phase of lifecycle where a stabilised/constant global asset identifier does not
    already exist, the corresponding attribute :attr:`~global_asset_ID` is optional.
    """

    asset_kind: 'Asset_kind'
    """
    Denotes whether the Asset is of kind "Type" or "Instance".
    """

    global_asset_ID: Optional['Reference']
    """
    Reference to either an Asset object or a global reference to the asset the AAS is
    representing.

    This attribute is required as soon as the AAS is exchanged via partners in the life
    cycle of the asset. In a first phase of the life cycle the asset might not yet have
    a  global ID but already an internal identifier. The internal identifier would be
    modelled via :attr:`~specific_asset_ID`.
    """

    specific_asset_ID: Optional['Identifier_key_value_pair']
    """
    Additional domain-specific, typically proprietary, Identifier for the asset.

    For example, serial number.
    """

    bill_of_material: Optional[List['Submodel']]
    """
    A reference to a Submodel that defines the bill of material of the asset represented
    by the AAS.

    The submodels contain a set of entities describing the material used to compose
    the composite I4.0 Component.
    """

    default_thumbnail: Optional['File']
    """
    Thumbnail of the asset represented by the asset administration shell.

    Used as default.
    """

    def __init__(
            self,
            asset_kind: 'Asset_kind',
            global_asset_ID: Optional['Reference'] = None,
            specific_asset_ID: Optional['Identifier_key_value_pair'] = None,
            bill_of_material: Optional[List['Submodel']] = None,
            default_thumbnail: Optional['File'] = None
    ) -> None:
        # TODO (Nico & Marko, 2021-09-24):
        #  We did not know how to implement Constraint AASd-023,
        #  see page 63 in the book V3RC1
        self.asset_kind = asset_kind
        self.global_asset_ID = global_asset_ID
        self.specific_asset_ID = specific_asset_ID
        self.bill_of_material = [] if bill_of_material is None else bill_of_material
        self.default_thumbnail = default_thumbnail


@reference_in_the_book(section=(4, 7, 5), index=1)
class Asset_kind(Enum):
    """
    Enumeration for denoting whether an element is a type or an instance.
    """

    Type = 'Type'
    """
    hardware or software element which specifies the common attributes shared by all
    instances of the type

    [SOURCE: IEC TR 62390:2005-01, 3.1.25]
    """

    Instance = 'Instance'
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


@reference_in_the_book(section=(4, 7, 5), index=2)
class Identifier_key_value_pair(DBC, Has_semantics):
    """
    An IdentifierKeyValuePair describes a generic identifier as key-value pair.
    """

    key: str
    """Key of the identifier"""

    value: Optional[str]
    """The value of the identifier with the corresponding key."""

    external_subject_ID: Optional['Reference']
    """The (external) subject the key belongs to or has meaning to."""

    def __init__(
            self,
            key: str,
            value: Optional[str] = None,
            external_subject_ID: Optional['Reference'] = None,
            semantic_id: Optional['Reference'] = None
    ) -> None:
        Has_semantics.__init__(self, semantic_id)

        self.key = key
        self.value = value
        self.external_subject_ID = external_subject_ID


@reference_in_the_book(section=(4, 7, 6))
class Submodel(DBC, Identifiable, Has_kind, Has_semantics, Qualifiable,
               Has_data_specification):
    """
    A submodel defines a specific aspect of the asset represented by the AAS.

    A submodel is used to structure the digital representation and technical
    functionality of an Administration Shell into distinguishable parts. Each submodel
    refers to a  well-defined domain or subject matter. Submodels can become
    standardized and, thus, become submodels templates.
    """

    submodel_elements: List['Submodel_element']
    """A submodel consists of zero or more submodel elements."""

    def __init__(
            self,
            identification: 'Identifier',
            ID_short: str,
            submodel_elements: List['Submodel_element'],
            display_name: Optional['Lang_string_set'] = None,
            category: Optional[str] = None,
            description: Optional['Lang_string_set'] = None,
            administration: Optional['Administrative_information'] = None,
            kind: Optional['Modeling_kind'] = None,
            semantic_id: Optional['Reference'] = None,
            qualifiers: Optional[List['Constraint']] = None,
            data_specifications: Optional[List['Reference']] = None
    ):
        # TODO (Nico & Marko, 2021-09-24):
        #  How should we implement Constraint AASd-062 (page 64 in V3RC1)?
        #  Isn't this a constraint on the SubmodelElement?
        #  A submodel does not contain any attribute called ``Property``.

        Identifiable.__init__(
            self,
            identification=identification,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            administration=administration)

        Has_kind.__init__(
            self,
            kind=kind)

        Has_semantics.__init__(self, semantic_id=semantic_id)

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.submodel_elements = submodel_elements


@abstract
@reference_in_the_book(section=(4, 7, 7))
class Submodel_element(DBC, Referable, Has_kind, Has_semantics, Qualifiable,
                       Has_data_specification):
    """
    A submodel element is an element suitable for the description and differentiation of
    assets.

    It is recommended to add a semantic ID to a submodel element.
    """

    def __init__(
            self,
            ID_short: str,
            display_name: Optional['Lang_string_set'] = None,
            category: Optional[str] = None,
            description: Optional['Lang_string_set'] = None,
            kind: Optional['Modeling_kind'] = None,
            semantic_id: Optional['Reference'] = None,
            qualifiers: Optional[List['Constraint']] = None,
            data_specifications: Optional[List['Reference']] = None,
    ) -> None:
        Referable.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description)

        Has_kind.__init__(self, kind=kind)

        Has_semantics.__init__(self, semantic_id=semantic_id)

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(self, data_specifications=data_specifications)


# TODO (mristin, 2021-10-27, page 77):
#  Constraint AASd-055: If the semanticId of a RelationshipElement or an
#  AnnotatedRelationshipElement  submodel  element  references  a  ConceptDescription  then  the
#  ConceptDescription/category shall be one of  following values: RELATIONSHIP.
#
#  🠒 We really need to think hard how we resolve the references. Should this class be
#  implementation-specific?
@abstract
@reference_in_the_book(section=(4, 7, 8, 14))
class Relationship_element(Submodel_element):
    """
    A relationship element is used to define a relationship between two referable elements.
    """
    first: Referable
    """
    Reference to the first element in the relationship taking the role of the subject.
    """

    second: Referable
    """
    Reference to the second element in the relationship taking the role of the object.
    """

    def __init__(
            self,
            first: Referable,
            second: Referable,
            ID_short: str,
            display_name: Optional['Lang_string_set'] = None,
            category: Optional[str] = None,
            description: Optional['Lang_string_set'] = None,
            kind: Optional['Modeling_kind'] = None,
            semantic_id: Optional['Reference'] = None,
            qualifiers: Optional[List['Constraint']] = None,
            data_specifications: Optional[List['Reference']] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            kind=kind,
            semantic_id=semantic_id,
            qualifiers=qualifiers,
            data_specifications=data_specifications
        )

        self.first = first
        self.second = second


@abstract
@reference_in_the_book(section=(4, 7, 8, 5))
class Data_element(Submodel_element):
    """
    A data element is a submodel element that is not further composed out of
    other submodel elements.

    A data element is a submodel element that has a value. The type of value differs
    for different subtypes of data elements.
    """

    def __init__(
            self,
            ID_short: str,
            display_name: Optional['Lang_string_set'] = None,
            category: Optional[str] = None,
            description: Optional['Lang_string_set'] = None,
            kind: Optional['Modeling_kind'] = None,
            semantic_id: Optional['Reference'] = None,
            qualifiers: Optional[List[Constraint]] = None,
            data_specifications: Optional[List['Reference']] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            kind=kind,
            semantic_id=semantic_id,
            qualifiers=qualifiers,
            data_specifications=data_specifications
        )


@reference_in_the_book(section=(4, 7, 8, 1))
class Annotated_relationship_element(Relationship_element):
    """
    An annotated relationship element is a relationship element that can be annotated
    with additional data elements.
    """
    annotation: Optional[List[Data_element]]
    """
    A reference to a data element that represents an annotation that holds for
    the relationship between the two elements.
    """

    def __init__(
            self,
            ID_short: str,
            first: Referable,
            second: Referable,
            display_name: Optional['Lang_string_set'] = None,
            category: Optional[str] = None,
            description: Optional['Lang_string_set'] = None,
            kind: Optional['Modeling_kind'] = None,
            semantic_id: Optional['Reference'] = None,
            qualifiers: Optional[List[Constraint]] = None,
            data_specifications: Optional[List['Reference']] = None,
            annotation: Optional[List[Data_element]] = None
    ) -> None:
        Relationship_element.__init__(
            self,
            first=first,
            second=second,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            kind=kind,
            semantic_id=semantic_id,
            qualifiers=qualifiers,
            data_specifications=data_specifications
        )

        self.annotation = annotation if annotation is not None else []


# TODO (mristin, 2021-10-27):
#  Most of the classes inheriting from Data_element need to specify the invariant:
#  "Constraint AASd-090"
#  For  data elements DataElement/category shall be  one  of the
#  following values: CONSTANT, PARAMETER or VARIABLE. Exception: File and Blob
#  data elements.

# TODO (mristin, 2021-10-29): We can not implement this constraint, correct?
#  🠒 Double-check with Nico!
#  Constraint AASd-061:
#  If the semanticId of a Event submodel element references
#  a ConceptDescription then the category of the ConceptDescription shall be one of
#  the following: EVENT.

@abstract
@reference_in_the_book(section=(4, 7, 8, 7))
class Event(Submodel_element):
    """
    An event.
    """

    def __init__(
            self,
            ID_short: str,
            display_name: Optional['Lang_string_set'] = None,
            category: Optional[str] = None,
            description: Optional['Lang_string_set'] = None,
            kind: Optional[Modeling_kind] = None,
            semantic_id: Optional['Reference'] = None,
            qualifiers: Optional[List[Constraint]] = None,
            data_specifications: Optional[List['Reference']] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            kind=kind,
            semantic_id=semantic_id,
            qualifiers=qualifiers,
            data_specifications=data_specifications
        )


@abstract
@reference_in_the_book(section=(4, 7, 8, 2))
class Basic_Event(Event):
    """
    A basic event.
    """
    observed: Referable
    """
    Reference to a referable, e.g. a data element or a submodel, that is being 
    observed.
    """

    def __init__(
            self,
            observed: Referable,
            ID_short: str,
            display_name: Optional['Lang_string_set'] = None,
            category: Optional[str] = None,
            description: Optional['Lang_string_set'] = None,
            kind: Optional[Modeling_kind] = None,
            semantic_id: Optional['Reference'] = None,
            qualifiers: Optional[List[Constraint]] = None,
            data_specifications: Optional[List['Reference']] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            kind=kind,
            semantic_id=semantic_id,
            qualifiers=qualifiers,
            data_specifications=data_specifications
        )

        self.observed = observed


@invariant(lambda self: len(self.keys) >= 1)
@reference_in_the_book(section=(4, 7, 11), index=0)
class Reference(DBC):
    """
    Reference to either a model element of the same or another AAs or to an external
    entity.

    A reference is an ordered list of keys, each key referencing an element. The
    complete list of keys may for example be concatenated to a path that then gives
    unique access to an element or entity.
    """
    keys: List['Key']
    """Unique references in their name space."""

    def __init__(self, keys: List['Key']) -> None:
        self.keys = keys


# fmt: off
@invariant(
    lambda self:
    not (self.ID_type == Key_type.IRI) or is_IRI(self.value)
)
@invariant(
    lambda self:
    not (self.ID_type == Key_type.IRDI) or is_IRDI(self.value)
)
@invariant(
    lambda self:
    not (type == Key_elements.Global_reference)
    or (self.ID_type != Key_type.ID_short and self.ID_type != Key_type.Fragment_ID),
    "Constraint AASd-080"
)
@invariant(
    lambda self:
    not (type == Key_elements.Asset_administration_shell)
    or (self.ID_type != Key_type.ID_short and self.ID_type != Key_type.Fragment_ID),
    "Constraint AASd-081"
)
@reference_in_the_book(section=(4, 7, 11), index=1)
# fmt: on
class Key(DBC):
    """A key is a reference to an element by its id."""

    type: 'Key_elements'
    """
    Denote which kind of entity is referenced.

    In case type = :attr:`Key_elements.Global_reference` then the key represents
    a global unique id.

    In case type = :attr:`Fragment_ID` the key represents a  bookmark or
    a  similar local identifier within its parent element as specified by the key that
    precedes this key.

    In all other cases the key references a model element of the same or of another AAS.
    The name of the model element is explicitly listed.
    """

    value: str
    """The key value, for example an IRDI if the :attr:`~ID_type` is IRDI."""

    ID_type: 'Key_type'
    """Type of the key value."""

    def __init__(self, type: 'Key_elements', value: str, ID_type: 'Key_type') -> None:
        self.type = type
        self.value = value
        self.ID_type = ID_type


@reference_in_the_book(section=(4, 7, 11), index=2)
class Key_elements(Enum):
    """Enumeration of different key value types within a key."""

    Global_reference = "GlobalReference"
    """reference to an element not belonging to an asset administration shell"""

    Fragment_reference = "FragmentReference"
    """
    unique reference to an element within a file.

    The file itself is assumed to be part of an asset administration shell.
    """

    Access_permission_rule = "AccessPermissionRule"
    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Asset = "Asset"
    Asset_administration_shell = "AssetAdministrationShell"
    Basic_event = "BasicEvent"
    Blob = "Blob"
    Capability = "Capability"
    Concept_description = "ConceptDescription"
    Concept_dictionary = "ConceptDictionary"
    Data_element = "DataElement"
    """
    Data element.

    .. note::

        Data Element is abstract, *i.e.* if a key uses :attr:`Data_element`
        the reference may be a Property, a File *etc.*
    """

    Entity = "Entity"
    Event = "Event"
    """
    Event.

    .. note::

        Event is abstract.
    """

    File = "File"
    Multi_language_property = "MultiLanguageProperty"
    """Property with a value that can be provided in multiple languages"""

    Operation = "Operation"
    Property = "Property"
    Range = "Range"
    """Range with min and max"""

    Reference_element = "ReferenceElement"
    Relationship_element = "RelationshipElement"
    Submodel = "Submodel"
    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, *i.e.* if a key uses :attr:`Submodel_element`
        the reference may be a Property, a :class:`Submodel_element_collection`,
        an Operation *etc.*
    """

    Submodel_element_collection = "SubmodelElementCollection"
    View = "View"


@reference_in_the_book(section=(4, 7, 11), index=3)
class Referable_elements(Enum):
    """Enumeration of all referable elements within an asset administration shell"""

    Access_permission_rule = "AccessPermissionRule"
    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Asset = "Asset"
    Asset_administration_shell = "AssetAdministrationShell"
    Basic_event = "BasicEvent"
    Blob = "Blob"
    Capability = "Capability"
    Concept_description = "ConceptDescription"
    Concept_dictionary = "ConceptDictionary"
    Data_element = "DataElement"
    """
    Data element.

    .. note::

        Data Element is abstract, *i.e.* if a  key uses :attr:`Data_element`
        the reference may be a Property, a File *etc.*
    """

    Entity = "Entity"
    Event = "Event"
    """
    Event.

    .. note::

        Event is abstract.
    """

    File = "File"
    Multi_language_property = "MultiLanguageProperty"
    Operation = "Operation"
    Property = "Property"
    Range = "Range"
    Reference_element = "ReferenceElement"
    Relationship_element = "RelationshipElement"
    Submodel = "Submodel"
    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, *i.e.* if a key uses :attr:`Submodel_element`
        the reference may be a Property, a :class:`Submodel_element_collection`,
        an Operation *etc.*
    """

    Submodel_element_collection = "SubmodelElementCollection"
    View = "View"


@reference_in_the_book(section=(4, 7, 11), index=4)
class Identifiable_elements(Enum):
    """Enumeration of all identifiable elements within an asset administration shell."""

    Asset = "Asset"
    Asset_administration_shell = "AssetAdministrationShell"
    Concept_description = "ConceptDescription"
    Submodel = "Submodel"


assert {literal.value for literal in Referable_elements}.issubset(
    {literal.value for literal in Key_elements})

assert {literal.value for literal in Identifiable_elements}.issubset(
    {literal.value for literal in Referable_elements})


@reference_in_the_book(section=(4, 7, 11), index=5)
class Key_type(Enum):
    """Enumeration of different key value types within a key."""

    ID_short = "IdShort"
    """idShort of a referable element"""

    Fragment_ID = "FragmentId"
    """Identifier of a fragment within a file"""

    IRDI = "IRDI"
    """
    IRDI according to ISO29002-5 as an Identifier scheme for properties and
    classifications.
    """

    IRI = "IRI"
    """IRI according to Rfc 3987. Every URI is an IRI."""

    Custom = "Custom"
    """Custom identifiers like GUIDs (globally unique identifiers)"""


@reference_in_the_book(section=(4, 7, 11), index=6)
class Local_key_type(Enum):
    """Enumeration of different key value types within a key."""

    ID_short = "IdShort"
    """idShort of a referable element"""

    Fragment_ID = "FragmentId"
    """Identifier of a fragment within a file"""


assert (
        set(literal.value for literal in Key_type) ==
        set(literal.value for literal in Local_key_type).union(
            literal.value for literal in Identifier_type)
)


@reference_in_the_book(section=(4, 7, 13, 2), index=0)
class Data_type_def(Enum):
    Any_uri = "anyUri"
    Base64_binary = "base64Binary"
    Boolean = "boolean"
    Date = "date"
    Datetime = "dateTime"
    Datetime_stamp = "dateTimeStamp"
    Decimal = "decimal"
    Integer = "integer"
    Long = "long"
    Int = "int"
    Short = "short"
    Byte = "byte"
    Non_negative_integer = "nonNegativeInteger"
    Positive_integer = "positiveInteger"
    Unsigned_long = "unsignedLong"
    Unsigned_int = "unsignedInt"
    Unsigned_short = "unsignedShort"
    Unsigned_byte = "unsignedByte"
    Non_positive_integer = "nonPositiveInteger"
    Negative_integer = "negativeInteger"
    Double = "double"
    Duration = "duration"
    Day_time_duration = "dayTimeDuration"
    Year_month_duration = "yearMonthDuration"
    Float = "float"
    G_day = "gDay"
    G_month = "gMonth"
    G_month_day = "gMonthDay"
    G_year = "gYear"
    G_year_month = "gYearMonth"
    Hex_binary = "hexBinary"
    Notation = "NOTATION"
    Q_name = "QName"
    String = "string"
    Normalized_string = "normalizedString"
    Token = "token"
    Language = "language"
    Name = "Name"
    N_C_name = "NCName"
    Entity = "ENTITY"
    ID = "ID"
    IDREF = "IDREF"
    N_M_token = "NMTOKEN"
    Time = "time"


@implementation_specific
@reference_in_the_book(section=(4, 7, 13, 2), index=1)
class Value_data_type(DBC):
    """Any XSD atomic type as specified via :class:`Data_type_def`"""


@reference_in_the_book(section=(4, 7, 13, 11))
class Lang_string(DBC):
    """Give a text in a specific language."""

    language: str
    """Language of the :attr`~text`"""

    text: str
    """Content of the string"""

    # TODO (Nico & Marko, 2021-05-28): what is the format of the ``language``?
    def __init__(self, language: str, text: str) -> None:
        self.language = language
        self.text = text


@implementation_specific
# TODO (Nico & Marko, 2021-05-28):
#  Should the language be unique?
#  Or can we have duplicate entries for, say, "EN"?
# fmt: off
@invariant(lambda self: len(self.lang_strings) > 0)
@invariant(
    lambda self:
    are_unique(
        lang_string.language for lang_string in self.lang_strings
    ),
    "No duplicate languages allowed"
)
@reference_in_the_book(section=(4, 7, 13, 2), index=2)
# fmt: on
class Lang_string_set(DBC):
    """
    A set of strings, each annotated by the language of the string.

    The meaning of the string in each language shall be the same.
    """

    lang_strings: List[Lang_string]
    """Strings in the specified languages."""

    def __init__(self, lang_strings: List[Lang_string]) -> None:
        self.lang_strings = lang_strings

        # The strings need to be accessed by a dictionary;
        # how this dictionary is initialized is left to the individual implementation.

    @ensure(
        lambda self, language, result:
        not result
        or any(language == lang_string.language for lang_string in self.lang_strings)
    )
    def has_language(self, language: str) -> bool:
        """
        Check whether the string is available in the given language.

        :param language: language of interest
        :return: True if the string is available in the language
        """
        # The strings need to be accessed by a dictionary;
        # how this dictionary is accessed is left to the individual implementation.

    @ensure(
        lambda self, language, result:
        not (self.has_language(language) ^ (result is not None))
    )
    def by_language(self, language: str) -> Optional[str]:
        """
        Retrieve the string in the given language.

        :param language: language of interest
        :return: the string in the language, if available
        """
        # The strings need to be accessed by a dictionary;
        # how this dictionary is accessed is left to the individual implementation.


Qualifier_type = str  # reference_in_the_book(section=(4, 7, 13, 2))


ID = str  # reference_in_the_book(section=(4, 7, 13, 2))

# TODO (Nico & Marko, 2021-09-24):
#  We need to list in a comment all the constraints which were not implemented.

# TODO (mristin, 2021-10-27): re-order the entities so that they follow the structure
#  in the book as much as possible, but be careful about the inheritance

# TODO (mristin, 2021-10-27): write a code generator that outputs the JSON schema and
#  then compare it against the https://github.com/admin-shell-io/aas-specs/blob/master/schemas/json/aas.json
