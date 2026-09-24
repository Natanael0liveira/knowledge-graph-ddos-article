# Writing style for scientific papers

A portable style guide, extracted from repeated revision rounds on the NOMS
submission. The rules are general; the examples are drawn from this paper because
concrete failures teach better than abstract advice. Reusable on any paper.

Two things make this document worth keeping. The rules themselves, and the
**verification commands** in the last section, which turn most of them from
matters of taste into things a script can check before you hand the draft to
anyone.

---

## 1. Register

**Naturalized prose in the venue's idiom.** It should read as a careful
researcher writing plainly. Not as a machine performing sophistication, and not
as marketing copy. Fluid and revised, never merely assembled.

**No excessive jargon.** A term earns its place only when no ordinary word does
the same work. Terminology the field genuinely requires stays; ornament goes.

**Vocabulary: no exotic words, but no dull repetition either.** Keep the register
common enough to read at speed, and rotate word choice within that band so the
same word does not recur in adjacent sentences. Both failure modes are real: the
rare word that stops the reader, and the same verb four times in a paragraph.

> **Watch the repair, not only the fault.** Removing one tic tends to install
> another. Purging `rather than` from this paper produced nine new occurrences of
> `X itself` in a single pass, 14 in the file, which then had to be cut back to
> 7. Whenever you fix a pattern globally, count what you replaced it *with*.

## 2. Forbidden constructions

**No em dashes (`---`).** Restructure the sentence, or use a comma, a colon or a
parenthesis. This is absolute; the count should stay at zero.

**No "not X, but Y" antithesis.** This includes `is not ... but ...`,
`not merely ... but ...`, and heavy repetition of `rather than`. The pattern
reads as manufactured emphasis. State the positive claim directly.

| Before | After |
|---|---|
| `the collapse is a property of the representation, not of the learner` | `which locates the collapse in the representation: no hypothesis class recovers what the features discarded` |
| `Cross-session relatedness is not one relation but a structured family` | `Cross-session relatedness is a structured family of relations` |
| `The formalism is not intended to raise AUC but to provide a typed vocabulary` | `The formalism exists to provide a typed vocabulary` |
| `DDoS has changed in kind, not only in scale` | `DDoS attacks continue to grow in volume and frequency` |

Note that the rewrites are **shorter and stronger**, not merely compliant.

The last row is worth a second look: the aphorism was also **unsupported**. The
paragraph it opened only evidenced growth in scale, never a change in kind. An
antithesis often signals a claim the text does not back; checking that is a
second reason to remove it.

**When the contrast genuinely is the claim**, keep it, and keep it idiomatic. Two
survived in this paper on purpose: `calibrated rather than assumed` and
`reproducible rather than asserted`. Purging every instance mechanically makes
the prose stilted, which violates rule 1. The test: does removing the contrast
lose information, or only lose emphasis?

**Semicolons are a register marker, not a neutral join.** Three NOMS 2024 papers
used 0 to 0.6 per thousand words; this paper had 5.4. Keep them for separating
enumerated items, such as `(i) ...; (ii) ...`. A semicolon joining two independent
clauses becomes a full stop, which is also the cheapest way to cut long sentences.

**Long sentences.** NOMS prose runs at a median of 18 to 20 words per sentence,
with 1 to 3 percent above 45 words. Split any sentence above 45 unless it is a
definitional list. A contribution statement is never one sentence: here it was
187 words. `This paper makes four contributions. (i) We propose ...` keeps the
numbering and gives each contribution its own sentence and its own `we`.

## 3. Flow

**Paragraphs must connect.** Each opens by picking up where the previous landed.
`therefore` is the model connector. Continuity is built with small adjustments at
the seams, not with transitional boilerplate.

**Never go straight from a section heading to its first subsection.** Every
section needs a short paragraph announcing what the subsections will do. A
reader who lands mid-document should learn where they are before the detail
starts.

**Related work closes by stating the boundary.** Name the properties that no
published approach holds together, and therefore where this work acts and the
others do not. A related-work section that only summarizes has not done its job.

