from flask import Flask, render_template, redirect, session, flash

# SQL Alchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship)
from sqlalchemy import String, Integer, ForeignKey, select
from sqlalchemy.exc import NoResultFound

# Forms
from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, SubmitField, PasswordField,
                     BooleanField)
from wtforms.validators import DataRequired, Length, NumberRange

# Passwords
from flask_login import LoginManager, UserMixin, current_user, login_user
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

app = Flask(__name__)
app.config["SECRET_KEY"] = """
    e702bc4d1915c4735ca0c8cf8587674b92b9845d8e2705a931c741599b91b6a2
"""
login_manager = LoginManager()
hasher = PasswordHasher(time_cost=3, parallelism=4, memory_cost=65536)


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


class Login(Base):
    __tablename__ = "password_test_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(String)
    admin: Mapped[bool] = mapped_column(Integer)


db = SQLAlchemy(model_class=Base)


# Forms
class DataAdditionForm(FlaskForm):
    team_name = StringField("Team Name", validators=[
            Length(min=1, max=50), DataRequired()
        ]
    )
    year = IntegerField("Year", validators=[
            NumberRange(min=1945, max=2050), DataRequired()
        ]
    )
    placement = IntegerField("Championship Position", validators=[
            NumberRange(min=1, max=20), DataRequired()
        ]
    )
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[
            DataRequired(), Length(min=4, max=50)
        ]
    )
    password = PasswordField("Password", validators=[
            DataRequired(), Length(min=8, max=100)
        ]
    )
    remember = BooleanField("Remember Me?")
    sumbit = SubmitField("Submit")


# Flask-Login Architecture
class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    statement = select(Login).limit(1).where(Login.id == int(user_id))
    data = db.session.execute(statement)
    data = data.scalar()
    if data is None:
        return None
    return User(id=data.id)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///basic_db.db"
db.init_app(app)
login_manager.init_app(app)


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
        new_row = Teams(
            name=form.team_name.data,
            year=form.year.data,
            pos=form.placement.data
        )
        db.session.add(new_row)
        db.session.commit()
        redirect("/home")
    return render_template("data_addition.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    WRONG_PASSWORD_MESSAGE = "Incorrect Password"
    login_form = LoginForm()
    if login_form.validate_on_submit():
        form_username = login_form.username.data
        password = login_form.password.data
        sql_statment = select(Login).where(Login.username == form_username)
        try:
            hash_info = db.session.execute(sql_statment.limit(1)).one()
        except NoResultFound:
            return redirect("/signup")
        user_info: Login = hash_info[0]
        try:
            if hasher.verify(user_info.password, password):
                print(login_form.remember.data)
                login_user(User(str(user_info.id)), login_form.remember.data)
                return redirect("/")
        except VerifyMismatchError:
            flash(WRONG_PASSWORD_MESSAGE)
    return render_template("login.html", error=None, form=login_form)


if __name__ == "__main__":
    app.run(debug=True)
