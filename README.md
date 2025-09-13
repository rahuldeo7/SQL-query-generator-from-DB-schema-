# SQL-query-generator-from-DB-schema-

# 🧠 Interactive SQL Generator

This project provides an interactive endpoint (`/query/interactive`) that takes a **natural language user query** and a **database schema (JSON)** and:

1. Detects **relevant tables** based on the user query.
2. Detects **relevant columns inside those tables**.
3. Generates **SQL `SELECT` queries** to display the first 5 rows from those columns.

This helps users **explore and understand the schema** by asking questions in plain English.

---

## ⚙️ Requirements

- Python 3.10+
- Flask
- OpenAI Python SDK (`openai`)
- A valid **OpenAI GPT API key** (required for GPT-4.1 model calls)

---

## 🔑 Setup OpenAI API Key

Before running the project, set your GPT API key as an environment variable:

### macOS / Linux (bash/zsh)
```bash
export OPENAI_API_KEY="your_api_key_here"
