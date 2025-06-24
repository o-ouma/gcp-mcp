# GCP-MCP Server

This project makes use of an MCP server to implement AI-powered cloud management. With the server, one can:
 - List vpc networks and subnets
 - List ip addresses in a project and resources using them
 - List persistent disks in a project
 - List virtual machines running in a project

## Project Setup

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

## Project Structure

- `app.py`: Main application file
- `requirements.txt`: Python dependencies

