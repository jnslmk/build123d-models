# Skills eval suite

This is a small, hand-written evaluation suite for the nine agent skills under
`.claude/skills/` (`box-closures`, `build123d-geometry-ops`,
`fasteners-and-inserts`, `fdm-fits-and-clearances`, `part-joints`,
`printed-text`, `snap-fits`, `viewer-frontend`, `viewer-inspection`). It exists
to answer one question: **did the skills actually change the answer, and are
they right** — rather than assuming a skill helps just because it exists.

## Files

- `scenarios.md` — eleven design questions, each with an expected answer,
  checkable assertions, the skill that should fire, a citation into the
  skill's own source file and section, and the failure mode a skill-less
  agent would most plausibly produce.
- `baseline.md` — an **analytic** (not measured) prediction of what a
  reasonable agent without these skills would answer for each scenario, and
  why that answer is wrong or underspecified.

There is no executable grader in this suite. Every scenario's assertions are
prose checklists meant for a human reviewer or an LLM judge reading a
transcript — see [Running it](#running-it).

## Why Markdown, not JSON/YAML

`scenarios.md` is hand-authored Markdown rather than a structured data file.
Reasons, in order of weight:

1. **The task explicitly does not require an executable grader**, and a
   script nobody runs is worse than no script (the task's own words). Without
   a grader consuming the file programmatically, there is no benefit to a
   machine-parseable format and a real cost: JSON/YAML would force citations,
   prose caveats, and multi-line expected-answer text into escaped strings or
   block scalars, which is worse to read and worse to diff.
2. **The reviewer is a person or an LLM reading prose**, not a program
   comparing field values. A grader needs to read "at PLA's reopenable
   strain limit the bead comes out at 0.18 mm, which is impractically small"
   as connected reasoning, not `{"metric": "bead_mm", "expected": 0.18,
   "tol": 0.02}` — several assertions here are qualitative ("does not
   overgeneralise to X") and resist a single scalar comparison anyway.
3. **Every citation needs to sit next to the prose it supports** so a
   reviewer can check it in seconds. Markdown headings and a table of
   contents do that natively; a data format would need a second document for
   the same job, reintroducing the "one level of indirection too many"
   problem this repo's own skill-authoring rules warn against.
4. **Consistency with the artifact it evaluates.** The skills themselves are
   Markdown with YAML-only frontmatter. A JSON scenario file would be the odd
   one out in a repo that otherwise treats prose-with-structure as the native
   format for anything meant to be read by an agent or a person.

If this suite grows a real executable grader later (see Limitations), the
natural evolution is to keep the prompt, expected answer, citations and
narrative failure mode in Markdown, and promote only the `assertions`
checklist per scenario to a small YAML/JSON sidecar keyed by scenario ID —
not to convert the whole file.

## Running it

There is no `eval/run.py` or similar — this is a prompt-and-grade suite, not a
CI check. To run it:

1. Pick a scenario from `scenarios.md`.
2. Put its **prompt** to an agent — once with the relevant skill(s) available,
   once in a session with the skills disabled or unavailable (e.g. a repo
   checkout without `.claude/skills/`, or a model run without skill-tool
   access) — to get a same-skills-vs-no-skills comparison.
3. Compare the transcript against the scenario's **assertions**. Each is a
   yes/no check a careful human reviewer (or an LLM acting as a judge, given
   the transcript and the assertions list) can answer by reading the
   response — no numeric extraction pipeline is assumed.
4. A scenario **passes** when every assertion in its list is satisfied. A
   partial match (e.g. the right number but the wrong material) is a fail —
   these are design answers where "close" can mean "will crack in service,"
   not a fuzzy-match target.
5. Record the pass/fail per scenario. There is currently no persisted score
   file; add one (e.g. `eval/results/<date>.md`) if this suite starts running
   repeatedly, so runs are comparable over time as skills change.

**What "the skill should fire" means in practice.** Claude Code skills are
selected by the model reading each skill's `description` against the prompt —
there is no forced-invocation mode this suite can script. "Skill that should
fire" in each scenario is therefore a prediction to check after the fact
(did the transcript show the skill being invoked, and does the answer match
what only that skill's content would produce), not a lever this suite pulls
directly.

## What a pass means — and does not mean

A scenario passing means: **the response is traceable to, and consistent
with, what the cited skill file actually says**, on a question this suite's
author could construct a checkable answer for. It does not mean:

- The skill's content is correct about the physical world. See Limitations.
- The agent used the skill (it may have reached the same answer from
  training-data recall of similar DFM advice; the eval cannot distinguish
  "used the skill" from "already knew this").
- The skill generalizes to questions this suite did not think to ask.

## Limitations — read this before trusting a "100% pass"

This is a small suite (eleven scenarios) written by one author, and it has
structural limits that a passing score does not overcome:

1. **The scenarios were authored from the same skills they test.** Every
   expected answer, tolerance and citation in `scenarios.md` was derived by
   reading the skill file, not by independently deriving the physics and then
   checking the skill against it. A skill that is *internally consistent but
   wrong* — a formula transcribed with a sign error, a source misread, a
   citation that points at the wrong PDF section — will pass this suite with
   a perfect score, because the suite is grading agreement with the skill,
   not agreement with reality. This measures **internal consistency and
   recall**, not external ground truth.
2. **It cannot detect a skill being confidently wrong about the physical
   world.** If Covestro's own snap-fit formula is misapplied inside the skill
   (not just cited), or a materials figure is stale, this suite will not
   catch it — it would need an independent physical derivation or a printed
   test coupon per scenario, which is out of scope for a documentation eval.
   Several of the skills' own files openly record such risks (see the
   "Discrepancies" section of the implementer report for this task, which
   flags places the skill content itself looked questionable during
   authoring) — this suite does not adjudicate those, it just does not paper
   over them either.
3. **No measured pass rates exist yet.** `baseline.md` is an analytic
   prediction of what an agent without the skills would likely say, reasoned
   from well-known published defaults (the "0.5 mm bead" folklore, the 4.0 mm
   nominal insert-hole figure, "Acme prints better because it's flatter").
   It is not a controlled experiment, and no number in it should be read as a
   measured pass rate. Running the actual before/after comparison (step 2 in
   [Running it](#running-it)) across all eleven scenarios, several times each
   to account for model sampling variance, is the natural next step but was
   not performed as part of authoring this suite.
4. **Eleven scenarios cannot cover nine skills exhaustively.** Two skills
   (`viewer-frontend`, `viewer-inspection`) have no scenario at all — they are
   procedural workflow guides (how to rebuild a JS bundle, how to read a
   picker selection), not design questions with a checkable numeric or
   structural answer, so no scenario could be constructed for them under this
   suite's own rule that every answer must trace to specific skill content.
   That is a real gap in coverage, not a claim that those skills are
   unimportant.
5. **An LLM judge is not a neutral instrument.** If an LLM is used to grade
   transcripts against the assertions (as suggested in
   [Running it](#running-it)), it inherits the usual judge biases — a
   fluent, confident-sounding wrong answer can out-score a hedged correct
   one. The assertions are written as concrete, checkable claims (a number
   in a range, a named recommendation) specifically to reduce this, but it is
   a mitigation, not a fix.
6. **Single-author, single-pass authoring.** Nobody but the author of this
   suite (working from the skill files, in one sitting) has reviewed whether
   the expected answers and tolerances are reasonable. Treat a disagreement
   between this suite and a skill's actual content as more likely to be an
   authoring mistake in the eval than evidence the skill is wrong, until
   checked — and treat a disagreement between the skill and outside sources
   the other way around.

## Extending the suite

To add a scenario: find a design claim in a skill file that is specific
enough to check (a number, a named recommendation, a yes/no decision), write
a prompt that would surface it, and write the assertions before writing the
expected answer prose — if you cannot state a checkable assertion, the claim
is too vague to eval and probably needs tightening in the skill itself before
it needs a scenario here. Cite the exact file and heading. If you cannot trace
the answer to specific skill content, the scenario is out of scope for this
suite — drop it rather than eval-by-vibes.
