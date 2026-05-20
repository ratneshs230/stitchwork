// Stitchwork imprint: kitchen-table
// 5.5×8.5 trade non-fiction. Slightly more intimate.

#set document(title: "{{TITLE}}", author: "{{AUTHORS}}")
#set page(width: 5.5in, height: 8.5in, margin: 0.7in)
#set par(justify: true, leading: 0.7em, first-line-indent: 1em)
#set text(font: ("EB Garamond", "Garamond", "Georgia"), size: 10.5pt)
#set heading(numbering: none)

#show heading.where(level: 1): it => { pagebreak(weak: true); v(2em); text(size: 22pt, weight: "bold")[#it.body]; v(1em) }
#show heading.where(level: 2): it => { v(1em); text(size: 13pt, weight: "semibold")[#it.body]; v(0.3em) }

#align(center)[
  #v(2.5in)
  #text(size: 26pt, weight: "bold")[{{TITLE}}]
  #v(0.4em)
  #text(size: 12pt, style: "italic")[{{SUBTITLE}}]
  #v(1.5em)
  #text(size: 11pt)[{{AUTHORS}}]
]
#pagebreak()

{{BODY}}
