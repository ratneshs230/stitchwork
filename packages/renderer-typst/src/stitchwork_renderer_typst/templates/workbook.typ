// Stitchwork imprint: workbook
// 8.5×11 workbook / journal layout.

#set document(title: "{{TITLE}}", author: "{{AUTHORS}}")
#set page(width: 8.5in, height: 11in, margin: (top: 1in, bottom: 1in, inside: 1.1in, outside: 0.8in))
#set par(justify: false, leading: 0.85em)
#set text(font: ("Inter", "Helvetica Neue", "Arial"), size: 11pt)
#set heading(numbering: none)

#show heading.where(level: 1): it => { pagebreak(weak: true); v(1.5em); text(size: 24pt, weight: "bold")[#it.body]; v(1em) }
#show heading.where(level: 2): it => { v(1em); text(size: 14pt, weight: "semibold")[#it.body]; v(0.3em) }

#align(center)[
  #v(2in)
  #text(size: 32pt, weight: "bold")[{{TITLE}}]
  #v(0.4em)
  #text(size: 14pt, style: "italic")[{{SUBTITLE}}]
  #v(1.5em)
  #text(size: 12pt)[{{AUTHORS}}]
]
#pagebreak()

{{BODY}}
