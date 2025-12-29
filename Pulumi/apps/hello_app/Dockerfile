FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY req.txt .
RUN pip install --no-cache-dir -r req.txt

COPY . .
RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "hello_app.wsgi:application", "--bind", "0.0.0.0:8000"]