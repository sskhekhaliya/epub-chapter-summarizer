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

### Running the Pipeline
Place your EPUB file in the `book/` folder and run:
```bash
python main.py
```

### Options
- `--limit N`: Only process the first N chapters (useful for testing).
- `--model-name NAME`: Specify the LLM model (default: `llama3`).
- `--model-url URL`: Set the LLM API endpoint (default: `http://localhost:11434/v1`).

### Output
The pipeline generates a JSON file in the `output/` directory and automatically pushes it to Sanity if configured.

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
