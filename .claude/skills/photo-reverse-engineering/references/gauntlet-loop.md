# The gauntlet loop, adapted for CAD

A ready-to-use prompt template, and the reasoning behind each departure from the
original.

## Origin

Matt Shumer's "gauntlet loop", as walked through in [this
video](https://www.youtube.com/watch?v=BNjzXcEXmg4). The original is three lines:
a task, a build method (fan out subagents, each with a critic that checks it),
and a bar ("do not stop until each subagent is utterly wowed when compared with
the actual Call of Duty"). The video's own demo is a photo-reverse-engineering
job — a floor plan plus reference photos of an apartment, rebuilt as an
explorable 3D walkthrough, with critic agents comparing screenshots against the
original photos round after round.

The video also makes the point that matters most here, and makes it against its
own technique: run on a weak starting point, the loop produced a landing page
with a high finish that was off-brief, because a loop optimises toward whatever
it was pointed at. Its advice — start from a strong minimum viable version and
use the loop to sharpen it — is exactly right, and in CAD it is not a style
preference but a correctness requirement, because the visual gates are provably
unable to see a scale error (`scale_error_2pct`: 96.12% IoU on a part 2% too
large).

## What changes, and why

| Original | Here | Why |
|---|---|---|
| Bar is aesthetic ("utterly wowed") | Bar is a script's exit code | An aesthetic bar judged by the model producing the work is unfalsifiable. `silhouette_match.py` and `checks.py` already exit non-zero. |
| Compare against a named cultural reference | Compare against the reference photo and the ledger | "Call of Duty" works because everyone has seen it. The equivalent here is the artifact you are actually copying. |
| Loop until the critics are satisfied | Loop until the gates pass **and** the ratios are within 1% | IoU alone passes a 2% scale error. The ratio is the check that does not. |
| Start with the loop | Start with the ledger and a correct-scale skeleton | A loop cannot discover a dimension the photos never contained. |
| Visual critics are the verification | Visual critics are *half* of it | A silhouette is blind to internal geometry — `hidden_cavity`: 100% IoU, 25% of the material gone. `checks.py` is the other half and is not optional. |

## The template

Fill the bracketed parts. It is deliberately concrete about the gates, because
vagueness there is what turns the loop into an expensive way to polish the wrong
part.

> **Task.** Build `models/<name>/` from the photos in `<refs/>` and the
> measurement ledger at `<analysis/ledger.json>`.
>
> **Build method.** Break the part into its printable pieces and its distinct
> features. Fan out one subagent per piece. Give each one a separate critic
> subagent that has the reference photos, the ledger and the piece's build
> output, but **not** the builder's reasoning. Each critic runs
> `silhouette_match.py` for every view where a reference photo exists, plus the
> piece's own assertions, and reports the numbers rather than an opinion.
>
> **The bar.** A piece is done when, and only when:
> - `uv run check <name>` passes, including `sharp_convex_edges()`;
> - `silhouette_match.py` exits 0 for every view with a reference photo;
> - width and height ratios are within 1% of 1.000 for every one of those views;
> - every dimension in `config.py` carries a provenance comment, and every
>   `ASSUMED` one is listed in the final report.
>
> Do not stop while any gate fails. Do not change a gate to make it pass. If a
> gate cannot be met because the photos do not contain the information, say so
> and mark the dimension `ASSUMED` — that is a valid outcome and a silent guess
> is not.

## Running it well

- **Blind critics, genuinely.** Passing the builder's justification to the
  critic converts it into a ratifier. It gets the artifact and the reference.
- **One critic per lens beats three identical critics.** Silhouette match,
  geometry assertions, and printability (overhangs, print pose, bed contact) are
  different failure modes; three copies of the same check find one of them three
  times.
- **Cap the rounds.** The gates are numeric, so a piece that has not converged
  in three rounds is not going to — it is blocked on missing information, and
  the useful output is which dimension is missing, not another round.
- **The loop is the polish, not the build.** Land the ledger, the scale and the
  skeleton first. Everything above only sharpens what is already roughly right.
