from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.product import Product
from services.validation import require_non_empty, require_non_negative_number

logger = logging.getLogger(__name__)


class ProductsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_products(self) -> list[Product]:
        return list(self._session.scalars(select(Product).order_by(Product.name.asc())))

    def create_product(self, *, name: str, hsn_code: str, rate: float, gst_rate: float, image_path: str = "") -> Product:
        product = Product(
            name=require_non_empty(name, "Product name"),
            hsn_code=(hsn_code or "").strip(),
            rate=require_non_negative_number(rate, "Rate"),
            gst_rate=require_non_negative_number(gst_rate, "GST rate"),
            image_path=(image_path or "").strip(),
        )
        self._session.add(product)
        self._session.commit()
        logger.info("Created product id=%s name=%s", product.id, product.name)
        return product

    def update_product(
        self,
        product_id: int,
        *,
        name: str,
        hsn_code: str,
        rate: float,
        gst_rate: float,
        image_path: str = "",
    ) -> Product:
        product = self._session.get(Product, product_id)
        if not product:
            raise ValueError("Product not found.")

        product.name = require_non_empty(name, "Product name")
        product.hsn_code = (hsn_code or "").strip()
        product.rate = require_non_negative_number(rate, "Rate")
        product.gst_rate = require_non_negative_number(gst_rate, "GST rate")
        product.image_path = (image_path or "").strip()
        self._session.commit()
        logger.info("Updated product id=%s", product.id)
        return product

    def delete_product(self, product_id: int) -> None:
        product = self._session.get(Product, product_id)
        if not product:
            return
        self._session.delete(product)
        self._session.commit()
        logger.info("Deleted product id=%s", product_id)

