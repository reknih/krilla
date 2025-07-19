#!/usr/bin/env python3
"""
Generate Rust code for PDF tags from a JSON schema.
This script generates individual structs for each tag type and a TagKind enum that wraps them.
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from textwrap import dedent, indent

# Define the complete tag schema based on the current implementation
TAG_SCHEMA = {
    "tags": [
        {
            "name": "Part",
            "doc": "A part of a document that may contain multiple articles or sections.",
            "attrs": {}
        },
        {
            "name": "Article", 
            "doc": "An article with largely self-contained content.",
            "attrs": {}
        },
        {
            "name": "Section",
            "doc": "Section of a larger document.",
            "attrs": {}
        },
        {
            "name": "BlockQuote",
            "doc": "A paragraph-level quote.",
            "attrs": {}
        },
        {
            "name": "Caption",
            "doc": "An image or figure caption.\n\n**Best Practice**: In the tag tree, this should appear\nas a sibling after the image (or other) content it describes.",
            "attrs": {}
        },
        {
            "name": "TOC",
            "doc": "Table of contents.\n\n**Best Practice**: Should consist of TOCIs or other nested TOCs.",
            "attrs": {}
        },
        {
            "name": "TOCI",
            "doc": "Item in the table of contents.\n\n**Best Practice**: Should only appear within a TOC. Should only consist of\nlabels, references, paragraphs and TOCs.",
            "attrs": {}
        },
        {
            "name": "Index",
            "doc": "Index of the key terms in the document.\n\n**Best Practice**: Should contain a sequence of text accompanied by\nreference elements pointing to their occurrence in the text.",
            "attrs": {}
        },
        {
            "name": "P",
            "doc": "A paragraph.",
            "attrs": {}
        },
        {
            "name": "Hn",
            "doc": "Heading level `n`, including an optional title of the heading.\n\nThe title is required for some export modes, like for example PDF/UA.",
            "attrs": {
                "required": [
                    {"name": "level", "type": "NonZeroU32", "doc": "The heading level"}
                ],
                "optional": []
            }
        },
        {
            "name": "L",
            "doc": "A list.\n\n**Best practice**: Should consist of an optional caption followed by\nlist items.",
            "attrs": {
                "required": [
                    {"name": "numbering", "type": "ListNumbering", "doc": "The list numbering style"}
                ]
            }
        },
        {
            "name": "LI",
            "doc": "A list item.\n\n**Best practice**: Should consist of one or more list labels and/or list bodies.",
            "attrs": {}
        },
        {
            "name": "Lbl",
            "doc": "Label for a list item.",
            "attrs": {}
        },
        {
            "name": "LBody",
            "doc": "Description of the list item.",
            "attrs": {}
        },
        {
            "name": "Table",
            "doc": "A table, with an optional summary describing the purpose and structure.\n\n**Best practice**: Should consist of an optional table header row,\none or more table body elements and an optional table footer. Can have\ncaption as the first or last child.",
            "attrs": {
                "optional": [
                    {"name": "summary", "type": "String", "category": "table_attr"},
                    {"name": "bbox", "type": "Rect", "category": "layout_attr"},
                    {"name": "width", "type": "f32", "category": "layout_attr"},
                    {"name": "height", "type": "f32", "category": "layout_attr"}
                ]
            }
        },
        {
            "name": "TR",
            "doc": "A table row.\n\n**Best practice**: May contain table headers cells and table data cells.",
            "attrs": {}
        },
        {
            "name": "TH",
            "doc": "A table header cell.",
            "attrs": {
                "required": [
                    {"name": "scope", "type": "TableHeaderScope", "doc": "The scope of this header cell"}
                ],
                "optional": [
                    {"name": "headers", "type": "SmallVec<[TagId; 1]>", "category": "table_attr"},
                    {"name": "span", "type": "TableCellSpan", "category": "table_attr"},
                    {"name": "width", "type": "f32", "category": "layout_attr"},
                    {"name": "height", "type": "f32", "category": "layout_attr"}
                ]
            }
        },
        {
            "name": "TD",
            "doc": "A table data cell.",
            "attrs": {
                "optional": [
                    {"name": "headers", "type": "SmallVec<[TagId; 1]>", "category": "table_attr"},
                    {"name": "span", "type": "TableCellSpan", "category": "table_attr"},
                    {"name": "width", "type": "f32", "category": "layout_attr"},
                    {"name": "height", "type": "f32", "category": "layout_attr"}
                ]
            }
        },
        {
            "name": "THead",
            "doc": "A table header row group.",
            "attrs": {}
        },
        {
            "name": "TBody", 
            "doc": "A table data row group.",
            "attrs": {}
        },
        {
            "name": "TFoot",
            "doc": "A table footer row group.",
            "attrs": {}
        },
        {
            "name": "InlineQuote",
            "doc": "An inline quotation.",
            "attrs": {}
        },
        {
            "name": "Note",
            "doc": "A foot- or endnote, potentially referred to from within the text.\n\n**Best practice**: It may have a label as a child.",
            "attrs": {}
        },
        {
            "name": "Reference",
            "doc": "A reference to elsewhere in the document.\n\n**Best practice**: The first child of a tag group with this tag should be a link annotation\nlinking to a destination in the document, and the second child should consist of\nthe children that should be associated with that reference.",
            "attrs": {}
        },
        {
            "name": "BibEntry",
            "doc": "A reference to the external source of some cited document.\n\n**Best practice**: It may have a label as a child.",
            "attrs": {}
        },
        {
            "name": "Code",
            "doc": "Computer code.",
            "attrs": {}
        },
        {
            "name": "Link",
            "doc": "A link.\n\n**Best practice**: The first child of a tag group with this tag should be a link annotation\nlinking to an URL, and the second child should consist of the children that should\nbe associated with that link.",
            "attrs": {}
        },
        {
            "name": "Annot",
            "doc": "An association between an annotation and the content it belongs to. PDF\n\n**Best practice**: Should be used for all annotations, except for link annotations and\nwidget annotations. The first child should be the identifier of a non-link annotation,\nand all other subsequent children should be content identifiers associated with that\nannotation.",
            "attrs": {}
        },
        {
            "name": "Figure",
            "doc": "Item of graphical content.\n\nProviding alt_text is required in some export modes, like for example PDF/UA1.",
            "attrs": {
                "optional": [
                    {"name": "bbox", "type": "Rect", "category": "layout_attr"},
                    {"name": "width", "type": "f32", "category": "layout_attr"},
                    {"name": "height", "type": "f32", "category": "layout_attr"}
                ]
            }
        },
        {
            "name": "Formula",
            "doc": "A mathematical formula.\n\nProviding alt_text is required in some export modes, like for example PDF/UA1.",
            "attrs": {
                "optional": [
                    {"name": "bbox", "type": "Rect", "category": "layout_attr"},
                    {"name": "width", "type": "f32", "category": "layout_attr"},
                    {"name": "height", "type": "f32", "category": "layout_attr"}
                ]
            }
        },
        {
            "name": "Datetime",
            "doc": "A date or time.",
            "attrs": {}
        },
        {
            "name": "Terms",
            "doc": "A list of terms.",
            "attrs": {}
        },
        {
            "name": "Title",
            "doc": "A title.",
            "attrs": {}
        }
    ],
    "global_attrs": [
        {"name": "id", "type": "Option<TagId>", "doc": "The tag identifier"},
        {"name": "lang", "type": "Option<String>", "doc": "The language of this tag"},
        {"name": "alt_text", "type": "Option<String>", "doc": "An optional alternate text that describes the text"},
        {"name": "expanded", "type": "Option<String>", "doc": "If the content is an abbreviation, the expanded form"},
        {"name": "actual_text", "type": "Option<String>", "doc": "The actual text represented by the content"},
        {"name": "location", "type": "Option<Location>", "doc": "The location of the tag"},
        {"name": "placement", "type": "Option<Placement>", "doc": "The positioning of the element"},
        {"name": "writing_mode", "type": "Option<WritingMode>", "doc": "The writing mode"},
        {"name": "title", "type": "Option<String>", "doc": "The title of the element"}
    ]
}

def snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0 and (i + 1 < len(name) and name[i + 1].islower() or name[i - 1].islower()):
            result.append('_')
        result.append(char.lower())
    return ''.join(result)

def generate_struct_fields(attrs: Dict[str, Any], global_attrs: List[Dict[str, Any]]) -> str:
    """Generate struct field definitions."""
    fields = []
    
    # Add global attributes
    for attr in global_attrs:
        doc = f"    /// {attr['doc']}\n" if 'doc' in attr else ""
        fields.append(f"{doc}    pub {attr['name']}: {attr['type']},")
    
    # Add required attributes
    if 'required' in attrs:
        for attr in attrs['required']:
            doc = f"    /// {attr['doc']}\n" if 'doc' in attr else ""
            fields.append(f"{doc}    pub {attr['name']}: {attr['type']},")
    
    # Add optional attributes  
    if 'optional' in attrs:
        for attr in attrs['optional']:
            doc_text = attr.get('doc', f"The {attr['name']} attribute")
            doc = f"    /// {doc_text}\n"
            # Some types are already Option, so don't double-wrap
            type_str = attr['type']
            if not type_str.startswith('Option<'):
                type_str = f"Option<{type_str}>"
            fields.append(f"{doc}    pub {attr['name']}: {type_str},")
    
    return '\n'.join(fields)

def generate_constructor(tag_name: str, attrs: Dict[str, Any]) -> str:
    """Generate constructor implementation."""
    required = attrs.get('required', [])
    
    # Constructor parameters
    params = []
    for attr in required:
        params.append(f"{attr['name']}: {attr['type']}")
    param_str = ", ".join(params)
    
    # Field initializations
    inits = []
    
    # Initialize required fields
    for attr in required:
        inits.append(f"            {attr['name']},")
    
    # Initialize optional fields to None
    if 'optional' in attrs:
        for attr in attrs['optional']:
            inits.append(f"            {attr['name']}: None,")
    
    # Initialize global attributes
    global_attrs = TAG_SCHEMA['global_attrs']
    for attr in global_attrs:
        inits.append(f"            {attr['name']}: None,")
    
    init_str = '\n'.join(inits)
    
    if params:
        return f"""
    /// Create a new {tag_name} tag.
    pub fn new({param_str}) -> Self {{
        Self {{
{init_str}
        }}
    }}"""
    else:
        return f"""
    /// Create a new {tag_name} tag.
    pub fn new() -> Self {{
        Self {{
{init_str}
        }}
    }}"""

def generate_builder_methods(tag_name: str, attrs: Dict[str, Any]) -> str:
    """Generate builder methods for optional attributes."""
    methods = []
    
    # Builder methods for optional attributes
    if 'optional' in attrs:
        for attr in attrs['optional']:
            method_name = f"with_{attr['name']}"
            doc = attr.get('doc', f"Set the {attr['name']}")
            methods.append(f"""
    /// {doc}
    pub fn {method_name}(mut self, {attr['name']}: {attr['type']}) -> Self {{
        self.{attr['name']} = Some({attr['name']});
        self
    }}""")
    
    # Builder methods for global attributes
    for attr in TAG_SCHEMA['global_attrs']:
        if attr['name'] in ['id', 'lang', 'alt_text', 'expanded', 'actual_text', 'location', 'placement', 'writing_mode', 'title']:
            base_type = attr['type'].replace('Option<', '').replace('>', '')
            method_name = f"with_{attr['name']}"
            doc = attr.get('doc', f"Set the {attr['name']}")
            methods.append(f"""
    /// {doc}
    pub fn {method_name}(mut self, {attr['name']}: {base_type}) -> Self {{
        self.{attr['name']} = Some({attr['name']});
        self
    }}""")
    
    return '\n'.join(methods)

def generate_accessor_impl_for_tag(tag: Dict[str, Any]) -> str:
    """Generate attribute accessor implementations for a specific tag."""
    name = tag['name']
    struct_name = f"{name}Tag"
    attrs = tag.get('attrs', {})
    
    # Generate list_attrs implementation
    list_attrs_impl = "BSet::new()"
    if name == "L":
        list_attrs_impl = """
        let mut attrs = BSet::new();
        attrs.items.push(ListAttr::Numbering(self.numbering));
        attrs"""
    
    # Generate table_attrs implementation  
    table_attrs_impl = "BSet::new()"
    table_attrs_items = []
    
    if name == "Table" and 'optional' in attrs:
        if any(a['name'] == 'summary' for a in attrs['optional']):
            table_attrs_items.append("""
        if let Some(ref summary) = self.summary {
            attrs.items.push(TableAttr::Summary(summary.clone()));
        }""")
    
    if name == "TH":
        table_attrs_items.append("""
        attrs.items.push(TableAttr::HeaderScope(self.scope));""")
    
    if name in ["TH", "TD"] and 'optional' in attrs:
        if any(a['name'] == 'headers' for a in attrs['optional']):
            table_attrs_items.append("""
        if let Some(ref headers) = self.headers {
            attrs.items.push(TableAttr::CellHeaders(headers.clone()));
        }""")
        if any(a['name'] == 'span' for a in attrs['optional']):
            table_attrs_items.append("""
        if let Some(ref span) = self.span {
            attrs.items.push(TableAttr::CellSpan(*span));
        }""")
    
    if table_attrs_items:
        table_attrs_impl = f"""
        let mut attrs = BSet::new();{''.join(table_attrs_items)}
        attrs"""
    
    # Generate layout_attrs implementation
    layout_attrs_impl = """
        let mut attrs = BSet::new();
        if let Some(ref placement) = self.placement {
            attrs.items.push(LayoutAttr::Placement(*placement));
        }
        if let Some(ref writing_mode) = self.writing_mode {
            attrs.items.push(LayoutAttr::WritingMode(*writing_mode));
        }"""
    
    layout_attrs_items = []
    if 'optional' in attrs:
        if any(a['name'] == 'bbox' for a in attrs['optional']):
            layout_attrs_items.append("""
        if let Some(ref bbox) = self.bbox {
            attrs.items.push(LayoutAttr::BBox(*bbox));
        }""")
        if any(a['name'] == 'width' for a in attrs['optional']):
            layout_attrs_items.append("""
        if let Some(width) = self.width {
            attrs.items.push(LayoutAttr::Width(width));
        }""")
        if any(a['name'] == 'height' for a in attrs['optional']):
            layout_attrs_items.append("""
        if let Some(height) = self.height {
            attrs.items.push(LayoutAttr::Height(height));
        }""")
    
    layout_attrs_impl += ''.join(layout_attrs_items) + """
        attrs"""
    
    # Handle special case for Hn tag which has HeadingLevel attribute
    attrs_impl_extra = ""
    if name == "Hn":
        attrs_impl_extra = """
        attrs.items.push(Attr::HeadingLevel(self.level));"""
    
    return f"""
