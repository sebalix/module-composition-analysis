Code timelines are available through the *Odoo MCA / Data / Code / Code
Timelines* menu.

To declare what a code element became starting from a given Odoo version,
create a timeline and select:

- the element type (Model, Field, Method or Data),
- the element concerned (in its current version),
- its state: *renamed* (with the new element) or *removed*.

The *Notes* field can be used to document the details of a migration, for
instance when an element has been split into several other elements: the
timeline declares the main successor, and the note explains the whole story
(e.g. which fields moved where).

The next version lookups on the code elements (e.g. the *Next Odoo Version
Field* on a field form) follow these declarations, as well as the module
renames/replacements declared in the module timelines.

Each code element also displays its *Next Version State*:

| State | Description |
| ----- | ----------- |
| *Unknown* | The next version of the module has not been scanned yet |
| *Available* | The element (or its renamed version) exists in the next scanned version |
| *Removed* | The element no longer exists in the next scanned version |

The states are refreshed on each scan, when timelines change, and daily by
a scheduled action which reclassifies the elements still in the *Unknown*
state.
