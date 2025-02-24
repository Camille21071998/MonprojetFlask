from flask import Flask, render_template, request 

app = Flask(__name__)

# Tous les frais sont en TTC
TVA = 1.2  # Multiplicateur pour obtenir les valeurs TTC
FRAIS_BENEFICIAIRES_EFFECTIFS_TTC = round(29.65 * TVA, 2)  # 35.58€

# Frais INPI en TTC
FRAIS_INPI = {
    "Dépot des comptes": 5.90,
    "Radiation un établissement": 5.90,
    "Mise en activité": 5.90,
    "Immatriculation avec activité": 0.00,
    "Immatriculation sans activité": 0.00,
}

def calculer_frais(operation, forme_juridique, associe_unique=False, modifie_beneficiaires=False):
    frais = {
        "Immatriculation avec activité": {
            "SA": (round(46.61 * TVA, 2), round(395 * TVA, 2)),  
            "SAS": (round(46.61 * TVA, 2), round(197 * TVA, 2)),
            "SASU": (round(46.61 * TVA, 2), round(141 * TVA, 2)),
            "SARL": (round(46.61 * TVA, 2), round(147 * TVA, 2)),
            "EURL": (round(46.61 * TVA, 2), round(123 * TVA, 2)),
            "SNC": (round(46.61 * TVA, 2), round(218 * TVA, 2)),
            "SCI": (round(69.90 * TVA, 2), round(189 * TVA, 2)),
        },
        "Immatriculation sans activité": {
            "SA": (round(69.90 * TVA, 2), round(395 * TVA, 2)),
            "SAS": (round(69.90 * TVA, 2), round(197 * TVA, 2)),
            "SASU": (round(69.90 * TVA, 2), round(141 * TVA, 2)),
            "SARL": (round(69.90 * TVA, 2), round(147 * TVA, 2)),
            "EURL": (round(69.90 * TVA, 2), round(123 * TVA, 2)),
            "SNC": (round(69.90 * TVA, 2), round(218 * TVA, 2)),
            "SCI": (round(69.90 * TVA, 2), round(189 * TVA, 2)),
        },
        "Transfert de siège (même département)": (round(147.51 * TVA, 2), round(108 * TVA, 2)),
        "Transfert de siège (hors département)": (round(183.11 * TVA, 2), round(216 * TVA, 2)),
        "Changement de dirigeant": (round(147.51 * TVA, 2), round(108 * TVA, 2)),
        "Modification du capital social": (round(147.51 * TVA, 2), round(135 * TVA, 2)),
        "Modification de l’objet social": (round(147.51 * TVA, 2), round(135 * TVA, 2)),
        "Changement de dénomination": (round(147.51 * TVA, 2), round(197 * TVA, 2)),
        "Mise en activité": (round(44.48 * TVA, 2), 0),
        "Transformation": (round(163.40 * TVA, 2), round(197 * TVA, 2)),
        "Dissolution": (round(147.51 * TVA, 2), round(152 * TVA, 2)),
        "Radiation un établissement": (round(11.275 * TVA, 2), round(110 * TVA, 2)),
        "Dépot des comptes": (round(32.54 * TVA,2), 0),
        "Modifications multiples": (round(147.51 * TVA,2), "0,187 € HT par caractère dans l'annonce légale"),
    }

    # Ajouter les frais INPI pour toutes les modifications non listées avec 11,80 €
    frais_inpi = FRAIS_INPI.get(operation, 11.80)

    # Vérification de l'opération
    if operation.startswith("Immatriculation"):
        result = frais[operation].get(forme_juridique, "Forme juridique non reconnue")
    else:
        result = frais.get(operation, "Opération non reconnue")

    if isinstance(result, tuple):
        greffe_ttc, annonce_ttc = result

        # Ajouter les frais des bénéficiaires effectifs si nécessaire
        if modifie_beneficiaires and operation not in ["Immatriculation avec activité", "Immatriculation sans activité", "Dépot des comptes","Radiation un établissement","Mise en activité"]:
            greffe_ttc += FRAIS_BENEFICIAIRES_EFFECTIFS_TTC

        # Appliquer la réduction BODACC pour associé unique
        if associe_unique and operation not in ["Immatriculation avec activité", "Immatriculation sans activité", "Dépot des comptes", "Radiation un établissement", "Mise en activité"]:
            if operation == "Transfert de siège (hors département)":
                greffe_ttc -= 146  # Réduction en TTC
            else:
                greffe_ttc -= 116  # Réduction en TTC

        # Sécuriser pour éviter des frais négatifs
        greffe_ttc = max(0, greffe_ttc)

        # Calcul du total
        if isinstance(annonce_ttc, (int, float)):
            total_ttc = greffe_ttc + annonce_ttc + frais_inpi
            annonce_ttc = round(annonce_ttc, 2)
        else:
            total_ttc = greffe_ttc + frais_inpi  # On ignore annonce_ttc si c'est une chaîne


        # Ajout de "+ annonce légale" pour les modifications multiples
        total_general = f"{round(total_ttc, 2)} €"
        if operation == "Modifications multiples":
            total_general += " + annonce légale"

        return {
            "greffe_ttc": round(greffe_ttc, 2),
            "frais_inpi_ttc": round(frais_inpi, 2),
            "total_frais": round(greffe_ttc + frais_inpi, 2),
            "annonce_ttc": annonce_ttc,
            "total_general": total_general,
        }

    else:
        return {"message": result}

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    operation = ""
    forme_juridique = ""
    associe_unique = False
    modifie_beneficiaires = False

    if request.method == "POST":
        operation = request.form.get("operation", "")
        forme_juridique = request.form.get("forme_juridique", "")
        associe_unique = request.form.get("associe_unique") == "on"
        modifie_beneficiaires = request.form.get("modifie_beneficiaires") == "on"

        result = calculer_frais(operation, forme_juridique, associe_unique, modifie_beneficiaires)

    return render_template("index.html", result=result, operation=operation, forme_juridique=forme_juridique)

if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)



