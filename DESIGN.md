---
name: TANIM
description: A calm field logbook for crop planning in Luzon.
colors:
  field: "#185c39"
  field-deep: "#102f1f"
  ink: "#1a241d"
  page: "#f4f6ee"
  paper: "#fffef9"
  muted: "#53655a"
  line: "#d4e0d6"
  input-line: "#8b9d90"
  nav-active: "#e8f0e9"
  table-head: "#eef4ef"
  error-line: "#a63131"
  error-wash: "#fff2f2"
  error-ink: "#7b2020"
  success-wash: "#edf6ee"
  success-ink: "#173f2a"
  warning-line: "#9a6b15"
  warning-wash: "#fff8e7"
  warning-ink: "#62450d"
  risk-low: "#dcefe1"
  risk-moderate: "#fff2c7"
  risk-high: "#f5d9d7"
  risk-nodata: "#e7e9e8"
  map-line: "#44584a"
typography:
  display:
    fontFamily: "system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 5vw, 2.5rem)"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "system-ui, sans-serif"
    fontSize: "clamp(1.35rem, 4vw, 1.8rem)"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  cover:
    fontFamily: "system-ui, sans-serif"
    fontSize: "clamp(2.5rem, 9vw, 4.5rem)"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.03em"
  lede:
    fontFamily: "system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.5
  body:
    fontFamily: "system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  brand:
    fontFamily: "system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: "0.04em"
rounded:
  sm: "6px"
  md: "12px"
  lg: "14px"
  pill: "999px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.field}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "0.55rem 0.9rem"
  button-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.field}"
    rounded: "{rounded.sm}"
    padding: "0.55rem 0.9rem"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.field}"
    rounded: "{rounded.sm}"
    padding: "0.55rem 0.9rem"
  card:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.lg}"
    padding: "clamp(1rem, 4vw, 2rem)"
  input:
    backgroundColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "0.55rem 0.65rem"
  status-stamp:
    backgroundColor: "transparent"
    rounded: "{rounded.pill}"
    padding: "0.4rem 0.7rem"
---

# Design System: TANIM

Seed key: 995a9d63. World chosen from the direction round, built code-led on the platform core flow.

## Overview

Creative North Star: "The Field Logbook".

TANIM looks like a paper logbook kept at the farm gate, not a software dashboard. Pages sit on a pale green paper ground. Content lives on lighter paper cards with plain 1px borders. Numbers read as ruled ledger rows. Risk reads as a stamped mark with a plain label, never as a glowing badge.

The mood is calm public service. Headings speak alone, with no kicker above them. Color is quiet except for the three risk inks, which always arrive with text labels. The one motion in the system is the stamp settling when a risk or status mark appears.

Key Characteristics:

- Paper ground with paper cards, flat and border-drawn
- Ledger rows for facts, figures, and plan lists
- Stamped risk marks with plain Low, Moderate, and High labels
- System typeface with tabular numerals for all data
- One settle motion, disabled under reduced motion

## Colors

The palette is ink green on paper white, with warm risk inks used only where a level must be read at a glance.

### Primary

