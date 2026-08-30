---
name: multi-format-paper-publisher
description: Publish a paper as .tex (embedded thebibliography, no .bib), .pdf, .docx, and .txt under Downloads. Run the Simon Willison LLM cliché highlighter patterns on the plain text before calling the job done.
---

# Multi-format paper publisher

## Output

Write all four files to `/workspace/Downloads/` (and the project `Downloads/` tree if that is where the Mac sync looks):

- `<stem>.tex`
- `<stem>.pdf` (pdflatex twice)
- `<stem>.docx` (pandoc from the .tex)
- `<stem>.txt` (pandoc `-t plain` from the .tex)

Do not emit `references.bib`. Use `\begin{thebibliography}...\end{thebibliography}`.

## LaTeX rules

- `article`, 11pt, `amsmath`, `hyperref`, `url`
- Acknowledgments section must name Cursor for drafting, formatting, and solutioning
- Compile with `pdflatex` twice from the output directory

## Cliche gate

Before finish, run `scripts/check-llm-cliches.py` (or the Node port of https://tools.simonwillison.net/llm-cliche-highlighter) on the `.txt`. Zero matches required. Rewrite any hit. Avoid Wikipedia “Signs of AI writing” tails: participle “, highlighting …”, “not only/just … but”, AI vocab (delve, tapestry, pivotal, …), “experts argue”, “despite these challenges”, colon-triples, three identical sentence openers.
