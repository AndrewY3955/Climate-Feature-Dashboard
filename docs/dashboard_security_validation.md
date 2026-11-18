# Dashboard security and accessibility validation

## Scope

The production dashboard is a public, static GitHub Pages site. It serves HTML, CSS, JavaScript, and a read-only JSON data payload. It has no login, server-side write endpoint, database, user-submitted form, or private data store. The local Python prototype is a separate loopback-only server and adds response headers in `climate_dashboard/dashboard.py`.

## Controls applied to the static site

- A restrictive Content Security Policy (CSP) is declared in an early `meta http-equiv` element. It limits scripts, styles, fonts, and data connections to the site's own origin, allows only the embedded decorative data-URI image source, blocks objects, and disallows a base URL override.
- JavaScript and CSS are loaded as same-origin external files; no inline script or style blocks are required.
- Source and DOI links are created only for HTTPS URLs and open with `rel="noopener noreferrer"`.
- The dashboard has no form submission or state-changing browser endpoint.
- The interface exposes skip navigation, visible keyboard focus, semantic tables, labeled controls, live result summaries, and horizontally scrollable data regions.
- Security-control status is derived from the generated register and checked against the expected nine unique controls: six implemented in their stated scope, one documented manual review, and two recommended/not deployed.

## GitHub Pages response-header limitation

GitHub Pages does not provide this repository with a supported mechanism for setting arbitrary HTTP response headers. The CSP meta policy is therefore a browser-enforced defense-in-depth measure, not an HTTP CSP response header. Meta-delivered CSP cannot enforce every header-only directive; in particular, `frame-ancestors` must be delivered as an HTTP header. This project does not claim that clickjacking protection, HSTS, `X-Content-Type-Options`, or `Referrer-Policy` have been configured by this repository at the edge. GitHub Pages manages its own transport and hosting headers.

If the project is moved behind a configurable reverse proxy/CDN, configure response headers there, including an HTTP CSP with `frame-ancestors 'none'`, HSTS, `X-Content-Type-Options: nosniff`, and an appropriate `Referrer-Policy`. Do not add unsupported meta equivalents and describe them as response headers.

## Validation performed and limitations

The CI suite checks the CSP declaration, absence of inline script/style blocks, HTTPS-only external-link construction, status-register invariants, semantic/live-status markup, keyboard-focus styling, and narrow-screen layout rules. Browser QA exercises navigation, research-paper selection, records search, security-control filtering, viewport sizes, keyboard traversal, runtime exceptions, and automated accessibility rules.

This is a scoped, non-destructive security review of a static classroom application. It is not a penetration test of an authenticated production service: there is no authenticated service, write API, or server-side application to attack. No credential attack, destructive payload, denial-of-service test, or intrusive scanner is run against GitHub Pages. A matching SHA-256 manifest is not an authorization mechanism and does not prove source accuracy.

Automated accessibility checks do not replace testing with actual assistive technology. NVDA, JAWS, VoiceOver, and mobile screen-reader behavior require manual testing on their supported operating systems. Automated color-contrast rules are run against rendered pages where the browser test runner is available; any untested browser/assistive-technology combination remains explicitly unverified.
