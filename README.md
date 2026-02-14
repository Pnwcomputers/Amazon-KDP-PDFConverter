# 📘 Amazon KDP PDF Conversion Python Script (Size A4)

# 🧱 Print-Ready PDF Pipeline (Pandoc + XeLaTeX)
## Compiles a multi-part Markdown book into an Amazon KDP-friendly **A4 (210×297mm)** paperback PDF
### Built for real-world publishing pain: margins, image scaling, code overflow, and deterministic chapter ordering
---

## 🎯 START HERE

### ✅ **What this repo does**
This repo contains a Python build script that:
- Collects Markdown chapters from your book folder structure
- Preprocesses Markdown to reduce PDF/KDP formatting failures
- Builds a single **A4 paperback-ready PDF** using **Pandoc + XeLaTeX**
- Outputs your final PDF to `./build/`

### 📄 Output file
- `build/Book_Name.pdf`

---

## 🚀 QUICK BUILD

### 1) Install dependencies
You need:
- **Python 3.8+**
- **Pandoc**
- **XeLaTeX** (via MiKTeX / TeX Live / MacTeX)

### 2) Run the build (from repo root)
~~~bash
python3 build_a4_kdp.py
~~~

Windows alternative:
~~~powershell
py build_a4_kdp.py
~~~

Expected console output includes:
- `Build Mode: A4 KDP Paperback (210x297mm)`
- `+ Prepared: <chapter.md>`
- `>> Running Pandoc/XeLaTeX Build...`
- `SUCCESS! A4 PDF created at: build/PDF_Book_Name.pdf`

---

## 🗂️ REQUIRED REPO STRUCTURE

The script searches these folders at the repo root (exact names):

- `Part I - Computer Fundamentals`
- `PDF_Book_Name`
- `Part III - Computer Maintenance & Care`
- `Part V - Networking & Connectivity`
- `Part VI - Account Management & Recovery`
- `Part VII - Practical Tips & Advanced Basics`
- `Appendices`

### 📌 How files are collected
- Recursively scans each part folder
- Includes `*.md` files only
- Sorts filenames alphabetically within each folder tree
- Prefixes prepared files with a counter (`001_`, `002_`, etc.) to force deterministic order in Pandoc

Example:
~~~text
Part I - Computer Fundamentals/
  001_Intro.md
  010_Hardware_Basics.md
PDF_Book_Name/
  005_Scams.md
Appendices/
  A_Troubleshooting.md
images/
  diagram.png
build_a4_kdp.py
~~~

---

## 🧠 WHAT THE SCRIPT DOES (UNDER THE HOOD)

### ✅ Stage 1 — Preprocess Markdown (KDP/PDF hardening)
The function `preprocess_markdown()` performs:

#### 1) YAML Frontmatter Neutralization
Any line that is exactly:
- `---`

Gets replaced with:
- `***`

This prevents Pandoc from interpreting unintended YAML frontmatter boundaries.

#### 2) HTML <img> → Markdown image conversion
Example:
- `<img src="images/foo.png">`

Becomes:
- `![](images/foo.png)`

#### 3) Image path normalization (critical)
For Markdown images:
- `![Alt](../../images/My%20Image.png)`

The script:
- URL-decodes `%20` → space
- strips leading `../` segments so lookup becomes repo-root relative
- removes leading `/`

Result:
- `![Alt](images/My Image.png)`

#### 4) Zero-width space removal
Removes:
- `\u200B`

#### 5) Code block hard-wrapping
Inside fenced code blocks, lines longer than ~75 characters are hard-wrapped to reduce page overflow.

---

## 🧾 PDF BUILD CONFIGURATION

### 📕 Book metadata
Set in the script:
- `BOOK_TITLE`
- `BOOK_AUTHOR`
- `PDF_OUTPUT`

Defaults:
- `BOOK_TITLE = "The Computer Handbook"`
- `BOOK_AUTHOR = "Jon-Eric Pienkowski"`
- `PDF_OUTPUT = "PDF_Book_Name.pdf"`

