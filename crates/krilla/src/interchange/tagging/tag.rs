//! Tag definitions for PDF structure elements.
//!
//! This module provides types for creating tagged PDF documents with proper semantic structure.
//! Instead of using complex macros, we now use generated code from a Python script that creates
//! individual structs for each tag type with type-safe builder methods.
//!
//! # Example
//! ```
//! use std::num::NonZeroU32;
//! use krilla::tagging::{TagGroup, TagTree};
//! use krilla::tagging::tag::{TableCellSpan, TableHeaderScope, Tag, TagId, THTag};
//!
//! let tag = THTag::new(TableHeaderScope::Row)
//!     .with_id(TagId::from(*b"this id"))
//!     .with_span(TableCellSpan::col(NonZeroU32::new(3).unwrap()))
//!     .with_headers([TagId::from(*b"parent id")].into())
//!     .with_width(250.0)
//!     .with_height(100.0);
//! let group = TagGroup::new(tag);
//!
//! let mut tree = TagTree::new();
//! tree.push(group);
//! ```

use std::num::NonZeroU32;
use smallvec::SmallVec;
use crate::geom::Rect;
use crate::surface::Location;

// Include generated tag definitions
include!("generated.rs");

/// An identifier of a tag.
#[derive(Debug, Clone, Eq, PartialEq, Ord, PartialOrd, Hash)]
pub struct TagId(pub(crate) SmallVec<[u8; 16]>);

impl<I: IntoIterator<Item = u8>> From<I> for TagId {
    fn from(value: I) -> Self {
        // Disambiguate ids provided by the user from ids automatically assigned
        // to notes by prefixing them with a `U`.
        let bytes = std::iter::once(b'U').chain(value).collect();
        TagId(bytes)
    }
}

impl TagId {
    /// Returns the identifier as a byte slice.
    pub fn as_bytes(&self) -> &[u8] {
        self.0.as_slice()
    }
}

/// The list numbering type.
#[derive(Debug, Copy, Clone, Eq, PartialEq, Hash)]
pub enum ListNumbering {
    /// No numbering.
    None,
    /// Solid circular bullets.
    Disc,
    /// Open circular bullets.
    Circle,
    /// Solid square bullets.
    Square,
    /// Decimal numbers.
    Decimal,
    /// Lowercase Roman numerals.
    LowerRoman,
    /// Uppercase Roman numerals.
    UpperRoman,
    /// Lowercase letters.
    LowerAlpha,
    /// Uppercase letters.
    UpperAlpha,
}

impl ListNumbering {
    pub(crate) fn to_pdf(self) -> pdf_writer::types::ListNumbering {
        match self {
            ListNumbering::None => pdf_writer::types::ListNumbering::None,
            ListNumbering::Disc => pdf_writer::types::ListNumbering::Disc,
            ListNumbering::Circle => pdf_writer::types::ListNumbering::Circle,
            ListNumbering::Square => pdf_writer::types::ListNumbering::Square,
            ListNumbering::Decimal => pdf_writer::types::ListNumbering::Decimal,
            ListNumbering::LowerRoman => pdf_writer::types::ListNumbering::LowerRoman,
            ListNumbering::UpperRoman => pdf_writer::types::ListNumbering::UpperRoman,
            ListNumbering::LowerAlpha => pdf_writer::types::ListNumbering::LowerAlpha,
            ListNumbering::UpperAlpha => pdf_writer::types::ListNumbering::UpperAlpha,
        }
    }
}

/// The scope of a table header cell.
#[derive(Debug, Copy, Clone, Eq, PartialEq, Hash)]
pub enum TableHeaderScope {
    /// The header cell refers to the row.
    Row,
    /// The header cell refers to the column.
    Column,
    /// The header cell refers to both the row and the column.
    Both,
}

impl TableHeaderScope {
    pub(crate) fn to_pdf(self) -> pdf_writer::types::TableHeaderScope {
        match self {
            TableHeaderScope::Row => pdf_writer::types::TableHeaderScope::Row,
            TableHeaderScope::Column => pdf_writer::types::TableHeaderScope::Column,
            TableHeaderScope::Both => pdf_writer::types::TableHeaderScope::Both,
        }
    }
}

/// The span of a table cell.
#[derive(Debug, Copy, Clone, Eq, PartialEq, Hash)]
pub struct TableCellSpan {
    /// The number of spanned rows inside the enclosing table.
    pub rows: NonZeroU32,
    /// The number of spanned cells inside the enclosing table.
    pub cols: NonZeroU32,
}

impl Default for TableCellSpan {
    fn default() -> Self {
        Self::ONE
    }
}

impl TableCellSpan {
    /// A table cell that spans only one row and column.
    pub const ONE: Self = Self::new(NonZeroU32::MIN, NonZeroU32::MIN);

    /// Create a new table cell span.
    pub const fn new(rows: NonZeroU32, cols: NonZeroU32) -> Self {
        Self { rows, cols }
    }

    /// Create a new table cell span that spans a number of rows.
    pub const fn row(rows: NonZeroU32) -> Self {
        Self {
            rows,
            cols: NonZeroU32::MIN,
        }
    }

