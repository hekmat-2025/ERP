from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    def __repr__(self) -> str:
        return f"Customer(id={self.id!r}, name={self.name!r})"

