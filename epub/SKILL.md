---
name: epub
description: Use this skill whenever the user wants to read, parse, extract content from, modify, or otherwise process an .epub file. Triggers include any mention of ".epub", "ebook", "epub file", or requests to extract chapters, table of contents, text, images, or metadata from an ebook. Also use when the user wants to convert epub content to another format, inspect epub structure, or edit epub files. Since epub files are ZIP archives in disguise, this skill uses a reliable unzip-then-parse approach that always works. Use this skill even for seemingly simple epub tasks like "read this epub" or "show me the chapters" — the extraction workflow is always needed.
---

# EPUB Processing Guide

## Core Insight: EPUB is a ZIP Archive

An `.epub` file is simply a ZIP archive with a specific internal structure. The most reliable way to process any epub is:

1. **Copy** the file to the working directory
2. **Rename** it from `.epub` → `.zip`
3. **Unzip** it into a folder
4. **Find and read** the navigation/TOC file first (e.g. `nav.xhtml`, `nav.html`, `toc.ncx`)
5. **Then** read content files as needed

This approach works 100% of the time and requires no special epub libraries.

---

## Step-by-Step Workflow

### Step 1: Extract the EPUB

```bash
# Copy uploaded file to working directory
cp /mnt/user-data/uploads/book.epub /home/claude/book.epub

# Rename to .zip and extract
cp /home/claude/book.epub /home/claude/book.zip
unzip -o /home/claude/book.zip -d /home/claude/book_extracted/

# List the extracted contents
find /home/claude/book_extracted/ -type f | sort
```

### Step 2: Find the Navigation File (Highest Priority)

The navigation file is the table of contents — it tells you the book's structure, chapter order, and file layout. Always find and read this first.

```bash
# Look for nav files (in priority order)
find /home/claude/book_extracted/ -type f \( \
  -name "nav.xhtml" -o \
  -name "nav.html" -o \
  -name "toc.ncx" -o \
  -name "*nav*" -o \
  -name "*toc*" \
\) | sort
```

**Nav file priority order:**
1. `nav.xhtml` or `nav.html` — EPUB3 navigation document (preferred)
2. `toc.ncx` — EPUB2 navigation control file (older format)
3. Any file with "nav" or "toc" in its name

```bash
# Read the nav file to understand structure
cat /home/claude/book_extracted/OEBPS/nav.xhtml
# or
cat /home/claude/book_extracted/EPUB/nav.html
```

### Step 3: Find the OPF Package File

The `.opf` file (Open Packaging Format) contains metadata and the full reading order manifest.

```bash
# Find the OPF file
find /home/claude/book_extracted/ -name "*.opf" | head -5

# Read it for metadata and spine (reading order)
cat /home/claude/book_extracted/OEBPS/content.opf
```

The `<spine>` element in the OPF file defines chapter reading order. The `<metadata>` block has title, author, language, etc.

### Step 4: Read Content Files

```bash
# Find all HTML/XHTML content files
find /home/claude/book_extracted/ -type f \( -name "*.html" -o -name "*.xhtml" \) | sort

# Read a specific chapter
cat /home/claude/book_extracted/OEBPS/chapter01.xhtml
```

To extract clean text from HTML content:

```python
from bs4 import BeautifulSoup

with open("/home/claude/book_extracted/OEBPS/chapter01.xhtml", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")
    
# Remove script/style tags
for tag in soup(["script", "style"]):
    tag.decompose()

text = soup.get_text(separator="\n", strip=True)
print(text)
```

---

## Typical EPUB Directory Structure

```
book_extracted/
├── mimetype                    ← Must contain "application/epub+zip"
├── META-INF/
│   └── container.xml           ← Points to the OPF file
└── OEBPS/   (or EPUB/, or OPS/)
    ├── content.opf             ← Package manifest + metadata + spine
    ├── nav.xhtml               ← ★ TABLE OF CONTENTS (read this first!)
    ├── toc.ncx                 ← Older TOC format (EPUB2)
    ├── chapter01.xhtml
    ├── chapter02.xhtml
    ├── ...
    ├── images/
    │   └── cover.jpg
    ├── css/
    │   └── styles.css
    └── fonts/
```

### Reading container.xml to find the OPF path

```bash
cat /home/claude/book_extracted/META-INF/container.xml
```

This file always points to the root OPF file via `<rootfile full-path="...">`.

---

## Common Tasks

### Extract All Text (Full Book)

