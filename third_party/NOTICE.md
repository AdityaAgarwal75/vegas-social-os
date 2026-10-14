# Third-party Flow craft materials

`flow-video-producer/` is a byte-preserved portable skill snapshot from zysilm/video-producer-skill, commit b02ae80e438526ecb906009d5faf0e397037554f, MIT, copyright 2026 zysilm-ai.

`flow-scripting/` is a byte-preserved selected documentation snapshot from agbelemi/google-flow-scripting-skill, commit 6e97dbb280c8349b7757210c061888817e0cbd1f, MIT, copyright 2026 Agbelemi. It is not a standalone installation; follow Vegas's adapter.

Each folder includes its upstream LICENSE. `vso/continuity.py` adapts last-retained-frame index arithmetic from the producer's `scripts/extract_frame.py`; the MIT notice remains in `flow-video-producer/LICENSE`. Other runtime modules remain original Vegas implementations. See docs/FLOW-SKILL-INTEGRATION.md for active behavior and overrides.
