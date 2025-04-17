FROM python:3.12-slim

WORKDIR /traxus
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-u", "__main__.py"]
