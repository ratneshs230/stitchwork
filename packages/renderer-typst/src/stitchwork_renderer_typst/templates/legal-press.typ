// Stitchwork imprint: legal-press
// 6×9 trade non-fiction template. Typst 0.14+.

#set document(title: "{{TITLE}}", author: "{{AUTHORS}}")
#set page(
  paper: "us-letter",
  width: 6in,
  height: 9in,
  margin: (top: 0.85in, bottom: 0.95in, inside: 0.75in, outside: 0.6in),
  binding: left,
)
#set par(justify: true, leading: 0.72em, first-line-indent: 1em)
#set text(font: ("Source Serif Pro", "Source Serif 4", "Georgia", "Times New Roman"), size: 10.5pt)
#set heading(numbering: none)

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(2em)
  text(size: 22pt, weight: "bold")[#it.body]
  v(1.2em)
}
#show heading.where(level: 2): it => {
  v(1em)
  text(size: 14pt, weight: "semibold")[#it.body]
  v(0.4em)
}
#show heading.where(level: 3): it => {
  v(0.6em)
  text(size: 12pt, weight: "semibold")[#it.body]
  v(0.2em)
}

#show footnote.entry: set text(size: 9pt)
#show link: it => underline(it)

// Title page
#align(center)[
  #v(2.5in)
  #text(size: 28pt, weight: "bold")[{{TITLE}}]
  #v(0.6em)
  #text(size: 13pt, style: "italic")[{{SUBTITLE}}]
  #v(2em)
  #text(size: 12pt)[{{AUTHORS}}]
  #v(0.4em)
  #text(size: 9pt, fill: luma(120))[legal-press · Stitchwork]
]
#pagebreak()

// Body
{{BODY}}
