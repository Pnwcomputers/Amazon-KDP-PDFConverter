#!/usr/bin/env python3
import os
import re
import sys
import shutil
import tempfile
import subprocess
from urllib.parse import unquote

# ──────────────────────────────────────────────
# BOOK METADATA
# ──────────────────────────────────────────────
BOOK_TITLE = "The Book Title"
BOOK_SUBTITLE = "Replace with your subheading"
BOOK_AUTHOR = "Author"
PDF_OUTPUT = "Book_Name_A4_KDP.pdf"

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
\usepackage{xurl} 

% 1. INDEPENDENT IMAGE CONSTRAINTS
\makeatletter
\newlength{\kdpmaxwidth}
\newlength{\kdpmaxheight}
\setlength{\kdpmaxwidth}{0.85\linewidth}
\setlength{\kdpmaxheight}{0.35\textheight}
\makeatother
\setkeys{Gin}{width=\kdpmaxwidth,height=\kdpmaxheight,keepaspectratio}

% 2. FIGURE LOCKING (Prevents bottom-margin overflow)
\let\origfigure\figure
\let\origendfigure\endfigure
\renewenvironment{figure}[1][H]{\origfigure[H]}{\origendfigure}

% 3. TEXT WRAPPING & TABLE FIX
% Forces longtables to respect text width and prevents squishing
\usepackage{array}
\newcolumntype{L}[1]{>{\raggedright\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}
\sloppy
\setlength{\emergencystretch}{3em}

% 4. A4 GEOMETRY
\usepackage[paperwidth=210mm,paperheight=297mm,
            inner=""" + INNER_MARGIN + r""",outer=""" + OUTER_MARGIN + r""",
            top=""" + TOP_BOTTOM + r""",bottom=""" + TOP_BOTTOM + r""",
            footskip=12mm,headsep=10mm,headheight=15pt]{geometry}

% 5. HEADERS
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE,RO]{\thepage}
\fancyhead[RE]{\textit{The Book Title}}
\renewcommand{\headrulewidth}{0.4pt}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
"""

# EXACT CHAPTER ORDER - NO AUTOMATED CRAWLING
PARTS = [
    {"folder": "Part I - Computer Fundamentals", "title": "Part I: Computer Fundamentals", "subtitle": "The essential building blocks of your computer and system setup.",
     "chapters": [
         "Part I - Computer Fundamentals/Chapter 1 - Understanding Your Computer/Chapter1_Understanding_Your_Computer.md",
         "Part I - Computer Fundamentals/Chapter 2 - Operating Systems Basics/Chapter2-Operating_Systems_Basics.md",
         "Part I - Computer Fundamentals/Chapter 3 - Setting Up a New Computer/Chapter3-Setting_Up_a_New_Computer.md",
     ]},
    {"folder": "Part II - Internet Safety & Cybersecurity", "title": "Part II: Internet Safety & Cybersecurity", "subtitle": "Recognizing modern threats and implementing a strong defensive posture.",
     "chapters": [
         "Part II - Internet Safety & Cybersecurity/Chapter 4 - Understanding Cyber Threats/Chapter4-Understanding_Cyber_Threats.md",
         "Part II - Internet Safety & Cybersecurity/Chapter 5 - Protecting Yourself Online/Chapter5-Protecting_Yourself_Online.md",
         "Part II - Internet Safety & Cybersecurity/Chapter 6 - Antivirus and Security Software/Chapter6-Antivirus_and_Security_Software.md",
         "Part II - Internet Safety & Cybersecurity/Chapter 7 - What to Do If You're Infected/Chapter7-WhattoDo_IfYoure_Infected.md",
     ]},
    {"folder": "Part III - Computer Maintenance & Care", "title": "Part III: Computer Maintenance & Care", "subtitle": "Professional procedures for cleaning, troubleshooting, and hardware diagnosis.",
     "chapters": [
         "Part III - Computer Maintenance & Care/Chapter 8 - Keeping Your Computer Healthy/Chapter8-Keeping_Your_Computer_Healthy.md",
         "Part III - Computer Maintenance & Care/Chapter 9 - Data Backup Essentials/Chapter9-Data_Backup_Essentials.md",
         "Part III - Computer Maintenance & Care/Chapter 10 - Basic Troubleshooting/Chapter10-Basic_Troubleshooting.md",
         "Part III - Computer Maintenance & Care/Chapter 11 - Understanding Hardware Problems/Chapter11-UnderstandingHardwareProblems.md",
         "Part III - Computer Maintenance & Care/Chapter 12 - Basic Hardware Maintenance/Chapter12-BasicHardwareMaintenance.md",
     ]},
    {"folder": "Part V - Networking & Connectivity", "title": "Part IV: Networking & Connectivity", "subtitle": "Home network, peripherals, and connections.",
     "chapters": [
         "Part V - Networking & Connectivity/Chapter 13 - Home Network Basics/Chapter13-HomeNetworkBasics.md",
         "Part V - Networking & Connectivity/Chapter 14 - Internet Troubleshooting/Chapter14-InternetTroubleshooting.md",
         "Part V - Networking & Connectivity/Chapter 15 - Printer and Peripheral Setup/Chapter15-PrinterandPeripheralSetup.md",
     ]},
    {"folder": "Part VI - Account Management & Recovery", "title": "Part V: Account Management & Recovery", "subtitle": "Digital identity management.",
     "chapters": [
         "Part VI - Account Management & Recovery/Chapter 16 - Managing Online Accounts/Chapter16-ManagingOnlineAccounts.md",
         "Part VI - Account Management & Recovery/Chapter 17 - When Things Go Wrong/Chapter17-WhenThingsGoWrong.md",
     ]},
    {"folder": "Part VII - Practical Tips & Advanced Basics", "title": "Part VI: Practical Tips & Advanced Basics", "subtitle": "Lasting performance.",
     "chapters": [
         "Part VII - Practical Tips & Advanced Basics/Chapter 18 - Software Management/Chapter18-SoftwareManagement.md",
         "Part VII - Practical Tips & Advanced Basics/Chapter 19 - Performance Optimization/Chapter19-PerformanceOptimization.md",
         "Part VII - Practical Tips & Advanced Basics/Chapter 20 - Planning for the Future/Chapter20-PlanningfortheFuture.md",
     ]}
]

def preprocess_markdown(content):
    content = re.sub(r'\A\s*---\s*\n.*?\n---(?:\s*\n|$)', '', content, flags=re.DOTALL)
    content = re.sub(r'<img\s+[^>]*src="([^"]+)"[^>]*>', r'![](\1)', content)
    def fix_match(match):
        alt, raw_path = match.group(1), match.group(2)
        clean = re.sub(r'^(\.\./)+', '', raw_path).lstrip('/')
        return f"![{alt}]({clean})"
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_match, content)
    content = content.replace('\u200B', '')
    content = re.sub(r'^#{2,}\s*(Chapter\s+\d+.*)$', r'# \1', content, flags=re.MULTILINE | re.IGNORECASE)
    content = re.sub(r'^(#+)(?=[A-Za-z0-9])', r'\1 ', content, flags=re.MULTILINE)
    return content

def main():
    repo_root = os.path.abspath(os.getcwd())
    output_dir = os.path.join(repo_root, "build")
    os.makedirs(output_dir, exist_ok=True)
    build_temp = tempfile.mkdtemp()
    
    try:
        prepared_files = []
        file_counter = 0

        for part in PARTS:
            file_counter += 1
            path = os.path.join(build_temp, f"{file_counter:03d}_Divider.md")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"\n\\newpage\n\n# {part['title']}\n\n*{part['subtitle']}*\n\n\\newpage\n\n")
            prepared_files.append(path)

            for ch_path in part["chapters"]:
                src = os.path.join(repo_root, ch_path)
                if not os.path.exists(src): continue
                with open(src, 'r', encoding='utf-8-sig', errors='replace') as f:
                    content = preprocess_markdown(f.read()) + "\n\n"
                file_counter += 1
                dest = os.path.join(build_temp, f"{file_counter:03d}_{os.path.basename(ch_path)}")
                with open(dest, 'w', encoding='utf-8') as f:
                    f.write(content)
                prepared_files.append(dest)

        header_path = os.path.join(build_temp, "header.tex")
        with open(header_path, 'w', encoding='utf-8') as f: f.write(LATEX_HEADER)
        
        output_pdf = os.path.join(output_dir, PDF_OUTPUT)
        cmd = ["pandoc", *prepared_files, "-f", "markdown-yaml_metadata_block", "--pdf-engine=xelatex", f"--resource-path={repo_root}", "-H", header_path, "--toc", "--top-level-division=chapter", "-V", "documentclass=book", "-V", "classoption=openany", "--dpi=300", "-o", output_pdf]
        subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(f"SUCCESS: {output_pdf}")

    finally:
        shutil.rmtree(build_temp, ignore_errors=True)

if __name__ == "__main__":
    main()