**Single-sentence paragraphs are weak in two-column layouts.** Merge them into a
neighbour. In this paper the typographic fix and the prose fix coincided: a
one-sentence paragraph was both a widow generator and a structural blemish.

## 4. Citations

**A citation is never a grammatical subject.**

| Wrong | Right |
|---|---|
| `\cite{x} applies PCA to flow statistics` | `PCA is applied to flow statistics~\cite{x}` |
| `The meta-analysis of \cite{x} finds` | `A meta-analysis of seventy-five studies finds~\cite{x}` |

**Author names in the body reduce to the citation alone**, including in table row
labels. Describe the method, cite the source: `PCA over flow statistics~\cite{x}`
rather than `Fernandes et al.~\cite{x}`. Exception: a named system you compare
against throughout (KLAGE here) keeps its name, because the reader needs a handle
for it.

## 5. Typography

**No paragraph should end with one or two words on their own line.** A widow line
wastes a full line of a page-limited paper. Fix it by removing redundant words
from anywhere in the paragraph, not by padding.

The arithmetic: a column holds roughly 58--62 characters. To absorb an orphan of
*n* characters you must free about *n* characters anywhere in that paragraph.
Expect to iterate, because each fix reflows the text and can create a new widow
elsewhere. In this paper it took four rounds to go from 33 widows to zero.

Cuts that worked, none of which lost meaning:

- `which is precisely what makes them difficult` → `which is what makes them difficult`
- `with perfectly known coordination ground truth` → `with known coordination ground truth`
- `all of them laboratory testbed captures` → `all laboratory testbed captures`
- `A human-analyst study remains future work` → `A human-analyst study is future work`

**Table and figure captions belong on one rendered line.** Parameters move to a
table note (`\vspace{2pt}` plus a `\footnotesize` block after the `tabular`),
which is more compact than a caption: notes are justified across the full column
width, captions are centred small caps that break early and eat vertical space.

**Float placement.** In a two-column document, `[!ht]` on a `figure*`/`table*` is
a trap: LaTeX silently ignores the `h`, and the `!` discards the float-placement
parameters the preamble tuned. Use `[t]`. When two single-column floats stack in
the same column, give the second `[b]` so body text separates them.

**Check the page limit by where the body ends, column included.** The body ends
where the first back-matter heading (Acknowledgment, References) starts. With
`pdftotext -layout`, find that heading and read its horizontal offset: in a
two-column page, text starting past the middle is in the right column, which
means the whole left column above it is still body. A check that only records
which page the heading is on reported "within limits" for weeks while a third of
a column of body had spilled onto the next page.

**Wide floats slip in cascades.** A `table*` or `figure*` lands at the top of the
page *after* its declaration. If the text before it grows, it slips a page and
pushes the next wide float too. Declare wide floats a little earlier in the
source than where they are discussed; the printed position then stays put.

**Verify placement by measuring, not by intuition.** Two float moves in this
paper looked right in the abstract and were wrong in the PDF; both were reverted
after measurement. A float belongs on the same page as the text discussing it,
and moving it "somewhere cleaner" usually breaks that.

## 6. Unfinished text

Review notes and placeholders reach the PDF if nobody sweeps for them. Search
before every build for: `TODO`, `FIXME`, `<...>` angle-bracket placeholders,
sentences trailing off in `....`, and `%` comments in the author's own language
where the rest of the file is English. In this paper that sweep found four live
gaps, including a `<descrever rapidamente o que a solucao faz>` and a sentence
ending `neither approach relies on....`, both of which would have printed.

## 7. Grammar offenders to grep for

Recurring failures caught in review, worth checking on any draft:

- Dangling participles: `thus, requiring...`
- Sentence fragments: `Hence, rendering this type of attack difficult.`
- Number disagreement: `These type of attacks`; `sessions, in which these are ... before it reaches`
- Comma after a citation: `KLAGE \cite{x}, builds`

## 8. Verification commands

