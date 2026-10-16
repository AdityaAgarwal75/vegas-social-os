# Vegas Studio workspace — 0.12

A social production workspace in the warm-grey / white / sage direction of the owner's supplied reference. The interface prioritizes a readable workflow over decorative animation. DM Sans remains self-hosted. Cards use a 16/20px radius scale, pill buttons and 10/12px input radii. Dark mode uses the same hierarchy in forest-tinted charcoal. Native HTML, CSS Grid and the existing dependency-free JavaScript preserve the server's installation footprint.

## Product map

| Area | Route | Purpose |
| --- | --- | --- |
| Public product page | `/` when signed out; `/about` always | Explain the workflow, setup and sign-in. Product images are screenshots of disposable sample data; no owner data is embedded. |
| Access | `/login`, `/password`, `/forgot-password`, `/help` | Existing password, private recovery and setup flows in the same visual system. |
| Overview | `/dashboard#home` | Four summaries, observed CPU/memory/storage, dated Flow balances, recent projects, upcoming releases and actual specialist activity. |
| Projects | `#projects`, `#project/ID` | Separate Images, Scene clips, Final exports and Audio sections. Script, storyboard review, revisions, selected looks, jobs and releases remain accessible. |
| Media library | `#media`, `#unassigned` | Kind filters with project grouping; older unrelated files stay in a separate assignment inbox. No inferred project membership, file moves or media deletion. |
| Shot library | `#templates` | Existing template search, settings, compiled prompts and persistent project direction. Library failure does not block other pages. |
| Planning | `#planning` | Channel strategy, concepts and saved briefs. |
| Posts & releases | `#publishing` | Ordered media, caption, destination, cover, explicit YouTube audience, tags, visibility and optional exact schedule; distinct review, scheduled, published and attention views. |
| Calendar | `#schedule` | Navigable month, day filter and separate scheduled-upload/editorial-plan filters. Display timezone is explicit. |
| Insights | `#analytics` | Saved provider observations and production job counts; no invented reach or growth. |
| Specialists / activity | `#agents`, `#activity` | Actual recorded tool/host activity, with idle and unconfirmed states. No simulated autonomous workers. |
| Connections | `#accounts`, `#flow` | Separate Instagram, Facebook Page, YouTube and Flow groups; actual IDs, linked Instagram identities and available grants. |
| Settings / system | `#setup`, `#system`, `/admin` | Provider app settings, Meta developer guide, themes, owner profile, resources and exact-operation administrator approvals. |

## Release behavior

Preparing a post creates a frozen local review record; it does not publish. UI approval, scheduling, publishing, retry/resume and Instagram deletion are separate explicit user actions through existing backend gates. A schedule must exactly match the reviewed time. Instagram public visibility/JPEG media and Reel cover restrictions, YouTube MP4/audience rules and Facebook posting permissions remain provider-specific. Existing uploads are reconciled or resumed rather than recreated. Only failed YouTube thumbnails expose a thumbnail-only retry. Supported Instagram deletion requires reviewing the account/media ID and typing that exact media ID before the existing prepare/approve/execute sequence. An unknown result is shown as unconfirmed, never treated as deleted or automatically retried.

No account consent, provider app grant, publishing authorization or automatic paid-generation capability is introduced by this frontend. Browser refreshes observe local records; Flow balance refresh remains an explicit operation.

## Resilience and accessibility

- Background polling retains focused controls and active video/private-browser sessions.
- Optional shot-library failure has its own retry state. Initial workspace failure is actionable and leaves navigation visible.
- Keyboard focus rings, skip links, semantic controls, native modal focus containment and reduced-motion behavior are supported.
- Mobile navigation includes a backdrop, Escape handling and close-on-selection. Search remains accessible on mobile.
- Project media opens original image previews and native video controls without autoplay.
- Public HTML contains only sample imagery; account APIs remain authenticated with no changes to CSRF, session, encryption or OAuth checks.

## Design sources

- Owner-supplied dashboard screenshot: visual reference, not a licensed template/code import.
- Installed `taste-skill` at revision `18dfc928b135629e0eddfdd445a06400d04ed439`: `skills/taste-skill/SKILL.md` and `skills/redesign-skill/SKILL.md`. Applied hierarchy, palette, state, responsive and anti-template audit guidance. No implementation copied; dashboard-specific judgments follow the supplied reference.
- Existing project native controls and attributed Horizon reference sources retained where relevant; current pages no longer include `horizon.css`. The legacy asset route remains available for compatibility.
- Self-hosted DM Sans and its existing OFL license. Existing Vegas SVG mark retained with the new palette.

## Verification and rollback

Run the existing Python/Node/shell checks and all four browser suites in `.github/workflows/test.yml`. `tests/workspace.browser.cjs` verifies actual local preparation, media ordering, cover/audience/tags, exact scheduling, approval/cancellation, project media filters, catalog failure isolation and public landing responsiveness. It blocks external requests and uses only disposable state under `/tmp`. These checks do not prove provider authorization or remote publishing.

Before deployment, pin the tested Git revision, preserve the previous source revision and use the service's existing interpreter/runtime environment. Restart only the Social OS gateway, verify `/health`, public assets, login and unauthenticated API rejection. Keep `/var/lib/vegas-social-os`, provider browser profiles and developer credentials untouched. Roll back to the recorded source revision and restart the same service if health or route checks fail. No database migration is required.
