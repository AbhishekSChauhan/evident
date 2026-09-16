# Demo runbook

**What this is.** The presentable parts of seven demo documents, merged. The
hackathon those documents were written for ran 10–11 Sep 2026; the gap analyses,
G1–G8 build order and seven-day plan that filled most of their ~4,900 lines are
spent and sit in [`archive/`](archive/). What survives is the part that is still
useful every time this product is shown to anyone: the script, the failure
matrix, and the rules about what not to say.

---

## ⚠️ Verify the numbers before you present

**The scores in §2 are the ones the original runbook was rehearsed against
(2026-09-06) and they no longer match the working tree.** Read out of the local
`proofscreen.sqlite3` on 2026-09-17:

| candidate | resume | runbook competence | local DB competence |
|---|---:|---:|---:|
| Maya Krishnan | 50 | 61 | **38** |
| Priya Raghavan | 28 | 56 | **24** |
| Arjun Mehta | 34 | 46 | **26** |
| Rohit Verma | **59** | 14 | **14 / 9** |

Resume scores are unchanged. Competence has moved, and **Priya and Arjun have
swapped** — the runbook's "mirror image" beat (§2 step 6) depends on Priya
outscoring Arjun and she currently does not.

That local database may be mid-experiment rather than a clean seed. **Run
`python seed.py --reset` and read the real numbers off `/recruiter/candidates`
before rehearsing**, then update this file. Do not present a number you have not
seen today.

**The thesis does not depend on the exact values.** Rohit has the best resume
(59) and the worst competence (14) in every version measured so far. That
inversion is the demo. The supporting numbers around it are not.

---

## 1. Before speaking

- `python seed.py --reset` run today, numbers read off the screen
- one candidate pre-run to `COMPLETE` about an hour earlier
- tabs open on `/recruiter/candidates` and `/candidate`
- handset mirrored
- **the demo phone number never used in rehearsal** — the 24-hour window and the
  opt-in flow both behave differently on a number that has already messaged us
- `/api/health` checked

**8 minutes. Act 1 (4 min) cannot fail. Act 2 (4 min) may, and costs nothing.**

---

## 2. Act 1 — the thesis

Runs on `PROOFSCREEN_FIXTURES=fallback` with **no backend**. Nothing in this act
needs WhatsApp, OpenAI or the API.

**1 · `/recruiter/candidates`** — four candidates, ranked by competence.

> "Four candidates, ranked. Not by their resumes — by what they could actually
> evidence when someone asked a follow-up question. Watch the bottom of the
> list."

**2 · point at Rohit's row** — resume 59, the highest on screen; competence
lowest; 1 contradiction.

> "Rohit has the best resume here. Every keyword the job description asks for. It
> reads like it was written to beat an ATS, because that is exactly what it is.
> He ranks last on competence."

**3 · click Rohit** — the score strip shows three numbers.

> "Three numbers, never one. Fifty-nine on paper. Lower once we asked him about
> it. Lower again after consistency."

**4 · scroll to Consistency** — the multiplier and the contradiction that caused
it: *"Team size — said 45 earlier, then 20 — 56% apart · MAJOR"*.

> "He told us he managed forty-five agents. Four questions later, twenty. That is
> not the AI having an opinion — it is two numbers and a subtraction."

**5 · expand a claim's Transcript.**

> "And here is why the evidence score was low to begin with. 'Team management is
> really about leadership and communication.' 'I'm not sure how it was
> calculated.' 'I don't remember the details.' No numbers, no process, no
> incident he can recall. There is nothing to count."

Point at the TRANSFER labels:

> "After two answers that produced no evidence, the system stopped asking what he
> did and started asking what he *would* do — a scenario assembled from his own
> other claims. A memorised resume can be recited. It cannot be transferred."

> ⚠️ **Do not say "he got a shorter interview."** Everyone gets the same budget.

**6 · open the candidate with the weakest resume and a strong competence score**
— the mirror image.

> "The worst resume here. She does not write for keywords. Then you ask her:
> thirty-five agents across four pods, CSAT seventy-eight to ninety-two, and the
> specific week three people resigned before month-end."

> ⚠️ **Check today which candidate this is.** See the warning at the top — it was
> Priya, and on the current data it may not be.

**7 · back to the list, switch the lens.** People-First vs Ops-Excellence — the
ranking reorders.

> "Same evidence, two openings. Nobody was re-interviewed and no model was
> called — every dimension score is already stored, so this is arithmetic, in
> milliseconds."

**— The thesis is proven here. Everything after this is optional. —**

---

## 3. Act 2 — the live journey

**8 · `/candidate`**, open a role, click Apply.

**9 · Upload the resume** — on the web, or send the PDF straight to WhatsApp.

> "Three claims worth checking, pulled straight out of the document."

**10 · Tap "Open WhatsApp"** — the opt-in code is prefilled; send it. Expect an
acknowledgement within ~2s, then question 1.

> "Sending that code is the consent step. Meta will not let us message a
> candidate first, so the interview waits for them."

**11 · Answer with a voice note.** A script that exercises every signal class:

> *"I ran a team of eighteen agents across two shifts. First-response time was
> around fifty minutes because tickets were triaged by whoever picked them up
> first, so in March we moved to skills-based routing in Zendesk and I built a
> saved view for the overflow queue. By May first-response was down to
> twenty-two minutes. The worst week was before the April billing run — two
> people out sick, and I cleared about sixty tickets myself on the Saturday."*

