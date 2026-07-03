<div align="center">

# 🚀 ArsipCerdas

### *Intelligent Document Search Engine for Everyone*

![Version](https://img.shields.io/badge/version-0.3.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Offline](https://img.shields.io/badge/100%25-Offline-orange?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Powered-purple?style=for-the-badge)

<p align="center">
  <img src="https://raw.githubusercontent.com/duhemen/arsipcerdas/main/docs/screenshot.png" alt="ArsipCerdas Screenshot" width="800">
</p>

---

## 🌟 **Why ArsipCerdas?**

> *"Find your documents by meaning, not just by name."*

ArsipCerdas is a **modern, AI-powered document search engine** that runs **100% offline** on your laptop. No cloud, no subscription, no privacy concerns.

### 🎯 **The Problem We Solve**

| Traditional Search | ArsipCerdas |
|-------------------|-------------|
| ❌ Search by filename only | ✅ Search by **meaning & context** |
| ❌ Can't find "surat cuti Pak Budi" | ✅ Understands **natural language** |
| ❌ Requires internet | ✅ **100% offline** |
| ❌ Uploads your documents to cloud | ✅ **Your data stays with you** |
| ❌ Needs expensive GPU | ✅ Runs on **laptop kasir** |**SELAMAT EMEN!** 🎉🎉🎉

---

## 🚀 **Quick Start**

### 📦 **Installation**

```bash
#### 1. Clone repository
git clone https://github.com/duhemen/arsipcerdas.git
cd arsipcerdas

#### 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

#### 3. Install dependencies
pip install -r requirements.txt

#### 4. Run the application
python main.py
```

### 🌐 **Access the Application**

```
http://localhost:52341
```

### 🎯 **First Use Guide**

#### 1. **Upload Documents** - Drag & drop PDFs or click upload button
#### 2. **Search** - Type your query in the search bar
#### 3. **Preview** - Click "Preview" on any result
#### 4. **Export** - Export results to CSV/PDF

---

## 📖 **User Guide**

### 🔍 **Search Tips**

| Query Type | Example | Result |
|------------|---------|--------|
| **Natural Language** | `"surat cuti pak budi"` | Finds all leave letters |
| **Document Number** | `"440/012/2026"` | Finds specific document |
| **Date Range** | `"Juni 2026"` | Finds documents from June 2026 |
| **File Type** | `"format:pdf"` | Shows only PDF files |
| **Combined** | `"nomor 440 dan cuti"` | Combines multiple criteria |

### ⌨️ **Keyboard Shortcuts**

| Shortcut | Action |
|----------|--------|
| `Ctrl + K` | Focus search bar |
| `Escape` | Clear search / Close preview |
| `Enter` | Execute search |
| `Ctrl + +` | Zoom in (PDF preview) |
| `Ctrl + -` | Zoom out (PDF preview) |

### 📁 **Supported File Types**

| Type | Extensions | Max Size | Status |
|------|------------|----------|--------|
| PDF | `.pdf` | 100 MB | ✅ Full |
| Word | `.docx` | 100 MB | ✅ Full |
| PowerPoint | `.pptx` | 100 MB | ✅ Full |
| Excel | `.xlsx` | 100 MB | ✅ Full |
| Text | `.txt` | 100 MB | ✅ Full |
| Images | `.jpg`, `.png`, `.gif`, `.bmp` | 50 MB | ⚠️ OCR Required |

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    ARSIP CERDAS ARCHITECTURE               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                           │
│  │   Frontend  │  HTML + Tailwind + Alpine.js              │
│  │  (UI/UX)    │  PDF.js for preview                       │
│  └──────┬──────┘                                           │
│         │ HTTP API                                          │
│  ┌──────▼──────┐                                           │
│  │   Backend   │  FastAPI + Uvicorn                        │
│  │    (API)    │  RESTful endpoints                        │
│  └──────┬──────┘                                           │
│         │                                                   │
│  ┌──────▼──────┐                                           │
│  │   Services  │  Parser + AI + Database                   │
│  │   (Core)    │  Document processing pipeline             │
│  └──────┬──────┘                                           │
│         │                                                   │
│  ┌──────▼──────┐                                           │
│  │   Storage   │  LanceDB (Vector) + SQLite (Metadata)    │
│  │   (Data)    │  File System (Documents)                  │
│  └─────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 🧠 **AI Pipeline**

```
1. Document Upload
   ↓
2. Text Extraction (PyMuPDF / OCR)
   ↓
3. Smart Chunking (500-800 chars)
   ↓
4. Vector Embedding (all-MiniLM-L6-v2)
   ↓
5. Store in LanceDB (Vector + FTS)
   ↓
6. Search Query → Embed → Hybrid Search → Rerank
   ↓
7. Results with Highlight
```

---

## 🛠️ **Tech Stack**

### Backend
- **Python 3.10+** - Core language
- **FastAPI** - REST API framework
- **Uvicorn** - ASGI server
- **PyMuPDF** - PDF parsing
- **Sentence-Transformers** - AI embeddings
- **LanceDB** - Vector database
- **SQLite** - Metadata storage

### Frontend
- **HTML5** - Structure
- **Tailwind CSS** - Styling
- **Alpine.js** - Interactivity
- **PDF.js** - PDF rendering
- **Font Awesome** - Icons

### AI Models
- **all-MiniLM-L6-v2** - Embedding model (80MB)
- **Optional**: multilingual-e5-small (420MB)

---

## 📊 **Performance**

| Metric | Value |
|--------|-------|
| **Search Time** | < 1 second (10,000 docs) |
| **Memory Usage** | < 500MB idle |
| **RAM Usage** | < 1.2GB during search |
| **Index Speed** | 1 page/second (CPU) |
| **Model Size** | 80MB - 420MB |

---

## 🤝 **Contributing**

We welcome contributions! Here's how you can help:

1. 🐛 **Report Bugs** - Open an issue
2. 💡 **Suggest Features** - Start a discussion
3. 📝 **Improve Docs** - Submit a PR
4. 💻 **Fix Issues** - Send a pull request

### Development Setup

```bash
# Clone and install
git clone https://github.com/duhemen/arsipcerdas.git
cd arsipcerdas
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Build installer
python build.py
```

---

## 📄 **License**

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **Meta AI** - For inspiring this project
- **Google Gemini** - For validation and feedback
- **DeepSeek** - For development assistance
- **Open Source Community** - For amazing libraries

---

## 📞 **Contact**

- **GitHub**: [@duhemen](https://github.com/duhemen)
- **Repository**: [arsipcerdas](https://github.com/duhemen/arsipcerdas)
- **Issues**: [Report a bug](https://github.com/duhemen/arsipcerdas/issues)

---

<div align="center">

### ⭐ **If you like this project, give it a star!**

Made with ❤️ by [duhemen](https://github.com/duhemen)

</div>
```

---
