FROM python:3.12-slim

WORKDIR /app

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

CMD ["python", "-m", "pytest", "tests/", \
     "--junitxml=junit.xml", \
     "--cov=src", \
     "--cov-report=html:htmlcov", \
     "--cov-report=xml:coverage.xml", \
     "--cov-report=term-missing", \
     "-v"]
