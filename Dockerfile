# Clean Agent — production image
# Build:  docker build -t clean-agent .
# Run:    docker run --rm -it --network host -v $(pwd)/data:/app/data clean-agent
# Ollama must be reachable (host network or OLLAMA_HOST)

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY config.py main.py ./
COPY core ./core
COPY memory ./memory
COPY channels ./channels
COPY skills ./skills

RUN pip install --no-cache-dir -e ".[telegram]"

# Persist memory/skills/logs outside container
ENV CLEAN_AGENT_ROOT=/app/data
RUN mkdir -p /app/data/memory /app/data/skills /app/data/logs

# Default: CLI. Override: dream | telegram | status
ENTRYPOINT ["python", "main.py"]
CMD ["cli"]
