FROM python:latest

WORKDIR /app

COPY . .

RUN mv .env.copy .env

# Install project dependencies
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "mcp_server.py"]