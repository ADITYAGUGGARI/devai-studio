# Focused studio workflow

The previous navigation mixed source discovery, manual input, source excerpts, job logs, drafts, and administration. The redesign uses progressive disclosure and a single next action for each stage. A built-in AI image-generation tool produced a four-screen mobile wireframe as the visual reference; its example story text is conceptual design content, never production research. Generated reference artwork is not committed.

## Mobile navigation

| Destination     | Purpose                                                       | Secondary screens/actions                                                 |
| --------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Today           | Recommended next step, three status counts, two recent drafts | Activity and Settings                                                     |
| Discover        | Compact ranked story cards, Queue/Approved/Archived filters   | Search, Add source, Story details                                         |
| Story details   | Source link and evidence review                               | Sticky verify/approve/generate action; collapsed priority/archive options |
| Library         | Carousel cards and All/Drafts/Review/Approved filters         | Review carousel                                                           |
| Review carousel | One image at a time, thumbnail rail, focused next action      | Slides, Copy, Approval, History sections                                  |
| Publishing      | Review-ready/approved content and existing schedules          | Publication controls inside Approval; cancellation retained               |
| Activity        | Durable jobs with Active/Needs attention/History filters      | Expand diagnostics, retry eligible jobs, open generated drafts            |
| Settings        | Account and service overview                                  | Summary/Schedule/Accounts/Usage sections; role-sensitive controls         |

Primary actions use lilac; secondary tools use neutral bordered surfaces. Cards retain generous spacing, touch targets are at least 44 points, full source evidence stays accessible, and topic/approval controls keep their existing server authorization. Pull-to-refresh updates Today, Discover, Library and Activity. Topic decisions and review section transitions are separated from server diagnostics. Publishing always remains gated by human approval.

## Web navigation

The desktop redesign uses a separate AI-generated two-screen reference for research and the carousel editor. The reference is conceptual; all production stories, evidence and images remain backed by real APIs. The existing React application was retained.

A persistent sidebar separates Today, Research, Library and Publishing from Activity and Settings. Today recommends one next action. Research is a ranked list beside a selected-story evidence/approval pane with search/category/archive filters; manual source entry opens a native dialog with Escape dismissal and focus restoration. Daily status and topic maintenance are disclosures. Library shows real image covers with search and status filters.

The desktop editor keeps a vertical slide rail, a full-image canvas and a right inspector with Slide, Copy, Approval and History sections. Arrow keys navigate slides; export remains in the heading, and submission opens Approval. Human approval, validation and version invalidation remain enforced. Publishing separates ready, review, published and scheduled content; scheduling is disclosed per approved version. Settings separates health, daily research, provider usage and accounts. Narrow screens stack these workspaces without changing the native iOS app.

## Verification

Browser tests exercise the redesigned navigation and prove that topic approval, generation, review, retry, source diagnostics and publishing guards still work. Connected browser tests use real FastAPI/PostgreSQL and real generated images in an isolated test schema. The running iOS Expo Go carousel screen was visually inspected through simulator screenshots. Native automated Maestro acceptance remains separately tracked; a screenshot does not establish every native journey.

Xcode 27 manages simulator screens through Device Hub (`Xcode > Open Developer Tool > Device Hub`). The absence of a standalone Simulator app is not evidence of a broken Xcode installation.

## Background interactions and edits

A second AI-generated interaction board explored running, completed and failed tasks and saved feedback. The implemented task strip is in normal document flow so it cannot cover editor controls. It remains visible across workspaces, lets people expand diagnostics and open the resulting draft/research queue, and preserves uncertain-publication reconciliation. Starting research or generation retains the current screen. Activity provides explicit filters. Native iOS navigation is unchanged.

Editor navigation and slide changes protect unsaved input. Saves preserve pending edits in other sections; unsaved input blocks actions that would operate on an older saved version. Mutation feedback is dismissible, and form validation points to the invalid field without closing its dialog. Publishing checks configuration before enabling its actions.
