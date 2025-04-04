FROM python:3.12-slim

WORKDIR /app
COPY src/ ./src/
COPY data/ ./data/
COPY pyproject.toml uv.lock README.md ./  
RUN pip install uv
RUN uv pip install . --system


EXPOSE 8501
CMD ["streamlit", "run", "src/main.py", "--server.address", "0.0.0.0", "--server.port", "8501"]