import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    price = []
    shares = []
    table_row = []
    ident = session["user_id"]
    cash = db.execute("SELECT cash FROM users WHERE id = :username", username=ident)
    symbol = db.execute("SELECT symbol FROM stocks WHERE user_id = :username", username=ident)
    for i in range(len(symbol)):
        price.append(lookup(symbol[i].lower))
        shares.append(db.execute("SELECT shares FROM users WHERE symbol = :symbol", symbol=symbol[i]))
    price = usd(price)
    cash = cash[0]
    cash = cash['cash']
    for i in range(len(symbol)):
        tcash = {{price[i]}}
        tshare = {{shares[i]}}
        tsym = {{symbol[i]}}
        table_row.append(f"<tr> <td> {tsym} </td> <td> {tshare} </td> <td> {tcash} </td> </tr>")
    return render_template("index.html", table_row=table_row);
        





@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        sym = lookup(request.form.get("symbol"))
        sym["price"] = usd(sym["price"])
        return render_template("quoted.html", sym=sym);
    else:
        return render_template("quote.html");


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        pas = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users(username, hash) VALUES(:usern, :password)", usern=username, password=pas)
        return redirect("/")
    else:
        return render_template("register.html");
    
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        ident = session["user_id"]
        shares = request.form.get("shares")
        sym = lookup(request.form.get("symbol"))
        amount = db.execute("SELECT cash FROM users WHERE id = :username", username=ident)
        cost = sym["price"]
        amount =amount[0]
        amount = amount['cash']
        price = amount - cost
        db.execute("INSERT INTO stocks(symbol, shares, user_id) VALUES(:symbol, :shares, :username)", symbol=sym["symbol"], shares=int(shares), username=ident)
        db.execute("UPDATE users SET cash = :cash WHERE id = :username", cash = price, username = ident)
        return redirect("/")
    else:
        return render_template("buy.html");


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
