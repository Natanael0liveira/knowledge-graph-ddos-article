# Writing style for scientific papers

A portable style guide, drawn from many revision rounds of the NOMS 2027 submission. The rules are
general. The examples come from this paper, because concrete failures teach better than abstract
advice.

The verification commands in the last section turn most rules into checks a script can run before
anyone reads the draft.

---

## 1. Register

**Naturalized prose in the venue's idiom.** It should read as a careful researcher writing plainly.
It should read neither as a machine performing sophistication nor as marketing copy. It should be
fluid and revised.

**Plain, frequent words, one idea per sentence.** The content is already hard, so the prose should
be easy. Pick the most common word that is still exact. Give each sentence one idea. Leave to the
tables the numbers they already print.

**No excessive jargon.** A term earns its place only when no ordinary word does the same work.
Terminology the field requires stays. Ornament goes.

**Vary common words.** Keep the register common enough to read at speed, and rotate word choice
within that band, so the same word does not recur in adjacent sentences. Both failure modes are
real: the rare word that stops the reader, and the same verb four times in a paragraph.

**American spelling.** Write analyzed, behavior, modeling, catalog, centered. Quoted titles keep
their own spelling.

> **Watch the repair as well as the fault.** Removing one tic tends to install another. Purging
> `rather than` from this paper produced nine new occurrences of `X itself` in a single pass, 14 in
> the file, which then had to be cut back to 7. Whenever you fix a pattern globally, count what you
> replaced it with.

## 2. Forbidden constructions

**No em dashes.** In LaTeX that is `---`, in Markdown the character itself. Restructure the
sentence, or use a comma, a colon or a parenthesis. The count stays at zero. In Markdown, write
number ranges with the en dash (58–62), since `--` is LaTeX syntax.

**No "not X, but Y" antithesis.** This includes `is not ... but ...`, `not merely ... but ...`,
`X, not only Y`, `X, not Y`, and heavy use of `rather than`. The pattern reads as manufactured
emphasis. State the positive claim directly. If the contrast is needed, carry it across two
sentences.

| Before | After |
|---|---|
| `the collapse is a property of the representation, not of the learner` | `which locates the collapse in the representation: no hypothesis class recovers what the features discarded` |
| `Cross-session relatedness is not one relation but a structured family` | `Cross-session relatedness is a structured family of relations` |
| `The formalism is not intended to raise AUC but to provide a typed vocabulary` | `The formalism exists to provide a typed vocabulary` |
| `DDoS has changed in kind, not only in scale` | `DDoS attacks continue to grow in volume and frequency` |

The rewrites are also shorter and stronger.

The last row deserves a second look: the aphorism was also unsupported. The paragraph it opened only
showed growth in scale, never a change in kind. An antithesis often signals a claim the text does
not back, which is a second reason to remove it.

**Keep a contrast only when it is the claim.** The test: does removing the contrast lose
information, or only emphasis? Purging every instance mechanically makes the prose stilted, which
breaks rule 1. The current paper keeps none. One earlier survivor,
`calibrated rather than assumed`, was removed because it was false (section 9).

**"As does X" extends every qualifier.** `with no observed collateral, as does an unseen filter`
gave that filter "no observed collateral", when it had 0.03%. Give X its own number.

**Semicolons are a register marker.** Three NOMS 2024 papers used 0 to 0.6 per thousand words. This
paper once had 5.4. Round 75 has two in the body, both inside parentheses, about 0.3 per thousand
words. Keep semicolons for separating enumerated items, such as `(i) ...; (ii) ...`. A semicolon
that joins two independent clauses becomes a full stop, which is also the cheapest way to cut a long
sentence.

**Long sentences.** NOMS prose runs at a median of 18 to 20 words per sentence, with 1 to 3 percent
above 45 words. Split any sentence above 45 words unless it is a definitional list. A contribution
statement is never one sentence: here it once ran to 187 words. `This paper makes three
contributions. (i) \emph{Profile-relative scoping.} We select fingerprints that occur more often
than expected from normal traffic.` keeps the numbering, names each contribution and gives it its
own sentences.

## 3. Flow

**Paragraphs connect.** Each opens by picking up where the previous one landed. `therefore` is the
model connector. Build continuity with small adjustments at the seams. Transitional boilerplate adds
words without adding continuity.

**Paragraphs of even length.** Keep body paragraphs at about 60 to 200 words, with a median near
120. Section lead-ins stay one short sentence by design. Split a long paragraph only where the topic
turns, so that the next sentence already opens the new topic. Merge a lone short paragraph into the
one it leads into.

