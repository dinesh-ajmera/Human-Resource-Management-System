FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN useradd --create-home --shell /usr/sbin/nologin appuser
WORKDIR /home/appuser/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .
RUN chmod +x entrypoint.sh

USER appuser
EXPOSE 5000
CMD ["./entrypoint.sh"]