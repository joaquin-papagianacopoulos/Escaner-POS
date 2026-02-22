from flask import Flask, request, jsonify
from printer import print_ticket

app = Flask(__name__)

@app.route("/print", methods=["POST"])
def print_product():
    data = request.json
    print_ticket(data)
    return jsonify({"success": True})

app.run(port=9100)
