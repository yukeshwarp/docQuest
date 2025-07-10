# docQuest

**docQuest** is an intelligent document analysis and question-answering application powered by LLMs (Large Language Models) and Azure OpenAI. It allows users to upload documents (PDF, Word, Excel, and more), ask questions, and receive answers enhanced with web search and metadata insights.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Running the App](#running-the-app)
- [Celery & Background Worker Setup](#celery--background-worker-setup)
- [Office-to-PDF Azure Function Setup](#office-to-pdf-azure-function-setup)
- [Usage](#usage)
- [Advanced Features](#advanced-features)
- [Project Structure](#project-structure)
- [Concurrency & Global State](#concurrency--global-state)
- [Token & Size Limits](#token--size-limits)
- [Search Logic](#search-logic)
- [Error Handling & Retry Strategy](#error-handling--retry-strategy)
- [Metadata & Information Extraction](#metadata--information-extraction)
- [Dependencies](#dependencies)
- [Environment Variables](#environment-variables)

---

## Features

- **Multi-format Document Upload:** Supports PDF, DOCX, XLSX, CSV, PPTX, and more.
- **Document Parsing & Storage:** Documents are preprocessed, tokenized, persisted in Redis (for session state), and also uploaded to Azure Blob Storage.
- **LLM-Powered Q&A:** Ask questions about your uploaded documents, retrieve contextual answers, and get references to source documents.
- **Automatic Summarization:** Request detailed or topic-wise summaries of your documents.
- **Bing Web Search Integration:** Augments answers with relevant Bing search results for broader context.
- **Chat History & Export:** Every Q&A session is saved in chat history, with the ability to download chat responses as formatted Word documents.
- **Token Management:** Handles large documents by tracking token usage and warning when limits are exceeded.
- **Concurrent Processing:** Efficiently processes multiple documents using batch logic and background workers.
- **Document Insights:** Extracts metadata like domain, subject matter, expertise level, style, and tone from document content.
- **Robust Error Handling:** Implements exponential back-off and retry logic for resilient OpenAI API calls.

---

## Getting Started

### Prerequisites

- Python 3.8+
- Access to Azure OpenAI (API Key, Endpoint, Model, API Version)
- Azure Blob Storage credentials
- Redis server (local or remote)
- Bing Search API Key (for web augmentation)
- [OPTIONAL] Azure Functions for Office-to-PDF conversion (see below)
- [OPTIONAL] Celery + Redis for background task processing

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yukeshwarp/docQuest.git
   cd docQuest
   ```

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
   AZURE_BLOB_CONTAINER_NAME=...       # NOTE: Use exact case as in Azure portal
   AZURE_FUNCTION_URL=...              # Required for Office-to-PDF conversion
   REDIS_HOST=...
   REDIS_PASS=...
   CELERY_BROKER_URL=redis://...       # Required for background worker
   SEARCH_ENGINE_VERSION=...           # (e.g., "v7")
   BING_KEY=...
   BING_ENDPOINT=...
   ```

   > **Case Sensitivity:**  
   > Environment variable names are case-sensitive. For Azure Blob, always use `AZURE_BLOB_CONTAINER_NAME` (not `azure_container_name`).

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

## Celery & Background Worker Setup

Some features (e.g., file processing) require background task execution.  
This app uses **Celery** with Redis as the broker.

1. **Start the Celery worker:**
   ```bash
   celery -A pdf_processing worker --loglevel=info
   ```
   - Replace `pdf_processing` with the actual module if different in your deployment.

2. **Configure Redis queues:**
   - By default, Celery uses the broker URL specified in `CELERY_BROKER_URL`.
   - Make sure the value matches your `REDIS_HOST` and credentials.

3. **Why is this needed?**  
   Certain tasks (e.g. Office file conversion, large document processing) run asynchronously via Celery to keep the web app responsive.

---

## Office-to-PDF Azure Function Setup

To handle Office-to-PDF conversion, the backend posts files to an Azure Function.  
You **must** deploy and configure this function and provide its endpoint as `AZURE_FUNCTION_URL`or use an already hosted function endpoint.

1. **Deploy the Azure Function:**
   - The function code is in `/azure-function` (or as specified).
   - Deploy to your Azure account following [Azure Functions documentation](https://docs.microsoft.com/en-us/azure/azure-functions/).

2. **Set Environment Variable:**
   - Add `AZURE_FUNCTION_URL` to your environment.
   - Example:  
     ```
     AZURE_FUNCTION_URL=https://<your-function-app>.azurewebsites.net/api/convert
     ```

3. **Usage in code:**
   - `file_conversion.py` posts files to this URL for Office document conversion.

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
  file_conversion.py     # File type conversion and MIME handling (calls Azure Function)
  config.py              # Configuration and environment variable loading
requirements.txt         # Python dependencies
streamlit.sh             # Startup script
celery_worker.py         # Celery background worker entrypoint
```

---

## Concurrency & Global State

- The app uses a **global variable** (`generated_system_prompt`) and Redis to manage session state and prompt templates.
- **Caveat:**  
  If you deploy multiple instances or serve many users simultaneously, these globals and Redis key schemes may collide.  
  > **Warning:** For multi-user environments, ensure unique keys per user/session to avoid prompt collisions or data leaks.

---

## Token & Size Limits

- **Document Limit:**  
  Each document is limited to **600,000 tokens**. Uploads beyond this are rejected.
- **Question Window Limit:**  
  Each question context is limited to **50,000 tokens**.
- **Implications:**  
  These hard limits are enforced to prevent excessive memory/compute usage and avoid model errors.  
  Users are notified if they exceed these limits.

---

## Search Logic

- **Bing Web Search Integration:**  
  - Only the **top three URLs** (no titles/snippets) are appended to answers for web augmentation.
  - Rate limits are handled gracefully; if Bing API quota is exceeded, web results are omitted with a warning.
  - Search queries are generated via the `bing_search_topics` function based on document context and question.
- **Note:**  
  Web results are used to supplement answers, but heavy reliance may hit Bing quotas in high-usage scenarios.

---

## Error Handling & Retry Strategy

- For OpenAI API timeouts and transient errors, the code implements **exponential back-off and retry**.
- This reduces the chance of failed responses due to temporary outages or rate limits.
- **Operational Note:**  
  Retries increase response time and may incur additional API costs if failures persist.  
  Monitor logs and set sensible retry/backoff parameters for your deployment.

---

## Metadata & Information Extraction

**Metadata** is the "brain" of this application, serving as a foundational layer for intelligent document understanding, question answering, and contextual search. Here’s a detailed breakdown of how metadata is extracted, stored, and utilized throughout the system:

### Extracted Metadata

For every uploaded document, docQuest extracts and stores the following metadata:

- **Domain**: The field or industry the document pertains to (e.g., legal, financial, medical, technical, academic).
- **Subject Matter**: The main topic(s) or themes discussed in the document.
- **Expertise Level**: Intended audience sophistication (e.g., beginner, intermediate, expert).
- **Style & Tone**: Formality, tone (e.g., formal, informal, persuasive, explanatory).
- **File Properties**: Author, creation/modification timestamps, file type, word count, page count, and other embedded properties.

### How is Metadata Extracted?

- **Automated Analysis**: On upload, the system uses NLP models and heuristics to auto-detect domain, subject, and expertise based on content sampling and keyword analysis.
- **LLM Augmentation**: For richer context, the LLM may be prompted to summarize or classify the document’s characteristics.
- **File Inspection**: Technical properties (author, page count, etc.) are pulled directly from the file headers or properties.

### How is Metadata Used?

Metadata is not just for display — it plays a crucial role in enabling powerful, accurate, and context-aware document analysis:

#### 1. **Improved Question Answering**
- When a user asks a question, the system leverages the document’s domain, subject, and expertise metadata to fine-tune LLM prompts.
- For example, a legal document’s answers are framed with legal terminology, and medical documents are answered with appropriate caution and jargon.

#### 2. **Adaptive Summarization**
- Summaries are tailored based on the style and audience; a summary for an expert-level document will include more technical details, while one for a general audience will be simplified.

#### 3. **Contextual Search & Ranking**
- When searching within or across documents, metadata helps prioritize more relevant sections or documents based on the user’s query.
- For example, if a user asks a technical question, the system can prioritize sections marked as “expert” or documents from a technical domain.

#### 4. **Web Search Query Optimization**
- The Bing search integration uses extracted topics and subject matter to craft more precise search queries, resulting in higher-quality web results tailored to the document context.

#### 5. **Session State & Prompt Engineering**
- Metadata is often embedded in session state for persistent, context-aware interactions.
- Prompt templates dynamically adapt to include or reference metadata, making question answering more robust and contextually relevant.

#### 6. **User Guidance & UI Display**
- The UI displays metadata to help users understand what kind of information is available and to guide their questioning (e.g., showing “Domain: Finance” encourages finance-related questions).

#### 7. **Filtering, Tagging, and Routing**
- Metadata allows for powerful filtering (e.g., “show only technical documents”) and routing of questions to the right processing pipelines or LLM models.

### Why is Metadata Important?

- **Accuracy & Relevance**: By leveraging metadata, the system can provide more accurate and contextually appropriate answers.
- **Performance**: Metadata enables smart shortcuts for search and retrieval, reducing unnecessary computation.
- **Explainability**: Exposed metadata helps users understand why the system responds in certain ways, improving trust and usability.


---


---

## Dependencies

See `requirements.txt` for the full list. Major libraries include:

* `streamlit` (web app)
* `azure-storage-blob`
* `redis`
* `celery`
* `nltk`
* `scikit-learn`
* `tiktoken`
* `PyMuPDF`, `PyPDF2`, `python-docx`, `python-pptx`
* `requests`
* `Pillow`

---

## Environment Variables

All sensitive credentials and configuration options must be provided as environment variables.  
**Required variables:**  
- See [Installation](#installation) for the complete list, including:
  - `AZURE_FUNCTION_URL` (for Office conversion)
  - `AZURE_BLOB_CONTAINER_NAME` (case-sensitive)
  - `CELERY_BROKER_URL`
  - `SEARCH_ENGINE_VERSION`
  - All Azure, Redis, and Bing keys

---
