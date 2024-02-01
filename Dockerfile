
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

COPY . /app
WORKDIR /app

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]