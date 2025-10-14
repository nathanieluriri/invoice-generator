import math
import os
import time
import uuid
from typing import List, Optional

import pdfkit
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse,HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from limits import parse
from limits.storage import RedisStorage
from limits.strategies import FixedWindowRateLimiter
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

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


# --- Application Setup ---
app = FastAPI(title="Invoice generator",summary="This project is a FastAPI-based API designed to dynamically generate professional PDF invoices from JSON data.",description="It automatically calculates totals and VAT, converts numerical amounts to words in Nigerian Naira (NGN), and provides an HTML endpoint for live previews. The entire application is containerized using Docker and includes a Redis-backed rate limiting system, making it a robust and easily deployable solution for any system needing automated invoicing.")

# --- Configuration ---
# IMPROVEMENT: Use environment variables for configuration to avoid hardcoding.
# This makes the app portable to different environments (dev, prod, Docker, etc.).
WKHTMLTOPDF_PATH = os.getenv("WKHTMLTOPDF_PATH", r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
if not os.path.exists(WKHTMLTOPDF_PATH):
    print(f"WARNING: wkhtmltopdf not found at configured path: {WKHTMLTOPDF_PATH}")
    # On Linux/macOS, it might be in the system PATH, so pdfkit might find it.
    # If not, pdfkit will raise an error.
    config = {}
else:
    config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files to serve images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 template environment
templates = Environment(loader=FileSystemLoader("templates"))


# --- Rate Limiting (Your implementation was already good) ---
# NOTE: The dependencies `repositories.tokens_repo` and `schemas.response_schema`
# are assumed to exist and function as in your original code. For this example to be
# runnable, these would need to be defined or stubbed.

# Stubbing dependencies for demonstration purposes
class MockAccessToken:
    def __init__(self, userId, role):
        self.userId = userId
        self.role = role

async def get_access_tokens_no_date_check(accessToken: str):
    # This is a mock. In a real app, you'd verify the token.
    if accessToken == "admin-token":
        return MockAccessToken("admin_user_123", "admin")
    if accessToken == "member-token":
        return MockAccessToken("member_user_456", "member")
    return None

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

# Construct the connection string dynamically.
storage = RedisStorage(f"redis://{REDIS_HOST}:6379/0")
limiter = FixedWindowRateLimiter(storage)
RATE_LIMITS = {
    "annonymous": parse("500/minute"),
    "member": parse("1000/minute"),
    "admin": parse("1400/minute"),
}
import decimal

# Use the Decimal type for financial calculations to avoid floating-point inaccuracies
# For example, float(19.99) * 100 can be 1998.9999999999998
# Decimal('19.99') * 100 is exactly Decimal('1999.00')
Context = decimal.Context(prec=32)

# --- Define the building blocks for number-to-word conversion ---
LESS_THAN_20 = [
    "ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", 
    "TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN", 
    "SEVENTEEN", "EIGHTEEN", "NINETEEN"
]
TENS = [
    "", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"
]
THOUSANDS = [
    "", "THOUSAND", "MILLION", "BILLION", "TRILLION"
]

def _number_to_words_less_than_thousand(n):
    """Converts a number from 0 to 999 into words."""
    if n < 20:
        return LESS_THAN_20[n]
    elif n < 100:
        tens_part = TENS[n // 10]
        ones_part = LESS_THAN_20[n % 10] if n % 10 != 0 else ""
        return f"{tens_part} {ones_part}".strip()
    else: # n >= 100
        hundreds_part = f"{LESS_THAN_20[n // 100]} HUNDRED"
        remainder = n % 100
        if remainder == 0:
            return hundreds_part
        else:
            # Using "AND" is common in financial text
            return f"{hundreds_part} AND {_number_to_words_less_than_thousand(remainder)}"

def number_to_words(num):
    """Converts a non-negative integer into its English word representation."""
    if num < 0:
        raise ValueError("Cannot convert negative numbers.")
    if num == 0:
        return "ZERO"

    # Process the number in chunks of three digits (thousands, millions, etc.)
    parts = []
    thousand_level = 0
    while num > 0:
        chunk = num % 1000
        if chunk != 0:
            chunk_in_words = _number_to_words_less_than_thousand(chunk)
            scale_word = THOUSANDS[thousand_level]
            parts.append(f"{chunk_in_words} {scale_word}".strip())
        num //= 1000
        thousand_level += 1
    
    return " ".join(reversed(parts)).strip()

def amount_to_words_ngn(total_due):
    """
    Converts a numerical amount into its proper word representation in Nigerian Naira and Kobo.
    
    Args:
        total_due (float, int, or decimal.Decimal): The numerical amount.
    
    Returns:
        str: The amount in words, e.g., "ONE THOUSAND NAIRA AND FIFTY KOBO ONLY".
    """
    try:
        # Use Decimal for precision
        total_due = Context.create_decimal(total_due)
        if total_due < 0:
            return "INVALID AMOUNT: Cannot process negative values."

        # Quantize to 2 decimal places, rounding to the nearest cent (kobo)
        total_due = total_due.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)
        
        naira = int(total_due)
        # Calculate kobo from the decimal part to avoid float precision issues
        kobo = int((total_due - naira) * 100)

        if naira == 0 and kobo == 0:
            return "ZERO NAIRA ONLY"

        naira_words = number_to_words(naira) if naira > 0 else ""
        kobo_words = number_to_words(kobo) if kobo > 0 else ""

        result = []

        if naira > 0:
            result.append(naira_words)
            result.append("NAIRA")

        if kobo > 0:
            if naira > 0:
                result.append("AND")
            result.append(kobo_words)
            result.append("KOBO")
        
        result.append("ONLY")
        
        return " ".join(result)

    except (ValueError, TypeError, decimal.InvalidOperation):
        return "INVALID AMOUNT: Please provide a valid number."

async def get_user_type(request: Request) -> tuple[str, str]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        ip_address = request.headers.get("X-Forwarded-For", request.client.host)
        return ip_address, "annonymous"

    token = auth_header.split(" ")[1]
    access_token = await get_access_tokens_no_date_check(accessToken=token)

    if not access_token:
        ip_address = request.headers.get("X-Forwarded-For", request.client.host)
        return ip_address, "annonymous"

    user_id = access_token.userId
    user_type = access_token.role
    return user_id, user_type if user_type in RATE_LIMITS else "annonymous"


# --- Middleware ---
class RateLimitingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_id, user_type = await get_user_type(request)
        rate_limit_rule = RATE_LIMITS[user_type]
        allowed = limiter.hit(rate_limit_rule, user_id)
        reset_time, remaining = limiter.get_window_stats(rate_limit_rule, user_id)
        seconds_until_reset = max(math.ceil(reset_time - time.time()), 0)

        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={
                    "X-User-Type": user_type, "X-User-Id": user_id,
                    "X-RateLimit-Limit": str(rate_limit_rule.amount),
                    "X-RateLimit-Remaining": str(max(remaining, 0)),
                    "X-RateLimit-Reset": str(seconds_until_reset),
                    "Retry-After": str(seconds_until_reset),
                },
                content={"detail": "Too Many Requests", "retry_after": seconds_until_reset},
            )

        response = await call_next(request)
        response.headers["X-User-Id"] = user_id
        response.headers["X-User-Type"] = user_type
        response.headers["X-RateLimit-Limit"] = str(rate_limit_rule.amount)
        response.headers["X-RateLimit-Remaining"] = str(max(remaining, 0))
        response.headers["X-RateLimit-Reset"] = str(seconds_until_reset)
        return response

