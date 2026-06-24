---
name: slides
version: "1.0.0"
description: |
  Presentation/slide deck generation. Create PPTX files with title slides,
  content slides, charts, images, and speaker notes. Uses python-pptx for
  native PowerPoint format. Supports multiple themes and layouts.
license: MIT
compatibility: Python 3.10+ with python-pptx, PIL (for image handling)
metadata:
  author: hermeshub
  hermes:
    tags: [slides, powerpoint, pptx, presentation, deck, keynote]
    category: documents
    requires_tools: [terminal, execute_code, image_generate]
    priority: medium
---

# Slides (PPTX) Skill

Create presentation decks natively via python-pptx. Produces real .pptx
files that open in PowerPoint, Keynote, and LibreOffice Impress.

## When to Use
- User wants a presentation, slides, or a deck created
- User wants to turn research/report content into slides
- User asks for a pitch deck, lecture slides, or summary deck
- User says "make slides", "create a presentation", "build a deck"

## Creating a Deck

    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Title slide
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Quarterly Report"
    slide.placeholders[1].text = "Q2 2026 Results"

    # Content slide with bullets
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Key Findings"
    body = slide.placeholders[1].text_frame
    body.text = "Revenue up 23 percent year over year"
    p = body.add_paragraph()
    p.text = "Customer retention at 94 percent"
    p = body.add_paragraph()
    p.text = "New market expansion on track"

    prs.save("/tmp/deck.pptx")

## Slide Types
- Title slide (layout 0): big title + subtitle
- Section header (layout 2): divider between sections
- Content/bullets (layout 1): title + bullet points
- Two-column (layout 3): comparison layout
- Image+caption (layout 8): picture with text
- Blank (layout 6): fully custom layout

## Design Guidelines
- Max 6 bullets per slide, max 8 words per bullet
- Use the title to state the slide's main point
- Speaker notes go in notes_slide (not on the slide itself)
- For charts: generate with matplotlib, save as PNG, insert as image
- Consistent color palette across all slides

## Converting Research to Slides
When turning a research report into a deck:
1. Executive summary becomes the title + first content slide
2. Each report section becomes 1-2 slides
3. Data tables become chart slides
4. Sources go on the final slide

## Qwopus-Specific Notes
- Build the outline first (one line per slide), then fill each slide
- Keep text minimal on slides — put detail in speaker notes
- Generate charts as images first, then insert (more reliable than native PPTX charts)
- Use working_memory to hold the deck structure while building
