FROM python:3.11-slim
WORKDIR /srv/rag
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt ./
RUN pip install --no-cache-dir torch==2.13.0+cpu --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 10001 rag && mkdir -p .cache && chown rag:rag .cache
COPY app ./app
COPY corpus ./corpus
COPY sql ./sql
USER rag
RUN python -m app.smoke model --download
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "8", "--no-access-log"]
