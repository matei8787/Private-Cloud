FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gcc libpq-dev netcat-openbsd && apt-get clean

COPY req.txt .
RUN pip install --no-cache-dir -r req.txt

COPY . .
RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "vpn_provisioner.wsgi:application", "--bind", "0.0.0.0:8000"]

