---
ddx:
  id: truss.design-system
  type: design-system
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.prd
      kind: informed_by
    - id: truss.brand-voice
      kind: informed_by
---
# DESIGN.md — Truss microsite

## Design brief

Create an editorial developer microsite that makes Truss understandable in one screen and inspectable in one session. Audience: PostgreSQL platform engineers. Primary path: overview → model → evidence → source. Success: readers can distinguish Truss's design from its experiments and find the governing artifacts without guessing. The brand voice is specified in `brand-voice.md` before implementation.

The visual idea is an engineering field sheet: warm paper, ink, restrained rust accents and an original truss diagram. Avoid cloud-console chrome and decorative stock imagery. The diagram communicates the schema/storage/compiler division and has a text alternative. No graphic claims that the runtime is complete.

## Navigation and Active State

Four destinations: Overview, Model, Evidence and Start here. A persistent header exposes all four, followed by Source. Each current link carries `aria-current="page"`; CSS derives a rust underline and heavier weight from that attribute. Footer links support continuation. Mobile navigation wraps without hiding destinations. A keyboard-visible skip link reaches main content.

## Visual Hierarchy

Home opens with a development label, a large two-line headline, an explanatory paragraph and two calls to action. A structural diagram occupies the second column. An ordered three-part thesis follows, then a candid status band. Interior pages use a narrow reading column and generous section separation. Headline width is bounded; body copy stays within 68 characters. Diagram labels are real text.

## Interaction States

Links underline on hover. Keyboard focus has a 3px rust outline with offset. Current state is semantic and visible. Static pages have no loading, disabled, form or asynchronous states. Small screens stack the hero and thesis; reduced motion requires no special behavior because no animations are used.

## Tokens

Color: paper #f5f2e9, ink #192d2a, muted #50625b, rust #a83d24, pale #e6e9de, rule #bdc7bb. Typography: Georgia display, system sans body, system monospace labels. Headline clamp(48px,7vw,96px), interior title clamp(40px,5vw,64px), h2 30px, body 18px/1.65, labels 12px. Spacing: 8/16/24/32/48/64/96px. Maximum canvas 1240px; reading width 760px. Corners remain square; rules and structural lines provide grouping.

## Content and accessibility

Use the brand voice's claim ladder. The development label is visible before the main promise. Text links explain their destinations. Maintain readable contrast, meaningful heading order, keyboard access and usable layouts at 390px and 1440px. Every authored page displays an Innsigle colophon that identifies model-primary composition and signature scope.

## Non-Goals

This interface system excludes runtime architecture, data flow, component internals and architecture decisions. The site is an evaluation publication, not a graph admin UI or product runtime. Deployment/signing operations belong in the microsite runbook.
