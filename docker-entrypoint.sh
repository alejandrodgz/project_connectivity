#!/bin/bash
set -e

echo "🚀 Starting Django application..."

# Wait for database to be ready
echo "⏳ Waiting for database..."

# Extract database info from DATABASE_URL or use individual env vars
if [ -n "$DATABASE_URL" ]; then
    # Parse DATABASE_URL: mysql://user:pass@host:port/dbname
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_PASSWORD=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
fi

max_retries=30
retry_interval=2

for i in $(seq 1 $max_retries); do
    if python3 -c "import MySQLdb; MySQLdb.connect(host='${DB_HOST}', user='${DB_USER}', passwd='${DB_PASSWORD}', db='${DB_NAME}', port=${DB_PORT:-3306})" 2>/dev/null; then
        echo "✅ Database is ready!"
        break
    else
        if [ $i -eq $max_retries ]; then
            echo "❌ Database connection failed after $max_retries attempts"
            exit 1
        fi
        echo "⏳ Database not ready yet (attempt $i/$max_retries), waiting ${retry_interval}s..."
        sleep $retry_interval
    fi
done

# Run database migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# Collect static files (if needed in production)
if [ "$DJANGO_ENV" = "production" ]; then
    echo "📁 Collecting static files..."
    python manage.py collectstatic --noinput --clear
fi

# Create superuser automatically if environment variables are set
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "👤 Creating superuser..."
    python manage.py createsuperuser \
        --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL" \
        2>/dev/null || echo "ℹ️  Superuser already exists or creation skipped"
fi

# Create service accounts for external services
echo "🔐 Creating service accounts..."

# Document Service Account
if [ -n "$DOCUMENT_SERVICE_USERNAME" ] && [ -n "$DOCUMENT_SERVICE_PASSWORD" ]; then
    python manage.py create_service_accounts \
        --service-name "document-service" \
        --username "$DOCUMENT_SERVICE_USERNAME" \
        --password "$DOCUMENT_SERVICE_PASSWORD" \
        --email "$DOCUMENT_SERVICE_EMAIL" \
        2>/dev/null || echo "ℹ️  Document service account already exists"
fi

# Auth Service Account
if [ -n "$AUTH_SERVICE_USERNAME" ] && [ -n "$AUTH_SERVICE_PASSWORD" ]; then
    python manage.py create_service_accounts \
        --service-name "auth-service" \
        --username "$AUTH_SERVICE_USERNAME" \
        --password "$AUTH_SERVICE_PASSWORD" \
        --email "$AUTH_SERVICE_EMAIL" \
        2>/dev/null || echo "ℹ️  Auth service account already exists"
fi

# Generic service account (if needed)
if [ -n "$SERVICE_ACCOUNT_USERNAME" ] && [ -n "$SERVICE_ACCOUNT_PASSWORD" ]; then
    python manage.py create_service_accounts \
        --service-name "${SERVICE_ACCOUNT_NAME:-generic-service}" \
        --username "$SERVICE_ACCOUNT_USERNAME" \
        --password "$SERVICE_ACCOUNT_PASSWORD" \
        --email "${SERVICE_ACCOUNT_EMAIL:-service@system.local}" \
        2>/dev/null || echo "ℹ️  Generic service account already exists"
fi

echo "✅ Initialization complete!"
echo "🌐 Starting server..."

# Execute the main command (passed as arguments to this script)
exec "$@"