// Additional accessor methods for mod.rs compatibility
impl {struct_name} {{
    /// Get the attributes as internal BSet types.
    pub(crate) fn attrs(&self) -> BSet<Attr> {{
        let mut attrs = BSet::new();
        if let Some(ref id) = self.id {{
            attrs.items.push(Attr::Id(id.clone()));
        }}
        if let Some(ref title) = self.title {{
            attrs.items.push(Attr::Title(title.clone()));
        }}
        if let Some(ref lang) = self.lang {{
            attrs.items.push(Attr::Lang(lang.clone()));
        }}
        if let Some(ref alt_text) = self.alt_text {{
            attrs.items.push(Attr::AltText(alt_text.clone()));
        }}
        if let Some(ref expanded) = self.expanded {{
            attrs.items.push(Attr::Expanded(expanded.clone()));
        }}
        if let Some(ref actual_text) = self.actual_text {{
            attrs.items.push(Attr::ActualText(actual_text.clone()));
        }}{attrs_impl_extra}
        attrs
    }}
    
    pub(crate) fn list_attrs(&self) -> BSet<ListAttr> {{{list_attrs_impl}
    }}
    
    pub(crate) fn table_attrs(&self) -> BSet<TableAttr> {{{table_attrs_impl}
    }}
    
    pub(crate) fn layout_attrs(&self) -> BSet<LayoutAttr> {{{layout_attrs_impl}
    }}
}}"""

def generate_tag_struct(tag: Dict[str, Any]) -> str:
    """Generate a complete tag struct definition."""
    name = tag['name']
    struct_name = f"{name}Tag"
    doc = tag['doc'].replace('\n\n', '\n///\n/// ').replace('\n', ' ').replace('`', "'")
    attrs = tag.get('attrs', {})
    
    # Generate struct definition
    fields = generate_struct_fields(attrs, TAG_SCHEMA['global_attrs'])
    constructor = generate_constructor(name, attrs)
    builders = generate_builder_methods(name, attrs)
    accessor_impl = generate_accessor_impl_for_tag(tag)
    
    # Add Default implementation if no required fields
    default_impl = ""
    if not attrs.get('required'):
        default_impl = f"""
impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}"""
    
    return f"""
/// {doc}
#[derive(Clone, Debug, PartialEq)]
pub struct {struct_name} {{
{fields}
}}

impl {struct_name} {{{constructor}{builders}
}}
{accessor_impl}{default_impl}"""

def generate_tag_kind_enum(tags: List[Dict[str, Any]]) -> str:
    """Generate the TagKind enum."""
    variants = []
    for tag in tags:
        name = tag['name']
        struct_name = f"{name}Tag"
        doc = tag['doc'].replace('\n\n', '\n    ///\n    /// ').replace('\n', ' ').replace('`', "'")
        variants.append(f"""
    /// {doc}
    {name}({struct_name}),""")
    
    variant_str = ''.join(variants)
    
    # Generate From implementations
    from_impls = []
    for tag in tags:
        name = tag['name']
        struct_name = f"{name}Tag"
        from_impls.append(f"""
impl From<{struct_name}> for TagKind {{
    fn from(tag: {struct_name}) -> Self {{
        TagKind::{name}(tag)
    }}
}}""")
    
    from_impls_str = '\n'.join(from_impls)
    
    # Generate inner() method match arms
    inner_arms = []
    for tag in tags:
        name = tag['name']
        inner_arms.append(f"            TagKind::{name}(tag) => tag,")
    inner_arms_str = '\n'.join(inner_arms)
    
    # Generate accessor methods for specific tag types
    accessor_methods = generate_tag_accessor_methods(tags)
    
    return f"""
