# Système de Suivi des Retards Fiscaux

Application web de démonstration pour le suivi des dossiers fiscaux, des paiements et des retards de paiement.

> **Périmètre :** ce projet est une application pédagogique utilisant une base de données locale et des données de démonstration. Il n'est pas connecté aux systèmes officiels de la Direction Générale des Impôts, à GID ou à Rokhas.
>
> **Ne pas utiliser avec des données fiscales réelles** sans authentification renforcée, journalisation d'audit, politique de conservation et hébergement sécurisé.

## Technologies

- Python 3.11+
- Flask + Flask-SQLAlchemy + Flask-Migrate + Flask-WTF + Flask-Login
- SQLite (par défaut) — PostgreSQL possible via `DATABASE_URL`
- Pandas / OpenPyXL (imports Excel)
- ReportLab (PDF)
- Pytest

## Structure

```text
suivi-retards-fiscaux/
├── app/
│   ├── auth/            # Connexion, utilisateurs, décorateurs de rôles
│   ├── accueil/
│   ├── contribuables/
│   ├── dossiers/
│   ├── importation/
│   ├── models/
│   ├── paiements/
│   ├── parametres/
│   ├── rapports/
│   ├── recherche/
│   ├── relances/
│   ├── services/
│   ├── suivi_impayes/
│   ├── synthese/
│   ├── types_taxes/
│   ├── static/
│   └── templates/
├── migrations/
├── tests/
├── requirements.txt
├── run.py
└── README.md
```

## Installation

```powershell
py -3.11 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

Éditez `.env` et définissez un `SECRET_KEY` fort :

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Premier démarrage

```bash
# 1. Appliquer les migrations (recommandé)
flask --app run.py db upgrade

# Ou créer les tables manquantes :
flask --app run.py init-auth-db

# 2. Créer le premier administrateur
flask --app run.py create-admin

# 3. Lancer l'application
python run.py
```

Ouvrez http://127.0.0.1:5000

### Rôles

| Rôle | Droits |
|------|--------|
| `admin` | Tout + paramètres + gestion des comptes |
| `agent` | Lecture et écriture métier |
| `consultation` | Lecture seule (GET) |

## Tests

```bash
python -m pytest
python -m pytest --cov=app --cov-report=term-missing   # optionnel
```

## Sécurité

- Définir `SECRET_KEY` via l'environnement (jamais dans le dépôt).
- Ne pas déployer avec le serveur de développement Flask.
- Mot de passe : minimum 12 caractères, majuscule, minuscule, chiffre.
- Verrouillage temporaire après 5 échecs de connexion (15 minutes).
- Les relances enregistrées dans l'app ne prouvent pas l'envoi réel d'un SMS/e-mail/courrier.
- Les journaux d'audit applicatifs ne sont pas un stockage inviolable.

## Déploiement (aperçu)

Pour un usage hors démonstration :

1. `SECRET_KEY` fort + `FLASK_DEBUG=False`
2. Base PostgreSQL via `DATABASE_URL`
3. Serveur WSGI (Gunicorn / Waitress) derrière un reverse proxy HTTPS
4. Sauvegardes régulières et politique de conservation des données

## Licence / usage pédagogique

Projet de démonstration. Toute utilisation sur des données personnelles ou fiscales réelles engage la responsabilité de l'opérateur.
