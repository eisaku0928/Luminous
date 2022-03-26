from flask import Flask, redirect, render_template, request, session, flash
from flask_session import Session
# from flask.ext.session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import datetime
import matplotlib.pyplot as plt

import sqlite3

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False

# configure filesystem
app.config["SESSION_TYPE"] = "filesystem"

# Enable sessions for this app
Session(app)

# Specify sql database
# db = SQL("sqlite:///users.db")
db = sqlite3.connect("users.db")

# login required decoration from PSET9 Finance
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Show welcome page
@app.route("/")
def index():
    """Show welcome page if not logged in. If logged in, show homepage"""
    if "user_id" in session:
        return redirect("/homepage")
    else:
        return render_template("welcome.html")

@app.route("/homepage")
@login_required
def homepage():
    """Shows homepage for user with options and todolist"""
    name = session["name"]
    id = session["user_id"]

    # Query database for todolist
    incomplete_todos = db.execute("SELECT * FROM todos WHERE id = :id AND complete = :complete", id=id, complete='n')
    complete_todos = db.execute("SELECT * FROM todos WHERE id = :id AND complete = :complete", id=id, complete='y')
    return render_template("user.html", name=name, incomplete_todos=incomplete_todos, complete_todos=complete_todos)


@app.route("/add", methods=["POST"])
@login_required
def add():
    """Adds tasks to todo list"""
    todo = request.form.get("todoitem")
    db.execute("INSERT INTO todos (id, todo) VALUES (:id, :todo)", id=session["user_id"], todo=todo)
    return redirect("/homepage")

@app.route("/delete/<int:todoid>")
@login_required
def delete(todoid):
    """Deletes tasks from todo list"""
    db.execute("DELETE FROM todos WHERE id = :id AND todoid = :todoid", id=session["user_id"], todoid=todoid)
    return redirect("/homepage")

@app.route("/complete/<int:todoid>")
@login_required
def complete(todoid):
    """Updates database when checkbox is clicked in todolist"""

    # Get the specific todo from todos and store the complete_value in variable
    task = db.execute("SELECT complete FROM todos WHERE id = :id AND todoid = :todoid", id=session["user_id"], todoid=todoid)
    complete_value = task[0]["complete"]

    # Update database with opposite value
    if complete_value == 'n':
        complete = 'y'
    else:
        complete = 'n'
    db.execute("UPDATE todos SET complete = :complete WHERE id = :id AND todoid = :todoid", complete=complete, id=session["user_id"], todoid=todoid)
    return redirect("/homepage")

@app.route("/journal")
@login_required
def journal():
    """Shows journal page"""
    # Retrieve all journal entries of the current user and render journal.html
    # Render with entries stacked
    entries = db.execute("SELECT * FROM journal WHERE user_id = :user_id ORDER BY created_at DESC", user_id=session["user_id"])
    return render_template("journal.html", name=session["name"], entries=entries)

@app.route("/new_entry")
@login_required
def new_entry():
    """Shows journal page"""
    # render new journal entry template
    return render_template("new_entry.html", name=session["name"])

@app.route("/open_entry/<int:entry_id>")
@login_required
def open_entry(entry_id):
    """Opens a Journal entry"""

    # Find specific entry information from database
    entry = db.execute("SELECT * FROM journal WHERE user_id = :user_id AND entry_id = :entry_id", user_id=session["user_id"], entry_id=entry_id)

    # pass in mood_emoji as mood_value for html page
    entry_mood_emoji = entry[0]["mood"]
    # mood_emoji associated with mood_value in dictionary
    mood_dict = {20:'😩', 40:'😞', 60:'🙂', 80:'😄', 100:'😆', 120:'😊'}

    # compare mood_emoji of opened entry to each mood_emoji and find value
    for value, mood_emoji in mood_dict.items():
        if entry_mood_emoji == mood_emoji:

            # Pass in mood_value in entry as well for slider
            entry[0]["mood_value"] = value

            # break out when the right mood emoji is found
            break

    return render_template("open_entry.html", name=session["name"], entry=entry[0])

@app.route("/insert_new_entry", methods=["POST"])
@login_required
def insert_new_entry():
    """Inserts new journal entry"""

    # If there has been a new journal entry added, insert that into database
    title = request.form.get("title")
    if not title:
        title = "No Title"
    mood_value = int(request.form.get("mood_slider"))
    text = request.form.get("text")
    if not text:
        text = "No Text"

    # mood_emoji associated with mood_value in dictionary
    mood_dict = {20:'😩', 40:'😞', 60:'🙂', 80:'😄', 100:'😆', 120:'😊'}

    # compare mood_value to each mood_emoji
    for value, mood_emoji in mood_dict.items():
        if mood_value <= value:
            mood = mood_emoji

            # break out when the right mood emoji is found
            break
    # insert journal entry into database
    db.execute("INSERT INTO journal (user_id, mood, title, text, mood_value) VALUES (:user_id, :mood, :title, :text, :mood_value)", user_id=session["user_id"], mood=mood, title=title, text=text, mood_value=mood_value)

    return redirect("/journal")

