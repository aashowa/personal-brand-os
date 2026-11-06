# Motion library: select, adapt, verify

Use the [local motion inventory](../../../brand-system/motion-inventory/README.md) for reusable icons/components and the [iart.ai pack index](../../../brand-system/motion-inventory/iart/README.md) for motion-design knowledge. The latter holds five pinned packs (22 skill documents) from the MIT-licensed [iart-ai/motion-skills](https://github.com/iart-ai/motion-skills); if your repo has no `brand-system/motion-inventory/`, clone the packs you need there. It is a reference library, not a new runtime or automatic global skill installation.

## Choose only the relevant references

Start with art direction when designing a substantial new sequence or correcting “basic”, busy or inconsistent motion. Read one or two execution references for the actual beat; do not load all packs.

All paths in this table are relative to the inventory's `iart/` directory.

| Need | Local reference |
|---|---|
| Motion language, focal hierarchy, consistent pacing | `motion-design-skills/skills/motion-art-direction/SKILL.md` |
| Easing, weight, anticipation, follow-through | `motion-design-skills/skills/animation-principles/SKILL.md` |
| Camera framing and composition | `motion-design-skills/skills/shot-composition/SKILL.md` |
| Headlines, masked reveals, word/line choreography | `kinetic-typography-skills/skills/kinetic-typography/SKILL.md` |
| Nodes, connectors, systems and customer journeys | `explainer-video-skills/skills/diagram-animation/SKILL.md` |
| Spoken explanation into visual beats | `explainer-video-skills/skills/explainer-video/SKILL.md` |
| Verified numbers, charts and data stories | `data-animation-skills/skills/chart-animation/SKILL.md` or `animated-infographic/SKILL.md` in the same skills directory |
| Vertical pacing and safe areas | `tiktok-video-skills/skills/short-form-video/SKILL.md` |
| Captions / lower thirds | `tiktok-video-skills/skills/caption-animation/SKILL.md` or `lower-thirds/SKILL.md` in the same skills directory |

Follow each chosen document to its relevant reference recipes. Other included modules are optional techniques, not steps every video must perform.

## Adapt craft to this workflow

Upstream documents supply creative recipes; this skill and the current user brief own the deliverable. Their install commands, platform defaults, intake questions, fixed timing numbers and renderer choices do not override existing authorization or reopen answered questions.

- Palmier owns the cut, linked dialogue, captions and final timeline. HyperFrames owns code-authored graphic renders. Do not switch to Remotion, After Effects or Manim because a borrowed recipe names them.
- Translate browser autoplay, hover triggers, `requestAnimationFrame`, clock-driven counters and infinite loops into one paused, registered HyperFrames timeline with finite, deterministic motion. Load the installed HyperFrames core/animation/keyframe contract before implementation.
- Do not transplant the upstream `?t=N` browser harness into a HyperFrames composition. Use its native check/snapshot/keyframe tools. Upstream shell/JSX helpers are archived source, not preapproved commands; inspect a helper and its dependencies before using it.
- Upstream constraints such as “one wow moment”, numeric stagger limits, three mandatory motion layers or a default branding style are starting points, not universal rules. Use only what improves this footage and preserves readability.
- Keep the user's palette/branding scope. Preserve exact supplied content and verified values; recipe/demo numbers are never evidence.

## Build from inventory

Match a spoken idea to an asset or mechanism: labour → clock; local discovery → map pin; channel mix → connecting nodes; comparison → aligned change; a key phrase → deliberate typographic reveal. Generic motion applied to every item is not a visual explanation.

Use existing rendered episode assets when they fit. External inventory entries marked source-only need adaptation and an actual render check before they become reusable video assets. Preserve upstream license notices and source revision in the episode's provenance notes.

For a new or substantially revised sequence, record one short motion-language choice (energy, entrance/exit easing, transition family, focal hierarchy) and the cue/hold for each beat. Reuse that language across related shots; avoid making the viewer read a caption and unrelated large copy simultaneously.

When stronger examples are needed or the user requests research, inspect a few relevant references, record their links and the specific technique being adapted. Distinguish a page/transcript/styleframe review from watching the animation. Research is for direction; do not copy unlicensed reference footage.

## Acceptance

Review actual movement and exact boundary frames as well as static layout. Check first frame, peak action, readable hold and exit; verify that icons explain the speech, connectors reach their targets, captions remain legible, and motion never resets after a trim. Check the integrated Palmier export, not only the HTML preview. Keep the prior timeline and state any unperformed playback/listening checks honestly.
