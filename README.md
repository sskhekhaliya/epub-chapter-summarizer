# 📚 EPUB Chapter Summarizer

A powerful, AI-driven pipeline designed to ingest EPUB books, segment them into parts and chapters, and generate high-quality, narrative-style summaries. Features seamless integration with **Ollama** (for local LLMs) and **Sanity.io** (for content management).

![Sanity Dashboard](https://img.shields.io/badge/Sanity-F04544?style=for-the-badge&logo=sanity&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenAI API](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)

---

## ✨ Features

- **EPUB Ingestion**: Automatically extracts content, metadata, and cover images from EPUB files.
- **Intelligent Segmentation**: Detects book structure (Parts vs. Chapters) using structural and text-based heuristics.
- **Narrative Summarization**: Leverages LLMs to generate summaries that mimic the author's prose style while avoiding generic AI phrasing.
- **Highlight Extraction**: Automatically identifies key takeaways and profound insights.
- **Portable Text Formatting**: Generates Sanity-ready Portable Text blocks with consistent styling and UUID keys.
- **Auto-Cleanup**: Built-in validation layer to strip "meta-talk" and artifacts from LLM outputs.
- **Sanity Integration**: Direct upload of book data, summaries, highlights, and covers to your Sanity project.

---

## 🛠️ Tech Stack

- **Python 3.10+**: Core logic and pipeline orchestration.
- **Ebooklib & BeautifulSoup**: EPUB parsing and HTML cleaning.
- **OpenAI Python SDK**: Interface for local (Ollama) or remote (OpenAI) models.
- **Requests & HTTPX**: Robust API communication for Sanity and LLM backends.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: Ensure Python 3.10+ is installed.
- **Ollama**: (Optional) Run `ollama serve` and `ollama run llama3` for local summarization.
- **Sanity Account**: A project ID and API token with write permissions.

### 2. Installation
```bash
git clone https://github.com/sskhekhaliya/epub-chapter-summarizer.git
cd epub-chapter-summarizer
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
NEXT_PUBLIC_SANITY_PROJECT_ID=your_project_id
SANITY_API_TOKEN=your_write_token
```

---

## 📖 Usage

### 🚀 Quick Start
Place your EPUB file in the `book/` folder and run the interactive pipeline:
```bash
run.bat
```
Or for a fully automated run (defaults to rating 4.5 and fresh start):
```bash
run.bat auto
```

### 🎛️ Command Reference

#### Main Pipeline
```bash
# Standard run (checks 'book/' folder, prompts for details)
python main.py

# Advanced usage with arguments
python main.py --limit 5 --rating 4.5 --model-name llama3
```
**Arguments:**
- `--limit N`: Process only the first N chapters (useful for testing).
- `--rating N`: Set book rating (0-5).
- `--restart`: Ignore previous incomplete runs and start fresh.
- `--model-name NAME`: LLM model to use (default: `llama3`).
- `--model-url URL`: LLM API endpoint (default: `http://localhost:11434/v1`).
- `--affiliate-link URL`: Amazon affiliate link.

#### Sanity Upload
Interactively choose a generated JSON summary from `output/` to upload:
```bash
upload.bat
# or manually
python scripts/manual_upload.py output/your_book.json
```

#### Utility Tools (`run.bat` shortcuts)

**Inspect EPUB Structure (Hierarchy)**  
View the Table of Contents hierarchy before processing to verify part/chapter detection:
```bash
run.bat structure
# or manually
python scripts/inspect_structure.py
```

**Inspect EPUB Table Map (Terminal)**
View a flat table of files and TOC titles directly in the terminal:
```bash
python debug_structure.py
```

**Regenerate Highlights**  
Re-run highlight extraction for a specific book slug:
```bash
run.bat highlights <book-slug>
```

**Generate Description**  
Create a book description from an existing JSON summary file:
```bash
run.bat description output/your_book_summary.json
```

**Dump Raw Structure to File**
Generates a detailed `structure_full.txt` file mapping TOC entries to file paths and H1 tags:
```bash
python dump_structure.py
```

---

## 📁 Project Structure

- `pipeline/`: Core logic (Ingest, Clean, Segment, Summarize, Upload).
- `book/`: Store your EPUB files here (ignored by git).
- `output/`: Generated JSON summaries (ignored by git).
- `scripts/`: Maintenance and cleanup utilities.

---

## ⚖️ License
MIT License. See [LICENSE](LICENSE) for details.

---
*Created by [sskhekhaliya](https://github.com/sskhekhaliya)*
