from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from models.invoice import Invoice
from utils.config import Settings
from utils.money_words import amount_to_words, currency_units

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PdfPaths:
    output_pdf: Path


def generate_invoice_pdf(*, invoice: Invoice, settings: Settings, output_pdf: Path, app_root: Path) -> PdfPaths:
    """
    Creates a professional invoice PDF using reportlab.
    """
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    canvas = Canvas(str(output_pdf), pagesize=A4)
    width, height = A4

    margin_x = 18 * mm
    y = height - 18 * mm

    # Header: logo + company name
    logo_path = (app_root / settings.logo_path).resolve()
    if logo_path.exists():
        try:
            canvas.drawImage(str(logo_path), margin_x, y - 22 * mm, width=22 * mm, height=22 * mm, mask="auto")
        except Exception:  # noqa: BLE001
            logger.exception("Failed to draw logo: %s", logo_path)

    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(margin_x + 26 * mm, y - 8 * mm, settings.company_name or "Aftab Sahar Blue Cons.")
    canvas.setFont("Helvetica", 10)
    addr = (settings.company_address or "").strip()
    if addr:
        canvas.drawString(margin_x + 26 * mm, y - 14 * mm, addr)
    phone = (settings.company_phone or "").strip()
    if phone:
        canvas.drawString(margin_x + 26 * mm, y - 19 * mm, f"Phone: {phone}")

    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawRightString(width - margin_x, y - 10 * mm, "INVOICE")

    y -= 28 * mm
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(1)
    canvas.line(margin_x, y, width - margin_x, y)
    y -= 10 * mm

    # Invoice meta + customer details
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(margin_x, y, "Bill To:")
    canvas.setFont("Helvetica", 10)
    cust = invoice.customer
    canvas.drawString(margin_x, y - 5 * mm, cust.name)
    if (cust.address or "").strip():
        canvas.drawString(margin_x, y - 10 * mm, cust.address)
    if (cust.phone or "").strip():
        canvas.drawString(margin_x, y - 15 * mm, f"Phone: {cust.phone}")

    canvas.setFont("Helvetica", 10)
    canvas.drawRightString(width - margin_x, y, f"Invoice No: {invoice.invoice_no}")
    canvas.drawRightString(width - margin_x, y - 6 * mm, f"Date: {invoice.invoice_date.isoformat()}")

    y -= 22 * mm

    # Items table columns (explicit, avoids index errors)
    x_left = margin_x
    x_right = width - margin_x
    col_product = x_left
    col_hsn = x_left + 75 * mm
    col_gst = x_left + 105 * mm
    col_rate = x_left + 125 * mm
    col_qty = x_left + 145 * mm
    col_amount = x_right

    def row_line(ypos: float) -> None:
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(0.7)
        canvas.line(margin_x, ypos, width - margin_x, ypos)

    # Header row
    canvas.setFillColor(colors.black)
    canvas.setFont("Helvetica-Bold", 9)
    header_y = y
    row_line(header_y + 4 * mm)
    canvas.drawString(col_product + 2, header_y, "Product")
    canvas.drawString(col_hsn + 2, header_y, "HSN")
    canvas.drawString(col_gst + 2, header_y, "GST %")
    canvas.drawString(col_rate + 2, header_y, "Rate")
    canvas.drawString(col_qty + 2, header_y, "Qty")
    canvas.drawRightString(col_amount - 2, header_y, "Amount")
    y -= 7 * mm
    row_line(y + 3 * mm)

    canvas.setFont("Helvetica", 9)
    for item in invoice.items:
        if y < 50 * mm:
            canvas.showPage()
            y = height - 18 * mm
        canvas.drawString(col_product + 2, y, item.product_name)
        canvas.drawString(col_hsn + 2, y, item.hsn_code or "")
        canvas.drawRightString(col_rate - 2, y, f"{item.gst_rate:.2f}")
        canvas.drawRightString(col_qty - 2, y, f"{item.rate:.2f}")
        canvas.drawRightString(col_amount - 55 * mm, y, f"{item.quantity:g}")
        canvas.drawRightString(col_amount - 2, y, f"{item.amount:.2f}")
        y -= 6 * mm

    y -= 6 * mm
    row_line(y + 10 * mm)

    # Totals
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawRightString(width - margin_x, y, f"Gross: {invoice.gross_amount:.2f}")
    y -= 6 * mm
    canvas.setFont("Helvetica", 10)
    canvas.drawRightString(width - margin_x, y, f"Tax: {invoice.tax_amount:.2f}")
    y -= 6 * mm
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawRightString(width - margin_x, y, f"Grand Total: {invoice.grand_total:.2f}")

    y -= 10 * mm
    canvas.setFont("Helvetica", 9)
    units = currency_units(settings.currency_code)
    canvas.drawString(
        margin_x,
        y,
        f"Amount in words: {amount_to_words(invoice.grand_total, major_unit=units.major, minor_unit=units.minor)}",
    )

    # Signature area
    y -= 20 * mm
    canvas.setFont("Helvetica", 10)
    canvas.drawRightString(width - margin_x, y, "Authorized Signature")
    canvas.line(width - margin_x - 55 * mm, y - 3 * mm, width - margin_x, y - 3 * mm)

    canvas.showPage()
    canvas.save()
    return PdfPaths(output_pdf=output_pdf)

