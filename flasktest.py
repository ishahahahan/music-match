from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Drink Water!!"

@app.route("/hello")
def hello():
    return "Hello World!"

app.run(host="0.0.0.0", port=80)