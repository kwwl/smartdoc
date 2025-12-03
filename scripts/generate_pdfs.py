#!/usr/bin/env python3
"""
generate_pdfs.py
Génère automatiquement des PDFs réalistes pour les catégories :
- facture
- devis
- contrat
- fiche_paie
- documents_rh
- notes_frais

Usage:
    python generate_pdfs.py --out dataset --count 50
"""

import os
import random
from datetime import datetime, timedelta
from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
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
    w, h = draw.textsize(initials, font=font)
    draw.text(((size[0] - w) / 2, (size[1] - h) / 2), initials, fill="white", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def save_pdf(filepath, draw_fn):
    c = canvas.Canvas(filepath, pagesize=A4)
    w, h = A4
    draw_fn(c, w, h)
    c.showPage()
    c.save()


# --- Fonctions de génération par catégorie ---


def generate_invoice(path):
    company = fake.company()
    company_addr = fake.address().replace("\n", ", ")
    client = fake.name()
    client_addr = fake.address().replace("\n", ", ")
    invoice_no = f"F-{random.randint(1000,9999)}"
    date = random_date()
    due = date + timedelta(days=30)
    items = [
        (
            fake.sentence(nb_words=random.randint(3, 7)),
            random.randint(1, 5),
            round(random.uniform(20, 1200), 2),
        )
        for _ in range(random.randint(2, 6))
    ]
    total = round(sum(q * p for (_, q, p) in items), 2)
    logo_buf = make_logo("".join([w[0] for w in company.split()][:2]))

    def draw(c, w, h):
        c.drawImage(
            logo_buf, 20 * mm, h - 30 * mm, width=50 * mm, height=15 * mm, mask="auto"
        )
        c.setFont("Helvetica-Bold", 16)
        c.drawString(20 * mm, h - 40 * mm, company)
        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, h - 46 * mm, company_addr)
        c.drawString(120 * mm, h - 30 * mm, f"Facture: {invoice_no}")
        c.drawString(120 * mm, h - 36 * mm, f"Date: {date.strftime('%d/%m/%Y')}")
        c.drawString(120 * mm, h - 42 * mm, f"Échéance: {due.strftime('%d/%m/%Y')}")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, h - 60 * mm, "Facturer à :")
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, h - 66 * mm, client)
        c.drawString(20 * mm, h - 72 * mm, client_addr)
        data = (
            [["Description", "Qté", "Prix Unitaire", "Total"]]
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
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(20 * mm, 30 * mm, "Merci pour votre confiance.")

    save_pdf(path, draw)


# --- Devis, Contrat, Fiche de paie, Documents RH, Notes de frais ---
# Fonctions similaires à generate_invoice, adaptées à chaque catégorie
# Pour simplifier ici, on réutilise la fonction invoice mais tu peux créer des variantes plus détaillées


def generate_generic_pdf(path, title):
    def draw(c, w, h):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(20 * mm, h - 40 * mm, title)
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, h - 60 * mm, fake.paragraph())

    save_pdf(path, draw)


GEN_FN = {
    "facture": generate_invoice,
    "devis": lambda path: generate_generic_pdf(path, "Devis"),
    "contrat": lambda path: generate_generic_pdf(path, "Contrat"),
    "fiche_paie": lambda path: generate_generic_pdf(path, "Fiche de paie"),
    "documents_rh": lambda path: generate_generic_pdf(path, "Document RH"),
    "notes_frais": lambda path: generate_generic_pdf(path, "Note de frais"),
}


# --- Main ---
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
    print(f"✅ Génération terminée dans: {output_dir}")


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
