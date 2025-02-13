from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuration de la base de données SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///recettes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Définition du modèle de données pour les recettes
class Recette(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Recette {self.nom}>"

# Création de la base de données (à exécuter une seule fois)
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/recettes")
def afficher_recettes():
    recettes = Recette.query.all()
    return render_template("recettes.html", recettes=recettes)

@app.route("/recette/<int:id>")
def afficher_recette(id):
    recette = Recette.query.get_or_404(id)
    return render_template("recette.html", recette=recette)

@app.route("/ajouter", methods=["GET", "POST"])
def ajouter_recette():
    if request.method == "POST":
        nom = request.form["nom"]
        ingredients = request.form["ingredients"]
        instructions = request.form["instructions"]

        if nom and ingredients and instructions:
            nouvelle_recette = Recette(nom=nom, ingredients=ingredients, instructions=instructions)
            db.session.add(nouvelle_recette)
            db.session.commit()
            return redirect(url_for("afficher_recettes"))

    return render_template("ajouter_recette.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        nom = request.form["nom"]
        message = request.form["message"]
        return f"<h1>Merci {nom}!</h1><p>Votre message : {message}</p>"

    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)


@app.route("/modifier/<int:id>", methods=["GET", "POST"])
def modifier_recette(id):
    recette = Recette.query.get_or_404(id)

    if request.method == "POST":
        recette.nom = request.form["nom"]
        recette.ingredients = request.form["ingredients"]
        recette.instructions = request.form["instructions"]
        
        db.session.commit()
        return redirect(url_for("afficher_recettes"))

    return render_template("modifier_recette.html", recette=recette)



@app.route("/supprimer/<int:id>", methods=["POST"])
def supprimer_recette(id):
    recette = Recette.query.get_or_404(id)
    db.session.delete(recette)
    db.session.commit()
    return redirect(url_for("afficher_recettes"))