- Field Green (#185c39): links, primary buttons, focus rings, text selection, chart lines, and active map fills. The only strong color on a calm page.

### Neutral

- Page Ground (#f4f6ee): the app background, chosen for bright outdoor light.
- Logbook Paper (#fffef9): card and page surfaces.
- Ink (#1a241d): body text.
- Muted Sage (#53655a): secondary text, always tinted from the field hue, never gray. Passes 4.5 to 1 on paper and on all risk washes.
- Rule Line (#d4e0d6): card and row borders.
- Input Line (#8b9d90): form field borders.
- Active Wash (#e8f0e9): current nav item and selected rows.
- Table Head (#eef4ef): table header fill.

### Named Rules

The Plain Label Rule. A color fill never carries meaning alone. Every risk fill, map region, and legend mark ships with its text label next to it.

The Quiet Page Rule. Field Green is the single voice. Risk inks appear only on risk marks, map regions, and their legend.

## Typography

Display Font: system-ui (with sans-serif fallback)
Body Font: system-ui (with sans-serif fallback)
Label/Mono Font: none distinct. Data uses tabular numerals from the system stack, never monospace as decoration.

Character: a workhorse public-service voice. Headings are bold and tightly set with balanced wrapping. Body text stays near a 65 character measure for easy reading on phones.

### Hierarchy

- Display (700, clamp 1.75rem to 2.5rem, 1.15): page titles only. Letter spacing minus 0.02em, balanced wrap, max 24ch.
- Headline (700, clamp 1.35rem to 1.8rem, 1.15): section titles. Same spacing and wrap as display.
- Body (400, 1rem, 1.5): paragraphs and list text, max 65ch.
- Label (400, 0.875rem, 1.5): secondary text, form labels use semibold weight instead.

### Named Rules

The Heading Speaks Rule. No kicker or eyebrow sits above a heading. If a line adds nothing the heading does not say, delete the line.

The Data Lines Up Rule. Ratios, areas, counts, and step counts always use tabular numerals so digits align down a ledger column.

## Layout

Pages center in a reading column. Shared screens use a 42rem column inside a 72rem shell. Platform screens use a 76rem page inside a 92rem shell. Stacks gap at 1rem, with 0.9rem inside dense utility cards.

Filters lay out as auto-fitting grids that collapse to one column on narrow phones. Data tables keep a fixed layout on desktop and reflow to labeled ledgers rows under 48rem, with table headers hidden accessibly. A five item bottom bar replaces desktop nav on phones, with safe area padding.

## Elevation and Depth

The system is flat. Depth comes from borders and tonal washes, never from shadows.

### Named Rules

The One Edge Rule. A surface declares elevation once, with a border. No card pairs a 1px border with a soft shadow.

## Shapes

Cards use a large soft corner (14px). Alerts, notices, and small utility cards use 12px. Buttons, inputs, and selects use a small 6px corner. Status and suitability marks are full pills. Map regions keep round joins on their strokes. Focus rings are 3px field green with 3px offset everywhere.

## Components

### Buttons

- Shape: 6px corner, 0.55rem vertical by 0.9rem horizontal padding, semibold text, min height 2.75rem for touch.
- Primary: field green fill with white text and matching border.
- Hover and Focus: 3px field green focus ring with 3px offset. Disabled buttons wait with reduced opacity.
- Secondary: paper fill with field green text and border. Quiet: transparent with field green text and border.

### Status Stamp

The signature component. A pill with a 1px border that lands with the logbook settle motion, a short exponential ease from a slightly scaled and blurred start. Used for plan status and suitability verdicts. Suitability stamps fill with their risk ink.

### Cards and Containers

- Corner Style: 14px.
- Background: logbook paper on the page ground.
- Shadow Strategy: none, per the One Edge Rule.
- Border: 1px rule line.
- Internal Padding: clamp 1rem to 2rem shared, clamp 1rem to 1.5rem in utilities.

### Inputs and Fields

- Style: white fill, 1px input line border, 6px corner, min height 2.75rem, full width. Caret tinted field green.
- Focus: the global 3px field green ring.
- Error and Disabled: errors render as full bordered washes with the problem named beside a retry action. Disabled waits with reduced opacity.

### Notices

- Style: full 1px border in the message hue, 12px corner, tinted wash with dark text. Error, success, and warning each name the problem and the recovery.

### Ledger Rows

- Style: label on the left, value on the right, divided by a 1px rule. Values are semibold with tabular numerals. Used for plan metrics, supply facts, and simple lists.

### Navigation

- Style: text links with 0.15em underline offset. The current page gets the active wash with bold text and no underline.
- Mobile treatment: fixed five item bottom bar with a filled primary slot for the add plan action, plus an overflow sheet in paper with a 12px corner.

### Supply Map Regions

- Style: regions fill with their risk ink and draw a 0.6px map line stroke. Hover and selection deepen the stroke to field deep. Keyboard focus uses the global ring. A text region list mirrors the map so no meaning lives in color alone.

### Surface Shells

Three small shells carry the shared world onto the landing, auth, and docs surfaces. Each one reuses the card, ledger row, and button components above.

- Cover (landing): the logbook cover. A masthead with the brand wordmark, a ruled ledger list of plain facts, and signing actions for entering the app or creating an account. The cover title sets at clamp 2.5rem to 4.5rem with minus 0.03em spacing.
- Signature consent (auth): the consent line is the signature. The required consent checkbox label carries a 2px ink underline, so agreement reads as signing the logbook. Optional research consent stays a plain checkbox with no underline.
- Leaflet (docs): one card with ruled sections. Each section after the first takes a 1px rule on top with 1rem of air, so the page reads as one folded leaflet.

## Do's and Don'ts

Concrete guardrails from the built platform core. They bind new surfaces unless the user changes them.

### Do

- Do pair every risk fill with its plain text label and keep the label readable on the wash.
- Do keep body and secondary text at 4.5 to 1 or better, tinting secondary text from the field hue.
- Do theme selection, caret, focus, scrollbars, underline offset, and numerals from the palette.
- Do give headings more air above than below and let them wrap in balance.
- Do honor reduced motion by disabling the stamp settle entirely.

### Don't

- Don't put a kicker or eyebrow above a heading.
- Don't mark cards, alerts, or list items with a thick colored side border.
- Don't pair a border with a shadow on the same card.
- Don't use gradient text, glass blur, hard offset shadows, sparklines, or emoji icons.
- Don't use monospace to look technical. Reserve it for code and measurement only.
- Don't ship a raster, photo, or illustration without provenance in the shipping file.
