from authlib.integrations.flask_client import OAuth
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = "supersecretkey"

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id='606472210191-n9vqana4v7isnm6dr2scaq9b6rvv4jv9.apps.googleusercontent.com',
    client_secret='hidden',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

login_manager = LoginManager(app)
login_manager.login_view = "login"

USERS = {}
todos = {}
next_id = [1]

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id in USERS else None

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("All fields are required.")
            return redirect(url_for("register"))

        if username in USERS:
            flash("Username already exists.")
            return redirect(url_for("register"))

        USERS[username] = password

        flash("Registration successful.")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route('/google-login')
def google_login():
    return google.authorize_redirect(url_for('callback', _external=True))

@app.route('/callback')
def callback():

    token = google.authorize_access_token()

    user_info = token.get('userinfo')

    username = user_info['email']

    if username not in USERS:
        USERS[username] = 'google_account'

    login_user(User(username))

    return redirect(url_for('index'))

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username in USERS and USERS[username] == password:

            login_user(User(username))
            return redirect(url_for("index"))

        flash("Invalid username or password.")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():

    user_todos = {
        k: v for k, v in todos.items()
        if v["owner"] == current_user.id
    }

    return render_template(
        "index.html",
        todos=user_todos,
        user=current_user.id
    )

@app.route("/add", methods=["POST"])
@login_required
def add():

    text = request.form.get("text", "").strip()

    if not text:
        flash("Todo cannot be empty.")

    else:
        todos[next_id[0]] = {
            "text": text,
            "done": False,
            "owner": current_user.id
        }

        next_id[0] += 1

    return redirect(url_for("index"))

@app.route("/toggle/<int:tid>")
@login_required
def toggle(tid):

    if tid in todos and todos[tid]["owner"] == current_user.id:
        todos[tid]["done"] = not todos[tid]["done"]

    return redirect(url_for("index"))

@app.route("/delete/<int:tid>")
@login_required
def delete(tid):

    if tid in todos and todos[tid]["owner"] == current_user.id:
        del todos[tid]

    return redirect(url_for("index"))

@app.route("/edit/<int:tid>", methods=["POST"])
@login_required
def edit(tid):

    text = request.form.get("text", "").strip()

    if tid in todos and todos[tid]["owner"] == current_user.id:

        if not text:
            flash("Todo cannot be empty.")

        else:
            todos[tid]["text"] = text

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)