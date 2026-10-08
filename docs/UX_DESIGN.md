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

Overview contains one recommended next action, status counts, recent drafts and a compact link to running tasks. Research contains topic selection and collapsible daily status/manual source entry. Library contains only drafts. Activity holds job logs/retries. Existing editor, publishing and administration functionality remains available. Starting discovery or generation opens Activity so progress is visible.

## Verification

Browser tests exercise the redesigned navigation and prove that topic approval, generation, review, retry, source diagnostics and publishing guards still work. Connected browser tests use real FastAPI/PostgreSQL and real generated images in an isolated test schema. The running iOS Expo Go carousel screen was visually inspected through simulator screenshots. Native automated Maestro acceptance remains separately tracked; a screenshot does not establish every native journey.

Xcode 27 manages simulator screens through Device Hub (`Xcode > Open Developer Tool > Device Hub`). The absence of a standalone Simulator app is not evidence of a broken Xcode installation.
