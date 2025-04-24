from flask import Flask, render_template, request, send_file
from crawler import get_companies_in_industry, save_to_excel
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    file_path = None
    if request.method == "POST":
        url = request.form.get("url")
        industry_name = request.form.get("name") or "Ngành chưa đặt tên"
        if url:
            companies = get_companies_in_industry(industry_name, url)
            file_path = f"downloads/{industry_name.replace(' ', '_')}.xlsx"
            os.makedirs("downloads", exist_ok=True)
            save_to_excel(companies, filename=file_path)
    return render_template("index.html", file_path=file_path)

@app.route("/download")
def download():
    path = request.args.get("file")
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
