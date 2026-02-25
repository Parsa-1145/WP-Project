#--------- Builder image ---------#
FROM python:3.13-slim AS builder
WORKDIR /app

# Configure PDM to use an in-project virtualenv at .venv
ENV PDM_USE_VENV=true \
    PDM_VENV_IN_PROJECT=true \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install PDM and project dependencies into a local venv (.venv)
RUN pip install --upgrade pip && pip install pdm

COPY pyproject.toml pdm.lock ./
RUN pdm install --prod --no-self




#--------- Final runtime image ---------#
FROM python:3.13-slim AS runner


WORKDIR /app

# Create non-root user
RUN useradd -m appuser

# Copy application code + virtualenv + collected static files from builder
COPY --from=builder /app/.venv /app/.venv

COPY . .

ENV PATH="/app/.venv/bin:${PATH}"

COPY entrypoint.sh /entrypoint.sh

# Ensure proper ownership
RUN mkdir -p /app/staticfiles && \
    chown -R appuser:appuser /app && \
    chmod +x /entrypoint.sh
USER appuser

EXPOSE 8000

ENTRYPOINT [ "/entrypoint.sh" ]

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-"]
