This module extends `odoo_repository_code` to analyze the evolution of the
code elements of modules between Odoo versions.

It relies on the timelines mechanism provided by `odoo_repository_migration`
(used to declare what a module became in a given Odoo version) and extends
it to the code elements:

- Odoo models
- Fields
- Methods
- Data records (XML and CSV)

Through *code timelines*, you can declare that a code element has been
renamed or removed starting from a given Odoo version. The next version
lookups on the code elements then follow these declarations, as well as the
module renames/replacements declared in the module timelines.

Each code element also gets a *Next Version State* telling whether it still
exists in the next scanned version of its module. It helps to detect the
elements that disappeared (or were renamed) between two Odoo versions, and
to build a consolidated knowledge database across versions for everyone:
functionals and developers.
