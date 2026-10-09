from app.documents.ocr import extract_document_text


IMAGE_PATH = "test_document.png"


with open(IMAGE_PATH, "rb") as file:
    content = file.read()


text = extract_document_text(content)


print("\n===== OCR RESULT =====\n")
print(text)
print("\n======================\n")