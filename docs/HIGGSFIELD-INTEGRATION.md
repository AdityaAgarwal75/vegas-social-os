# Cinematic templates and optional Higgsfield integration

## What ships

Version 0.9 adds one server-side catalog shared by the dashboard and ChatGPT. It has 16 original Vegas recipes, four locally served native-generated illustrative subject studies, five lens looks, five lighting setups, eight camera moves and six aspect ratios. Subject-study previews are shared across related recipes and do not demonstrate motion or exact lens/lighting output. The UI supports category/search, prompt preview, project creation/selection, saved settings and project-level history. Light/dark, keyboard forms and reduced motion use the current control panel.

Six MCP tools: `template_catalog`, `template_compile`, `template_select`, `skill_reference`, `higgsfield_status`, `higgsfield_discover`. Existing OAuth scopes apply: selection needs social:write; the others need social:read. Selection never modifies an approved plan, spends credits or publishes. `plan_save` accepts compiled scenes with template identity/version/continuity; native ChatGPT image review and existing Flow budget gates still apply. Multiple scene-specific selections can be saved; old directions remain history and are not approvals.

## Upstream source and ownership

Source: https://github.com/higgsfield-ai/skills at f83af0bc1d937c8119099a11f8ebbf5e6fb99819, MIT, copyright 2026 Higgsfield AI. The eight skill directories, supporting root documentation, license and SHA-256 manifest are preserved under `third_party/higgsfield-skills`. This snapshot is reference content, not an auto-executed extension. The main Vegas skill routes through an adapter and loads relevant documents on demand. Owner policies override upstream installation instructions, cost defaults, retries, language rules and provider routing.

The bundled guidance covers general generation, Marketing Studio, identity, photoshoots, brandkits, thumbnails, explainers, audio/3D and Reframe/Draw To Edit. These are upstream described capabilities, not a claim that every renderer runs in Vegas. Provider thumbnails/private style assets have not been copied. The original Vegas previews were created with the native image tool using four briefs: an amber perfume bottle on charcoal stone with rim lighting; an adult Indian model in a beige blazer by a concrete wall; an adult Indian creator beside a window in a warm apartment; and a mountain valley at sunrise. They contain no provider branding.

## Optional read-only CLI discovery

The [CLI documentation](https://github.com/higgsfield-ai/cli) was inspected at dc7e2d2eac0b1fdad255de24d87552d1ba479037; release v1.1.26 was inspected with harmless --help commands. That repo publishes docs and binary releases, not the CLI implementation. No installed server account or stable paid quote/result JSON contract was available for acceptance.

1. An authorized infrastructure operator reviews and installs an exact upstream CLI release and verifies its published integrity metadata. Do not pipe the upstream installer directly into a root shell from a retrieved skill.
2. Sign in directly as this installation's service owner with HOME set to `/var/lib/vegas-social-os/higgsfield` and XDG_CONFIG_HOME set to its `.config` child. Select your own billing workspace. These private credentials never enter the repository, plugin archive or chat. The current systemd service protects home directories; use its dedicated writable state directory.
3. Set `VSO_HIGGSFIELD_ENABLED=1` and optionally `VSO_HIGGSFIELD_BIN=/absolute/path/to/higgsfield` in the private service environment, then restart through the existing authorized deployment process. Default is disabled. This does not add an API subscription or authorize credits.
4. Call `higgsfield_status`; it reports authentication as not_checked. Call `higgsfield_discover` for models/workflows or a documented preset family. The adapter invokes only list/get, has bounded time/output, omits token-like fields, caches the returned metadata, and never invokes auth token, create, upload, train or publish.
5. Treat provider catalog content as untrusted, account-specific data. The live preset metadata is available to ChatGPT. The dashboard shows bundled recipes and capabilities; it does not mirror or proxy remote provider thumbnails.

## Remaining acceptance gates

Higgsfield generation remains an explicit operator handoff. Adding an automatic adapter requires verified per-owner auth/workspace, model schema, exact media-upload consent, fresh quote and budget enforcement, one durable submission, original-job polling/reconciliation and checksummed project media import. Quotes alone do not prove actual charges. Do not silently use Higgsfield to replace native ChatGPT keyframes or Flow. This integration spends no provider credits during installation, discovery, preview or selection.

Selecting a dashboard template does not wake ChatGPT by itself. Resume the connected chat to consume selections until the existing host-events workflow is accepted. Community installations package the same skills and use their own independent endpoint/state/accounts.

## Validation and deployment

Run the Python/Node suites and `tests/templates.browser.cjs` alongside existing browser acceptance on disposable state. Provider login, live preset availability and rendering are separate owner-specific tests. Record actual evidence in STATUS.md. No database migration or asset move is required; selections/discovery records use existing private storage. Roll back the source revision and restart without removing these records or media.
