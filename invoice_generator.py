from jinja2 import Environment, FileSystemLoader
import pdfkit

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('templates/invoice_template.html')
path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
data = {
    "brand_name": "Zatras Global Services Limited",
    "brand_logo_url": "https://placehold.co/700x100",
    "brand_color": "#000080",
    "accent_color": "#FF0000",
    "rc_number": "692291",
    "address": "No 4 Ockemesi Crescent, Garki 2, Abuja",
    "phone": "+2348037184337",
    "email": "zatrasglobalservicesltd@gmail.com",
    "invoice_number": "100",
    "date": "10th October, 2025",
    "client_name": "NNPC Academy",
    "payee_name": "Zatras Global Services",
    "account_number": "0071806298",
    "bank_name": "Sterling Bank",
    "invoice_title": "Delivery of Training on Global Sustainability Reporting Standards and Performance Metrics",
    "items": [
        {"quantity": 18, "description": "Participant’s Expenses", "unit_price": 650000, "total": 11700000},
        {"quantity": 2, "description": "Venue Logistics", "unit_price": 100000, "total": 200000},
    ],
    "subtotal": 11900000,
    "vat_rate": 7.5,
    "vat_amount": 892500,
    "total_due": 12792500,
    "total_in_words": "TWELVE MILLION SEVEN HUNDRED NINETY-TWO THOUSAND FIVE HUNDRED NAIRA ONLY",
    "watermark_url": "https://placehold.co/700x100"
}

html = template.render(data)

# To generate a PDF (optional)
pdfkit.from_string(html, "invoice.pdf", configuration=config)