@app.route("/update_entry", methods=["POST"])
@login_required
def update_entry():
    """Updates an existing journal entry"""

    # Store updated entry information in variables
    title = request.form.get("title")
    if not title:
        title = "No Title"
    mood_value = int(request.form.get("mood_slider"))
    text = request.form.get("text")
    if not text:
        text = "No Text"

    entry_id = request.form.get("entry_id")


    # mood_emoji associated with mood_value in dictionary
    mood_dict = {20:'😩', 40:'😞', 60:'🙂', 80:'😄', 100:'😆', 120:'😊'}

    # compare mood_value to each mood_emoji
    for value, mood_emoji in mood_dict.items():
        if mood_value <= value:
            mood = mood_emoji

            # break out when the right mood emoji is found
            break

    # insert journal entry into database
    db.execute("UPDATE journal SET title = :title, mood = :mood, text = :text, mood_value = :mood_value WHERE user_id = :user_id AND entry_id = :entry_id", title=title, mood=mood, text=text, mood_value=mood_value, user_id=session["user_id"], entry_id=entry_id)

    return redirect("/journal")

@app.route("/delete_entry/<int:entry_id>")
@login_required
def delete_entry(entry_id):
    """Deletes journal entry from journal"""
    db.execute("DELETE FROM journal WHERE user_id = :user_id AND entry_id = :entry_id", user_id=session["user_id"], entry_id=entry_id)
    return redirect("/journal")



# import necessary modules for mood tracker
import matplotlib
matplotlib.use("Agg")
from pylab import *

@app.route("/mood_tracker")
@login_required
def mood_tracker():
    """Shows mood_tracker page with updated mood tracking. Calculates and shows the
    average mood value and emoji of each day using matplotlib"""
    rows = db.execute("SELECT AVG(mood_value), created_date FROM JOURNAL WHERE user_id = 7 GROUP BY created_date ORDER BY created_date DESC LIMIT 5;")

    mood_avg_value = []
    dates = []
    for row in rows:
        mood_avg_value.append(row["AVG(mood_value)"])
        dates.append(row["created_date"])
    # reverse dates to make most recent 5 ascending
    dates.reverse()
    # mood_emoji associated with mood_value in dictionary
    mood_dict = {20:'😩', 40:'😞', 60:'🙂', 80:'😄', 100:'😆', 120:'😊'}

    # compare mood_value to each mood_value on each date and store in new list
    mood_avg_emoji = []
    for val in mood_avg_value:
        for value, mood_emoji in mood_dict.items():
            if val <= value:
                mood_avg_emoji.append(mood_emoji)
                # break out when the right mood emoji is found
                break

    # label graph
    ax = plt.axes()
    x_pos = [i for i in range(len(rows))]
    graph = plt.bar(x_pos, mood_avg_value, 0.5, color="#e74c3c")
    ax.set_ylabel("Average Mood Values Out of 120 of Each Day")
    ax.set_xlabel("Date")
    plt.title("Average Mood Values for Each Day")
    plt.xticks(x_pos, dates)

    # tips on labelling from https://towardsdatascience.com/how-i-got-matplotlib-to-plot-apple-color-emojis-c983767b39e0
    plt.ylim(0, plt.ylim()[1]+30)
    # Label bars with Emojis
    for bar, label in zip(graph, mood_avg_emoji):
        bar_height = bar.get_height()
        plt.annotate(
            label,
            (bar.get_x() + bar.get_width()/2, bar_height+5),
            ha="center",
            va="bottom",
            fontsize=15,
            )

    savefig("static/test.png")

    return render_template("mood_tracker.html", name=session["name"])



@app.route("/register", methods=["GET", "POST"])
def register():
    """Registers new users"""
    if request.method == "GET":
        return render_template("register.html")

    # When form is submitted via POST, insert the new user into users table
    else:
        # store user's name
        name = request.form.get("name")
        if not name:
            flash("Please provide your name.")
            return render_template("register.html")

        # get username, check if provided
        username = request.form.get("username")
        if not username:
            flash("Please provide a username.")
            return render_template("register.html")
        # Query database for username to ensure username is not used
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                        username)
        if len(rows) != 0:
            flash("Username already used. Please provide another username.")
            return render_template("register.html")

        # get password, check validity
        password = request.form.get("password")
        if not password:
            flash("Please provide a password")
            return render_template("register.html")
        elif password != request.form.get("confirmation"):
            flash("Password and confirmation do not match.")
            return render_template("register.html")

        # Hash the user's password and insert into users
        hash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (name, username, hash) VALUES (:name, :username, :hash)", name=name, username=username, hash=hash)

        # Remember which user has logged in
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)
        session["user_id"] = rows[0]["id"]
        session["name"] = rows[0]["name"]

        # Redirect user to home page
        return redirect("/homepage")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Please provide a username")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Please provide a password")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["name"] = rows[0]["name"]

        # Redirect user to home page
        return redirect("/homepage")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to welcome page
    return redirect("/")