/// A tag kind.
#[derive(Clone, Debug, PartialEq)]
pub enum TagKind {{{variant_str}
}}

impl TagKind {{
    /// Get a reference to the inner tag's global attributes.
    pub fn inner(&self) -> &dyn TagTrait {{
        match self {{
{inner_arms_str}
        }}
    }}
{accessor_methods}
}}
{from_impls_str}"""

def generate_tag_accessor_methods(tags: List[Dict[str, Any]]) -> str:
    """Generate accessor methods for specific tag types."""
    methods = []
    
    # Find tags with special attributes that need accessors
    for tag in tags:
        name = tag['name']
        attrs = tag.get('attrs', {})
        
        # Hn tag needs level accessor
        if name == "Hn":
            methods.append("""
    /// Get the heading level if this is an Hn tag.
    pub(crate) fn heading_level(&self) -> Option<NonZeroU32> {
        match self {
            TagKind::Hn(tag) => Some(tag.level),
            _ => None,
        }
    }""")
        
        # L tag needs numbering accessor
        elif name == "L":
            methods.append("""
    /// Get the list numbering if this is an L tag.
    pub(crate) fn list_numbering(&self) -> Option<ListNumbering> {
        match self {
            TagKind::L(tag) => Some(tag.numbering),
            _ => None,
        }
    }""")
        
        # TH tag needs scope accessor
        elif name == "TH":
            methods.append("""
    /// Get the header scope if this is a TH tag.
    pub(crate) fn header_scope(&self) -> Option<TableHeaderScope> {
        match self {
            TagKind::TH(tag) => Some(tag.scope),
            _ => None,
        }
    }""")
    
    # Add methods that check tag types
    methods.append("""
    /// Check if this tag should have alt text.
    pub(crate) fn should_have_alt(&self) -> bool {
        matches!(self, TagKind::Figure(_) | TagKind::Formula(_))
    }
    
    /// Check if this tag can have a title.
    pub(crate) fn can_have_title(&self) -> bool {
        matches!(self, TagKind::Hn(_))
    }""")
    
    return ''.join(methods)

def generate_tag_trait() -> str:
    """Generate the TagTrait for accessing common attributes."""
    return """
