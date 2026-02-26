from flask import Flask, render_template, redirect

# DB
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship)
from sqlalchemy import String, Integer, ForeignKey, select

# Forms
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length

app = Flask(__name__)
app.config["SECRET_KEY"] = "a-very-secret-secret-key"


# Tables
class Base(DeclarativeBase):
    pass


class Engines(Base):
    __tablename__ = "engine_maker"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    team_years: Mapped[list["Teams"]] = relationship(back_populates="engine")


class Teams(Base):
    __tablename__ = "team_performance"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    engine_id: Mapped[int] = mapped_column(ForeignKey("engine_maker.id"))
    engine: Mapped[Engines] = relationship(back_populates="team_years")
    year: Mapped[int] = mapped_column(Integer)
    pos: Mapped[int] = mapped_column(Integer)
    era: Mapped[str] = mapped_column(String)


# Forms
class DataAdditionForm(FlaskForm):
    team_name = StringField("Team Name", validators=[Length(min=1, max=50)])
    year = IntegerField("Year", validators=[Length(min=4, max=4)]) # BROKEN
    placement = IntegerField("Championship Position", validators=[Length(min=1, max=2)]) # BROKEN
    submit = SubmitField("Submit")


db = SQLAlchemy(model_class=Base)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///basic_db.db"
db.init_app(app)


@app.route("/")
def home():
    results = db.session.execute(select(Teams)).scalars()
    return render_template("home.html", data=results)


@app.route("/years/<int:year_results>")
def years(year_results):
    statement = select(Teams).where(Teams.year == year_results)
    statement = statement.order_by(Teams.pos)
    results = db.session.execute(statement).scalars()
    return render_template("year.html", data=results)


@app.route("/data-add", methods=["GET", "POST"])
def data_addition():
    form = DataAdditionForm()
    if form.validate_on_submit():
        return redirect("/home")
    return render_template("data_addition.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)
