from flask import Flask, render_template
from app import app  # Импортируем приложение из __init__.py

@app.route("/")
def index():
    return render_template("base.html")

if __name__ == "__main__":
    app.run(debug=True)
