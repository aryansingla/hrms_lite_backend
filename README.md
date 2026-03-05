## HRMS Lite Backend

**Tech stack**: Django 5, Django REST Framework, SQLite (local), Mongo-related libs (not yet used), `django-cors-headers`.

### Local setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# optional: copy env template
cp .env.example .env

# run migrations and start server
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Environment variables

- `MONGODB_URL` – MongoDB connection string (optional, not required for SQLite).
- `MONGODB_NAME` – MongoDB database name (default: `hrms_lite`).

### Production (example: Railway)

- Install dependencies from `requirements.txt` (includes `gunicorn`).
- Use a start command like:

```bash
gunicorn hrms_lite_backend.wsgi:application --bind 0.0.0.0:$PORT
```

