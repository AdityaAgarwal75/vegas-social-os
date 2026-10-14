# Complete Flow execution contract — 14 October 2026

The accepted product direction prioritizes reliable Flow execution before expanding the content platform. This checkpoint packages a complete execution dependency, replacing the independent experimental submission algorithm. It does not claim that the entire production workflow is validated.

## One execution path

The normal VPS installer invokes `scripts/install-flow-engine.sh`. It fetches the exact revision in `deploy/flow-engine/lock.json`, checks that revision, applies reviewed compatibility changes, installs the lockfile dependencies with lifecycle scripts disabled, and compiles the complete source. Repeated installation of the same contract is a no-op; a conflicting destination is preserved and rejected.

The dashboard launches its own private Chrome and graphical desktop per new account. A managed engine attaches to that Chrome over loopback CDP. The attach-only patch prevents the dependency from silently launching another Chrome/profile. The app's service owns its subprocesses and private state. Existing imported services retain their already-running engine, profiles and desktop; they are not replaced during onboarding.

Scene production, standalone clips and diagnostic images use the same local API adapter. Legacy independent generation/download code is disabled and removed. Model discovery uses the idle browser and refuses active or unresolved app work. Generation calls use explicit settings, one output, zero retries and durable job identifiers. Campaign keyframes still come from native host image tools with verified byte transfer.

## Dependency provenance

Complete dependency: https://github.com/GTAI-1/flow-mcp.git, pinned `06ceeab230da519a7686a12c6c9711eae20ea165`. Its package manifest declares ISC; this revision has no standalone LICENSE file. The installer preserves the complete source/package metadata and writes `.vso-source.json`; the project does not relabel that engine as original Vegas code. Local compatibility changes are retained in `deploy/flow-engine/`. Skill packs have their separate MIT notices in `third_party/NOTICE.md`.

The private source modifications studied on the existing VPS cover Linux narration, output path containment, durable queue checkpoints, exact tile rename and settings popover behavior. Additional managed changes verify radio selection, apply aspect after selecting the model, recheck the final quote immediately before submission, and prohibit fallback browser launch.

## Feature acceptance matrix

| Operation | Implementation | Evidence / remaining test |
| --- | --- | --- |
| New private profile + remote login browser | App-owned browser/desktop and complete attached engine | Disposable signed-out infrastructure checks; owner sign-in remains personal |
| Video model/duration/resolution/aspect/output controls | Complete engine's real settings function | 33 no-credit control probes across five signed-in accounts; all four families, Omni durations/resolutions, both aspects and compatible mode selection |
| Text, first/end frames, ingredients | One scene contract, explicit model validation | Settings mode verified; real attachment/render trials still required |
| Final credit guard | Settings/quote rechecked after references and prompt, before Generate | Compiled source contract; positive-quote cap-zero guards previously stopped; new final guard needs controlled rendering acceptance |
| Exact generation/download | Complete engine job queue + original result import | Historical download/import passed; newly packaged paid rendering remains unverified |
| Restart recovery | Private checkpoint; interrupted jobs suspended without automatic submission | Disposable synthetic queue test; synthetic evidence is not real render recovery |
| Continuity handoff | Last retained frame extracted locally from imported MP4 | Synthetic two-color media test; no source overwrite |
| Extend | Not wired into Social OS | Current Google model/clip compatibility and capped execution needed |
| Video editing / upscale | Not wired into Social OS | Quote/eligibility and exact-output recovery must be verified before exposure |
| Avatars, characters, custom voices, tools, Agent | Not wired into Social OS | Separate capability and authorization contracts required |
| Complete Reel / publication | Existing planning, assembly and publisher adapters | Real end-to-end creative and official publishing trials remain pending |

Official feature reference: https://support.google.com/flow/answer/16352836?hl=en. Documentation is not an account capability guarantee. This audit observed fixed 8s Veo settings despite documented shorter durations. Unsupported controls must fail before generation; no silent substitution.

No credits or social posts were created by these control probes. Source tests, browser fixtures, actual UI controls, media recovery and newly rendered output are separate kinds of evidence.
