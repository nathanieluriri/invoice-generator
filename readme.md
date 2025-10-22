
# 🚀 FastAPI Invoice Generator API

A powerful and simple API built with FastAPI to generate professional PDF invoices from JSON data. It's designed for easy integration into any application needing dynamic invoicing capabilities.

---

## ✨ Features

-   📄 **Dynamic PDF Generation**: Create clean, professional PDF invoices directly from a JSON payload.
-   👁️ **Live HTML Preview**: An endpoint to render an HTML preview of the invoice before generating the final PDF.
-   💰 **Automatic Calculations**: Automatically computes subtotals, VAT, and the total amount due based on the items provided.
-   ✍️ **Amount-to-Words Conversion**: Converts the final numerical amount into a text representation, specifically tailored for Nigerian Naira (NGN) and Kobo.
-   🛡️ **Rate Limiting**: Built-in rate limiting using Redis to prevent abuse and ensure service stability for different user types.
-   🎨 **Customizable Templates**: Uses Jinja2 for HTML templating, making the invoice design easy to modify and brand.
-   🐳 **Dockerized for Easy Deployment**: Comes with a `Dockerfile` and `docker-compose.yml` for a simple, one-command setup.

---

## 🛠️ Technology Stack

-   **Backend**: Python 3.10, FastAPI
-   **PDF Generation**: `pdfkit` (a wrapper for `wkhtmltopdf`)
-   **Rate Limiting & Caching**: Redis
-   **Web Server**: Gunicorn with Uvicorn workers
-   **Containerization**: Docker & Docker Compose

---

## 🚀 Getting Started

### Prerequisites

-   [Docker](https://www.docker.com/get-started)
-   [Docker Compose](https://docs.docker.com/compose/install/)

### Installation & Running

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    ```

2.  **Create an environment file (optional but recommended):**
    If using the provided `docker-compose.yml` with Celery, create a `.env` file and add the following:
    ```env
    CELERY_BROKER_URL=redis://redis:6379/0
    CELERY_RESULT_BACKEND=redis://redis:6379/1
    ```

3.  **Build and run the application with Docker Compose:**
    This single command will build the Docker image, start the FastAPI application, and launch the Redis service.
    ```bash
    docker-compose up --build
    ```

4.  **Access the application:**
    The API will be running and available at `http://localhost:7860`.

---

## 📁 Project Structure

````

.
├── docker-compose.yml    \# Defines the services, network, and volumes
├── Dockerfile            \# Instructions to build the application image
├── main.py               \# The main FastAPI application code
├── requirements.txt      \# Python dependencies
├── static/               \# For serving static files like logos
│   └── uploads/
├── templates/            \# Jinja2 HTML templates
│   └──├── editor.html
│      ├── invoice_template.html
│      ├── invoice_template1.html
            

````



## 🔌 API Endpoints

Here are the primary endpoints for the service:

-   `GET /`
    -   **Description**: Serves the main HTML page for the invoice editor.
    -   **Response**: `HTMLResponse`

-   `POST /render_invoice`
    -   **Description**: Renders an HTML preview of the invoice. Useful for live updates in a UI.
    -   **Body**: JSON object containing invoice data.
    -   **Response**: JSON with the rendered HTML string: `{"html": "..."}`.

-   `POST /generate_pdf`
    -   **Description**: The main endpoint. Generates the final PDF from the invoice data.
    -   **Body**: JSON object containing the complete invoice data.
    -   **Response**: A PDF file (`application/pdf`) as an attachment.

---



## 📄 License

This project is licensed under the MIT License.
```