# Pinned Flow skill integration

Reviewed 14 October 2026. The operator asked to reuse premade skills. Two MIT-licensed documentation packs are included directly, with their original attribution. Vegas's active `skills/flow-production/SKILL.md` maps them to the installed tool registry and current constraints.

| Source | Pinned commit | Included/use |
| --- | --- | --- |
| https://github.com/zysilm/video-producer-skill | b02ae80e438526ecb906009d5faf0e397037554f | Complete portable skill folder, references and optional scripts: scene/segment manifests, retained-frame chaining, exact-download checks |
| https://github.com/agbelemi/google-flow-scripting-skill | 6e97dbb280c8349b7757210c061888817e0cbd1f | Selected skill, orchestrator, assets, continuity, ads and dated feature documentation: self-contained prompts and identity/state locks |

Also researched https://github.com/ffroliva/gflow-cli at 1fe635593897ec464ef9075cfc2e7f61c9a4f15f and https://github.com/Hao0321/ai-media-generator at edc8aa5227f4a58f9a3a88c7bf3e99bdda2a4361. These are not installed as competing runtime drivers. gflow's host-specific limitations and persist-before-spend/one-profile serialization are useful research; its private API/auth path is not our implementation.

## Adaptations that matter

- Official model data and actual account controls override dated defaults. This installation currently exposes fixed 8s Veo controls, whereas current documentation describes a broader rollout.
- Some producer examples recommend Quality with elements and default landscape/8 seconds. Our adapter rejects Quality ingredients and uses the operator's actual settings.
- Upstream scene/keyframe generators can use Flow images. Campaign keyframes here remain separate native host images. A montage/contact sheet is not substituted for approved individual scene images.
- Upstream phase-by-phase confirmations and automatic error retries are adapted to existing user authorization, explicit caps and original-job recovery. No duplicate uncertain submission.
- Third-party source files are inert references unless a supported Vegas operation invokes an adapted helper. Their presence does not install Claude tooling, gflow, a second browser, a paid API, or extra provider permissions.
- `continuity_frame` adapts the producer's last-retained-frame arithmetic to FFmpeg/ffprobe. It accepts only private imported MP4s, leaves the original untouched, imports a checksummed PNG and records provenance. No MoviePy dependency is required by the runtime.

Current account menus/quote guards and local media validation are distinct from paid output quality. Extend, conversational video edit, advanced voice controls, project characters and upscaling remain research opportunities, not implemented claims.
