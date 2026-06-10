from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = "secret123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

    habits = db.relationship('Habit', backref='user', lazy=True)


class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.String(500)
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

## -------------------------Home-------------------------

@app.route("/")
def home():
    return render_template("home.html")

## -------------------------Register-------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # Check username
        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:

            flash(
                "Username already exists",
                "danger"
            )

            return render_template("register.html")

        # Check email
        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:

            flash(
                "Email already exists",
                "danger"
            )

            return render_template("register.html")

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "Account created successfully. Please login.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")


## -------------------------Login-------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            session["username"] = user.username

            return redirect(url_for("dashboard"))

        flash("Invalid email or password", "danger")

        return render_template("login.html")

    return render_template("login.html")

## -------------------------Logout-------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

## -------------------------Dashboard-------------------------
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    habits = Habit.query.filter_by(
        user_id=session["user_id"]
    ).all()

    total_habits = len(habits)

    completed_habits = len(
        [h for h in habits if h.completed]
    )

    if total_habits > 0:
        progress = int(
            (completed_habits / total_habits) * 100
        )
    else:
        progress = 0

    return render_template(
        "dashboard.html",
        habits=habits,
        username=session["username"],
        total_habits=total_habits,
        completed_habits=completed_habits,
        progress=progress
    )

## -------------------------Add habit-------------------------

@app.route("/add_habit", methods=["POST"])
def add_habit():

    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form["title"]
    description = request.form["description"]

    habit = Habit(
        title=title,
        description=description,
        user_id=session["user_id"]
    )

    db.session.add(habit)
    db.session.commit()

    return redirect(url_for("dashboard"))

## -------------------------Delete habit-------------------------

@app.route("/delete_habit/<int:id>")
def delete_habit(id):

    habit = Habit.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    db.session.delete(habit)
    db.session.commit()

    return redirect(url_for("dashboard"))

## -------------------------Update habit-------------------------

@app.route("/edit_habit/<int:id>", methods=["GET", "POST"])
def edit_habit(id):

    habit = Habit.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    if request.method == "POST":

        habit.title = request.form["title"]
        habit.description = request.form["description"]

        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template(
        "edit_habit.html",
        habit=habit
    )

@app.route("/toggle_habit/<int:id>")
def toggle_habit(id):

    habit = Habit.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    habit.completed = not habit.completed

    db.session.commit()

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)