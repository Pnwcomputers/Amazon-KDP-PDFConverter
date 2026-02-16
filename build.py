#!/usr/bin/env python3
import os
import re
import shutil
import tempfile
import subprocess
from urllib.parse import unquote

# ──────────────────────────────────────────────
# TOOL PATHS (adjust if your installations differ)
# ──────────────────────────────────────────────
PANDOC_BIN = r"C:\Program Files\Pandoc\pandoc.exe"
XELATEX_BIN = r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe"

# ──────────────────────────────────────────────
# BOOK METADATA
# ──────────────────────────────────────────────
BOOK_TITLE = "The Computer Handbook"
BOOK_SUBTITLE = "Maintenance, Security, Troubleshooting"
BOOK_AUTHOR = "Jon-Eric Pienkowski"
PDF_OUTPUT = "The_Computer_Handbook_A4_KDP.pdf"

# ──────────────────────────────────────────────
# KDP A4 GEOMETRY (210mm x 297mm)
# Margins are passed via Pandoc -V flags ONLY
# to prevent double-loading of the geometry package.
# ──────────────────────────────────────────────
INNER_MARGIN = "25mm"
OUTER_MARGIN = "20mm"
TOP_MARGIN = "20mm"
BOTTOM_MARGIN = "20mm"

# ──────────────────────────────────────────────
# LATEX HEADER
# NOTE: geometry is NOT loaded here. It is set
# exclusively through Pandoc -V flags so that
# there is exactly ONE geometry specification
# in the final LaTeX document. Loading geometry
# here AND via Pandoc flags causes a conflict
# where some pages use the wrong text width,
# producing the "narrow column" bug.
# ──────────────────────────────────────────────
LATEX_HEADER = r"""
\usepackage{graphicx}
\usepackage{float}
\usepackage{fvextra}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{fancyhdr}
\usepackage{xurl}
\usepackage{placeins}

% ── IMAGE CONSTRAINTS ──────────────────────────
% Cap images to the full text width and 35% of
% text height. Using \linewidth (not a fraction)
% so images fill the column properly on all pages.
\makeatletter
\def\maxwidth{\ifdim\Gin@nat@width>\linewidth\linewidth\else\Gin@nat@width\fi}
\def\maxheight{\ifdim\Gin@nat@height>0.35\textheight 0.35\textheight\else\Gin@nat@height\fi}
\makeatother
\setkeys{Gin}{width=\maxwidth,height=\maxheight,keepaspectratio}

% ── FIGURE LOCKING ─────────────────────────────
% Force all figures to render exactly where they
% appear in the source (H = "Here, absolutely").
\let\origfigure\figure
\let\origendfigure\endfigure
\renewenvironment{figure}[1][H]{\origfigure[H]}{\origendfigure}

% Place a float barrier at every subsection so
% figures never drift past the next heading.
\let\Oldsubsection\subsection
\renewcommand{\subsection}{\FloatBarrier\Oldsubsection}

% ── TEXT & CODE WRAPPING ───────────────────────
\fvset{breaklines=true,breakanywhere=true,fontsize=\footnotesize}
\sloppy
\setlength{\emergencystretch}{3em}
\tolerance=2000
\hyphenpenalty=100

% ── HEADERS / FOOTERS ─────────────────────────
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE,RO]{\thepage}
\fancyhead[RE]{\textit{The Computer Handbook}}
\fancyhead[LO]{\textit{\leftmark}}
\renewcommand{\headrulewidth}{0.4pt}
\providecommand{\tightlist}{%
  \setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
"""

PARTS = [
    {"folder": "Part I - Computer Fundamentals", "title": "Part I: Computer Fundamentals", "subtitle": "The essential building blocks of your computer and system setup."},
    {"folder": "Part II - Internet Safety & Cybersecurity", "title": "Part II: Internet Safety & Cybersecurity", "subtitle": "Recognizing modern threats and implementing a strong defensive posture."},
    {"folder": "Part III - Computer Maintenance & Care", "title": "Part III: Computer Maintenance & Care", "subtitle": "Professional procedures for cleaning, troubleshooting, and hardware diagnosis."},
    {"folder": "Part V - Networking & Connectivity", "title": "Part IV: Networking & Connectivity", "subtitle": "Setting up and mastering your home network, peripherals, and connections."},
    {"folder": "Part VI - Account Management & Recovery", "title": "Part V: Account Management & Recovery", "subtitle": "Strategies for digital identity management and disaster recovery."},
    {"folder": "Part VII - Practical Tips & Advanced Basics", "title": "Part VI: Practical Tips & Advanced Basics", "subtitle": "Strategies for lasting performance and smart long-term technology investments."}
]