/// Trait for accessing common tag attributes.
pub trait TagTrait {
    /// Get the tag identifier.
    fn id(&self) -> Option<&TagId>;
    /// Get the language.
    fn lang(&self) -> Option<&str>;
    /// Get the alternate text.
    fn alt_text(&self) -> Option<&str>;
    /// Get the expanded form.
    fn expanded(&self) -> Option<&str>;
    /// Get the actual text.
    fn actual_text(&self) -> Option<&str>;
    /// Get the location.
    fn location(&self) -> Option<&Location>;
    /// Get the placement.
    fn placement(&self) -> Option<&Placement>;
    /// Get the writing mode.
    fn writing_mode(&self) -> Option<&WritingMode>;
    
    /// Get the title.
    fn title(&self) -> Option<&str>;
    /// Get the headers.
    fn headers(&self) -> Option<&[TagId]>;
    
    /// Get the general attributes.
    fn attrs(&self) -> BSet<Attr>;
    /// Get the list attributes.
    fn list_attrs(&self) -> BSet<ListAttr>;
    /// Get the table attributes.
    fn table_attrs(&self) -> BSet<TableAttr>;
    /// Get the layout attributes.
    fn layout_attrs(&self) -> BSet<LayoutAttr>;
}

// Re-export internal types for use in crate
pub(crate) use crate::interchange::tagging::tag::internal::{Attr, ListAttr, TableAttr, LayoutAttr, BSet};"""

def generate_tag_trait_impl(tag: Dict[str, Any]) -> str:
    """Generate TagTrait implementation for a tag struct."""
    struct_name = f"{tag['name']}Tag"
    
    # Check if tag has headers attribute
    attrs = tag.get('attrs', {})
    has_headers = False
    if 'optional' in attrs:
        has_headers = any(a['name'] == 'headers' for a in attrs['optional'])
    
    headers_impl = "None"
    if has_headers:
        headers_impl = "self.headers.as_ref().map(|v| v.as_slice())"
    
    return f"""
