from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Stockage temporaire des recettes
recettes = [
    {"id": 1, "nom": "Spaghetti Bolognese", "ingredients": "Pâtes, viande hachée, sauce tomate", "instructions": "Faire cuire les pâtes..."},
    {"id": 2, "nom": "Omelette", "ingredients": "Œufs, sel, poivre", "instructions": "Battre les œufs et cuire à la poêle..."}
]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/recettes")
def afficher_recettes():
    return render_template("recettes.html", recettes=recettes)

@app.route("/recette/<int:id>")
def afficher_recette(id):
    recette = next((r for r in recettes if r["id"] == id), None)
    return render_template("recette.html", recette=recette)

@app.route("/ajouter", methods=["GET", "POST"])
def ajouter_recette():
    if request.method == "POST":
        nom = request.form["nom"]
        ingredients = request.form["ingredients"]
        instructions = request.form["instructions"]

        if nom and ingredients and instructions:
            nouvelle_recette = {
                "id": len(recettes) + 1,
                "nom": nom,
                "ingredients": ingredients,
                "instructions": instructions
            }
            recettes.append(nouvelle_recette)
            return redirect(url_for("afficher_recettes"))

    return render_template("ajouter_recette.html")

if __name__ == "__main__":
    app.run(debug=True)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        nom = request.form['nom']
        message = request.form['message']
        return f"<h1>Merci {nom}!</h1><p>Votre message : {message}</p>"

    return render_template('contact.html')  # Afficher le formulaire si on est en GET

if __name__ == '__main__':
    app.run(debug=True)