#!/bin/bash
set -e

# ---------------------------------------------------------------------------
# Google Cloud credentials (for Vertex AI on Render / non-GCP hosts)
#
# On Cloud Run, credentials come automatically via the attached service account.
# On Render (or any host without ADC), set the env var:
#   GOOGLE_APPLICATION_CREDENTIALS_JSON=<contents of your service account key JSON>
#
# This block writes that JSON to a temp file and sets the standard
# GOOGLE_APPLICATION_CREDENTIALS env var that the GCP SDK reads.
# ---------------------------------------------------------------------------
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS_JSON" ]; then
    echo "Writing Google credentials from env var..."
    CREDS_FILE="/tmp/gcp-credentials.json"
    echo "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > "$CREDS_FILE"
    export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_FILE"
    echo "GOOGLE_APPLICATION_CREDENTIALS set to $CREDS_FILE"
fi

echo "Running database migrations..."
alembic upgrade head

echo "Starting server on port ${PORT:-8000}..."
exec gunicorn backend.main:app \
    -k uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 1 \
    --threads 4 \
    --timeout 120
