> Historical checklist for the original submission. The post-review revision
> is documented in `FEEDBACK_RESPONSE.md`; the earlier page-count and bundle
> checks below do not certify the revised artifacts.

# AAAI-27 Meta-Routing Submission Checklist

Checked against the official AAAI-27 Main Technical Track submission
instructions, AAAI-27 supplementary-material instructions, the provided
AAAI-27 Author Kit, and the OpenReview form snapshot.

## Main PDF

- File: `submission/AAAI27_Anonymous.pdf`
- Format: AAAI-27 anonymous submission template via `\usepackage[submission]{aaai2027}`.
- Paper size: US Letter, 8.5 x 11 inches.
- Length: 7 pages total in the current PDF.
- Content length: pages 1--6 contain technical content; page 7 is references only.
- Author block: anonymous (`Anonymous Submission`, empty affiliations).
- Acknowledgments omitted for anonymous review.
- Ethical statement included inside the 7-page content limit.
- Reproducibility checklist: available separately as `submission/AAAI27_ReproducibilityChecklist.pdf`.
- No external artifact link is included in the anonymous paper.
- PDF metadata was stripped by `prepare_submission.py`.

AAAI-27 instructions state that review submissions must be anonymous, use the
AAAI two-column camera-ready style, be US Letter, and contain at most 7 pages of
non-reference content, with pages 8--9 reserved exclusively for references. The
completed reproducibility checklist must be uploaded separately from the main
paper in the designated OpenReview field.

## OpenReview Upload Fields

- Main PDF: `submission/AAAI27_Anonymous.pdf`
- Reproducibility Checklist: `submission/AAAI27_ReproducibilityChecklist.pdf`
- Code and Data Supplement: `submission/code_data_supplement.zip`
- Technical Supplement: leave blank unless adding a separate anonymous PDF.
- Media Supplement: leave blank unless adding anonymous media.
- Country of Institutions: United States.
- License: CC BY 4.0.
- Submission-policy acknowledgements: check only after confirming every author
  has a complete OpenReview profile, the paper is not under review at another
  archival venue, and any simultaneous related submissions are cited anonymously.

## arXiv / Source Compilation Package

Use `submission/AAAI27_MetaRoute_arxiv_source.zip` when a system asks for LaTeX source files. This archive is intentionally separate from the code/data supplement.

Included source files:

- `main.tex`
- `main.bbl`
- `references.bib`
- `aaai2027.sty`
- `aaai2027.bst`
- `figures/executable_tradeoffs.pdf`
- `figures/executable_tradeoffs.png`

Validation completed from a clean temporary extraction:

- `pdflatex main.tex`
- `pdflatex main.tex`

Result: compiled successfully with no undefined citations and no missing `figures/executable_tradeoffs.pdf` error.

## Code/Data Supplement

Use `submission/code_data_supplement.zip` only for the AAAI code/data supplement. It is not a complete LaTeX source package and should not be uploaded as the arXiv/source compilation bundle.

The code/data supplement has been scanned for author names, affiliations, and
repository URLs and should remain anonymous during review.
