FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files (if any) - ignore failure in case staticfiles not configured
RUN python manage.py collectstatic --noinput || true

# Default port
EXPOSE 8000

CMD ["gunicorn", "agricultural_project.wsgi:application", "--bind", "0.0.0.0:8000"]
