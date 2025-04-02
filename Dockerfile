FROM python:3.12-slim

WORKDIR /app
COPY data/ ./data/
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY pyproject.toml uv.lock README.md main.py config.py ./  
RUN pip install uv
RUN uv pip install . --system
#
EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.address", "0.0.0.0", "--server.port", "8501"]