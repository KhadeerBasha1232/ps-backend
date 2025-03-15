# Product Space Backend

This is the backend for the Product Space application. It fetches job listings from Naukri and LinkedIn and stores them in Supabase. The application uses Flask for the web server, Celery for task management, and Redis as the message broker.

## Prerequisites

- Docker
- Docker Compose

## Setup

1. Clone the repository:
   ```sh
   git clone <repository-url>
   cd product-space/backend
   ```

2. Create a `.env` file with your Supabase URL and ANON key:
   ```plaintext
   SUPABASE_URL=<your-supabase-url>
   SUPABASE_KEY=<your-supabase-key>
   ```

3. Build and start the Docker containers:
   ```sh
   docker-compose up --build
   ```

## Endpoints

### Fetch Jobs

- **URL:** `/fetch-jobs`
- **Method:** `GET`
- **Query Parameters:**
  - `keyword` (optional): The job keyword to search for.
  - `location` (optional): The job location to search for.

This endpoint triggers the job fetching process. If `keyword` and `location` are provided, it fetches jobs for the specified keyword and location. Otherwise, it iterates through predefined lists of keywords and locations.

### Get Jobs

- **URL:** `/get-jobs`
- **Method:** `GET`
- **Query Parameters:**
  - `keyword` (optional): Filter jobs by keyword.
  - `location` (optional): Filter jobs by location.
  - `company` (optional): Filter jobs by company.
  - `technology` (optional): Filter jobs by technology.
  - `source` (optional): Filter jobs by source.
  - `limit` (optional): Number of jobs per request (default: 10).
  - `offset` (optional): Pagination offset (default: 0).

This endpoint retrieves jobs from the Supabase database based on the provided filters.

## Application Explanation

- **Flask:** The web server framework used to create the API endpoints.
- **Celery:** The task management library used to handle background job fetching tasks.
- **Redis:** The message broker used by Celery.
- **Supabase:** The database service used to store job listings.
- **Gunicorn:** The WSGI HTTP server used to serve the Flask application.
- **Supervisord:** The process manager used to run both Gunicorn and Celery in the same container.

## Directory Structure

```
backend/
├── app.py                # Main Flask application
├── celery_app.py         # Celery application setup
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Dockerfile for building the Docker image
├── requirements.txt      # Python dependencies
├── supervisord.conf      # Supervisord configuration
├── tasks.py              # Celery tasks
├── .env                  # Environment variables
├── .gitignore            # Git ignore file
└── README.md             # This README file
```
