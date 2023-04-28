<!-- markdownlint-disable -->

<style>
.bg-primary { background-color: var(--md-accent-fg-color--transparent); }
ol.loweralpha { list-style: lower-alpha; }
ol.upperalpha { list-style: upper-alpha; }
ol.lowerroman { list-style: lower-roman; }
ol.upperroman { list-style: upper-roman; }
</style>


# MyST MarkDown Typography

MyST is a strict superset of the [CommonMark syntax specification](https://spec.commonmark.org/).
It adds features focussed on scientific and technical documentation authoring, as detailed below.

## Headings

Markdown syntax denotes headers starting with between 1 to 6 #.

<div class="results">

```{code-block} myst
### Heading Level 3
```

<div class="result">

### Heading Level 3

</div></div>

Note, that headings that are not at the root level of the document
will not be included in the table of contents.
Using the [attrs_block](#syntax/attributes/block) extension,
you can also add classes to headings

<div class="results">

```{code-block} myst
> {.bg-primary}
> ### Paragraph heading
```

<div class="result">

> {.bg-primary}
> ### Paragraph heading

</div></div>

```{seealso}
To structure single and multiple documents into table of contents, see the [organizing content section](#organising-content).

To reference a heading in your text, see the [cross-referencing section](#syntax/referencing).
```

## Paragraphs

Paragraphs are block of text separated by a blank line.

Using the [attrs_block](#syntax/attributes/block) extension,
you can also add classes to paragraphs:

<div class="results">

```{code-block} myst
{.bg-primary}
Here is a paragraph with a class to control its formatting.
```

<div class="result">

{.bg-primary}
Here is a paragraph with a class to control its formatting.

</div></div>

## Thematic breaks

You can create a thematic break, to break content between themes, using three or more `*`, `-`, or `_` characters on a line by themselves.

<div class="results">

```{code-block} myst

* * *
```

<div class="result">

* * *

</div></div>

## Inline Text Formatting

Standard inline formatting including bold, italic, code, as well as escaped symbols and line breaks:

<div class="results">

```{code-block} myst
**strong**, _emphasis_, `literal text`, \*escaped symbols\*
```

<div class="result">

**strong**, _emphasis_, `literal text`, \*escaped symbols\*

</div></div>

The [strikethrough](syntax/strikethrough) extension allows you to add strike-through text:

<div class="results">

```{code-block} text
~~strikethrough with *emphasis*~~
```

<div class="result">

```{only} html
~~strikethrough with *emphasis*~~
```

</div></div>

The [smartquotes](syntax/smartquotes) and [replacements](syntax/replacements) extensions can improve the typography of common symbols:

<div class="results">

```{code-block} myst
Smart-quotes 'single quotes' and "double quotes".

+-, --, ---, ... and other replacements.
```

<div class="result">

Smart-quotes 'single quotes' and "double quotes".

+-, --, ---, ... and other replacements.

</div></div>

Using the [attrs_inline](syntax/attributes/inline) extension,
you can also add classes to inline text spans:

<div class="results">

```{code-block} myst
A paragraph with a span of [text with attributes]{.bg-primary}
```

<div class="result">

A paragraph with a span of [text with attributes]{.bg-primary}

</div></div>

## Line Breaks

To put a line break, without a paragraph, use a `\` followed by a new line. This corresponds to a `<br>` in HTML and `\\` in LaTeX.

<div class="results">

```{code-block} myst
Fleas \
Adam \
Had 'em.
```

<div class="result">

Fleas \
Adam \
Had 'em.

</div></div>

## Bullet points and numbered lists

You can use bullet points and numbered lists as you would in standard Markdown.
Starting a line with either a `-` or `*` for a bullet point, and `1.` for numbered lists.
These lists can be nested using two spaces at the start of the line.

<div class="results">

```{code-block} myst
- Lists can start with `-` or `*`
  * My other, nested
  * bullet point list!

1. My numbered list
2. has two points
```

<div class="result">

- Lists can start with `-` or `*`
  * My other, nested
  * bullet point list!

1. My numbered list
2. has two points

</div></div>

For numbered lists, you can start following lines with any number, meaning they don't have to be in numerical order, and this will not change the rendered output.
The exception is the first number, which if it is not `1.` this will change the start number of the list.

````{tip}
:title: Alternate numbering styles
:collapsible:

Using the [attrs_block](#syntax/attributes/block) extension,
you can also specify a alternative numbering styles:

<div class="results">

```{code-block} myst
{style=lower-alpha}
1. a
2. b

{style=upper-alpha}
1. a
2. b

{style=lower-roman}
1. a
2. b

{style=upper-roman}
1. a
2. b
```

<div class="result">

{style=lower-alpha}
1. a
2. b

{style=upper-alpha}
1. a
2. b

{style=lower-roman}
1. a
2. b

{style=upper-roman}
1. a
2. b

</div></div>

````

Using the [tasklist](syntax/tasklists) extension,
you can also create task lists:

<div class="results">

```{code-block} myst
- [ ] An item that needs doing
- [x] An item that is complete
```

<div class="result">

- [ ] An item that needs doing
- [x] An item that is complete

</div></div>

## Subscript & Superscript

For inline typography for subscript and superscript formatting,
the `sub` and `sup` {{role}}, can be used respectively.

<div class="results">

```{code-block} myst
H{sub}`2`O, and 4{sup}`th` of July
```

<div class="result">

H{sub}`2`O, and 4{sup}`th` of July

</div></div>

## Quotations

Quotations are controlled with standard Markdown syntax, by inserting a caret (>) symbol in front of one or more lines of text.

<div class="results">

```{code-block} myst
> We know what we are, but know not what we may be.
```

<div class="result">

> We know what we are, but know not what we may be.

</div></div>

Using the [attrs_block](#syntax/attributes/block) extension,
you can also add an `attribution` attribute to a block quote:

<div class="results">

```{code-block} myst
{attribution="Hamlet act 4, Scene 5"}
> We know what we are, but know not what we may be.
```

<div class="result">

{attribution="Hamlet act 4, Scene 5"}
> We know what we are, but know not what we may be.

</div></div>

## Definition lists and glossaries

Using the [definition lists](syntax/definition-lists) extension,
you can define terms in your documentation, using the syntax:

<div class="results">

```{code-block} myst
Term 1
: Definition

Term 2
: Longer definition

  With multiple paragraphs

  - And bullet points

```

<div class="result">

Term 1
: Definition

Term 2
: Longer definition

  With multiple paragraphs

  - And bullet points

</div></div>

Using the [attrs_block](#syntax/attributes/block) extension,
you can also add a `glossary` class to a definition list, that will allow you to reference terms in your text using the [`term` role](syntax/roles):

<div class="results">

```{code-block} myst
{.glossary}
my term
: Definition of the term

{term}`my term`
```

<div class="result">

{.glossary}
my term
: Definition of the term

{term}`my term`

</div></div>

## Field lists

Using the [field lists](syntax/fieldlists) extension,
you can create field lists, which are useful in source code documentation (see [Sphinx docstrings](https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#info-field-lists)):

<div class="results">

```{code-block} myst

:param arg1: A description of arg1
:param arg2: A longer description,
    with multiple lines.

    - And bullet points
:return: A description of the return value
```

<div class="result">

:param arg1: A description of arg1
:param arg2: A longer description,
    with multiple lines.

    - And bullet points
:return: A description of the return value

</div></div>

## Comments

You may add comments by putting the `%` character at the beginning of a line. This will
prevent the line from being parsed into the output document.

For example, this won't be parsed into the document:

```{code-block} myst
% my comment
```

````{warning}
:title: Comments split paragraphs
:collapsible:

Since comments are a block-level entity, they will terminate the previous block.
In practical terms, this means that the following lines
will be broken up into two paragraphs, resulting in a new line between them:

<div class="results">

```{code-block} myst
a line
% a comment
another line
```

<div class="result">

a line
% a comment
another line

</div></div>

````

## Footnotes

Footnotes use the [pandoc specification](https://pandoc.org/MANUAL.html#footnotes).
Their labels **start with `^`** and can then be any alphanumeric string (no spaces), which is case-insensitive.

- If the label is an integer, then it will always use that integer for the rendered label (i.e. they are manually numbered).
- For any other labels, they will be auto-numbered in the order which they are referenced, skipping any manually numbered labels.

All footnote definitions are collected, and displayed at the bottom of the page (in the order they are referenced).
Note that un-referenced footnote definitions will not be displayed.

<div class="results">

```{code-block} myst
- This is a manually-numbered footnote reference.[^3]
- This is an auto-numbered footnote reference.[^myref]

[^myref]: This is an auto-numbered footnote definition.
[^3]: This is a manually-numbered footnote definition.
```

<div class="result">

- This is a manually-numbered footnote reference.[^3]
- This is an auto-numbered footnote reference.[^myref]

[^myref]: This is an auto-numbered footnote definition.
[^3]: This is a manually-numbered footnote definition.

</div></div>

Any preceding text after a footnote definitions, which is
indented by four or more spaces, will also be included in the footnote definition, and the text is rendered as MyST Markdown, e.g.

<div class="results">

```{code-block} myst
A longer footnote definition.[^mylongdef]

[^mylongdef]: This is the _**footnote definition**_.

    That continues for all indented lines

    - even other block elements

    Plus any preceding unindented lines,
that are not separated by a blank line

This is not part of the footnote.
```

<div class="result">

A longer footnote definition.[^mylongdef]

[^mylongdef]: This is the _**footnote definition**_.

    That continues for all indented lines

    - even other block elements

    Plus any preceding unindented lines,
that are not separated by a blank line

This is not part of the footnote.

</div></div>

```{important}
Although footnote references can be used just fine within directives, e.g.[^myref],
it is recommended that footnote definitions are not set within directives,
unless they will only be referenced within that same directive:

This is because, they may not be available to reference in text outside that particular directive.
```

By default, a transition line (with a `footnotes` class) will be placed before any footnotes.
This can be turned off by adding `myst_footnote_transition = False` to the config file.
