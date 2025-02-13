function validerFormulaire() {
    let nom = document.getElementById("nom").value;
    let ingredients = document.getElementById("ingredients").value;
    let instructions = document.getElementById("instructions").value;

    if (!nom || !ingredients || !instructions) {
        alert("Veuillez remplir tous les champs !");
        return false;
    }
    return true;
}

function filtrerRecettes() {
    let recherche = document.getElementById("search").value.toLowerCase();
    let recettes = document.querySelectorAll("#recette-list li");

    recettes.forEach(function (recette) {
        let texte = recette.textContent.toLowerCase();
        recette.style.display = texte.includes(recherche) ? "block" : "none";
    });
}
