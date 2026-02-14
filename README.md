# A4 KDP PDF Builder (Pandoc + XeLaTeX)

This repository includes a Python build script that compiles multiple Markdown chapters into a single, print-focused PDF sized for Amazon KDP paperback on A4 (210mm × 297mm).

It is designed to reduce common KDP preflight issues like:
- images drifting outside margins
- long code lines overflowing the page width
- inconsistent image path references across folders

## What it does

- Walks a defined set of “Part” folders (in a specific order)
- Finds all .md files (recursively) and sorts them
- Preprocesses Markdown:
  - removes/neutralizes YAML frontmatter delimiters
  - converts HTML <img> tags to Markdown image syntax
  - fixes common image path issues (URL decoding, removes ../../)
  - removes zero-width spaces
  - hard-wraps long lines inside fenced code blocks
- Builds a PDF using Pandoc + XeLaTeX
- Writes the finished PDF to ./build/

## Output

- Default PDF name:
  - build/The_Computer_Handbook_A4_KDP.pdf

## Requirements

### 1) Python
- Python 3.8+ recommended

### 2) Pandoc
- Pandoc must be installed and available in your PATH
- Verify:
  ~~~bash
  pandoc --version
  ~~~

### 3) XeLaTeX (TeX Distribution)
You need a TeX distribution that provides xelatex.

Common options:
- Windows: MiKTeX or TeX Live
- macOS: MacTeX
- Linux: TeX Live packages (including xelatex)

Verify:
~~~bash
xelatex --version
~~~

## Repository structure (expected)

The script searches these folders at the repo root (exact names):

- Part I - Computer Fundamentals
- Part II - Internet Safety & Cybersecurity
- Part III - Computer Maintenance & Care
- Part V - Networking & Connectivity
- Part VI - Account Management & Recovery
- Part VII - Practical Tips & Advanced Basics
- Appendices

Each folder may contain subfolders. The script will recursively include every .md file it finds.

Example:
~~~text
Part I - Computer Fundamentals/
  001_Intro.md
  010_Hardware_Basics.md
Part II - Internet Safety & Cybersecurity/
  005_Scams.md
Appendices/
  A_Troubleshooting.md
images/
  diagram.png
build_a4_kdp.py
~~~

## Running the build

Run from the repo root so resource paths resolve correctly:

~~~bash
python3 build_a4_kdp.py
~~~

On Windows (depending on your environment):

~~~powershell
py build_a4_kdp.py
~~~

You should see logs like:
- Build Mode: A4 KDP Paperback (210x297mm)
- + Prepared: filename.md
- >> Running Pandoc/XeLaTeX Build...
- SUCCESS! A4 PDF created at: ./build/The_Computer_Handbook_A4_KDP.pdf

## Configuration

Edit these constants near the top of the script:

- BOOK_TITLE
- BOOK_AUTHOR
- PDF_OUTPUT

Margins (A4 trim, KDP-style layout) are controlled here:

- INNER_MARGIN (default 25mm)
- OUTER_MARGIN (default 20mm)
- TOP_BOTTOM (default 20mm)

If KDP Preview flags margin issues, these values are the first place to adjust.

## How Markdown is preprocessed (important)

The script applies several transformations to make Pandoc + print layout more reliable.

### 1) YAML frontmatter delimiter neutralization
Any line that is exactly:
- ---

Is replaced with:
- ***

This helps avoid Pandoc YAML parsing behavior if frontmatter isn’t intended or is malformed.

### 2) Convert HTML <img> tags to Markdown images
Example:
- <img src="images/foo.png">

Becomes:
- ![](images/foo.png)

### 3) Image path normalization
For Markdown images like:
- ![alt](../../images/My%20Image.png)

The script:
- URL-decodes %20 into spaces
- removes leading ../ sequences so paths resolve from repo root
- strips leading /

So the example becomes:
- ![alt](images/My Image.png)

### 4) Removes zero-width spaces
These invisible characters can cause weird formatting and copy/paste artifacts:
- \u200B

### 5) Wraps long code lines inside fenced code blocks
Inside triple-backtick fenced code blocks in the source Markdown, lines longer than ~75 characters are hard-wrapped to reduce layout overflow.

Note:
- This is a pragmatic print-layout fix, but it can change how code appears (line breaks). For publication, prefer writing code examples with reasonable line lengths.

## Images: best practices

Because the build runs with:
- --resource-path=<repo_root>

Your images should be referenced as paths that resolve from the repository root.

Recommended patterns:
- ![Alt text](images/diagram.png)
- ![Alt text](Part II - Internet Safety & Cybersecurity/images/phishing.png)

Avoid:
- absolute paths like /images/diagram.png
- fragile deep paths like ../../../images/diagram.png (the script tries to fix these, but correctness depends on your real folder layout)

## Troubleshooting

### Pandoc not found
Symptom:
- pandoc: command not found

Fix:
- Install Pandoc
- Ensure it’s in PATH
- Reopen your terminal after installation

### XeLaTeX not found (or LaTeX package errors)
Symptom:
- xelatex not found
- LaTeX Error: File `...` not found

Fix:
- Install a TeX distribution (MiKTeX / TeX Live / MacTeX)
- On MiKTeX, allow on-the-fly package installs or install missing packages manually
- Confirm xelatex works in a fresh terminal

### Images not rendering in the PDF
Fix checklist:
- Confirm the referenced image file exists at the expected path
- Confirm the path resolves from repo root (or is correctly rewritten by the script)
- Avoid exotic characters in file names if possible
- Prefer consistent image directory organization (e.g., a top-level images/ folder)

### KDP “outside the margins” warnings
Common causes:
- images too large or floating unpredictably
- long unbroken text strings (URLs, code, hashes)
- tables wider than the text area

Mitigations included in this script:
- images constrained via \setkeys{Gin}{width=..., height=..., keepaspectratio}
- figures forced to [H] to prevent float drift
- code blocks break lines and shrink font
- sloppy/emergency stretch enabled to reduce overfull boxes

If warnings persist:
- reduce image sizes at the source
- manually break long strings in Markdown
- simplify wide tables (or use longtable formatting intentionally)

## Notes on build behavior

- The build output directory is created at:
  - ./build
- A temporary directory is created for the prepared Markdown + header.tex
- Prepared chapter files are renamed with a numeric prefix:
  - 001_filename.md, 002_filename.md, etc.
This ensures a deterministic compile order based on the script’s folder order and the alphabetical sort of filenames within each folder tree.

## License

Choose what fits your goals:
- MIT (for the build script)
- Proprietary (if you want to keep the publishing pipeline private)
- Dual approach: script permissive, book content copyrighted

## Author

- Jon-Eric Pienkowski
