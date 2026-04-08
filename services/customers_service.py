from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.customer import Customer
from services.validation import require_non_empty

logger = logging.getLogger(__name__)


class CustomersService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_customers(self) -> list[Customer]:
        return list(self._session.scalars(select(Customer).order_by(Customer.name.asc())))

    def create_customer(self, *, name: str, address: str, phone: str) -> Customer:
        customer = Customer(
            name=require_non_empty(name, "Customer name"),
            address=(address or "").strip(),
            phone=(phone or "").strip(),
        )
        self._session.add(customer)
        self._session.commit()
        logger.info("Created customer id=%s name=%s", customer.id, customer.name)
        return customer

    def update_customer(self, customer_id: int, *, name: str, address: str, phone: str) -> Customer:
        customer = self._session.get(Customer, customer_id)
        if not customer:
            raise ValueError("Customer not found.")
        customer.name = require_non_empty(name, "Customer name")
        customer.address = (address or "").strip()
        customer.phone = (phone or "").strip()
        self._session.commit()
        logger.info("Updated customer id=%s", customer.id)
        return customer

    def delete_customer(self, customer_id: int) -> None:
        customer = self._session.get(Customer, customer_id)
        if not customer:
            return
        self._session.delete(customer)
        self._session.commit()
        logger.info("Deleted customer id=%s", customer_id)

