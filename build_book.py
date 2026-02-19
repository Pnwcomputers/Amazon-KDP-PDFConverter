# KDP Book Build Script
import os
import re
import sys
import shutil
import tempfile
import subprocess
from urllib.parse import unquote

# ──────────────────────────────────────────────
# TOOL PATHS (Update these for your environment)
# ──────────────────────────────────────────────
PANDOC_BIN = "pandoc"  # Assumes pandoc is in your PATH
XELATEX_BIN = "xelatex" # Assumes xelatex is in your PATH

# ──────────────────────────────────────────────
# BOOK METADATA
# ──────────────────────────────────────────────
BOOK_TITLE = "Project Title"
BOOK_SUBTITLE = "Project Subtitle"
BOOK_AUTHOR = "Author Name"
PDF_OUTPUT = "Project_Output_KDP.pdf"

# ──────────────────────────────────────────────
# KDP 8.5x11 GEOMETRY
# ──────────────────────────────────────────────
PAPER_WIDTH = "8.5in"
PAPER_HEIGHT = "11in"
INNER_MARGIN = "1in"
OUTER_MARGIN = "0.75in"
TOP_MARGIN = "1in"
BOTTOM_MARGIN = "0.75in"

# ──────────────────────────────────────────────
# LATEX HEADER
# ──────────────────────────────────────────────
LATEX_HEADER = r"""
\usepackage{float}
\usepackage{fvextra}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{fancyhdr}
\PassOptionsToPackage{hyphens}{url}
\usepackage{xurl}
\usepackage{placeins}
\usepackage[width=0.9\linewidth,font=small]{caption}

% -- IMAGE CONSTRAINTS --
\makeatletter
\def\maxwidth{\ifdim\Gin@nat@width>0.8\linewidth 0.8\linewidth\else\Gin@nat@width\fi}
\def\maxheight{\ifdim\Gin@nat@height>0.35\textheight 0.35\textheight\else\Gin@nat@height\fi}
\makeatother
\setkeys{Gin}{width=\maxwidth,height=\maxheight,keepaspectratio}

% -- FIGURE PLACEMENT --
\let\Oldsubsection\subsection
\renewcommand{\subsection}{\FloatBarrier\Oldsubsection}

% -- TEXT & CODE WRAPPING --
\fvset{breaklines=true,breakanywhere=true,fontsize=\footnotesize}
\sloppy
\setlength{\emergencystretch}{3em}
\tolerance=2000
\hyphenpenalty=100

% -- HEADERS / FOOTERS --
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE,RO]{\thepage}
\fancyhead[RE]{\textit{\BOOK_TITLE}}
\fancyhead[LO]{\begin{minipage}[b]{0.8\textwidth}\raggedright\textit{\leftmark}\end{minipage}}
\renewcommand{\headrulewidth}{0.4pt}
\providecommand{\tightlist}{%
  \setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
""".replace("\BOOK_TITLE", BOOK_TITLE)

# ──────────────────────────────────────────────
# CHAPTER STRUCTURE
# ──────────────────────────────────────────────
PARTS = [
    {"folder": "Part-I", "title": "Part I: Introduction", "subtitle": "Introduction subtitle."},
    # Add more parts as needed
]
APPENDICES = [
    "Appendices/AppendixA.md",
]

# ══════════════════════════════════════════════
# PREPROCESSING FUNCTIONS
# ══════════════════════════════════════════════

def natural_keys(text):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]

def create_part_divider(title, subtitle):
    return f"\n\\newpage\n\n# {title}\n\n*{subtitle}*\n\n\\newpage\n\n"

