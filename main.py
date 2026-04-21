from flask import Flask, render_template

from config import SECRET_KEY
from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

db_session.global_init('db/data.db')


@app.route('/')
def m():
    return render_template('example4.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)