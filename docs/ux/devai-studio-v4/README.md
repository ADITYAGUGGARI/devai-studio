# DevAI Studio UX/UI handoff v4

Start with Executive-Summary.md and qa/review.md. This project contains design and engineering specifications; it does not implement or publish the application.

## Authority order

1. Latest user requirement: AI creates full images and Reels autonomously, with varied backgrounds and concepts. No required manual layout prompts.
2. handoff/ai-creative-autopilot.md and handoff/editor-contracts.md.
3. contracts/existing-api.md for source-verified current routes; required-contracts.md and contract-addenda.md for proposed capabilities.
4. Screen, interaction, state, accessibility and design-token specifications.
5. Visual references. Written behavior and tokens remain authoritative.

## Contents

| Folder | Deliverable |
|---|---|
| audit | Repository UX audit and prior design provenance |
| architecture | Sitemap, web routes, guards, redirects and native destinations |
| workflows | Complete A–O journeys and decision diagrams |
| design-system | JSON/CSS tokens, typography, sizing and contrast measurements |
| components | Reusable component props, variants, behavior and accessibility |
| screens | Individual desktop/native screen contracts and machine-readable index |
| interactions | Exact control operations, dialogs, sheets and notifications |
| states | Workflow transitions and state UI treatments |
| visuals | Separate SVG/PNG screen, state and dialog artboards |
| contracts | Existing API audit and explicitly proposed backend contracts |
| handoff | Editors, creative autopilot, persistence, jobs and implementation roadmap |
| accessibility | Web/native accessibility, responsive and keyboard specifications |
| acceptance | Deterministic fixtures, concrete production cases and control tests |
| qa | Requirement, control and state coverage; validation results and open release gates |

Open DevAI-Studio-UX-Gallery.html to filter visual designs by platform, screen and state. Open DevAI-Studio-Engineering-Handoff.html for the consolidated specifications. The archive includes editable vectors, token files, individual specifications and machine-readable indexes.

Artboard media is illustrative test content, not a production template or an actual generated post. iOS boards use physical viewports; long forms scroll as documented. Runtime safe areas, Dynamic Type and responsive rules must be implemented.

Generation, review and publication are separate authorizations. Each format approves independently. Scheduled media and captions stay frozen; uncertain publishing outcomes stay locked until reconciled. Paid regeneration uses an explicit budget confirmation. No automatic publishing is implied.


## Revision3 additions

Authoritative product loop: handoff/product-scope-v3.md. Premium styling: handoff/visual-quality-v3.md and design-system/polish-v3.md. Raster deviations: qa/raster-reconciliation.md. Use DevAI-Studio-Workflow-Blueprint.html to inspect each control's trigger,API,nextdestination,success,errorandrecovery. qa/workflow-visual-coverage.csv maps all A–O workflows to desktop/iOS andstate design artifacts. Prior scope remains intact.


## Revision 4 visual refinement

Current visual authority: design-system/polish-v4.md and the updated JSON/CSS token files. See handoff/visual-refinement-v4.md for screen changes and validation boundaries. The default gallery shows refreshed Build designs; older AI raster references require selecting Style references. All earlier product scope and control behavior are retained.


## GitHub download distribution

The repository gallery references bundled PNGs and opens locally after cloning. The original self-contained gallery and full ZIP are preserved byte-for-byte as numbered parts in downloads/. See downloads/README.md and run restore-downloads.py to restore both files with checksum verification. This packaging difference does not change the designs or product behavior.
