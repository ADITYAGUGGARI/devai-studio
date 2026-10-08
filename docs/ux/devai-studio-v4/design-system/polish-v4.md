# Warm editorial design system — revision 4

This revision supersedes the visual geometry in polish-v3.md. Existing behavioral, API, research, approval and publishing requirements stay intact. The token files are authoritative. The application shell uses warm cream and forest; generated media may use any editorially appropriate palette.

## Visual grammar

- Application background #F2EDE5; primary surface #FAF7F2; grouped secondary surface #E8E0D5. Forest #173D32 for selection and primary actions, hover #245646. Peach and sage are decorative accents, not body text or unlabelled status signals.
- Inputs and outlined actionable boundaries use controlBorder #82786B. Border #CFC6BA is reserved for decorative separators. Errors use #B42332 with exact text; warnings use #966000 with icon and text. Focus remains 2px forest-hover plus 2px gap.
- Control radius 12px, grouped panel 18px, feature 20px, sheet 24px, media 10px. Buttons are 48px high, fields 52px. A 20–24px icon always sits in a 44px minimum hit area. Do not make a glyph's visual width its tap target.
- Panel elevation is 0 5px 20px rgba(32,53,45,.065). Use it only for purposeful groups, content previews and overlays. Do not wrap every paragraph in a box.
- Editorial display: Georgia/system serif fallback, 32–40px desktop, 28–34pt native. UI: Inter/system sans on web, SF semantic text styles on iOS; body 16/24px web, 17/24pt native. Artboard labels and fixture annotations sit outside the product UI. Small tab and OS-status labels follow platform conventions; important instructions must wrap and remain readable.
- Meaningful icons are supplied in components/icons.svg. Forest sidebar contains icon and text, selected warm-green background and a peach edge marker. Native roots retain the five original tabs. Child editing and reviewing screens use a navigation stack.

## Distinct layouts

| Area | Desktop | Native iOS |
|---|---|---|
| Sign-in/onboarding | Editorial artwork introduction and bounded form | Single accessible form, keyboard-aware, no tabs |
| Home | Warm welcome, workflow shortcuts, diverse actual media previews | Next action plus content card; scroll to review/jobs |
| Discover/research | Ranked evidence-first rows, score explanation and coverage rail | Ranked finding cards, search/segments, research tools view |
| Topic/evidence/claims | Reading column and source rail | Focused reading stack with source and claim tools |
| Generation | Real stages and retained output, background job actions | Stage list, separate rendering/validation continuation |
| Carousel editor | Filmstrip, complete composition canvas, inspector | Large image, slide selector and focused copy/visual tools |
| Reel editor | Vertical video, scene inspector, timing strip | Preview plus scene/script/audio entry points; rendering tools below |
| Review | Current media beside checklist and decisions | Media and checklist stack; independent output decisions |
| Publish/schedule | Frozen approved media and account/time form | Account/time form and explicit confirmation; native pickers |
| Library | Thumbnail grid and state/search controls | One readable card at a time with contextual actions |
| Activity | State-aware job list and diagnostics | Job cards and focused recovery views |
| Analytics | Metric cards and labelled data view | Metric summary and chart; comparison is a separate paired-post view |
| Settings | Purposeful section groups and context rail | Native grouped forms and section navigation |

## Media fidelity

Thumbnail cards may crop the cover for browsing; opening Preview must show the complete image or actual validated MP4. Never infer video readiness from an image. Raster style references are optional inspiration and do not define buttons or route behavior. The refreshed editable vectors, written contracts and tokens are the implementation reference.

## Overflow and states

Native continuation artboards show the rest of a scroll view or appropriate contextual tools; they do not introduce mandatory additional wizard steps. The content container ends above a persistent tab bar. Its scroll position, selected entity and text buffer persist. Destructive, paid and publishing actions still open the exact catalogue confirmation. Fields retain input on error; uncertain publication offers reconciliation, never blind Retry.

All prior states/treatments.md, accessibility rules and acceptance criteria apply. Artwork in the package is illustrative. These design references do not certify live provider execution, iOS usability or built-client accessibility.
