FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY bitbucket-mcp/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY _common/mcp_common /app/mcp_common
COPY bitbucket-mcp/app /app/app

EXPOSE 8080
CMD ["python", "-m", "app.server"]
