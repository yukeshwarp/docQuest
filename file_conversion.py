import io
import requests
from utils.config import azure_function_url

MIME_TYPES = {
    "doc": "application/msword",
    "dot": "application/msword",
    "csv": "text/csv",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
    "docm": "application/vnd.ms-word.document.macroEnabled.12",
    "dotm": "application/vnd.ms-word.template.macroEnabled.12",
    "xls": "application/vnd.ms-excel",
    "xlt": "application/vnd.ms-excel",
    "xla": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xltx": "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
    "xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
    "xltm": "application/vnd.ms-excel.template.macroEnabled.12",
    "xlam": "application/vnd.ms-excel.addin.macroEnabled.12",
    "xlsb": "application/vnd.ms-excel.sheet.binary.macroEnabled.12",
    "ppt": "application/vnd.ms-powerpoint",
    "pot": "application/vnd.ms-powerpoint",
    "pps": "application/vnd.ms-powerpoint",
    "ppa": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "potx": "application/vnd.openxmlformats-officedocument.presentationml.template",
    "ppsx": "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
    "ppam": "application/vnd.ms-powerpoint.addin.macroEnabled.12",
    "pptm": "application/vnd.ms-powerpoint.presentation.macroEnabled.12",
    "potm": "application/vnd.ms-powerpoint.template.macroEnabled.12",
    "ppsm": "application/vnd.ms-powerpoint.slideshow.macroEnabled.12",
    "mdb": "application/vnd.ms-access",
}


def get_mime_type(file_name):
    """Get the MIME type based on the file extension."""
    extension = file_name.split(".")[-1].lower()
    return MIME_TYPES.get(extension, None)


def convert_office_to_pdf(office_file):
    """Convert Office files to PDF using Azure Function and return the PDF as a BytesIO object."""
    mime_type = get_mime_type(office_file.name)
    if mime_type is None:
        raise ValueError(f"Unsupported file type: {office_file.name}")

    headers = {
        "Content-Type": "application/octet-stream",
        "Content-Type-Actual": mime_type,
    }

    response = requests.post(
        azure_function_url, data=office_file.read(), headers=headers
    )

    if response.status_code == 200:
        return io.BytesIO(response.content)
    else:
        raise Exception(
            f"File conversion failed with status code: {response.status_code}, {response.text}"
        )
