# Use a newer Python base image
FROM python:3.9-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Add PostgreSQL apt repository and set timezone
RUN apt-get update \
    && apt-get install -y curl gnupg2 tzdata \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] http://apt.postgresql.org/pub/repos/apt bullseye-pgdg main" > /etc/apt/sources.list.d/postgresql.list \
    && ln -fs /usr/share/zoneinfo/Asia/Kolkata /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata

# Install system dependencies including PostgreSQL 14 client tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcups2-dev \
    netcat \
    postgresql-client-14 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies including development packages
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
    watchdog \
    python-dotenv \
    flask-shell-ipython \
    ipdb

# Copy the entrypoint script into the container
COPY entrypoint.sh .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Copy the rest of the application code
COPY . .

# Create and set permissions for backup directory
RUN mkdir -p /app/backups && chmod 755 /app/backups

# Set default environment variables
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/product_sticker_app
ENV POSTGRES_HOST=db
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=product_sticker_app
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV TZ=Asia/Kolkata

# Expose the port the app runs on
EXPOSE 5000

# Set the entrypoint script to be executed
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
