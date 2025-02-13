from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///recettes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Configuration de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Modèle Utilisateur
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

# Modèle Recette
class Recette(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Formulaires d'inscription et connexion
class RegisterForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirmer mot de passe", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("S'inscrire")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    submit = SubmitField("Se connecter")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 🚀 Correction de la route Home
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Inscription réussie ! Connectez-vous.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Connexion réussie !", "success")
            return redirect(url_for("home"))
        else:
            flash("Identifiants incorrects", "danger")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Déconnexion réussie.", "info")
    return redirect(url_for("login"))

@app.route("/ajouter", methods=["GET", "POST"])
@login_required
def ajouter_recette():
    if request.method == "POST":
        nom = request.form["nom"]
        ingredients = request.form["ingredients"]
        instructions = request.form["instructions"]
        if nom and ingredients and instructions:
            nouvelle_recette = Recette(nom=nom, ingredients=ingredients, instructions=instructions, user_id=current_user.id)
            db.session.add(nouvelle_recette)
            db.session.commit()
            return redirect(url_for("afficher_recettes"))
    return render_template("ajouter_recette.html")

@app.route("/recettes")
@login_required  # ✅ Uniquement pour les utilisateurs connectés
def afficher_recettes():
    recettes = Recette.query.filter_by(user_id=current_user.id).all()  # ✅ Filtrer par user_id
    return render_template("recettes.html", recettes=recettes)


@app.route("/recette/<int:id>")
def afficher_recette(id):
    recette = Recette.query.get_or_404(id)
    return render_template("recette.html", recette=recette)

@app.route("/modifier/<int:id>", methods=["GET", "POST"])
@login_required
def modifier_recette(id):
    recette = Recette.query.get_or_404(id)

    if recette.user_id != current_user.id:  # ✅ Vérification du propriétaire
        flash("Vous ne pouvez modifier que vos propres recettes.", "danger")
        return redirect(url_for("afficher_recettes"))

    if request.method == "POST":
        recette.nom = request.form["nom"]
        recette.ingredients = request.form["ingredients"]
        recette.instructions = request.form["instructions"]
        db.session.commit()
        return redirect(url_for("afficher_recettes"))

    return render_template("modifier_recette.html", recette=recette)


@app.route("/supprimer/<int:id>", methods=["POST"])
@login_required
def supprimer_recette(id):
    recette = Recette.query.get_or_404(id)

    if recette.user_id != current_user.id:  # ✅ Vérification du propriétaire
        flash("Vous ne pouvez supprimer que vos propres recettes.", "danger")
        return redirect(url_for("afficher_recettes"))

    db.session.delete(recette)
    db.session.commit()
    return redirect(url_for("afficher_recettes"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
