from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    hsn_code: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    gst_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    image_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    def __repr__(self) -> str:
        return f"Product(id={self.id!r}, name={self.name!r})"

