# Choose the asset engine by the job

For reusable motion recipes and external icon/component sources, start with [motion-library.md](motion-library.md). It routes to the pinned iart.ai craft packs and local asset inventory before authoring a substantial graphic from scratch.

| Need | First choice | Why / when to escalate |
|---|---|---|
| Thick X, arrows, search/download/image icons | Native SVG/DOM or licensed vector icons, animated in HyperFrames | Exact shape/color, transparent background and predictable timing; no model needed. Use two thick strokes for an X, with contrast against the picture. |
| Text, prompt typing, a screenshot search field | HyperFrames text over the original screenshot | Mask only the original query text, retain the real interface and icons, type the exact requested text. Never generate the entire UI to simulate typing. |
| Color variants with a fixed subject | Aligned cuts/wipes and one continuous image motion | Preserve face/product registration and supplied artwork; generated morphing can damage the product or identity. |
| Step explanation | Existing evidence + progressive cards, cursor/highlight and purposeful detail zoom | Keep the speaker's statement and visible asset consistent. |
| A static stretch with no new visual information | Presenter cutaway or real product B-roll | A face is often better than unrelated generation. Change at meaning boundaries and inspect the return transition. |
| Abstract motion texture / transition / atmospheric background | Existing licensed material, then a small Kie.ai test if authorized | Generation is useful where variation is acceptable and no exact text/product fidelity is required. |
| Realistic product/character movement | Appropriate image-to-video model with approved reference | Test one short low-cost draft; scrutinize hands, glass, food, logo, identity and temporal stability before using it. |

## Brand and icons

Load the brand at the beginning, not after an entire default green/dark treatment is finished. The kit's default brand lives in `brand-system/` at the repo root (paper, ink, marker yellow, Bricolage Grotesque + JetBrains Mono); a client or second brand needs its own system: its exact colors, supplied fonts and actual logo lockups. Do not retype logos. Square shapes, hard offset blocks and quick mechanical movement suit a bold, flat system; a softer brand wants softer motion.

The example used two red X strokes, Pinterest typing in the real query region, and faster 140–380ms entrances while preserving readable holds. Those are useful starting points, not mandatory speeds or layouts. Reserve the caption band before rendering. Pattern backgrounds should not compete with body text.

Use [Lucide](https://lucide.dev/) for suitable line icons when no brand-specific set exists. Check the [license](https://lucide.dev/license) and retain notices with copied assets. Its ISC/MIT-derived licensing has no per-generation charge. SVG is sharper and more editable than a generated bitmap icon. Use a consistent stroke weight; a bold warning X can be a deliberate separate emphasis.

For Lottie/stock assets, verify the individual download's license and applicable account terms, keep provenance, and inspect the actual animation. Do not generalize a provider's “free” label into unlimited commercial rights. Do not download whole libraries when a few assets suffice.

## Kie.ai: budgeted experiment, not an automatic step

1. Confirm current authorization, reference-upload scope and total spend cap including retries. Reuse a still-valid cap from this task; never inherit another project's budget or ask again unnecessarily. If no cap exists, finish the brief/read-only comparison while asking for the material spending decision.
2. Check **live official** model pricing and API schema. Select the cheapest model that supports the required inputs, duration, resolution and useful fidelity, not merely the lowest advertised price. Community reports can suggest candidates but are anecdotes, not benchmarks.
3. Verify the configured account/credit endpoint read-only. The key is `KIE_API_KEY` in the environment (the repo's `.env`). Never show keys. If you already have a working Kie helper script, reuse its auth/upload pattern, but not its default model or upload folder.
4. Write the exact reference/prompt/settings, expected cost, cap and job state to a project receipt. Submit one candidate first. Record its task ID immediately. An uncertain POST is not permission to retry: recover task status/history first. Poll the existing ID on timeout; stop dependent work on errors.
5. Read back job state, output and cost evidence. Balance changes may include concurrent jobs; prefer task billing when available and label balance-only estimates. Do not spend the unused cap just because it is available.
6. Inspect returned dimensions, duration, audio, color, shape stability and suitability. Requested settings are not proof of delivered format. Download the actual generated result for editing, mute unwanted generated audio, normalize timing/fps, and integrate only a useful result. If rejected, explain why; retry within the cap only with a concrete corrective prompt/model change.

### A worked result, not a standing price quote

In one worked run, a single `grok-imagine/image-to-video` request through Kie used a supplied brand pattern, 6 seconds, requested 720p/9:16 and mode `normal`. The observed credit delta was 27; at the verified listed `$0.005/credit` rate this was `$0.135`. The user authorized up to $5 for that experiment. This does not authorize future spending or fix future prices.

The response was 2128×416 and 6.0417 seconds, following the wide reference rather than the requested aspect ratio. It was useful as a full-width moving footer banner; stretching it vertically would have been worse. Exact X/text remained native. Only one paid candidate was needed.

Observed official endpoints: `POST https://api.kie.ai/api/v1/jobs/createTask`, `GET .../jobs/recordInfo?taskId=...`, credit `GET .../chat/credit`. The upload helper used `https://kieai.redpandaai.co/api/file-base64-upload`; the separate host and browser User-Agent mattered. Resolve these against current docs before use. Uploads can produce publicly accessible temporary URLs: send only the approved reference, under the right project's folder.

```json
{
  "model": "grok-imagine/image-to-video",
  "input": {
    "image_urls": ["PUBLIC_APPROVED_REFERENCE_URL"],
    "prompt": "Describe the desired motion, preserved geometry and practical restrictions.",
    "mode": "normal",
    "duration": "6",
    "resolution": "720p",
    "aspect_ratio": "9:16"
  }
}
```

This is a dated request example, not an executable purchase template. Sources: [Kie Grok pricing/model](https://kie.ai/grok-imagine), [Grok I2V schema](https://docs.kie.ai/market/grok-imagine/image-to-video), [Kie model catalog](https://kie.ai/).
