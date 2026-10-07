# Repository guidance

Read README.md and CONTRIBUTING.md before changing this project.

- Work within the existing `api`, `web`, and `mobile` boundaries.
- Run `make check` after functional changes; use focused tests while iterating.
- Never commit `.env`, local databases, generated assets, dependency directories, or credentials.
- Mock external calls in tests. Do not publish real Instagram content as a verification step.
- Preserve approval invalidation, source attribution, and reconciliation after uncertain publishing outcomes.
- Do not report a daily workflow as active unless its running scheduler and actual behavior have been verified.
- Keep docs/roadmap.md accurate as milestones are completed or limitations found.
