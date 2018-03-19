from flask import Flask, render_template, request, jsonify
application = Flask(__name__)


@application.route("/")
def index():
    return "index"

@application.route("/adduser", methods=['POST'])
def adduser():
    return jsonify({'status': 'OK'})

@application.route("/login", methods=['POST'])
def login():
    return jsonify({'status': 'OK'})

@application.route("/logout", methods=['POST'])
def logout():
    return jsonify({'status': 'OK'})

@application.route("/verify", methods=['POST'])
def verify():
    return jsonify({'status': 'OK'})

@application.route("/additem", methods=['POST'])
def additem():
	return jsonify({'status': 'OK'})

@application.route("/item", methods=['GET', 'POST'])
def item():
	return jsonify({'status': 'OK'})


if __name__ == "__main__":
    application.run(host='0.0.0.0', port = 80)