APPENDICES = [
    "Appendices/AppendixA-QuickReferenceGuides.md",
    "Appendices/AppendixB-RecommendedToolsSoftware.md",
    "Appendices/AppendixC-WhentoCallaProfessional.md",
    "Appendices/AppendixD-GlossaryofTechnicalTerms.md",
]


def resolve_executable(configured_path, fallback_name):
    """Resolve executable from configured absolute path or PATH fallback."""
    if configured_path and os.path.isfile(configured_path):
        return configured_path

    from_path = shutil.which(fallback_name)
    if from_path:
        return from_path

    return None

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

def _is_yaml_block(text):
    """Return True only if text looks like real YAML metadata (key: value pairs)."""
    for line in text.strip().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if ':' not in stripped:
            return False
    return True

def preprocess_markdown(content):
    # 1. Frontmatter removal — only strip genuine YAML blocks
    #    (files use decorative --- separators that are NOT yaml)
    if content.lstrip().startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3 and _is_yaml_block(parts[1]):
            content = parts[2].lstrip()

    # 2. Convert HTML <img> tags to Markdown image syntax
    content = re.sub(r'<img\s+[^>]*src="([^"]+)"[^>]*>', r'![](\1)', content)

    # 3. Normalise image paths — strip leading ../ so paths
    #    resolve relative to --resource-path (the repo root).
    def fix_match(match):
        alt, raw_path = match.group(1), match.group(2)
        clean = raw_path.strip().strip('\"\'')
        clean = unquote(clean)
        clean = re.sub(r'^(\.\./)+', '', clean).lstrip('/')
        return f"![{alt}]({clean})"
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_match, content)

    # 4. Remove zero-width spaces
    content = content.replace('\u200B', '')

    # 5. Heading normaliser — promote "Chapter N" headings to H1
    content = re.sub(r'^#{2,}\s*(Chapter\s+\d+.*)$', r'# \1',
                     content, flags=re.MULTILINE | re.IGNORECASE)
    content = re.sub(r'^(#+)(?=[A-Za-z0-9])', r'\1 ', content, flags=re.MULTILINE)

    return wrap_code_smart(content, max_width=75)