Run these on the `.tex` and on the compiled PDF before circulating a draft.

```bash
# em dashes: must be 0, including a spaced hyphen used as a dash
grep -c -- '---' article.tex
grep -n ' - ' article.tex | grep -v '&'        # table cells use '-' legitimately;
                                                # ignore hits inside verbatim code (e.g. ?n - 1)

# semicolons in the body, comments stripped: keep only enumeration separators
python3 - <<'EOF'
import re
s = open('article.tex').read()
b = s[s.index(r'\section{Introduction}'):s.index(r'\section*{Acknowledgment}')]
b = re.sub(r'(?<!\\)%.*', '', b)                  # drop comments
for m in re.finditer(r'(?<!\\);', b):              # skip \; math spacing
    print('...' + b[max(0, m.start()-50):m.start()].replace('\n', ' ') + ' ;')
EOF

# antithesis: review each hit, keep only those where contrast is the claim
grep -noE "rather than [^,.;]{0,45}|is not [^.]{3,45}but |not only [^.]{0,40}|, not [a-z]+ [a-z]+[,.]" article.tex

# citation as grammatical subject: must be empty
grep -noE "(^|\. |; )\\\\cite\{[^}]*\} [a-z]+" article.tex

# author names in the body: must be empty
grep -noE "[A-Z][a-z]+ (et al\.|and [A-Z][a-z]+)~?\\\\cite" article.tex

# section immediately followed by its first subsection: must be empty
awk '/^\\section\{/{s=NR; getline; getline; if ($0 ~ /^\\subsection/) print s}' article.tex

# unfinished text: must be empty
grep -n "TODO\|FIXME\|\.\.\.\.\|<[a-z].*>" article.tex
```

Widow detection needs the rendered PDF, since it depends on line breaking:

```bash
pdftotext article.pdf flow.txt
python3 - <<'PY'
lines = [l.rstrip() for l in open('flow.txt')]
bib = next((i for i,l in enumerate(lines) if 'EFERENCES' in l.upper()), len(lines))
for i, l in enumerate(lines):
    s = l.strip()
    if not s or len(s.split()) > 3 or len(s) > 32: continue
    prev = lines[i-1].strip() if i else ''
    if len(prev) < 44 or not s.endswith(('.', ')', '.]')): continue
    if bib < i < bib + 130: continue          # bibliography: leave alone
    print(f'widow: {s!r}  after ...{prev[-46:]}')
PY
```

Bibliography entries produce widows too. Leave them: they are generated from the
`.bib` fields, and shortening them mutilates the reference.

## 9. Coherence checks a style pass misses

Grep cannot see these, so read for them. Each one was found in this paper after
several style passes had already been declared clean.

- **A list that contradicts its own heading.** Per-session features (`connection
  duration, route entropy`) listed as signals that "live between sessions".
- **Unit drift.** `each request is indistinguishable` in a paper whose unit is
  the session.
- **A claim the paragraph refutes.** `both parameters are calibrated rather than
  assumed`, three sentences before admitting one is swept because no measurement
  exists.
- **The same fact stated twice with different numbers** (`over 75` and
  `seventy-five`).
- **Section headings that miscount.** "Five limitations" over seven paragraphs,
  two of which are not limitations.
- **A baseline described by its source's method, not by what was run.** Check
  every "we reimplement X" against the code.
- **Numbers in a table with no artifact behind them.** Every value should trace
  to a committed results file; trace them before submission.

## 10. Translated versions

When a paper has a translation, the two drift silently. Two lessons from this
repository:

**Port changes, do not re-translate from memory.** But first *verify* the
translation is where you think it is. The Portuguese version here carried a
commit message saying it had been resynced, yet had drifted in captions and ran
13% longer. Regenerating from the current source was more reliable than patching
a diff onto an unknown base.

**Page limits usually apply to one version only.** The widow compaction was
applied to the English submission and deliberately skipped in the Portuguese
rendering, which is not page-limited and runs 15--20% longer. Record such
asymmetries in the file header so the next person does not "fix" them.
