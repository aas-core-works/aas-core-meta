..
    NOTE (mristin, 2021-12-27):
    Please keep this file at 72 line width so that we can copy-paste
    the release logs directly into commit messages.

2022.6.21
=========
This is a minor enhancement version. We implement the invariant on
the category of a data element in a more systematic manner.

* Encapsulate data element category in V3RC02 (#121)
* Ensure Data element category in V3RC02

2022.6.20
=========
This is a minor bug-fix version. We release it so we can start working
on tests with XML data.

* Enforce Extension value match type in V3RC02 (#119)
* Revert back AASd-119 in V3RC02 (#118)

2022.6.19
=========
This is a version with fixes which were necessary for generating
the JSON test data automatically using aas-core3.0rc02-testgen,
and making sure that the aas-core-codegen generates the C# code
such that it passes all the unit tests for JSON.

XML tests are still pending.

* Invert AASd-119 in V3RC02 (#116)
* Fix ``xs:string`` pattern for V3RC02 (#115)
* Check non-none of message broker in inv. of V3RC02 (#114)
* Fix nullness in inv. AASd-119 in V3RC02 (#113)
* Remove ill-defined constraint 116 from V3RC02 (#111)
* Remove unique idShort from list elements in V3RC02 (#110)

2022.6.17
=========
This is a bug-fix version, where our spec turned out to be  incorrect
from the programming point of view.

* Fix invariant on specific_asset_id in V3RC2 (#108)
* Fix length invariant of id-shorts in V3RC2 (#107)
* Fix AnyURI patterns for UTF-32 (#106)

2022.6.3 (2022-06-03)
=====================
In this version we fix a couple of inconsistencies with the book which
were spotted during the reviews.

* Sort out ``modelType`` in V3RC02 (#104)
* Make ``RelationshipElement`` concrete in V3RC02 (#103)

2022.5.26 (2022-05-26)
======================
This is the version of our meta-model tailored to the finalized version
of the book for V3RC02.

2022.5.30a1 (2022-05-18)
========================
This is a pre-release version.

* Introduce ``get_*_or_default`` as methods to V3rc2 (#71)
* Remove setting default values in constructors (#70)
* Fix the nonsensical invariant in Entity in V3RC02 (#69)
* Check category only if set in V3RC02 (#68)
* Fix invariants in V3RC02 (#67)


2022.4.30a6 (2022-04-20)
========================
This is a pre-release version.

* Remove class ``View`` from V3RC02 (#65)

2022.4.30a5 (2022-04-09)
========================
This is a pre-release version.

* Fix dangling references in V3RC02 (#63)

2022.4.30a4 (2022-04-09)
========================
This is a pre-release version.

* Remove data specifications from V3RC02 (#61)

2022.4.30a3 (2022-04-09)
========================
This is a pre-release version.

* Review key.value and key_elements.fragment (#57)
* Re-order V3RC02 classes to match V3RC01 (#59)

2022.4.30a2 (2022-04-07)
========================
This is a pre-release version.

* Remove redundant nullability checks in V3RC02 (#55)
* Fix docstring for ``matches_BCP_47`` in V3RC02 (#54)

2022.4.30a1 (2022-04-07)
========================
This is a pre-release version.

* Revisit V3RC01 and V3RC02 according to the current state of the book.
* Formalize the constraints as invariants for V3RC02.
