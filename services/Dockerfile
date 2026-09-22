# syntax=docker/dockerfile:1
# One Dockerfile for every Python service. Build context: services/
#   docker build -f services/Dockerfile --build-arg SERVICE=sample-api services
# The service runs as `python -m <module>` where module = SERVICE with '-' -> '_'.

FROM ghcr.io/astral-sh/uv:0.12-python3.12-trixie-slim AS build
ARG SERVICE
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    test -n "$SERVICE" && \
    uv sync --frozen --no-dev --no-editable --package "$SERVICE"

FROM python:3.12-slim-trixie
ARG SERVICE
RUN useradd --system --uid 10001 app
COPY --from=build /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 SERVICE=${SERVICE}
USER 10001
EXPOSE 8000
CMD ["sh", "-c", "exec python -m $(echo \"$SERVICE\" | tr - _)"]
