from docx import Document
import os


def merge_docs(output_path, *input_paths):
    merged_doc = Document()

    for file_path in input_paths:
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            continue

        doc = Document(file_path)
        for element in doc.element.body:
            merged_doc.element.body.append(element)

    merged_doc.save(output_path)
    print(f"Documents merged successfully into {output_path}")


if __name__ == "__main__":
    output_file = "merged_document.docx"
    input_files = ["doc1.docx", "doc2.docx", "doc3.docx"]
    merge_docs(output_file, *input_files)
