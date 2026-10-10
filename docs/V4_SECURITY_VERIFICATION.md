# Revision 4 security verification — ongoing

This is an evidence log, not production security acceptance.

## Configuration and provider access

Credentials remain server-side and outside Git. A read-only OpenAI model-catalog check using the previously configured local key returned HTTP401 on October9,2026. No secret was printed and no paid generation was requested. Live AI acceptance requires a valid key in local server configuration. Instagram credentials are absent; no real Instagram content has been published during these tests. SMTP/Apple/production account configuration and broader authorization acceptance remain outstanding.

## Dependency checks

On October9,2026, `npm --prefix web install` with the PostCSS8.5.23 override reported **zero vulnerabilities**. The Expo54-compatible native time picker is8.4.4. A compatible native `npm audit fix` did not resolve the existing toolchain advisories; no forced framework change was applied. The same PostCSS8.5.23 override reduced the native audit from36to**35findings:23high,12moderate,zero critical**. Native lint, typechecking, bundle export and simulator testing are separate checks and do not establish advisory remediation.

The override addresses the [PostCSS source-map advisory](https://github.com/advisories/GHSA-fxqj-rqcc-2cmp), which identifies8.5.23as patched. Remaining upstream issues include [braces recursion](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) and [node-forge signature verification](https://github.com/advisories/GHSA-86w9-cpqp-85rv), both listing no patched release at verification time. [image-size parser fixes](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq) are available in2.0.3, while this Expo/Metro toolchain uses1.2.1; changing that major API requires explicit compatibility implementation and testing. These findings remain unresolved and must not be reported as passed production security acceptance.

Inference from the dependency tree: these packages are primarily Node build/development tooling, rather than the Python provider-media processing path. This narrows the likely exposure but does not dismiss the findings. Keep Metro/local development services private while remediation and full security review continue.

## Verified controls

- PostgreSQL-backed workspace isolation and owner-only research schedule updates.
- Revision conflicts and durable idempotent action receipts.
- Per-studio daily scheduling reservations and retry resource locks.
- Existing human approval and publishing safeguards preserved in browser regressions.
- No real publishing used to test authorization.

Full workspace/member permissions, provider vaults, account/session security, authenticated asset access and deployment hardening remain on the implementation checklist.