```python
import os
from bs4 import BeautifulSoup

extracted_dir = "/home/claude/book_extracted/OEBPS"
output_text = []

# Get ordered list of content files from OPF spine (or just sort them)
html_files = sorted([
    f for f in os.listdir(extracted_dir)
    if f.endswith((".html", ".xhtml")) and "nav" not in f.lower()
])

for filename in html_files:
    filepath = os.path.join(extracted_dir, filename)
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    for tag in soup(["script", "style", "head"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    output_text.append(f"\n\n--- {filename} ---\n\n{text}")

full_text = "\n".join(output_text)
with open("/mnt/user-data/outputs/book_full_text.txt", "w", encoding="utf-8") as f:
    f.write(full_text)
```

### Extract Metadata

```python
import xml.etree.ElementTree as ET

tree = ET.parse("/home/claude/book_extracted/OEBPS/content.opf")
root = tree.getroot()

# Namespace handling
ns = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc":  "http://purl.org/dc/elements/1.1/"
}

metadata = root.find("opf:metadata", ns)
if metadata is not None:
    title   = metadata.findtext("dc:title",    namespaces=ns)
    author  = metadata.findtext("dc:creator",  namespaces=ns)
    lang    = metadata.findtext("dc:language", namespaces=ns)
    pub     = metadata.findtext("dc:publisher",namespaces=ns)
    date    = metadata.findtext("dc:date",     namespaces=ns)
    print(f"Title:     {title}")
    print(f"Author:    {author}")
    print(f"Language:  {lang}")
    print(f"Publisher: {pub}")
    print(f"Date:      {date}")
```

### Parse Table of Contents from nav.xhtml

```python
from bs4 import BeautifulSoup

with open("/home/claude/book_extracted/OEBPS/nav.xhtml", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# Find the nav element with epub:type="toc"
nav = soup.find("nav", attrs={"epub:type": "toc"}) or soup.find("nav")

if nav:
    print("=== Table of Contents ===")
    for a in nav.find_all("a"):
        print(f"  {a.get_text(strip=True)}  →  {a.get('href', '')}")
```

### Parse TOC from toc.ncx (EPUB2)

```python
import xml.etree.ElementTree as ET

tree = ET.parse("/home/claude/book_extracted/OEBPS/toc.ncx")
root = tree.getroot()
ns = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}

print("=== Table of Contents (NCX) ===")
for navpoint in root.findall(".//ncx:navPoint", ns):
    label = navpoint.findtext("ncx:navLabel/ncx:text", namespaces=ns)
    src   = navpoint.find("ncx:content", ns)
    href  = src.get("src") if src is not None else ""
    print(f"  {label}  →  {href}")
```

### Extract Cover Image

```bash
# Find the cover image
find /home/claude/book_extracted/ -type f \( \
  -name "cover*" -o -name "*cover*" \
\) | grep -iE "\.(jpg|jpeg|png|gif|webp)$"
```

```python
import shutil

# Copy cover to output
shutil.copy(
    "/home/claude/book_extracted/OEBPS/images/cover.jpg",
    "/mnt/user-data/outputs/cover.jpg"
)
```

### Repack a Modified EPUB

If you've edited files inside the extracted folder and want to repack:

```bash
cd /home/claude/book_extracted/

# mimetype MUST be first and uncompressed
zip -0 -X /home/claude/modified_book.epub mimetype

# Add everything else
zip -r /home/claude/modified_book.epub . --exclude mimetype

# Copy to output
cp /home/claude/modified_book.epub /mnt/user-data/outputs/modified_book.epub
```

---

## Quick Reference

| Goal | File to Read | Tool |
|------|-------------|------|
| Understand structure | `META-INF/container.xml` → OPF path | `cat` / xml.etree |
| Table of contents | `nav.xhtml` or `nav.html` (EPUB3) | BeautifulSoup |
| Table of contents (old) | `toc.ncx` (EPUB2) | xml.etree |
| Book metadata | `*.opf` `<metadata>` block | xml.etree |
| Reading order | `*.opf` `<spine>` block | xml.etree |
| Chapter text | `*.xhtml` / `*.html` in OEBPS/ | BeautifulSoup |
| Cover image | `images/cover.*` or OPF `<item properties="cover-image">` | shutil.copy |

## Required Python Packages

```bash
pip install beautifulsoup4 lxml --break-system-packages
```

`unzip` is available by default on the system. No special epub library is needed.

---

## Troubleshooting

**"No nav file found"** — Try `find . -name "*.xhtml" -o -name "*.html" | xargs grep -l "epub:type" 2>/dev/null` to locate the navigation doc.

**Encoding errors** — Always use `encoding="utf-8", errors="ignore"` when opening HTML/XML files from epubs.

**Namespace issues in XML** — EPUB uses multiple XML namespaces. When using `xml.etree`, always pass the `ns` dict to `find`/`findall`, or use `{namespace_uri}tagname` syntax directly.

**Unusual directory layout** — Check `META-INF/container.xml` first; it always provides the canonical path to the root OPF file, regardless of directory naming conventions.