**Never go straight from a section heading to its first subsection.** Every section needs a short
paragraph announcing what the subsections will do. A reader who lands mid-document should learn
where they are before the detail starts.

**Related work closes by stating the boundary.** Name the properties that no published approach
holds together, and so where this work acts and the others do not. A related-work section that only
summarizes has not done its job.

**Single-sentence paragraphs are weak in two-column layouts.** Merge them into a neighbor. In this
paper the typographic fix and the prose fix coincided: a one-sentence paragraph was both a widow
generator and a structural blemish.

## 4. Claims and their scope

**The abstract says what was done and found.** Name the mechanism once, in plain words. Give three
or four headline numbers and keep every qualifier in short form. Define each coined term before its
first use. Close with what the results give an operator. The method's details belong in the body.

**Contributions name what the work delivers.** Here they are (i) profile-relative scoping, (ii)
statistical calibration and the calibration floor it sets, and (iii) the session ontology as the
specification the queries compile from. Give each one or two short sentences. The measurements are
the evidence behind them, and per-standard details belong in the body.

**A lead sentence carries the claim's scope.** When a paragraph's point moves to its first sentence
and the qualifiers move later, the lead must still be true on its own. Say which configurations,
pooled or per endpoint, alone or behind the gate. One rewrite lost "scope alone", "pooled across
endpoints" and "average stack", and made a claim false.

**Before writing "only", check every row.** Replacing a list that limited a claim with concrete
numbers once widened "only X" to every configuration in the table, though the unseen filter also
stayed within the budget.

**"Versus" for number comparisons.** Write `20 versus 31`. Keep "against" for its other senses,
such as tested against or judged against a profile.

**State limits in measured words.** Say what limits the evidence, such as few gate openings, and
call the evidence "limited". Words such as "weak" or "thin" judge the work instead of describing the
limit. Keep every number and qualifier.

**Keep every qualifier through a rewrite.** A language revision, whether from a tool, a coauthor or
the author, reads smoothly but tends to drop qualifiers (all, alone, there, any, only, post hoc). It
also changes key terms ("specify" into "represent"), joins clauses with semicolons, adds dashes and
`X, not Y`, and puts a wrong subject on a verb. Read every changed sentence against the original.
Accept a rewrite only if it keeps every qualifier, number and term. Then check the layout again,
since a line gained or lost moves headings and floats.

## 5. Citations

**A citation is never a grammatical subject.**

| Wrong | Right |
|---|---|
| `\cite{x} applies PCA to flow statistics` | `PCA is applied to flow statistics~\cite{x}` |
| `The meta-analysis of \cite{x} finds` | `A meta-analysis of seventy-five studies finds~\cite{x}` |

**Author names in the body reduce to the citation alone**, including in table row labels. Describe
the method and cite the source: `PCA over flow statistics~\cite{x}` replaces
`Fernandes et al.~\cite{x}`. Exception: a named system you compare against throughout (KLAGE here)
keeps its name, because the reader needs a handle for it.

**Check every changed citation against [`references.md`](references.md).** A rewrite can swap roles
(Fernandes and Bharathi), credit a figure to the wrong survey (Odusami's 75 studies and 47% given
to Tripathi) or reverse a claim under a new citation. Compare each changed citation with the role
recorded there. Check the cited claim against the source as well: a possessive once made a dataset
paper criticize itself, when it had criticized the earlier datasets.

## 6. Typography

**No paragraph should end with one or two words on their own line.** A widow line wastes a full line
of a page-limited paper. Fix it by removing redundant words from anywhere in the paragraph.

The arithmetic: a column holds roughly 58–62 characters. To absorb a widow of *n* characters, free
about *n* characters anywhere in that paragraph. Expect to iterate, because each fix reflows the
text and can create a new widow elsewhere. In this paper it took four rounds to go from 33 widows to
zero.

Cuts that worked, none of which lost meaning:

- `which is precisely what makes them difficult` → `which is what makes them difficult`
- `with perfectly known coordination ground truth` → `with known coordination ground truth`
- `all of them laboratory testbed captures` → `all laboratory testbed captures`
- `A human-analyst study remains future work` → `A human-analyst study is future work`

**Table and figure captions belong on one rendered line.** Parameters move to a table note
(`\vspace{2pt}` plus a `\footnotesize` block after the `tabular`), which is more compact than a
caption. Notes are justified across the full column width. Captions are centered small caps that
break early and eat vertical space.

