import os
import json
import fitz  # PyMuPDF
import argparse


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Erreur lecture {pdf_path}: {e}")
    return text.strip()


def main(input_dir, output_file):
    data = []
    if not os.path.exists(input_dir):
        print(f"Dossier {input_dir} n'existe pas !")
        return

    categories = [
        c for c in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, c))
    ]
    if not categories:
        print(f"Aucun sous-dossier trouvé dans {input_dir}")
        return

    for category in categories:
        cat_path = os.path.join(input_dir, category)
        print(f"Catégorie trouvée : {category}")
        pdf_files = [f for f in os.listdir(cat_path) if f.lower().endswith(".pdf")]
        if not pdf_files:
            print(f"Aucun PDF trouvé dans {cat_path}")
            continue
        for pdf_file in pdf_files:
            pdf_path = os.path.join(cat_path, pdf_file)
            print(f"Traitement : {pdf_path}")
            text = extract_text_from_pdf(pdf_path)
            if text:
                data.append({"text": text, "metadata": {"category": category}})
            else:
                print(f"PDF vide ou extraction échouée : {pdf_path}")

    if data:
        with open(output_file, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"Dataset JSONL généré dans {output_file}, {len(data)} entrées")
    else:
        print("Aucun PDF n'a été converti, JSONL non généré.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        dest="input_dir",
        default="dataset",
        help="Dossier contenant les PDFs",
    )
    parser.add_argument(
        "--output",
        dest="output_file",
        default="dataset.jsonl",
        help="Fichier JSONL de sortie",
    )
    args = parser.parse_args()
    main(args.input_dir, args.output_file)
