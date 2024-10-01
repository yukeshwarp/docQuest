import fitz  # PyMuPDF
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.ocr_detection import detect_ocr_images_and_vector_graphics
from utils.llm_interaction import summarize_page

def remove_stopwords_and_blanks(text):
    """Clean the text by removing extra spaces."""
    cleaned_text = ' '.join(word for word in text.split())
    return cleaned_text

def process_single_page(page_number, pdf_document, previous_summary):
    """Process a single page of the PDF."""
    page = pdf_document.load_page(page_number)
    text = page.get_text("text").strip()
    preprocessed_text = remove_stopwords_and_blanks(text)

    # Summarize the page text
    summary = summarize_page(preprocessed_text, previous_summary, page_number + 1)
    
    # Detect images or vector graphics on the page
    detected_images = detect_ocr_images_and_vector_graphics(pdf_document, 0.18)
    image_analysis = []

    for img_page, base64_image in detected_images:
        if img_page == page_number + 1:
            image_analysis.append({"page_number": img_page, "image_data": base64_image})

    return {
        "page_number": page_number + 1,
        "text_summary": summary,
        "image_analysis": image_analysis
    }, summary

def process_pdf_pages(uploaded_file):
    """Process the PDF and extract text/image summaries."""
    pdf_document = fitz.open(stream=io.BytesIO(uploaded_file.read()), filetype="pdf")
    document_data = {"pages": []}
    previous_summary = ""

    # Use ThreadPoolExecutor for parallel processing of pages
    with ThreadPoolExecutor() as executor:
        # Create future tasks for each page
        future_to_page = {
            executor.submit(process_single_page, page_number, pdf_document, previous_summary): page_number
            for page_number in range(len(pdf_document))
        }

        for future in as_completed(future_to_page):
            page_number = future_to_page[future]
            try:
                page_data, previous_summary = future.result()
                document_data["pages"].append(page_data)
            except Exception as e:
                print(f"Error processing page {page_number + 1}: {e}")

    return document_data
