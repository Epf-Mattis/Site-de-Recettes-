import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from PIL import Image
from flask_migrate import Migrate

app = Flask(__name__)

# Configuration de Flask et base de données
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///recettes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Création du dossier d'upload s'il n'existe pas
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

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
    image = db.Column(db.String(100), nullable=True)
    publique = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Modèle Notation
class Notation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.Integer, nullable=False)  # Note entre 1 et 5
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recette_id = db.Column(db.Integer, db.ForeignKey('recette.id'), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recette_id = db.Column(db.Integer, db.ForeignKey('recette.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('messages', lazy=True))
    recette = db.relationship('Recette', backref=db.backref('messages', lazy=True))


# Calcul de la note moyenne d'une recette
def get_average_rating(recette_id):
    notes = Notation.query.filter_by(recette_id=recette_id).all()
    if notes:
        return sum(note.note for note in notes) / len(notes)
    return 0  # Pas encore de note

# Formulaire d'inscription
class RegisterForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirmer mot de passe", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("S'inscrire")

# Formulaire de connexion
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    submit = SubmitField("Se connecter")

# Formulaire de recette avec upload d’image
class RecetteForm(FlaskForm):
    nom = StringField("Nom de la recette", validators=[DataRequired()])
    ingredients = TextAreaField("Ingrédients", validators=[DataRequired()])
    instructions = TextAreaField("Instructions", validators=[DataRequired()])
    image = FileField("Image de la recette", validators=[FileAllowed(['jpg', 'png', 'jpeg'], "Images uniquement!")])
    submit = SubmitField("Ajouter la recette")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    recettes_publiques = Recette.query.filter_by(publique=True).all()
    return render_template("index.html", recettes=recettes_publiques)

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
    form = RecetteForm()
    if form.validate_on_submit():
        image_file = form.image.data
        filename = None

        if image_file:
            ext = image_file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(filepath)

            img = Image.open(filepath)
            img.thumbnail((500, 500))
            img.save(filepath)

        nouvelle_recette = Recette(
            nom=form.nom.data,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            image=filename,
            user_id=current_user.id
        )
        db.session.add(nouvelle_recette)
        db.session.commit()
        return redirect(url_for("afficher_recettes"))

    return render_template("ajouter_recette.html", form=form)

@app.route("/recettes")
@login_required
def afficher_recettes():
    recettes = Recette.query.filter_by(user_id=current_user.id).all()
    return render_template("recettes.html", recettes=recettes)


@app.route("/recette/<int:id>")
@login_required
def afficher_recette(id):
    recette = Recette.query.get_or_404(id)
    moyenne_notes = get_average_rating(id)
    return render_template("recette.html", recette=recette, moyenne_notes=moyenne_notes)

@app.route("/recette/<int:id>/message", methods=["POST"])
@login_required
def ajouter_message(id):
    recette = Recette.query.get_or_404(id)
    content = request.form["content"]

    if content:
        message = Message(content=content, user_id=current_user.id, recette_id=id)
        db.session.add(message)
        db.session.commit()
        flash("Message ajouté !", "success")

    return redirect(url_for("afficher_recette", id=id))


@app.route("/publier/<int:id>", methods=["POST"])
@login_required
def publier_recette(id):
    recette = Recette.query.get_or_404(id)
    if recette.user_id != current_user.id:
        flash("Vous ne pouvez publier que vos propres recettes.", "danger")
        return redirect(url_for("home"))

    recette.publique = True
    db.session.commit()
    flash("Recette publiée avec succès !", "success")
    return redirect(url_for("afficher_recette", id=id))

@app.route("/modifier/<int:id>", methods=["GET", "POST"])
@login_required
def modifier_recette(id):
    recette = Recette.query.get_or_404(id)
    if recette.user_id != current_user.id:
        flash("Vous ne pouvez modifier que vos propres recettes.", "danger")
        return redirect(url_for("afficher_recettes"))

    if request.method == "POST":
        recette.nom = request.form["nom"]
        recette.ingredients = request.form["ingredients"]
        recette.instructions = request.form["instructions"]
        db.session.commit()
        flash("Recette mise à jour avec succès !", "success")
        return redirect(url_for("afficher_recettes"))

    return render_template("modifier_recette.html", recette=recette)


@app.route("/supprimer/<int:id>", methods=["POST"])
@login_required
def supprimer_recette(id):
    recette = Recette.query.get_or_404(id)

    # Vérifier si l'utilisateur est bien le propriétaire de la recette
    if recette.user_id != current_user.id:
        flash("Vous ne pouvez supprimer que vos propres recettes.", "danger")
        return redirect(url_for("afficher_recettes"))

    # Supprimer l'image si elle existe
    if recette.image:
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], recette.image)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(recette)
    db.session.commit()
    flash("Recette supprimée avec succès.", "success")
    return redirect(url_for("afficher_recettes"))


@app.route("/recette/<int:id>/noter", methods=["POST"])
@login_required
def noter_recette(id):
    recette = Recette.query.get_or_404(id)
    note = int(request.form["note"])
    if 1 <= note <= 5:
        nouvelle_note = Notation(note=note, user_id=current_user.id, recette_id=id)
        db.session.add(nouvelle_note)
        db.session.commit()
        flash("Votre note a été enregistrée !", "success")
    else:
        flash("Note invalide. Veuillez entrer une note entre 1 et 5.", "danger")

    return redirect(url_for("afficher_recette", id=id))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
