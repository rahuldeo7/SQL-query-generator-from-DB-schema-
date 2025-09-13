import json
import os
from flask import Blueprint, request, jsonify
from .utils import simplify_schema
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

main = Blueprint("main", __name__)

# In-memory storage
storage = {
    "user_query": None,         # Original user query
    "final_query": None,        # Confirmed query
    "raw_schema": None,
    "simplified_schema": None,
    "tables_detected": None     # Tables GPT thinks are relevant
}

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")


# ---- STEP 1: Receive User Query ----
@main.route("/query", methods=["POST"])
def receive_query():
    data = request.get_json()
    user_query = data.get("user_query")

    if not user_query:
        return jsonify({"error": "user_query is required"}), 400

    storage["user_query"] = user_query
    return jsonify({"message": "Query received", "user_query": user_query}), 201


# ---- STEP 2 & 3: Upload JSON Schema + Simplify ----
@main.route("/schema", methods=["POST"])
def receive_schema():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if not file.filename.endswith(".json"):
        return jsonify({"error": "Only .json files are allowed"}), 400

    try:
        raw_schema = json.load(file)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    simplified = simplify_schema(raw_schema)

    storage["raw_schema"] = raw_schema
    storage["simplified_schema"] = simplified

    return jsonify({
        "message": "Schema received & simplified",
        "simplified_schema": simplified
    }), 201


# ---- STEP 4: Display Simplified Schema ----
@main.route("/schema/simplified", methods=["GET"])
def get_simplified_schema():
    if not storage["simplified_schema"]:
        return jsonify({"error": "No schema uploaded yet"}), 404

    return jsonify({"simplified_schema": storage["simplified_schema"]}), 200


# ---- NEW: STEP 5A: Interactive Query → Table Detection ----
# @main.route("/query/interactive", methods=["POST"])
# def interactive_query():
#     user_query = request.get_json().get("user_query")
#     simplified = storage.get("simplified_schema")

#     if not user_query:
#         return jsonify({"error": "user_query is required"}), 400
#     if not simplified:
#         return jsonify({"error": "Schema must be uploaded first"}), 400

#     # GPT Prompt to detect relevant tables
#     prompt = f"""
# You are a database expert. Here is the simplified schema:
# {json.dumps(simplified, indent=2)}

# User query: "{user_query}"

# Return only JSON with the list of tables relevant to this query, in this format:
# {{"tables": ["table1", "table2"]}}
# Do not include any explanation.
# """

#     try:
#         response = openai.chat.completions.create(
#             model="gpt-4.1",
#             messages=[
#                 {"role": "system", "content": "You are a SQL and database expert."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0
#         )

#         # Extract GPT JSON response
#         tables_json = response.choices[0].message.content.strip()
#         tables_detected = json.loads(tables_json).get("tables", [])

#         # Store in memory
#         storage["tables_detected"] = tables_detected
#         storage["user_query"] = user_query

#         return jsonify({
#             "user_query": user_query,
#             "tables_detected": tables_detected,
#             "message": "Detected relevant tables. Please confirm or modify your query."
#         }), 200

#     except Exception as e:
#         return jsonify({"error": f"GPT table detection error: {e}"}), 500
    
# ------- Add-on ---------

@main.route("/query/interactive", methods=["POST"])
def interactive_query():
    user_query = request.get_json().get("user_query")
    simplified = storage.get("simplified_schema")

    if not user_query:
        return jsonify({"error": "user_query is required"}), 400
    if not simplified:
        return jsonify({"error": "Schema must be uploaded first"}), 400

    # GPT Prompt to detect relevant tables and columns
    prompt = f"""
You are a database expert. Here is the simplified schema:
{json.dumps(simplified, indent=2)}

User query: "{user_query}"

Identify:
1. Tables that are relevant to the query.
2. Columns inside those tables that match or are equivalent to the concepts in the query (even if the names are different).
3. For each table, create a SQL query that selects those columns and limits to 5 rows.

Return only JSON in this format:
{{
  "tables": [
    {{
      "name": "table_name",
      "columns": ["col1", "col2"]
    }}
  ],
  "sql_queries": [
    "SELECT col1, col2 FROM table_name LIMIT 5;"
  ]
}}
Do not include any explanation or commentary.
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a SQL and database expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        # Extract GPT JSON response
        gpt_output = response.choices[0].message.content.strip()
        result = json.loads(gpt_output)

        storage["tables_detected"] = result.get("tables", [])
        storage["sql_queries"] = result.get("sql_queries", [])
        storage["user_query"] = user_query

        return jsonify({
            "user_query": user_query,
            "tables_detected": result.get("tables", []),
            "sql_queries": result.get("sql_queries", []),
            "message": "Detected relevant tables and columns. Here are sample preview queries."
        }), 200

    except Exception as e:
        return jsonify({"error": f"GPT detection error: {e}"}), 500


# ---- NEW: STEP 5B: Confirm Query ----
@main.route("/query/confirm", methods=["POST"])
def confirm_query():
    data = request.get_json()
    confirmed = data.get("confirmed")
    final_query = data.get("final_query")

    if confirmed is None or not isinstance(confirmed, bool):
        return jsonify({"error": "confirmed must be true or false"}), 400
    if confirmed and not final_query:
        return jsonify({"error": "final_query is required when confirmed is true"}), 400

    if confirmed:
        storage["final_query"] = final_query
        storage["user_query"] = final_query

        # Call existing SQL generation logic
        simplified = storage.get("simplified_schema")
        prompt = f"""
You are an expert SQL generator. Use the following schema to generate a SQL query.

Schema Reference:
{json.dumps(simplified, indent=2)}

User Request:
{final_query}

Return only the SQL query, do not include any explanation.
"""
        try:
            response = openai.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a SQL expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            sql_query = response.choices[0].message.content.strip()
            return jsonify({
                "final_query": final_query,
                "sql_query": sql_query
            }), 200

        except Exception as e:
            return jsonify({"error": f"SQL generation error: {e}"}), 500

    else:
        # User wants to modify query
        storage["user_query"] = final_query or storage.get("user_query")
        return jsonify({
            "message": "Query not confirmed. You can modify and resubmit."
        }), 200