def wrap_code_smart(content, max_width=75):
    lines = content.split('\n')
    result = []
    in_code_block = False
    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
            continue
        if in_code_block and len(line) > max_width:
            stripped = line.lstrip()
            indent = line[:len(line) - len(stripped)]
            cont_indent = indent + "  "
            chunks, remaining, first_chunk = [], stripped, True
            while remaining:
                avail = max_width - len(indent if first_chunk else cont_indent)
                if avail < 10: avail = 10
                if len(remaining) <= avail:
                    chunks.append((indent if first_chunk else cont_indent) + remaining)
                    break
                break_at = -1
                for ch in [' ', ',', '|', '/', '.', '-', '\\', ':', ';', '=']:
                    pos = remaining.rfind(ch, 0, avail)
                    if pos > 0:
                        break_at = pos + 1
                        break
                if break_at <= 0: break_at = avail
                chunks.append((indent if first_chunk else cont_indent) + remaining[:break_at].rstrip())
                remaining = remaining[break_at:].lstrip()
                first_chunk = False
            result.append('\n'.join(chunks))
        else:
            result.append(line)
    return '\n'.join(result)

def preprocess_markdown(content):
    # Strip YAML and decorative separators
    content = re.sub(r'^-{3,}\s*$', '', content, flags=re.MULTILINE)
    # HTML to MD Images
    content = re.sub(r'<img\s+[^>]*src="([^"]+)"[^>]*>', r'![](\1)', content)
    # Path normalization
    def fix_match(match):
        alt, raw_path = match.group(1), match.group(2)
        clean = re.sub(r'^(\.\./)+', '', unquote(raw_path)).lstrip('/')
        return f"![{alt}]({clean})"
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_match, content)
    # Character cleaning
    content = content.replace('\u200B', '')
    # Convert MD links to bold (for print)
    content = re.sub(r'\[([^\]]+)\]\([^)]*\.md[^)]*\)', r'**\1**', content)
    return wrap_code_smart(content)

# ══════════════════════════════════════════════
# MAIN BUILD
# ══════════════════════════════════════════════

def main():
    repo_root = os.path.abspath(os.getcwd())
    output_dir = os.path.join(repo_root, "build")
    os.makedirs(output_dir, exist_ok=True)
    build_temp = tempfile.mkdtemp(prefix="book_build_")

    try:
        prepared_files = []
        file_counter = 0

        for part in PARTS:
            part_path = os.path.join(repo_root, part["folder"])
            if not os.path.exists(part_path): continue

            file_counter += 1
            divider_path = os.path.join(build_temp, f"{file_counter:03d}_Divider.md")
            with open(divider_path, 'w', encoding='utf-8') as f:
                f.write(create_part_divider(part["title"], part["subtitle"]))
            prepared_files.append(divider_path)

            for root, _, files in os.walk(part_path):
                for file in sorted(files, key=natural_keys):
                    if file.endswith(".md"):
                        file_counter += 1
                        src_path = os.path.join(root, file)
                        with open(src_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                            content = preprocess_markdown(f.read()) + "\n\n"
                        dest_path = os.path.join(build_temp, f"{file_counter:03d}_{file}")
                        with open(dest_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        prepared_files.append(dest_path)

        header_path = os.path.join(build_temp, "header.tex")
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(LATEX_HEADER)

        meta_path = os.path.join(build_temp, "meta.yaml")
        with open(meta_path, 'w', encoding='utf-8') as f:
            f.write(f'title: "{BOOK_TITLE}"\nauthor: "{BOOK_AUTHOR}"\n')

        output_pdf = os.path.join(output_dir, PDF_OUTPUT)
        cmd = [
            PANDOC_BIN, *prepared_files,
            "--metadata-file", meta_path,
            f"--pdf-engine={XELATEX_BIN}",
            f"--resource-path={repo_root}",
            "-H", header_path,
            "--toc",
            "-V", "documentclass=book",
            "-V", f"geometry:paperwidth={PAPER_WIDTH}",
            "-V", f"geometry:paperheight={PAPER_HEIGHT}",
            "-V", f"geometry:inner={INNER_MARGIN}",
            "-V", f"geometry:outer={OUTER_MARGIN}",
            "-V", "mainfont=Cambria",
            "-o", output_pdf
        ]
        
        print(">> Building PDF...")
        subprocess.run(cmd, check=True)
        print(f"Build successful: {output_pdf}")

    finally:
        shutil.rmtree(build_temp, ignore_errors=True)

if __name__ == "__main__":
    main()
