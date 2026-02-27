# 📘 KDP Paperback PDF Build Script (Pandoc + XeLaTeX)

## 🧱 Print-Ready PDF Pipeline
### Compiles a multi-part Markdown book into an Amazon KDP-compliant paperback PDF
#### Built for real-world publishing pain: margins, image scaling, code overflow, and deterministic chapter ordering

---

## 🎯 START HERE

### ✅ What this repo does
This repo contains a Python build script (`build_book_template.py`) that:
- Collects Markdown chapters from your book's folder structure
- Preprocesses Markdown to prevent common KDP/PDF formatting failures
- Builds a single print-ready PDF using **Pandoc + XeLaTeX**
- Outputs your final PDF to `./build/`

### 📄 Output file
- `build/Your_Book_KDP.pdf` *(filename set by `PDF_OUTPUT` in the script)*

---

## 🚀 QUICK BUILD

### 1) Install dependencies
You need:
- **Python 3.8+**
- **Pandoc** — https://pandoc.org
- **XeLaTeX** (via MiKTeX, TeX Live, or MacTeX)

### 2) Configure the script
Open `build_book_template.py` and fill in the configuration section at the top. At minimum, set:

~~~python
# Tool paths
PANDOC_BIN   = r"C:\Program Files\Pandoc\pandoc.exe"       # or "pandoc" on Linux/macOS
XELATEX_BIN  = r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe"  # or "xelatex"

# Book metadata
BOOK_TITLE    = "Your Book Title"
BOOK_SUBTITLE = "A Descriptive Subtitle"
BOOK_AUTHOR   = "Author Name"
BOOK_YEAR     = "2025"
PDF_OUTPUT    = "Your_Book_KDP.pdf"

# Page size and margins (defaults are 8.5x11 with KDP-safe margins)
PAPER_WIDTH   = "8.5in"
PAPER_HEIGHT  = "11in"

# Define your parts/chapters (see BOOK STRUCTURE section below)
PARTS = [...]
APPENDICES = [...]
~~~

### 3) Run the build (from repo root)
~~~bash
python3 build_book_template.py
~~~

Windows alternative:
~~~powershell
py build_book_template.py
~~~

Expected console output:
- `Build Mode: 8.5x11 KDP Paperback`
- `+ Chapter 1 - Introduction.md`
- `>> Building PDF via Pandoc + XeLaTeX...`
- `BUILD COMPLETE: build/Your_Book_KDP.pdf`

---

## 🗂️ BOOK STRUCTURE

### Folder layout
The script auto-discovers `.md` files inside whatever part folders you define in `PARTS`. A typical layout looks like this:

~~~text
/
├── Part I - Introduction/
│   ├── Chapter 1 - Getting Started.md
│   └── Chapter 2 - Core Concepts.md
├── Part II - Core Topics/
│   ├── Chapter 3 - Topic A.md
│   └── Chapter 4 - Topic B.md
├── Part III - Advanced Topics/
│   └── Chapter 5 - Deep Dive.md
├── Appendices/
│   ├── AppendixA-Reference.md
│   └── AppendixB-Glossary.md
├── images/
│   └── diagram.png
├── build/              ← generated PDF appears here
└── build_book_template.py
~~~

### Defining your parts in the script
Edit the `PARTS` list to match your actual folder names:

~~~python
PARTS = [
    {
        "folder":   "Part I - Introduction",       # folder name on disk
        "title":    "Part I: Introduction",         # printed in the PDF
        "subtitle": "Overview and foundational concepts.",
    },
    {
        "folder":   "Part II - Core Topics",
        "title":    "Part II: Core Topics",
        "subtitle": "The main body of the book.",
    },
    # Add or remove parts as needed
]

APPENDICES = [
    "Appendices/AppendixA-Reference.md",
    "Appendices/AppendixB-Glossary.md",
    # Set to [] if your book has no appendices
]
~~~

