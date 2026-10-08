# Visual refinement and handoff — revision 4

User request: carry the premium warm editorial direction into the remaining plain screens, including native iOS, dialogs and recovery states. No application implementation is authorized by this revision.

## Changes delivered

The previous sparse list/form default was replaced with distinct layouts for authentication, research/discovery, topic/evidence review, generation, content creation, review, publishing, library, activity, analytics and settings. Editors retain AI artwork and gain a structured canvas/inspector shell. All existing exact screen/state/dialog references were refreshed; 25 native continuation/contextual views were added.

Long native titles wrap. Input boundaries use the validated control border. Native root content is clipped above the tab bar. Version-history titles wrap inside their card. The Reel preview is playback-only and opens the editor via Edit; it no longer displays editing tools as preview controls. Analytics comparison shows separately selected content over an age-aligned period, rather than duplicating the overview.

## Authority and retained behavior

- design-system/tokens.json and polish-v4.md define the current visual system.
- screens/*.md, interactions/interactions.json, workflows/journeys.md and state transition contracts define behavior.
- Existing vs proposed APIs remain separated. No new backend endpoint is claimed as implemented.
- Rolling 24-hour developer AI research, explainable ranked findings and all captured findings remain as specified in product-scope-v3.md.
- AI selects complete carousel artwork and Reel concepts without a required user layout prompt. Recent/scheduled visual diversity checks remain defined in ai-creative-autopilot.md.
- Carousel and Reel approval remain independent. Material edits invalidate the appropriate approval. Explicit publishing authorization and unknown-outcome locks are retained.
- The original generated raster references are marked style-only and excluded from the gallery's default Build designs view.

## Engineering usage

Open the gallery, select a screen and platform, then inspect its default, recovery, dialog and continuation views. Use the workflow blueprint for every significant control's trigger, request, success destination and error/recovery behavior. Artboard annotations are handoff notes, not text to put into the product.

Do not treat continuation views as permission to expose destructive or paid controls in an ineligible state. Apply the existing preconditions and confirmations. Root navigation, deep links, draft persistence, native safe areas, Dynamic Type and responsive rules stay authoritative.

## Validation boundary

The package receives artifact, text-width, manifest, navigation-ID and source-link checks, plus rendered visual review. Acceptance cases remain design specifications; they have not been executed against a newly implemented application. Release requires built-client, real provider/Instagram, native accessibility and usability verification. This revision is a visual design correction, not production certification.
