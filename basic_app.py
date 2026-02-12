import sqlite3

from flask import Flask, request, render_template, g

app = Flask(__name__)
DATABASE = "basic_db.db"


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route("/")
def home():
    sql = """
            SELECT Team_Performance.name, Engine_Maker.name, year, pos, era
            FROM Team_Performance
            JOIN Engine_Maker on Team_Performance.engine = Engine_Maker.id
        """
    results = query_db(sql)
    return render_template("home.html", data=results)


@app.route("/year/<int:year>")
def year(year):
    sql = f"""
            SELECT Team_Performance.name, Engine_Maker.name, year, pos, era
            FROM Team_Performance
            JOIN Engine_Maker on Team_Performance.engine = Engine_Maker.id
            WHERE year = {year}
        """
    results = query_db(sql)
    return render_template("year.html", data=results)


if __name__ == "__main__":
    app.run(debug=True)
