FROM python:3.12-slim

WORKDIR /app
COPY copo_do_mundo_oficial.py ./
COPY copo_do_mundo.png ./
COPY pyproject.toml uv.lock README.md ./  
RUN pip install uv
RUN uv pip install . --system

EXPOSE 8501
CMD ["streamlit", "run", "copo_do_mundo_oficial.py", "--server.address", "0.0.0.0", "--server.port", "8501"]