Fill the transcription pause with the line that matters most commercially:

> "That was a voice note. Transcribed, then counted — quantities, process steps,
> a complete cause-action-outcome chain, a tool with described usage, a specific
> incident. We measure how long they spoke and how much they said, and nothing
> else. **Not accent, not fluency, not confidence** — those track region and
> class, not competence."

**12 · Answer weakly once:** *"We focused on quality and made sure standards were
maintained."*

> "And the next question goes back to what it could not establish. The interview
> adapts to the answer, not to a script."

**13 · `/recruiter/candidates`, refresh** — the live candidate appears with a
real score.

---

## 4. Close

> "Resumes are now written by AI, for AI. Ranking by resume quality ranks the
> writing. We rank by what a candidate can evidence when someone asks a
> follow-up — and the model never produces a score. It counts things and quotes
> them; Python does the arithmetic."

### If challenged on accuracy

> "Five hundred and nineteen real generated questions, measured against a blind
> human reviewer. Our question validator runs at fifty-four percent precision and
> we published that number. One research phase recommended *not* shipping a rule,
> because two humans could not label the category consistently."

**Never invent a number.** The precision figure is real
(`studies/phase3/confusion_matrix.md`); the research phase is real
(`studies/phase5/README.md`). Both are stronger answers than a confident guess,
and both are checkable by anyone in the room.

---

## 5. Failure matrix

Every row returns to Act 1, which needs neither WhatsApp, nor OpenAI, nor the
backend.

| Failure | Presenter does | Switches to | Thesis proven? |
|---|---|---|---|
| **Meta outage** | Finish Act 1; skip Act 2. *"The interview runs on WhatsApp — here is one that already did."* | Act 1 only | ✅ fully |
| **Webhook failure** (no reply in 15s) | One retry, then switch. *"Let me show you the same interview through our simulator."* | `/candidate/proof/interview` or `/recruiter/simulator` — same orchestrator, same rubric | ✅ fully |
| **OpenAI outage** | Nothing visible in Act 1 — those scores are already computed. Act 2 falls back to deterministic heuristics; **scoring arithmetic is byte-identical** | Continue; check `/api/dev/llm` | ✅ fully |
| **Voice transcription fails** | Type the answer. Identical path bar the voice weight | Same thread | ✅ fully |
| **Resume upload fails** | Use the web intake at `/candidate/start` | Act 2 from step 10 | ✅ fully |
| **Backend outage** | `PROOFSCREEN_FIXTURES=fallback` serves Act 1 from `lib/api/fixtures.ts`, including the lens inversion. Own the banner: *"that strip is the product being honest about where its numbers came from"* | Act 1 only | ✅ fully |
| **Frontend outage** | `curl /api/recruiter/candidates` on screen, or the screenshot deck | Terminal / deck | ⚠️ weakened |
| **Total loss** | Screenshot deck and the story | Deck | ⚠️ narrative only |

**Presenter rule: never debug on stage.** One attempt, then switch and keep
talking. Every fallback above is a rehearsed path, not an improvisation.

---

## 6. Things not to say

| Don't | Because |
|---|---|
| "He got a shorter interview" | Everyone gets the same question budget. The difference is what the answers contained |
| "The AI decided he was lying" | The model never produces a score or a judgement. A contradiction is two stored numbers and a subtraction |
| Any score you have not seen today | See the warning at the top of this file |
| "It scores communication / confidence / fluency" | It scores none of those, deliberately. That is a stated product decision, and it is the answer to the bias question |
| "We're compliant with DPDP" | The DPDP workstream is untouched — `PRODUCTION_READINESS.md` §7 |

If asked about auth: **one shared key per tenant, no users, no roles, no
rotation**, and `REQUIRE_API_KEY` defaults to `false`. Say so. It is a
pre-revenue prototype and pretending otherwise is the one answer that cannot
survive a follow-up.

---

## Provenance

Merged from seven demo documents (~4,900 lines) written for the hackathon of
10–11 Sep 2026. **Those files were deleted on 2026-09-17** — the hackathon is
over, and the gap analyses, G1–G8 build order and seven-day plan that made up
most of their bulk were spent the moment they shipped.

Everything still useful is above. Two durable findings they carried were moved
into `CLAUDE.md`'s gotchas rather than left here: `extract_text` gates on the
file extension, and `download_media` mislabels a document as `audio/ogg` when
Meta omits the mime type. Both were re-verified against the code before being
written down.

They are recoverable in full:

```bash
git show <commit>:docs/HACKATHON_DEMO_PLAN.md     # 1167 lines
git show <commit>:docs/DEMO_BUILD_ORDER.md        # 1133 lines
git show <commit>:docs/DEMO_EXECUTION_REVIEW.md   #  874 lines
git show <commit>:docs/DEMO_READINESS_FINAL.md    #  818 lines
git show <commit>:docs/DEMO_GAP_ANALYSIS.md       #  470 lines
git show <commit>:docs/DEMO_MODE_VALIDATION.md    #  306 lines
git show <commit>:docs/DEMO_MODE_MOVE_AUDIT.md    #  151 lines
```

where `<commit>` is any commit before the 2026-09-17 documentation triage.
