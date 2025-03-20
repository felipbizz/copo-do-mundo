FROM python:3.12-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy project files first to leverage Docker cache
COPY pyproject.toml .

# Install dependencies using UV
RUN uv pip install .

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p images

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "copo_do_mundo_oficial.py", "--server.address", "0.0.0.0", "--server.port", "8501"] 