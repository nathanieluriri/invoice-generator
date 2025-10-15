from pydantic import BaseModel,Field
from typing import Optional,List

# --- Pydantic Models for Data Validation ---
# By using Pydantic, FastAPI will automatically validate incoming request data.
# This prevents malformed data from causing runtime errors.


class InvoiceItem(BaseModel):
    description: str = "Item Description"
    quantity: float = 1
    unit_price: float = Field(0, alias="unit_price")
    total: float = 0


class InvoiceData(BaseModel):
    # Brand Details
    brand_name: Optional[str] = "Your Brand Name"
    brand_logo_url: Optional[str] = ""
    brand_color: Optional[str] = "#000000"
    accent_color: Optional[str] = "#808080"
    rc_number: Optional[str] = ""
    address: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""

    # Client & Invoice Details
    invoice_number: Optional[str] = "INV-001"
    date: Optional[str] = ""
    client_name: Optional[str] = "Client Name"
    invoice_title: Optional[str] = "Invoice Title"

    # Payment Details
    payee_name: Optional[str] = ""
    account_number: Optional[str] = ""
    bank_name: Optional[str] = ""

    # Items and Totals
    items: List[InvoiceItem] = []
    subtotal: Optional[float] = 0
    vat_rate: Optional[float] = 7.5
    vat_amount: Optional[float] = 0
    total_due: Optional[float] = 0
    total_in_words: Optional[str] = "ZERO NAIRA ONLY"
    watermark_url: Optional[str] = ""
