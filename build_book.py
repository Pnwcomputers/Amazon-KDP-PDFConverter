#!/usr/bin/env python3
import os
import re
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path
from urllib.parse import unquote

# ──────────────────────────────────────────────
# BOOK METADATA
# ──────────────────────────────────────────────
BOOK_TITLE = "The Computer Handbook"
BOOK_AUTHOR = "Jon-Eric Pienkowski"
PDF_OUTPUT = "The_Computer_Handbook_A4_KDP.pdf"

# ──────────────────────────────────────────────
# KDP A4 GEOMETRY (210mm x 297mm)
# ──────────────────────────────────────────────
INNER_MARGIN = "25mm" 
OUTER_MARGIN = "20mm"
TOP_BOTTOM = "20mm"

LATEX_HEADER = r"""
\usepackage{graphicx}
\usepackage{float}
\usepackage{fvextra}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{fancyhdr}

% 1. INDEPENDENT IMAGE CONSTRAINTS
\makeatletter
\newlength{\kdpmaxwidth}
\newlength{\kdpmaxheight}
\setlength{\kdpmaxwidth}{0.85\linewidth}
\setlength{\kdpmaxheight}{0.35\textheight}
\makeatother
\setkeys{Gin}{width=\kdpmaxwidth,height=\kdpmaxheight,keepaspectratio}

% 2. FIGURE LOCKING
\let\origfigure\figure
\let\origendfigure\endfigure
\renewenvironment{figure}[1][H]{\origfigure[H]}{\origendfigure}

% 3. TEXT WRAPPING
\fvset{breaklines=true,breakanywhere=true,fontsize=\footnotesize}
\sloppy
\setlength{\emergencystretch}{3em}

% 4. A4 GEOMETRY (Exact KDP Trim)
\usepackage[paperwidth=210mm,paperheight=297mm,
            inner=""" + INNER_MARGIN + r""",outer=""" + OUTER_MARGIN + r""",
            top=""" + TOP_BOTTOM + r""",bottom=""" + TOP_BOTTOM + r""",
            footskip=12mm,headsep=10mm,headheight=14pt]{geometry}

% 5. HEADERS
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE,RO]{\thepage}
\fancyhead[RE]{\textit{The Computer Handbook}}
\renewcommand{\headrulewidth}{0.4pt}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
"""

def preprocess_markdown(content):
    # 1. Aggressive YAML Frontmatter Removal
    content = re.sub(r'(?m)^---\s*$', '***', content)
    
    # 2. Convert HTML <img> to MD
    content = re.sub(r'<img\s+[^>]*src="([^"]+)"[^>]*>', r'![](\1)', content)
    
    # 3. FIX IMAGE PATHS (CRITICAL FOR IMAGES TO RENDER)
    def fix_match(match):
        alt = match.group(1)
        raw_path = match.group(2)
        clean = unquote(raw_path)               # Removes %20 URL encoding
        clean = re.sub(r'^(\.\./)+', '', clean) # Strips ../../ so it searches repo root
        clean = clean.lstrip('/')
        return f"![{alt}]({clean})"
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_match, content)

    # 4. Remove Zero-Width Spaces
    content = content.replace('\u200B', '')
    
    # 5. Wrap code blocks for A4 width
    lines = content.split('\n')
    res, in_block = [], False
    for l in lines:
        if l.strip().startswith('```'): in_block = not in_block
        if in_block and len(l) > 75:
            res.append('\n'.join([l[i:i+75] for i in range(0, len(l), 75)]))
        else: res.append(l)
    return '\n'.join(res)

def main():
    repo_root = os.path.abspath(os.getcwd())
    output_dir = os.path.join(repo_root, "build")
    os.makedirs(output_dir, exist_ok=True)
    build_temp = tempfile.mkdtemp()
    
    print(f"Build Mode: A4 KDP Paperback (210x297mm)\nTemp: {build_temp}")

    parts_structure = [
        "Part I - Computer Fundamentals",
        "Part II - Internet Safety & Cybersecurity",
        "Part III - Computer Maintenance & Care",
        "Part V - Networking & Connectivity",
        "Part VI - Account Management & Recovery",
        "Part VII - Practical Tips & Advanced Basics",
        "Appendices"
    ]

    prepared_files = []
    file_counter = 0

    for part_name in parts_structure:
        part_path = os.path.join(repo_root, part_name)
        if not os.path.exists(part_path): continue
        
        for root, dirs, files in os.walk(part_path):
            for file in sorted(files):
                if file.endswith(".md"):
                    file_counter += 1
                    src_path = os.path.join(root, file)
                    with open(src_path, 'r', encoding='utf-8') as f:
                        content = preprocess_markdown(f.read())
                    
                    dest_path = os.path.join(build_temp, f"{file_counter:03d}_{file}")
                    with open(dest_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    prepared_files.append(dest_path)
                    print(f"  + Prepared: {file}")

    header_path = os.path.join(build_temp, "header.tex")
    with open(header_path, 'w', encoding='utf-8') as f: f.write(LATEX_HEADER)
    
    output_pdf = os.path.join(output_dir, PDF_OUTPUT)
    print("\n>> Running Pandoc/XeLaTeX Build...")
    
    cmd = [
        "pandoc", *prepared_files,
        "-M", f'title={BOOK_TITLE}',
        "-M", f'author={BOOK_AUTHOR}',
        "--pdf-engine=xelatex",
        f"--resource-path={repo_root}",
        "-H", header_path,
        "--toc",
        "--top-level-division=chapter",
        "-V", "documentclass=book",
        "-V", "classoption=openany",
        "--dpi=300",
        "-o", output_pdf
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    
    if result.returncode != 0:
        print("\nBUILD FAILED!")
        print(result.stderr)
    else:
        print(f"\nSUCCESS! A4 PDF created at:\n{output_pdf}")

if __name__ == "__main__":
    main()
