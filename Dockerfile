# Stage 1: build the React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime serving both the API and the built frontend
FROM python:3.11-slim

# docling pulls in opencv-python (not the headless build), which needs
# libGL at import time - the exact same requirement already verified in
# .github/workflows/tests.yml for running the test suite.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app

RUN pip install --no-cache-dir --upgrade pip uv

COPY --chown=user pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY --chown=user src/ ./src
COPY --chown=user backend/ ./backend
COPY --chown=user --from=frontend-builder /frontend/dist ./frontend/dist

EXPOSE 8000

# Render injects PORT (default 10000) at runtime; ${PORT:-8000} falls back
# to 8000 for local `docker run` testing without needing to set it manually.
# Shell form (not exec-array form) is required for this expansion to work;
# the leading `exec` replaces the shell process with uvicorn instead of
# running it as a child, so SIGTERM (sent on redeploys/restarts) reaches
# uvicorn directly for a clean shutdown instead of being stuck at the shell.
#
# Deliberately no --workers flag: the job store in backend/jobs/store.py is
# an in-memory dict, correct only with exactly one worker process (the
# default). Adding workers would silently break job lookups whenever a
# request landed on a different worker than the one that created the job.
CMD exec uv run uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
