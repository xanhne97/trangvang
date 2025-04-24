from flask import Flask, render_template, request, send_file
from crawler import get_companies_in_industry, save_to_excel
import os
import uuid

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    file_url = None
    if request.method == "POST":
        url = request.form.get("url")
        industry = request.form.get("industry") or "Ngành chưa đặt tên"
        filename = f"{uuid.uuid4()}.xlsx"
        results = get_companies_in_industry(industry, url)
        save_to_excel(results, filename=filename)
        file_url = f"/download/{filename}" if results else None
    return render_template("index.html", file_url=file_url)

@app.route("/download/<filename>")
def download(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