**Float placement.** In a two-column document, `[!ht]` on a `figure*` or `table*` is a trap: LaTeX
silently ignores the `h`, and the `!` discards the float-placement parameters the preamble tuned.
Use `[t]`. When two single-column floats stack in the same column, give the second `[b]` so body
text separates them.

**Check the page limit where the rules put it.** Under the NOMS 2027 rules, the main text includes
the Acknowledgment and must end on page 8. References and appendices may follow, up to 12 pages in
all. With `pdftotext -layout`, find the REFERENCES heading and check that it starts on page 8,
after the Acknowledgment. Read the heading's horizontal offset as well: on a two-column page, text
that starts past the middle is in the right column. A check that recorded only the page of a heading
once reported "within limits" for weeks, while a third of a column of body had spilled onto the next
page.

**Wide floats slip in cascades.** A `table*` or `figure*` lands at the top of the page *after* its
declaration. If the text before it grows, it slips a page and pushes the next wide float too.
Declare wide floats a little earlier in the source than where they are discussed. The printed
position then stays put.

**Verify placement by measuring.** Two float moves in this paper looked right in the abstract and
were wrong in the PDF. Both were reverted after measurement. A float belongs on the same page as the
text discussing it, and moving it "somewhere cleaner" usually breaks that.

## 7. Unfinished text