    /// Create a new table cell span that spans a number of columns.
    pub const fn col(cols: NonZeroU32) -> Self {
        Self {
            rows: NonZeroU32::MIN,
            cols,
        }
    }

    pub(crate) fn row_span(self) -> Option<NonZeroU32> {
        (self.rows != NonZeroU32::MIN).then_some(self.rows)
    }

    pub(crate) fn col_span(self) -> Option<NonZeroU32> {
        (self.cols != NonZeroU32::MIN).then_some(self.cols)
    }
}

/// The positioning of the element with respect to the enclosing reference area
/// and other content.
/// When applied to an ILSE, any value except Inline shall cause the element to
/// be treated as a BLSE instead.
///
/// Default value: [`Placement::Inline`].
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub enum Placement {
    /// tacked in the block-progression direction within an enclosing reference
    /// area or parent BLSE.
    Block,
    /// Packed in the inline-progression direction within an enclosing BLSE.
    #[default]
    Inline,
    /// Placed so that the before edge of the element's allocation rectangle.
    /// (see "Content and Allocation Rectangles" in 14.8.5.4, "Layout Attributes")
    /// coincides with that of the nearest enclosing reference area. The element
    /// may float, if necessary, to achieve the specified placement. The element
    /// shall be treated as a block occupying the full extent of the enclosing
    /// reference area in the inline direction. Other content shall be stacked
    /// so as to begin at the after edge of the element's allocation rectangle.
    Before,
    /// Placed so that the start edge of the element's allocation rectangle
    /// (see "Content and Allocation Rectangles" in 14.8.5.4, "Layout Attributes")
    /// coincides with that of the nearest enclosing reference area. The element
    /// may float, if necessary, to achieve the specified placement. Other
    /// content that would intrude into the element's allocation rectangle
    /// shall be laid out as a runaround.
    Start,
    /// Placed so that the end edge of the element's allocation rectangle
    /// (see "Content and Allocation Rectangles" in 14.8.5.4, "Layout Attributes")
    /// coincides with that of the nearest enclosing reference area. The element
    /// may float, if necessary, to achieve the specified placement. Other
    /// content that would intrude into the element's allocation rectangle
    /// shall be laid out as a runaround.
    End,
}

impl Placement {
    pub(crate) fn to_pdf(self) -> pdf_writer::types::Placement {
        match self {
            Placement::Block => pdf_writer::types::Placement::Block,
            Placement::Inline => pdf_writer::types::Placement::Inline,
            Placement::Before => pdf_writer::types::Placement::Before,
            Placement::Start => pdf_writer::types::Placement::Start,
            Placement::End => pdf_writer::types::Placement::End,
        }
    }
}

/// The directions of layout progression for packing of ILSEs (inline progression)
/// and stacking of BLSEs (block progression).
/// The specified layout directions shall apply to the given structure element
/// and all of its descendants to any level of nesting.
///
/// Default value: [`WritingMode::LrTb`].
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub enum WritingMode {
    /// Inline progression from left to right; block progression from top to
    /// bottom. This is the typical writing mode for Western writing systems.
    #[default]
    LrTb,
    /// Inline progression from right to left; block progression from top to
    /// bottom. This is the typical writing mode for Arabic and Hebrew writing
    /// systems.
    RlTb,
    /// Inline progression from top to bottom; block progression from right to
    /// left. This is the typical writing mode for Chinese and Japanese writing
    /// systems.
    TbRl,
}

impl WritingMode {
    pub(crate) fn to_pdf(self) -> pdf_writer::types::WritingMode {
        match self {
            WritingMode::LrTb => pdf_writer::types::WritingMode::LtrTtb,
            WritingMode::RlTb => pdf_writer::types::WritingMode::RtlTtb,
            WritingMode::TbRl => pdf_writer::types::WritingMode::TtbRtl,
        }
    }
}

// Internal attribute types that are used within the crate for compatibility with existing code
pub(crate) mod internal {
    use super::*;

    /// An ordered set using binary search to find and insert items.
    #[derive(Clone, Debug, PartialEq)]
    pub struct BSet<A> {
        pub(crate) items: Vec<A>,
    }

    impl<A> BSet<A> {
        pub const fn new() -> Self {
            Self { items: Vec::new() }
        }
    }

    impl<A> std::ops::Deref for BSet<A> {
        type Target = [A];

        fn deref(&self) -> &Self::Target {
            &self.items
        }
    }

    #[derive(Clone, Debug, PartialEq)]
    pub enum Attr {
        Id(TagId),
        Title(String),
        Lang(String),
        AltText(String),
        Expanded(String),
        ActualText(String),
        HeadingLevel(NonZeroU32),
    }

    #[derive(Clone, Debug, PartialEq)]
    pub enum ListAttr {
        Numbering(ListNumbering),
    }

    #[derive(Clone, Debug, PartialEq)]
    pub enum TableAttr {
        Summary(String),
        HeaderScope(TableHeaderScope),
        CellHeaders(SmallVec<[TagId; 1]>),
        CellSpan(TableCellSpan),
    }

    #[derive(Clone, Debug, PartialEq)]
    pub enum LayoutAttr {
        Placement(Placement),
        WritingMode(WritingMode),
        BBox(Rect),
        Width(f32),
        Height(f32),
    }
}