### How files are collected
- Recursively scans each part folder
- Includes `*.md` files only
- Sorts filenames using natural ordering (so `Chapter 2` comes before `Chapter 10`)
- Prefixes prepared files with a counter (`001_`, `002_`, etc.) to enforce deterministic order in Pandoc

**Tip:** Use numeric prefixes in your filenames (e.g., `001_Intro.md`, `010_Core.md`) to lock the sort order regardless of filename wording.

---

## 🧠 WHAT THE SCRIPT DOES (UNDER THE HOOD)

### Stage 1 — Preprocess Markdown (KDP/PDF hardening)
The `preprocess_markdown()` function runs before Pandoc and handles:

#### 1) YAML Frontmatter Stripping
Genuine YAML frontmatter blocks (those containing `key: value` pairs) are stripped so Pandoc doesn't get confused by per-file metadata. Decorative `---` divider lines are also removed — Pandoc misinterprets them as table-row separators, which causes the "narrow column" layout bug.

#### 2) HTML `<img>` → Markdown image conversion
~~~html
<img src="images/foo.png">
~~~
becomes:
~~~markdown
![](images/foo.png)
~~~

#### 3) Image path normalization
For images like:
~~~markdown
![Alt](../../images/My%20Image.png)
~~~
The script:
- URL-decodes `%20` → space
- Strips leading `../` segments so the path resolves relative to the repo root
- Removes any leading `/`

Result:
~~~markdown
![Alt](images/My Image.png)
~~~

#### 4) Zero-width space removal
Strips `\u200B` characters — KDP flags these as non-printable markup.

#### 5) Internal `.md` cross-link conversion
Links like `[Chapter 4](../../Part II/Chapter4.md)` are meaningless in a print PDF and render as broken hyperlinks. They are replaced with bold text: `**Chapter 4**`.

#### 6) Heading normalization
Chapter and Appendix headings that are incorrectly set as H2+ are promoted to H1 to ensure correct PDF structure and table of contents generation.

#### 7) Code block hard-wrapping
Lines inside fenced code blocks that exceed ~75 characters are hard-wrapped before Pandoc sees them — the primary defense against code overflowing into the right margin.

---

## ⚙️ CONFIGURATION REFERENCE

### Book metadata
| Variable | Description |
|---|---|
| `BOOK_TITLE` | Title printed on the cover and in headers |
| `BOOK_SUBTITLE` | Subtitle (appears on title page) |
| `BOOK_AUTHOR` | Author name |
| `BOOK_YEAR` | Copyright year |
| `PDF_OUTPUT` | Output filename inside `./build/` |

### Page geometry
Defaults are set for **8.5×11 in (US Letter)** with margins that meet KDP minimums for 301–500 page books. Change `PAPER_WIDTH` / `PAPER_HEIGHT` and the margin variables for other trim sizes (e.g., A4, 6×9).

| Variable | Default | KDP Minimum |
|---|---|---|
| `INNER_MARGIN` (gutter) | `1in` | 0.625in |
| `OUTER_MARGIN` | `0.75in` | 0.25in |
| `TOP_MARGIN` | `1in` | 0.25in |
| `BOTTOM_MARGIN` | `0.75in` | 0.25in |

KDP margin requirements vary by page count and trim size. Always verify at: https://kdp.amazon.com/en_US/help/topic/G201834190

### Fonts
| Variable | Default | Notes |
|---|---|---|
| `MAIN_FONT` | `Cambria` | Body text — try `Georgia`, `EB Garamond` |
| `SANS_FONT` | `Calibri` | Headings — try `Arial`, `Open Sans` |
| `MONO_FONT` | `Consolas` | Code blocks — try `Fira Code`, `Courier New` |

Fonts must be installed on your system. XeLaTeX embeds them automatically.

---

## 🖼️ IMAGES: HOW TO NOT GET BURNED

Pandoc runs with `--resource-path=<repo_root>`, so image references should resolve from the repo root.

### ✅ Recommended image patterns
~~~markdown
![Alt text](images/diagram.png)
![Alt text](Part I - Introduction/images/picture.png)
~~~