impl TagTrait for {struct_name} {{
    fn id(&self) -> Option<&TagId> {{ self.id.as_ref() }}
    fn lang(&self) -> Option<&str> {{ self.lang.as_deref() }}
    fn alt_text(&self) -> Option<&str> {{ self.alt_text.as_deref() }}
    fn expanded(&self) -> Option<&str> {{ self.expanded.as_deref() }}
    fn actual_text(&self) -> Option<&str> {{ self.actual_text.as_deref() }}
    fn location(&self) -> Option<&Location> {{ self.location.as_ref() }}
    fn placement(&self) -> Option<&Placement> {{ self.placement.as_ref() }}
    fn writing_mode(&self) -> Option<&WritingMode> {{ self.writing_mode.as_ref() }}
    fn title(&self) -> Option<&str> {{ self.title.as_deref() }}
    fn headers(&self) -> Option<&[TagId]> {{ {headers_impl} }}
    
    fn attrs(&self) -> BSet<Attr> {{ self.attrs() }}
    fn list_attrs(&self) -> BSet<ListAttr> {{ self.list_attrs() }}
    fn table_attrs(&self) -> BSet<TableAttr> {{ self.table_attrs() }}
    fn layout_attrs(&self) -> BSet<LayoutAttr> {{ self.layout_attrs() }}
}}"""

def generate_convenience_constructors() -> str:
    """Generate the Tag struct with convenience constructors."""
    constructors = []
    
    for tag in TAG_SCHEMA['tags']:
        name = tag['name']
        struct_name = f"{name}Tag"
        attrs = tag.get('attrs', {})
        required = attrs.get('required', [])
        
        # Build parameter list
        params = []
        for attr in required:
            params.append(f"{attr['name']}: {attr['type']}")
        param_str = ", ".join(params) if params else ""
        
        # Build struct initialization
        if required:
            args = ", ".join([attr['name'] for attr in required])
            init = f"{struct_name}::new({args})"
        else:
            init = f"{struct_name}::new()"
        
        doc = tag['doc'].split('\n')[0].replace('`', "'")  # Just first line for brevity
        
        if params:
            constructors.append(f"""
    /// {doc}
    pub fn {name}({param_str}) -> TagKind {{
        TagKind::{name}({init})
    }}""")
        else:
            # Build struct initialization with all fields
            all_inits = [
                "        id: None,",
                "        lang: None,",
                "        alt_text: None,",
                "        expanded: None,",
                "        actual_text: None,",
                "        location: None,",
                "        placement: None,",
                "        writing_mode: None,",
                "        title: None,"
            ]
            
            # Add optional fields
            if 'optional' in attrs:
                for attr in attrs['optional']:
                    all_inits.append(f"        {attr['name']}: None,")
            
            all_inits_str = '\n'.join(all_inits)
            
            constructors.append(f"""
    /// {doc}
    pub const {name}: TagKind = TagKind::{name}({struct_name} {{
{all_inits_str}
    }});""")
    
    return f"""
/// Convenience constructors for tags.
pub struct Tag;

impl Tag {{{''.join(constructors)}
}}"""

def generate_rust_code() -> str:
    """Generate the complete Rust code."""
    # File header
    header = """// Generated tag definitions for PDF structure elements.
// This file is auto-generated by scripts/generate_tags.py - DO NOT EDIT MANUALLY!

// Types are imported in tag.rs
"""
    
    # Generate all components
    components = [
        header,
        generate_tag_trait(),
    ]
    
    # Generate all tag structs
    for tag in TAG_SCHEMA['tags']:
        components.append(generate_tag_struct(tag))
        components.append(generate_tag_trait_impl(tag))
    
    # Generate TagKind enum
    components.append(generate_tag_kind_enum(TAG_SCHEMA['tags']))
    
    # Generate convenience constructors
    components.append(generate_convenience_constructors())
    
    return '\n'.join(components)

def main():
    """Main entry point."""
    rust_code = generate_rust_code()
    
    # Write to file
    output_path = "src/interchange/tagging/generated.rs"
    with open(output_path, 'w') as f:
        f.write(rust_code)
    
    print(f"Generated {output_path}")

if __name__ == "__main__":
    main()