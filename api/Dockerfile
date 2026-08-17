FROM python:3.13-slim
WORKDIR /app
COPY . /app/
RUN rm datadog-dashboard.json
RUN pip install -r requirements.txt