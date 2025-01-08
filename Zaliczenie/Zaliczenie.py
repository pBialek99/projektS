from flask import Flask, jsonify, request
import sqlite3
from werkzeug.exceptions import BadRequest
from collections import OrderedDict
import json

# BAZA DANYCH
DB_PATH = r"C:\Users\Krem\Tools\sqlite\zaliczenie.db"
TABLE_NAME = "Books"

def init_db():
  with sqlite3.connect(DB_PATH) as conn:
    cur = conn.cursor()
    cur.execute(f"DELETE FROM sqlite_sequence WHERE name='{TABLE_NAME}'")
    cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT NOT NULL,
        Author TEXT NOT NULL
    )
    """)

def get_books():
  with sqlite3.connect(DB_PATH) as conn:
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {TABLE_NAME}")
    return cur.fetchall()

def get_book(book_id):
  with sqlite3.connect(DB_PATH) as conn:
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {TABLE_NAME} WHERE Id = ?", (book_id,))
    return cur.fetchone()

def add_book(title, author):
  with sqlite3.connect(DB_PATH) as conn:
    cur = conn.cursor()
    cur.execute(f"INSERT INTO {TABLE_NAME} (Title, Author) VALUES (?, ?)", (title, author))
    conn.commit()
    return cur.lastrowid

def delete_book(book_id):
  with sqlite3.connect(DB_PATH) as conn:
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {TABLE_NAME} WHERE Id = ?", (book_id,))
    conn.commit()
    return cur.rowcount

def update_book(book_id, title, author):
  with sqlite3.connect(DB_PATH) as conn:
    cur = conn.cursor()
    cur.execute(f"UPDATE {TABLE_NAME} SET Title = ?, Author = ? WHERE Id = ?", (title, author, book_id))
    conn.commit()
    return cur.rowcount

# FLASK
app = Flask(__name__)

@app.route("/books", methods=["GET"])
def fetch_books():
  books = get_books()
  return jsonify({"data": books}), 200

@app.route("/books/<int:book_id>", methods=["GET"])
def fetch_book(book_id):
  if book_id <= 0:
    return jsonify({"error": "Invalid book ID"}), 404

  book = get_book(book_id)
  if book:
    return jsonify({"data": book}), 200
  else:
    return jsonify({"error": "Book not found"}), 404

@app.route("/books", methods=["POST"])
def create_book():
  try:
    data = request.json
  except BadRequest:
    return jsonify({"error": "Invalid JSON format"}), 400

  if not data or "title" not in data or "author" not in data:
    return jsonify({"error": "Invalid data. 'title' and 'author' are required"}), 400

  if not isinstance(data["title"], str) or not isinstance(data["author"], str):
    return jsonify({"error": "'title' and 'author' must be strings"}), 400

  if not data["title"].strip() or not data["author"].strip():
    return jsonify({"error": "'title' and 'author' cannot be empty"}), 400

  if len(data["title"]) > 50 or len(data["author"]) > 50:
    return jsonify({"error": "'title' and 'author' must be at most 50 characters"}), 400

  book_id = add_book(data["title"], data["author"])
  response = OrderedDict([
    ("id", book_id),
    ("title", data["title"]),
    ("author", data["author"])
  ])
  response = json.dumps(response, ensure_ascii=False, sort_keys=False)
  return response, 201, {'Content-Type': 'application/json'}

@app.route("/books/<int:book_id>", methods=["DELETE"])
def remove_book(book_id):
  deleted_count = delete_book(book_id)
  if deleted_count:
    return '', 204
  else:
    return jsonify({"error": "Book not found"}), 404

@app.route("/books/<int:book_id>", methods=["PUT"])
def alter_book(book_id):
  if book_id <= 0:
    return jsonify({"error": "Invalid book ID"}), 400

  data = request.json
  if not data or "title" not in data or "author" not in data:
    return jsonify({"error": "Invalid data. 'title' and 'author' are required"}), 400

  if not isinstance(data["title"], str) or not isinstance(data["author"], str):
    return jsonify({"error": "'title' and 'author' must be strings"}), 400

  if not data["title"].strip() or not data["author"].strip():
    return jsonify({"error": "'title' and 'author' cannot be empty"}), 400

  if len(data["title"]) > 50 or len(data["author"]) > 50:
    return jsonify({"error": "'title' and 'author' must be at most 50 characters"}), 400

  book = get_book(book_id)
  if not book:
    return jsonify({"error": "Book not found"}), 404

  row_count = update_book(book_id, data["title"], data["author"])
  if row_count:
    response = OrderedDict([
      ("id", book_id),
      ("title", data["title"]),
      ("author", data["author"])
    ])
    response = json.dumps(response, ensure_ascii=False, sort_keys=False)
    return response, 200, {'Content-Type': 'application/json'}
  else:
    return jsonify({"error": "Failed to update book"}), 500

# DOKUMENTACJA API
@app.route("/docs", methods=["GET"])
def docs():
  documentation = {
    "/books": {
      # fetch_books()
      "GET": {
        "description": "Returns a list of all books in a table",
        "parameters": "None",
        "response": {
          "200": "Returns a list of all books",
          "500": "Server error"
        }
      },
      # create_book()
      "POST": {
        "description": "Creates a new book record in a table",
        "parameters": {
          "title": "String (Required, max length 50)",
          "author": "String (Required, max length 50)"
        },
        "response": {
          "201": "Return details about created book",
          "400": [
            "error: Invalid data. 'title' and 'author' are required",
            "error: 'title' and 'author' must be strings",
            "error: 'title' and 'author' cannot be empty",
            "error: 'title' and 'author' must be at most 50 characters"
          ],
          "500": "Server error"
        }
      }
    },
    "/books/<int:book_id>": {
      # fetch_book()
      "GET": {
        "description": "Displays details about book with specified ID",
        "parameters": {
          "book_id": "Integer (Required)"
        },
        "response": {
          "200": "Displays details about book with specified ID",
          "404": "error: Book not found",
          "500": "Server error"
        }
      },
      # alter_book()
      "PUT": {
        "description": "Alters data of a book with specified ID",
        "parameters": {
          "book_id": "Integer (Required)",
          "title": "String (Required, max length 50)",
          "author": "String (Required, max length 50)"
        },
        "response": {
          "200": "Returns details about updated book",
          "400": [
            "error: Invalid data. 'title' and 'author' are required",
            "error: 'title' and 'author' must be strings",
            "error: 'title' and 'author' cannot be empty",
            "error: 'title' and 'author' must be at most 50 characters"
          ],
          "404": "error: Book not found",
          "500": "Server error"
        }
      },
      # remove_book()
      "DELETE": {
        "description": "Deletes abook with specified ID",
        "parameters": {
          "book_id": "Integer (Required)"
        },
        "response": {
          "204": "",
          "404": "Book not found",
          "500": "Server error"
        }
      }
    }
  }
  return jsonify(documentation), 200

init_db()
app.run(host='localhost', port=8080)