def main():
    pandoc_cmd = resolve_executable(PANDOC_BIN, "pandoc")
    xelatex_cmd = resolve_executable(XELATEX_BIN, "xelatex")
    if not pandoc_cmd or not xelatex_cmd:
        print("[!] ERROR: Missing required tools.")
        print(f"    - pandoc:  {'FOUND' if pandoc_cmd else 'NOT FOUND'}")
        print(f"    - xelatex: {'FOUND' if xelatex_cmd else 'NOT FOUND'}")
        print("    Update PANDOC_BIN / XELATEX_BIN or install both tools on PATH.")
        return 1

    repo_root = os.path.abspath(os.getcwd())
    output_dir = os.path.join(repo_root, "build")
    os.makedirs(output_dir, exist_ok=True)
    build_temp = tempfile.mkdtemp()

    print(f"Build Mode: A4 KDP Paperback (210x297mm)\nTemp Workspace: {build_temp}\n")

    try:
        prepared_files = []
        file_counter = 0

        for part in PARTS:
            part_path = os.path.join(repo_root, part["folder"])
            if not os.path.exists(part_path):
                print(f"  [!] WARNING: Could not find folder '{part['folder']}'. Skipping.")
                continue

            file_counter += 1
            divider_path = os.path.join(build_temp, f"{file_counter:03d}_Divider.md")
            with open(divider_path, 'w', encoding='utf-8') as f:
                f.write(create_part_divider(part["title"], part["subtitle"]))
            prepared_files.append(divider_path)

            for root, dirs, files in os.walk(part_path):
                dirs.sort(key=natural_keys)
                for file in sorted(files, key=natural_keys):
                    if file.endswith(".md"):
                        file_counter += 1
                        src_path = os.path.join(root, file)

                        with open(src_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                            content = preprocess_markdown(f.read())

                        content += "\n\n"
                        dest_path = os.path.join(build_temp, f"{file_counter:03d}_{file}")
                        with open(dest_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        prepared_files.append(dest_path)
                        print(f"  + Loaded: {file}")

        appendices_dir = os.path.join(repo_root, "Appendices")
        if os.path.exists(appendices_dir):
            file_counter += 1
            app_divider_path = os.path.join(build_temp, f"{file_counter:03d}_App_Divider.md")
            with open(app_divider_path, 'w', encoding='utf-8') as f:
                f.write("\n\\newpage\n\n# Appendices\n\n\\newpage\n\n")
            prepared_files.append(app_divider_path)

            for ap_path in APPENDICES:
                src = os.path.join(repo_root, ap_path)
                if not os.path.exists(src):
                    continue

                with open(src, 'r', encoding='utf-8-sig', errors='replace') as f:
                    content = preprocess_markdown(f.read()) + "\n\n"

                file_counter += 1
                dest_path = os.path.join(build_temp, f"{file_counter:03d}_{os.path.basename(ap_path)}")
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                prepared_files.append(dest_path)
                print(f"  + Loaded: {os.path.basename(ap_path)}")

        if not prepared_files:
            print("\n[!] ERROR: No files processed.")
            return 1

        header_path = os.path.join(build_temp, "header.tex")
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(LATEX_HEADER)

        meta_path = os.path.join(build_temp, "meta.yaml")
        with open(meta_path, 'w', encoding='utf-8') as f:
            f.write(
                f'title: "{BOOK_TITLE}"\n'
                f'subtitle: "{BOOK_SUBTITLE}"\n'
                f'author: "{BOOK_AUTHOR}"\n'
                f'date: "2025"\n'
                f'rights: "Copyright (c) 2025 {BOOK_AUTHOR}. All rights reserved."\n'
            )

        output_pdf = os.path.join(output_dir, PDF_OUTPUT)
        print("\n>> Executing Pandoc / XeLaTeX Engine...")

        # ──────────────────────────────────────────
        # CRITICAL: Geometry is set ONLY via -V flags.
        # This feeds into Pandoc's default LaTeX
        # template which loads geometry exactly once.
        # The -H header must NOT load geometry again.
        # ──────────────────────────────────────────
        cmd = [
            pandoc_cmd, *prepared_files,
            "-f", "markdown-yaml_metadata_block",
            "--metadata-file", meta_path,
            f"--pdf-engine={xelatex_cmd}",
            f"--resource-path={repo_root}",
            "-H", header_path,
            "--toc",
            "--top-level-division=chapter",
            "-V", "documentclass=book",
            "-V", "classoption=openany",
            "-V", f"geometry:paperwidth=210mm",
            "-V", f"geometry:paperheight=297mm",
            "-V", f"geometry:inner={INNER_MARGIN}",
            "-V", f"geometry:outer={OUTER_MARGIN}",
            "-V", f"geometry:top={TOP_MARGIN}",
            "-V", f"geometry:bottom={BOTTOM_MARGIN}",
            "-V", "geometry:footskip=12mm",
            "-V", "geometry:headsep=10mm",
            "-V", "geometry:headheight=15pt",
            "-V", "mainfont=Cambria",
            "-V", "sansfont=Calibri",
            "-V", "monofont=Consolas",
            "--dpi=300",
            "-o", output_pdf
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding='utf-8', errors='replace'
        )

        if result.returncode != 0:
            print("\n[!] BUILD FAILED. LATEX LOG:")
            print(result.stderr)
            return result.returncode
        else:
            print(f"\n[OK] A4 PDF generated at:\n{output_pdf}")
            return 0

    finally:
        shutil.rmtree(build_temp, ignore_errors=True)
        print("  * Temporary workspace cleared.")

if __name__ == "__main__":
    raise SystemExit(main())
