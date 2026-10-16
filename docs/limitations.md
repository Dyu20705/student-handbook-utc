# Scope and limitations

- The source is the repository's K67 PDF. It does not automatically incorporate
  later regulations or policies from other campuses/cohorts.
- Text extraction is not specialized OCR or table reconstruction. Headings and
  printed page numbers are estimates; use PDF pages for verification.
- Citation validation establishes that IDs were retrieved. It does not establish
  entailment, completeness, or factual correctness. Answers can omit exceptions,
  negation, numeric thresholds or conditions spanning pages.
- Generation may over-refuse or vary between runs even with temperature zero.
  The q15 scholarship case has previously omitted conditions despite passing
  keyword matching, including a post-hardening benchmark and HTTP smoke with
  unchanged retrieved context. A final generation instruction now requires the
  full relevant condition list. Repeated tests and source comparison remain
  necessary; this instruction is not a completeness guarantee.
- The 25-question benchmark has 22 answerable and three unanswerable cases.
  Hit@k, keyword matches and citation-page matches are automatic proxies.
  Known-question development review is not an independent evaluation.
- A 9B model can take tens of seconds or longer on CPU. One inference at a time
  is supported. HTTP timeout is an I/O timeout, not an end-to-end deadline.
- This is a trusted single-machine deployment. Multi-worker serving, Internet
  exposure, multi-tenancy and the Chroma HTTP server are outside its supported scope.
- The removed research modules and unimplemented source-intake designs are not
  runtime features. The current loader accepts an operator-provided PDF or TXT file.

Historical qualification describes its recorded runtime commit only. Passing CI
does not qualify a new model, source or runtime. See [operations](operations.md)
for the separate local release gate and evidence retention policy.