### 📐 KDP A4 geometry (210mm × 297mm)
Margins set in the script:
- `INNER_MARGIN = "25mm"`
- `OUTER_MARGIN = "20mm"`
- `TOP_BOTTOM = "20mm"`

If KDP preview complains about margins or bleed, these are your first knobs to turn.

### 🧷 LaTeX safety features included
Injected via `header.tex`:
- `geometry` configured for exact A4
- `fancyhdr` headers (title + page)
- image constraint rules (max width/height with aspect ratio)
- figure locking to reduce float chaos
- code wrapping and sloppy stretch to reduce overfull boxes

---

## 🖼️ IMAGES: HOW TO NOT GET BURNED

Pandoc runs with:
- `--resource-path=<repo_root>`

So image references should resolve from the repo root.

### ✅ Recommended image patterns
- `![Alt](images/diagram.png)`
- `![Alt](PDF_Book_Name/images/phishing.png)`

### 🚫 Avoid (if you can)
- Absolute paths like `/images/foo.png`
- Deep relative paths like `../../../images/foo.png` (the script attempts to rewrite these, but correctness depends on your real layout)

---

## 🧯 TROUBLESHOOTING (COMMON FAILURES)

### ❌ `pandoc: command not found`
Cause: Pandoc not installed or not on PATH.

Fix:
- Install Pandoc
- Reopen terminal
- Verify:
~~~bash
pandoc --version
~~~

### ❌ `xelatex not found` / LaTeX package errors
Cause: TeX distribution missing or incomplete.

Fix:
- Install MiKTeX / TeX Live / MacTeX
- Verify:
~~~bash
xelatex --version
~~~
- If MiKTeX prompts for missing packages, allow install (or install manually)

### ❌ Images missing in the PDF
Fix checklist:
- Confirm the image file exists where the Markdown ultimately points (repo-root relative)
- Watch for filename mismatches (case sensitivity on Linux/macOS)
- Avoid weird characters in filenames when possible
- Ensure spaces are handled consistently (`%20` decoding is supported)

### ❌ KDP warns: “Text/Image outside margins”
Likely causes:
- an image is too large
- a table is too wide
- a long unbroken string (URLs, hashes, code, base64) is overflowing

Fixes:
- reduce image dimensions at source
- manually break long URLs/strings in Markdown
- simplify tables or convert to multi-line lists
- keep code examples reasonably line-limited

---

## 📦 BUILD ARTIFACTS

- Final PDF:
  - `./build/PDF_Book_Name.pdf`
- Temporary build directory:
  - created automatically (contains prepared Markdown + `header.tex`)
  - location is printed during build

---

## 🧪 ADVANCED NOTES (OPTIONAL)

### Deterministic ordering
Folder order is hard-coded in `parts_structure`. Within each part, files are sorted alphabetically.
Recommendation:
- Use numeric prefixes in filenames (e.g., `001_`, `010_`, `120_`) to lock order forever.

### Font handling
XeLaTeX is used for better font support and fewer Unicode headaches than pdfLaTeX.

---

## ⚖️ LEGAL / PUBLISHING DISCLAIMER

This build pipeline produces a PDF. You are responsible for:
- verifying layout in KDP Preview
- ensuring you have rights to all included content (text/images)
- complying with Amazon KDP print requirements

---

## 🙏 CREDITS

### 🧰 Toolchain
- **Pandoc** — Markdown-to-PDF conversion engine
- **XeLaTeX** — Unicode-friendly LaTeX engine
- **LaTeX packages** used include:
  - `geometry`, `graphicx`, `fancyhdr`, `longtable`, `booktabs`, `fvextra`, `float`

---

## 👤 AUTHOR

- Jon-Eric Pienkowski
- Pacific Northwest Computers

---

## ✅ TL;DR

1) Put your chapters into the required Part folders  
2) Run:
~~~bash
python3 build_a4_kdp.py
~~~
3) Grab your PDF here:
- `build/The_Name.pdf`
