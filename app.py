"""Smart Closet — backend Flask opzionale.

L'app web usa IndexedDB nel browser e non ha bisogno di questo server.
Il backend serve come API di esempio: valida moduli, categorie e transizioni
di stato in modo coerente con il frontend e salva i dati in un file JSON.

Variabili d'ambiente:
  HOST              indirizzo di ascolto (default 127.0.0.1, solo questo computer)
  PORT              porta (default 5000)
  FLASK_DEBUG=1     attiva il debugger (solo in sviluppo, mai con HOST=0.0.0.0)
  SMART_CLOSET_DATA percorso del file dati (default garments.json)
"""
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_FILE = Path(os.environ.get("SMART_CLOSET_DATA", "garments.json"))

ALLOWED = {
    "in_armadio": ["indossato", "in_lavanderia", "non_disponibile", "ritirato"],
    "indossato": ["in_armadio", "in_lavanderia", "non_disponibile"],
    "in_lavanderia": ["in_armadio", "in_pulizia"],
    "in_pulizia": ["in_armadio", "non_disponibile"],
    "non_disponibile": ["in_armadio", "in_lavanderia", "ritirato"],
    "ritirato": [],
}

# Stesse categorie del frontend (index.html / app.js).
CATEGORIES = {
    "civile": {
        "tshirt_polo": "Magliette e polo",
        "camicie": "Camicie",
        "maglioni": "Maglioni e cardigan",
        "felpe": "Felpe",
        "pantaloni": "Pantaloni e jeans",
        "pantaloncini": "Pantaloncini",
        "completi": "Abiti e completi",
        "gonne_vestiti": "Gonne e vestiti",
        "giacche": "Giacche e blazer",
        "cappotti_giubbotti": "Cappotti e giubbotti",
        "intimo_calze": "Intimo e calze",
        "casa_notte": "Pigiami e abbigliamento da casa",
        "scarpe": "Scarpe",
        "accessori": "Accessori",
    },
    "militare": {
        "uniformi": "Uniformi e mimetiche",
        "camicie_militari": "Camicie e polo",
        "tshirt_militari": "Magliette",
        "pantaloni_militari": "Pantaloni",
        "giacche_militari": "Bluse e giacche",
        "giacconi_militari": "Giacconi e impermeabili",
        "maglieria_militare": "Maglieria e pile",
        "intimo_militare": "Intimo tecnico e calze",
        "calzature_militari": "Anfibi e calzature",
        "copricapi_militari": "Copricapi",
        "cinture_militari": "Cinture e cinturoni",
        "accessori_militari": "Guanti e accessori",
        "equipaggiamento": "Equipaggiamento e zaini",
    },
    "sportivo": {
        "tshirt_sportive": "Magliette e canotte",
        "shorts_sportivi": "Pantaloncini",
        "pantaloni_sportivi": "Pantaloni e leggings",
        "felpe_sportive": "Felpe e tute",
        "giacche_sportive": "Giacche e antivento",
        "intimo_sportivo": "Intimo tecnico e calze",
        "costumi": "Costumi",
        "scarpe_sportive": "Scarpe sportive",
        "copricapi_sportivi": "Copricapi e guanti",
        "accessori_sportivi": "Protezioni e accessori",
    },
}
DEFAULT_CATEGORY = {
    "civile": "accessori",
    "militare": "equipaggiamento",
    "sportivo": "accessori_sportivi",
}

MODULES = set(CATEGORIES)
WASH_TYPES = {"normali", "delicati", "bianchi", "neri"}
CARE_LABELS = {"30", "40", "60", "delicato", "mano", "non_lavare"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_garments():
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def save_garments():
    """Scrittura atomica: un crash a metà non corrompe il file."""
    fd, tmp = tempfile.mkstemp(dir=DATA_FILE.resolve().parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(garments, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)
    except OSError:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


garments = load_garments()


def text_field(body, key, max_len=200):
    value = body.get(key)
    return value.strip()[:max_len] if isinstance(value, str) and value.strip() else None


@app.get("/")
def home():
    return jsonify({
        "name": "Smart Closet API",
        "storage": str(DATA_FILE),
        "modules": sorted(MODULES),
        "washTypes": sorted(WASH_TYPES),
        "careLabels": sorted(CARE_LABELS),
    })


@app.get("/api/categories")
def list_categories():
    return jsonify(CATEGORIES)


@app.get("/api/garments")
def list_garments():
    module = request.args.get("module")
    status = request.args.get("status")
    wash_type = request.args.get("washType")
    category = request.args.get("categoryId")
    result = [
        g for g in garments
        if (not module or g["module"] == module)
        and (not status or g["currentStatus"] == status)
        and (not wash_type or g.get("washType") == wash_type)
        and (not category or g.get("categoryId") == category)
    ]
    return jsonify({"data": result, "count": len(result)})


@app.post("/api/garments")
def create_garment():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Corpo JSON non valido"}), 400

    name = text_field(body, "name")
    if not name:
        return jsonify({"error": "Il campo name è obbligatorio"}), 400

    module = body.get("module", "civile")
    wash_type = body.get("washType", "normali")
    care_label = body.get("careLabel", "30")

    if module not in MODULES:
        return jsonify({"error": "Modulo non valido", "allowed": sorted(MODULES)}), 400
    if wash_type not in WASH_TYPES:
        return jsonify({"error": "Tipo di lavaggio non valido"}), 400
    if care_label not in CARE_LABELS:
        return jsonify({"error": "Etichetta di lavaggio non valida"}), 400

    category = body.get("categoryId") or DEFAULT_CATEGORY[module]
    if category not in CATEGORIES[module]:
        return jsonify({
            "error": "Categoria non valida per questo modulo",
            "allowed": sorted(CATEGORIES[module]),
        }), 400

    created = now()
    garment = {
        "id": str(uuid.uuid4()),
        "name": name,
        "brand": text_field(body, "brand"),
        "color": text_field(body, "color"),
        "size": text_field(body, "size", 40),
        "material": text_field(body, "material"),
        "categoryId": category,
        "module": module,
        "washType": wash_type,
        "careLabel": care_label,
        "hasPhoto": False,
        "currentStatus": "in_armadio",
        "statusHistory": [{"from": None, "to": "in_armadio", "at": created}],
        "createdAt": created,
    }
    garments.append(garment)
    save_garments()
    return jsonify(garment), 201


@app.get("/api/garments/<garment_id>")
def get_garment(garment_id):
    garment = next((g for g in garments if g["id"] == garment_id), None)
    if not garment:
        return jsonify({"error": "Capo non trovato"}), 404
    return jsonify(garment)


@app.delete("/api/garments/<garment_id>")
def delete_garment(garment_id):
    garment = next((g for g in garments if g["id"] == garment_id), None)
    if not garment:
        return jsonify({"error": "Capo non trovato"}), 404
    garments.remove(garment)
    save_garments()
    return "", 204


@app.post("/api/garments/<garment_id>/status")
def change_status(garment_id):
    body = request.get_json(silent=True)
    body = body if isinstance(body, dict) else {}
    target = body.get("status")
    garment = next((g for g in garments if g["id"] == garment_id), None)
    if not garment:
        return jsonify({"error": "Capo non trovato"}), 404

    allowed = ALLOWED[garment["currentStatus"]]
    if target not in allowed:
        return jsonify({
            "error": "Transizione non ammessa",
            "from": garment["currentStatus"],
            "to": target,
            "allowed": allowed,
        }), 409

    garment["statusHistory"].append({"from": garment["currentStatus"], "to": target, "at": now()})
    garment["currentStatus"] = target
    save_garments()
    return jsonify(garment)


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
