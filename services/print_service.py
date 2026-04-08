from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from reports.invoice_pdf import generate_invoice_pdf
from services.invoices_service import InvoicesService
from utils.config import Settings
from utils.paths import app_root

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PrintResult:
    output_path: Path


class PrintService:
    """
    Backend print/PDF module.
    Keeps UI thin by handling invoice loading + PDF generation here.
    """

    def __init__(self, session: Session, *, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    def invoice_to_pdf(self, *, invoice_id: int, output_pdf: Path) -> PrintResult:
        inv = InvoicesService(self._session).get_invoice(int(invoice_id))
        if not inv:
            raise RuntimeError("Invoice not found.")

        generate_invoice_pdf(
            invoice=inv,
            settings=self._settings,
            output_pdf=output_pdf,
            app_root=app_root(),
        )
        logger.info("Invoice PDF generated invoice_id=%s path=%s", invoice_id, output_pdf)
        return PrintResult(output_path=output_pdf)