### 🚫 Avoid if possible
- Absolute paths like `/images/foo.png`
- Deep relative paths like `../../../images/foo.png` *(the script attempts to rewrite these, but correctness depends on your actual folder layout)*

### Image size limits
The script caps images in LaTeX to prevent KDP margin violations:
- **Width:** max 80% of text width
- **Height:** max 35% of text height (~3.2in on 8.5×11)

This leaves room for the caption, float spacing, and surrounding text on the same page.

---

## 🧯 TROUBLESHOOTING

### ❌ `pandoc: command not found`
Pandoc is not installed or not on PATH.
~~~bash
pandoc --version    # verify installation
~~~
Reinstall from https://pandoc.org and reopen your terminal.

### ❌ `xelatex not found` / LaTeX package errors
TeX distribution missing or incomplete.
~~~bash
xelatex --version   # verify installation
~~~
Install MiKTeX / TeX Live / MacTeX. If MiKTeX prompts for missing packages during the build, allow the install (or pre-install the packages manually).

### ❌ A part folder is skipped with `[!] WARNING: Folder not found`
The `"folder"` value in your `PARTS` list doesn't match the actual folder name on disk. Folder names are case-sensitive on Linux/macOS.

### ❌ Images missing from the PDF
- Confirm the image file exists at the repo-root-relative path the Markdown references
- Watch for case mismatches in filenames (Linux/macOS are case-sensitive)
- Avoid unusual characters in filenames when possible
- `%20`-encoded spaces are decoded automatically

### ❌ KDP preview says "Text/Image outside margins"
Likely causes and fixes:
- **Image too large** — reduce source image dimensions, or lower the `maxheight`/`maxwidth` percentages in `LATEX_HEADER`
- **Table too wide** — simplify or convert to a list
- **Long unbroken string** (URL, hash, base64, long variable name) — manually break it in Markdown, or add a `\linebreak` hint

---

## 📦 BUILD ARTIFACTS

| Path | Description |
|---|---|
| `./build/Your_Book_KDP.pdf` | Final output PDF |
| Temp directory (printed during build) | Prepared Markdown files + `header.tex` — deleted automatically after build |

---

## 🧪 ADVANCED NOTES

### Deterministic chapter ordering
The script sorts files using natural ordering (so `Chapter 2` correctly precedes `Chapter 10`). To lock order unconditionally, use numeric prefixes in your filenames: `001_Intro.md`, `010_Core.md`, `120_Advanced.md`.

### Why XeLaTeX?
XeLaTeX handles Unicode and system fonts far more reliably than pdfLaTeX, which matters for books with special characters, non-Latin scripts, or modern font choices.

### Changing trim size (e.g., A4, 6×9)
Update `PAPER_WIDTH`, `PAPER_HEIGHT`, and the margin variables. Then verify KDP's margin requirements for that trim size and page count range before uploading.

### geometry is loaded once
`geometry` is passed exclusively through Pandoc's `-V` flags — it is not loaded in `LATEX_HEADER`. This prevents the double-loading conflict that causes cryptic LaTeX errors.

---

## ⚖️ LEGAL / PUBLISHING DISCLAIMER

This build pipeline produces a PDF file. You are responsible for:
- Verifying layout in KDP Preview before publishing
- Ensuring you have rights to all included content (text and images)
- Complying with Amazon KDP print publishing requirements

---

## 🙏 CREDITS

### Toolchain
- **Pandoc** — Markdown-to-LaTeX-to-PDF conversion engine
- **XeLaTeX** — Unicode-friendly LaTeX engine

### LaTeX packages used
`geometry`, `graphicx`, `fancyhdr`, `longtable`, `booktabs`, `fvextra`, `float`, `placeins`, `caption`, `xurl`

---

## ✅ TL;DR

1. Set your book metadata, font choices, page size, and folder structure in the script
2. Put your chapter Markdown files into the folders you defined in `PARTS`
3. Run:
~~~bash
python3 build_book_template.py
~~~
4. Grab your PDF:
~~~text
build/Your_Book_KDP.pdf
~~~