app.add_middleware(RateLimitingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Should be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Helper Functions ---
def calculate_totals(data: dict) -> dict:
    """Compute subtotal, VAT, and total_due."""
    items = data.get("items", [])
    subtotal = sum(float(item.get("quantity", 0)) * float(item.get("unit_price", 0)) for item in items)
    
    # Ensure items have the correct total
    for item in items:
        item['total'] = float(item.get("quantity", 0)) * float(item.get("unit_price", 0))

    vat_rate = float(data.get("vat_rate", 7.5))
    vat_amount = round(subtotal * vat_rate / 100, 2)
    total_due = round(subtotal + vat_amount, 2)

    data.update({
        "subtotal": subtotal,
        "vat_amount": vat_amount,
        "total_due": total_due,
        "total_in_words": f"{amount_to_words_ngn(total_due)}. "  # Basic implementation
    })
    return data


# --- API Endpoints ---
@app.get("/", include_in_schema=False)
async def editor_page(request: Request):
    # This route would serve your main HTML file
    # Assuming 'editor.html' is in a 'templates' directory
    template = templates.get_template('editor.html')
    return HTMLResponse(template.render({"request": request}))


@app.post("/render_invoice")
async def render_invoice(data: InvoiceData):
    """Renders invoice data to HTML for live preview."""
    data_dict = data.dict(by_alias=True)
    processed_data = calculate_totals(data_dict)
    template = templates.get_template('invoice_template.html')
    html = template.render(processed_data)
    return JSONResponse({"html": html})


@app.post("/upload_image")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """Handles image uploads, saving them with unique names."""
    # IMPROVEMENT: Generate a unique filename to prevent overwrites.
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    # URL for browser preview (e.g., http://.../static/uploads/file.jpg)
    base_url = str(request.base_url).rstrip("/")
    public_url = f"{base_url}/static/uploads/{unique_filename}"

    # Absolute file path for pdfkit (e.g., file:///C:/.../static/uploads/file.jpg)
    abs_path = os.path.abspath(file_path).replace("\\", "/")
    file_url_for_pdf = f"file:///{abs_path}"

    return {
        "url": public_url,      # For browser/preview use
        "pdf_url": file_url_for_pdf  # For pdfkit backend use
    }

@app.post("/generate_pdf")
async def generate_pdf(data: InvoiceData):
    """Generates a PDF from invoice data and returns it as a file response."""
    data_dict = data.dict(by_alias=True)
    processed_data = calculate_totals(data_dict)
    
    template = templates.get_template('invoice_template.html')
    html = template.render(processed_data)

    # IMPROVEMENT: Use a temporary file to handle concurrent requests safely.
    try:
        # FIX: Specify UTF-8 encoding to handle special characters like the Naira sign.
        options = {
            "enable-local-file-access": "",
            "encoding": "UTF-8",
        }
        
        pdf_bytes = pdfkit.from_string(
            html,
            False,  # Return as bytes instead of writing to a file directly
            configuration=config,
            options=options,
        )
        
        # Create a temporary file to send the response
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name
        
        filename = f"invoice_{data.invoice_number or 'draft'}.pdf"
        
        # Use a background task to clean up the file after the response is sent
        from starlette.background import BackgroundTask
        cleanup_task = BackgroundTask(os.remove, path=temp_pdf_path)

        return FileResponse(
            temp_pdf_path,
            media_type="application/pdf",
            filename=filename,
            background=cleanup_task
        )

    except Exception as e:
        # IMPROVEMENT: Graceful error handling if PDF generation fails.
        print(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed. Ensure wkhtmltopdf is installed and configured correctly. Error: {e}")
