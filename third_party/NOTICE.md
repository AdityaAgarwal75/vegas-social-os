# Third-party Flow craft materials

`flow-video-producer/` is a byte-preserved portable skill snapshot from zysilm/video-producer-skill, commit b02ae80e438526ecb906009d5faf0e397037554f, MIT, copyright 2026 zysilm-ai.

`flow-scripting/` is a byte-preserved selected documentation snapshot from agbelemi/google-flow-scripting-skill, commit 6e97dbb280c8349b7757210c061888817e0cbd1f, MIT, copyright 2026 Agbelemi. It is not a standalone installation; follow Vegas's adapter.

Each folder includes its upstream LICENSE. `vso/continuity.py` adapts last-retained-frame index arithmetic from the producer's `scripts/extract_frame.py`; the MIT notice remains in `flow-video-producer/LICENSE`. Other runtime modules remain original Vegas implementations. See docs/FLOW-SKILL-INTEGRATION.md for active behavior and overrides.

The complete browser execution dependency is installed separately from the exact source revision in `deploy/flow-engine/lock.json`. Its package manifest declares ISC; that revision has no standalone LICENSE file. Original source/package metadata and compatibility changes are preserved. See docs/FLOW-EXECUTION-CONTRACT.md. This dependency is not represented as original Vegas source.

## Higgsfield skill source

`higgsfield-skills/` preserves the eight Higgsfield skill folders plus supporting root documentation from https://github.com/higgsfield-ai/skills at f83af0bc1d937c8119099a11f8ebbf5e6fb99819. MIT, copyright 2026 Higgsfield AI. LICENSE and per-file SHA-256 provenance are included. These are reference snapshots, not auto-executed installers or a self-hosted Higgsfield service. Vegas recipes, dashboard, previews and adapter are original work. Provider images, branding and private templates were not copied.

## Horizon UI visual system

Vegas Studio's visual system adapts the official free Horizon UI source (https://github.com/horizon-ui/horizon-ui-chakra), pinned at 27a99f9fb391e9da126e91cf109b3afd953fb58b. MIT, copyright 2023 Horizon UI. The license and selected source files are byte-preserved under `horizon-ui/`, with SHA-256 provenance. The Python gateway and native JavaScript application keep their existing runtime; no third-party React/Chakra dependency is required. The Vegas Studio name and V mark are original branding. DM Sans is distributed under its SIL Open Font License at `web/fonts/OFL.txt`.
