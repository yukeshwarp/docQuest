# docQuest

**docQuest** is an intelligent document analysis and question-answering application powered by LLMs (Large Language Models) and Azure OpenAI. It allows users to upload documents (PDF, Word, Excel, etc.), analyze their content, and interactively ask questions or request summaries, all via a user-friendly web interface built on Streamlit.

## Features

- **Multi-format Document Upload:** Supports PDF, DOCX, XLSX, CSV, PPTX, and more.
- **Document Parsing & Storage:** Documents are preprocessed, tokenized, persisted in Redis (for session state), and also uploaded to Azure Blob Storage.
- **LLM-Powered Q&A:** Ask questions about your uploaded documents, retrieve contextual answers, and get references to source documents.
- **Automatic Summarization:** Request detailed or topic-wise summaries of your documents.
- **Bing Web Search Integration:** Augments answers with relevant Bing search results for broader context.
- **Chat History & Export:** Every Q&A session is saved in chat history, with the ability to download chat responses as formatted Word documents.
- **Token Management:** Handles large documents by tracking token usage and warning when limits are exceeded.
- **Concurrent Processing:** Efficiently processes multiple documents using batch logic.
- **Document Insights:** Extracts metadata like domain, subject matter, expertise level, style, and tone from document content.

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Running the App](#running-the-app)
- [Usage](#usage)
- [Advanced Features](#advanced-features)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Environment Variables](#environment-variables)
- [License](#license)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)

## Screenshots

*(Add screenshots here if available)*

---

## Getting Started

### Prerequisites

- Python 3.8+
- Access to Azure OpenAI (API Key, Endpoint, Model, API Version)
- Azure Blob Storage credentials
- Redis server (local or remote)
- Bing Search API Key (for web augmentation)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yukeshwarp/docQuest.git
   cd docQuest


2. **Install required packages:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   Create a `.env` file or export the following variables (see `utils/config.py` for exact names):

   ```
   AZURE_OPENAI_ENDPOINT=...
   AZURE_OPENAI_API_KEY=...
   AZURE_OPENAI_API_VERSION=...
   AZURE_OPENAI_MODEL=...
   AZURE_BLOB_CONNECTION_STRING=...
   AZURE_CONTAINER_NAME=...
   REDIS_HOST=...
   REDIS_PASS=...
   BING_KEY=...
   BING_ENDPOINT=...
   ```

4. **(Optional) Download NLTK stopwords:**
   The app downloads stopwords automatically on first run, but you may pre-download via:

   ```python
   python -c "import nltk; nltk.download('stopwords')"
   ```

---

## Running the App

You can start the application using the provided shell script or manually:

**Using the script:**

```bash
./streamlit.sh
```

**Or manually:**

```bash
pip install -r requirements.txt
python -m streamlit run main.py --server.port 8000 --server.address 0.0.0.0
```

The app will be accessible at: [http://localhost:8000](http://localhost:8000)

---

## Usage

1. **Upload Documents:** Drag and drop or select files to upload. Supported formats: PDF, DOCX, XLSX, CSV, PPTX, and more.
2. **Process Documents:** The app will parse and store your documents securely.
3. **Ask Questions / Request Summaries:** Use the chat input to ask questions or request summaries about your document content.
4. **Download Responses:** Each chat response can be downloaded as a Word document for record-keeping or sharing.

---

## Advanced Features

* **Batch Summarization:** Handles large documents or multiple files efficiently.
* **Topic Extraction:** Uses NMF topic modeling to extract and summarize key topics.
* **Configurable Token Limits:** Warns users when document size exceeds practical model limits.
* **Extensible:** Modular design for adding new file types, LLM backends, or custom analytics.

---

## Project Structure

```
main.py                  # Streamlit App Entry Point
extractor.py             # Document content extraction and summarization logic
respondent.py            # Question answering and Bing search integration
utils/
  llm_interaction.py     # LLM prompt handling and interaction utilities
  file_conversion.py     # File type conversion and MIME handling
  config.py              # Configuration and environment variable loading
requirements.txt         # Python dependencies
streamlit.sh             # Startup script
```

---

## Dependencies

See `requirements.txt` for the full list. Major libraries include:

* `streamlit` (web app)
* `azure-storage-blob`
* `redis`
* `nltk`
* `scikit-learn`
* `tiktoken`
* `PyMuPDF`, `PyPDF2`, `python-docx`, `python-pptx`
* `requests`
* `Pillow`
* `celery` (if using async tasks)

---

## Environment Variables

All sensitive credentials (Azure, Redis, Bing) must be provided as environment variables. See setup section above.

---

## License

MIT License

---

## Contributing

Pull requests and feature requests are welcome! Please open issues for bugs or feature suggestions.

---

## Acknowledgements

* Azure OpenAI
* Streamlit
* NLTK, scikit-learn
* Bing Search API
```