Review notes and placeholders reach the PDF if nobody sweeps for them. Search before every build for
`TODO`, `FIXME`, `<...>` angle-bracket placeholders, sentences trailing off in `....`, and `%`
comments in the author's own language where the rest of the file is English. In this paper that
sweep found four live gaps. Two of them would have printed: a
`<descrever rapidamente o que a solucao faz>` (Portuguese for "briefly describe what the solution
does") and a sentence ending `neither approach relies on....`.

## 8. Grammar offenders to grep for

Recurring failures caught in review, worth checking on any draft:

- Dangling participles: `thus, requiring...`
- Sentence fragments: `Hence, rendering this type of attack difficult.`
- Number disagreement: `These type of attacks`; `sessions, in which these are ... before it reaches`
- Comma after a citation: `KLAGE \cite{x}, builds`

## 9. Coherence checks a style pass misses

Grep cannot see these, so read for them. Each one was found in this paper after several style passes
had already been declared clean.

- **A list that contradicts its own heading.** Per-session features (`connection duration, route
  entropy`) listed as signals that "live between sessions".
- **Unit drift.** `each request is indistinguishable` in a paper whose unit is the session.
- **A claim the paragraph refutes.** `both parameters are calibrated rather than assumed`, three
  sentences before admitting that one is swept because no measurement exists.
- **The same fact stated twice with different numbers** (`over 75` and `seventy-five`).
- **Section headings that miscount.** "Five limitations" over seven paragraphs, two of which are not
  limitations.
- **A baseline described by its source's method instead of what was run.** Check every "we
  reimplement X" against the code.
- **Numbers in a table with no artifact behind them.** Every value should trace to a committed
  results file. Trace them before submission.
- **A statistic attached to one item.** `each alarm blocking a median 30%`: a median runs over the
  alarms, so write `its alarms blocking a median 30%`.
- **A word that rounds the number next to it.** `three times as many pairs` where the weights give
  1/0.3 = 3.3; `the same windows` for 71 versus 70 of 90. Recompute every ratio and "same" the
  prose asserts.
- **A pointer to where the claim is not.** An `(Appendix E)` attached to a sentence the appendix
  never discusses. Check each pointer against its target.
- **A symbol used before its definition, or two symbols for one set.** Read the method section in
  order and note where each symbol first appears.
- **A deliberate switch of polarity, "fixed" into a list.** `moves no rate by more than 0.3, no
  share by more than 4.5, and a collateral median by up to 7.2` flags the one quantity that does
  move. Folding it into the negated list turns a caveat into a robustness claim. Fix the grammar and
  keep the caveat.

## 10. Translated versions

When a paper has a translation, the two drift silently. Three lessons from this repository:

**Port each change, sentence by sentence.** First check which version the translation follows. The
Portuguese version here once carried a commit message saying it had been resynced, yet it had
drifted in captions and ran 13% longer. Regenerating it from the current source was more reliable
than patching a diff onto an unknown base. The Portuguese paper is now a sentence-by-sentence
translation of round 74, so each English edit is ported as the matching Portuguese sentence.

**Check meaning as well as numbers.** A number-by-number comparison of the two versions passed while
a rewrite had turned "corroborates" into "confirms", dropped "observed" and "only", and added an
explanation of DTW that credited it with what the use of inter-arrival intervals does. Read the
translation against the source paragraph by paragraph for qualifiers and claims.

**Page limits usually apply to one version only.** The widow compaction was applied to the English
submission and deliberately skipped in the Portuguese rendering, which is not page-limited and runs
15–20% longer. Record such asymmetries in the file header so the next person does not "fix" them.

## 11. Verification commands

Run these from the paper's directory, on the `.tex` and on the compiled PDF, before circulating a
draft. Every "must be" check passes on the round-75 source. The review checks list hits to read one
by one.

```bash
# em dashes: must be 0
grep -c -- '---' article.tex

# a spaced hyphen used as a dash: must be empty
# (comment lines and table rows are skipped; ignore hits inside verbatim code, such as ?n - 1)
grep -n ' - ' article.tex | grep -v '^[0-9]*:%' | grep -v '&'

# semicolons in the body, comments stripped: keep only enumeration separators
python3 - <<'EOF'
import re
s = open('article.tex').read()
b = s[s.index(r'\section{Introduction}'):s.index(r'\section*{Acknowledgment}')]
b = re.sub(r'(?<!\\)%.*', '', b)                  # drop comments
for m in re.finditer(r'(?<!\\);', b):              # skip \; math spacing
    print('...' + b[max(0, m.start()-50):m.start()].replace('\n', ' ') + ' ;')
EOF

# antithesis: review each hit, keep only those where the contrast is the claim
grep -c 'rather than' article.tex
grep -noE "rather than [^,.;]{0,45}|is not [^.]{3,45}but |not only [^.]{0,40}|, not [a-z]+ [a-z]+[,.]" article.tex
grep -n ', not ' article.tex | grep -v '^[0-9]*:%'      # the "X, not Y" form

# "as does X": review each hit, since X inherits every qualifier of the first clause
grep -nw -e 'as does' -e 'as do' article.tex | grep -v '^[0-9]*:%'

# citation as grammatical subject: must be empty
grep -noE "(^|\. |; )\\\\cite\{[^}]*\} [a-z]+" article.tex

# author names in the body: must be empty
grep -noE "[A-Z][a-z]+ (et al\.|and [A-Z][a-z]+)~?\\\\cite" article.tex

# section immediately followed by its first subsection: must be empty
awk '/^\\section\{/{s=NR; getline; getline; if ($0 ~ /^\\subsection/) print s}' article.tex

# unfinished text: must be empty
grep -n "TODO\|FIXME\|\.\.\.\.\|<[a-z].*>" article.tex

# paragraph lengths: review paragraphs outside 60 to 200 words (lead-ins are short by design)
python3 - <<'EOF'
import re
s = open('article.tex').read()
b = s[s.index(r'\section{Introduction}'):s.index(r'\section*{Acknowledgment}')]
b = re.sub(r'(?<!\\)%.*', '', b)                                   # drop comments
b = re.sub(r'\\begin\{(table\*?|figure\*?|listing)\}.*?\\end\{\1\}', '', b, flags=re.S)  # drop floats
for p in re.split(r'\n\s*\n', b):
    words = len(re.sub(r'\\(sub)?section\{[^}]*\}|\\label\{[^}]*\}', '', p).split())
    if words and not 60 <= words <= 200:
        print(words, ' '.join(p.split())[:70])
EOF
```

The page limit and the widows need the rendered PDF, since both depend on line breaking.

```bash
# page limit: under NOMS 2027 the REFERENCES heading must start on page 8
pdftotext -layout article.pdf layout.txt
python3 - <<'PY'
import re
pages = open('layout.txt').read().split('\f')
for i, page in enumerate(pages, 1):
    lines = page.splitlines()
    width = max((len(l) for l in lines), default=0)
    for line in lines:
        for name, pat in (('Acknowledgment', r'A\s?CKNOWLEDGMENT'), ('References', r'R\s?EFERENCES')):
            m = re.search(pat, line)
            if m:
                side = 'right' if m.start() > width / 2 else 'left'
                print(f'{name}: page {i}, {side} column')
PY

# widows: review each hit
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

Bibliography entries produce widows too. Leave them: they are generated from the `.bib` fields, and
shortening them mutilates the reference.
