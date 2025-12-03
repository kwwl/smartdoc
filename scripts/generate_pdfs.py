from reportlab.lib.utils import ImageReader
import os
import random
from datetime import datetime, timedelta
from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont
import io

fake = Faker("fr_FR")

CATEGORIES = [
    "facture",
    "devis",
    "contrat",
    "fiche_paie",
    "documents_rh",
    "notes_frais",
]


def ensure_dirs(base):
    for cat in CATEGORIES:
        os.makedirs(os.path.join(base, cat), exist_ok=True)


def random_date(start_days_back=365):
    return datetime.now() - timedelta(days=random.randint(0, start_days_back))


def make_logo(initials, size=(200, 60)):
    img = Image.new(
        "RGB",
        size,
        color=(
            random.randint(20, 200),
            random.randint(20, 200),
            random.randint(20, 200),
        ),
    )
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
    except:
        font = ImageFont.load_default()

    try:
        w, h = draw.textsize(initials, font=font)
    except AttributeError:
        bbox = draw.textbbox((0, 0), initials, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

    draw.text(((size[0] - w) / 2, (size[1] - h) / 2), initials, fill="white", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def generate_invoice(path):
    print(f"Création de la facture: {path}")
    company = fake.company()
    client = fake.name()
    invoice_no = f"F-{random.randint(1000,9999)}"
    date = random_date()
    due = date + timedelta(days=30)

    items = [
        (
            fake.sentence(nb_words=random.randint(3, 7)),
            random.randint(1, 5),
            round(random.uniform(20, 1200), 2),
        )
        for _ in range(3)
    ]
    total = sum(q * p for _, q, p in items)
    logo_buf = make_logo("".join([w[0] for w in company.split()][:2]))
    logo_image = ImageReader(logo_buf)  # <-- conversion BytesIO -> ImageReader

    def draw(c, w, h):
        c.drawImage(
            logo_image, 20 * mm, h - 30 * mm, width=50 * mm, height=15 * mm, mask="auto"
        )
        c.setFont("Helvetica-Bold", 16)
        c.drawString(20 * mm, h - 40 * mm, f"Facture {invoice_no}")
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, h - 60 * mm, f"Société: {company}")
        c.drawString(20 * mm, h - 70 * mm, f"Client: {client}")
        c.drawString(120 * mm, h - 60 * mm, f"Date: {date.strftime('%d/%m/%Y')}")
        c.drawString(120 * mm, h - 66 * mm, f"Échéance: {due.strftime('%d/%m/%Y')}")

        data = (
            [["Description", "Qté", "Prix U", "Total"]]
            + [
                [desc, str(qty), f"{price:.2f}", f"{qty*price:.2f}"]
                for desc, qty, price in items
            ]
            + [["", "", "Total TTC", f"{total:.2f}"]]
        )
        table = Table(data, colWidths=[90 * mm, 20 * mm, 30 * mm, 30 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("ALIGN", (-2, 1), (-1, -1), "RIGHT"),
                    ("SPAN", (0, -1), (2, -1)),
                    ("ALIGN", (2, -1), (3, -1), "RIGHT"),
                ]
            )
        )
        table.wrapOn(c, 20 * mm, h - 140 * mm)
        table.drawOn(c, 20 * mm, h - 140 * mm)

        styles = getSampleStyleSheet()
        para = Paragraph(fake.paragraph(nb_sentences=5), styles["BodyText"])
        para.wrapOn(c, 170 * mm, 100 * mm)
        para.drawOn(c, 20 * mm, h - 250 * mm)

        c.setFont("Helvetica-Oblique", 8)
        c.drawString(20 * mm, 30 * mm, "Merci pour votre confiance.")

    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    draw(c, w, h)
    c.showPage()
    c.save()


def generate_generic_pdf(path, title):
    def draw(c, w, h):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(20 * mm, h - 40 * mm, title)
        styles = getSampleStyleSheet()
        para = Paragraph(fake.paragraph(nb_sentences=7), styles["BodyText"])
        para.wrapOn(c, 170 * mm, 200 * mm)
        para.drawOn(c, 20 * mm, h - 100 * mm)

    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    draw(c, w, h)
    c.showPage()
    c.save()


GEN_FN = {
    "facture": generate_invoice,
    "devis": lambda path: generate_generic_pdf(path, "Devis"),
    "contrat": lambda path: generate_generic_pdf(path, "Contrat"),
    "fiche_paie": lambda path: generate_generic_pdf(path, "Fiche de paie"),
    "documents_rh": lambda path: generate_generic_pdf(path, "Document RH"),
    "notes_frais": lambda path: generate_generic_pdf(path, "Note de frais"),
}


def main(output_dir, count):
    ensure_dirs(output_dir)
    for cat in CATEGORIES:
        cat_dir = os.path.join(output_dir, cat)
        for i in range(count):
            filename = f"{cat}_{i+1:04d}.pdf"
            path = os.path.join(cat_dir, filename)
            try:
                GEN_FN[cat](path)
            except Exception as e:
                print(f"Erreur lors de la génération {path}: {e}")
    print(f"Génération terminée dans: {output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        "--output",
        dest="output_dir",
        default="dataset",
        help="Dossier de sortie",
    )
    parser.add_argument(
        "--count",
        dest="count",
        type=int,
        default=50,
        help="Nombre de PDF par catégorie",
    )
    args = parser.parse_args()
    main(args.output_dir, args.count)
