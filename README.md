# Système de Suivi des Retards Fiscaux

Application web de démonstration pour le suivi des dossiers fiscaux, des paiements et des retards de paiement.

> **Périmètre :** ce projet est une application pédagogique utilisant une base de données locale et des données de démonstration. Il n'est pas connecté aux systèmes officiels de la Direction Générale des Impôts, à GID ou à Rokhas.

## Technologies

- Python 3.11+
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-WTF
- SQLite (base locale par défaut)
- Pandas et OpenPyXL pour les traitements Excel
- ReportLab pour les documents PDF
- Pytest pour les tests

## Structure générale

```text
suivi-retards-fiscaux/
├── app/
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
├── tests/
├── requirements.txt
├── run.py
└── README.md
```

Les modules sont organisés par fonctionnalité avec une Application Factory (`create_app`). Les modèles sont regroupés dans `app/models`, tandis que les traitements transversaux se trouvent dans `app/services`.

## Installation sous Windows

Depuis le dossier du projet :

```powershell
py -3.11 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloque l'activation de l'environnement, utilisez l'invite de commandes :

```bat
env\Scripts\activate
```

## Lancement

```bash
python run.py
```

Par défaut, le mode debug est désactivé. Pour l'activer pendant le développement :

**PowerShell**
```powershell
$env:FLASK_DEBUG="1"
python run.py
```

**Invite de commandes**
```bat
set FLASK_DEBUG=1
python run.py
```

La base SQLite locale est créée à l'emplacement configuré par l'Application Factory. Vérifiez la configuration de `app/__init__.py` avant de supprimer ou déplacer le dossier `instance`.

## Tests

À la racine du projet :

```bash
python -m pytest
```

Pour obtenir le rapport de couverture (facultatif) :

```bash
python -m pip install pytest-cov
python -m pytest --cov=app --cov-report=term-missing
```

## Sécurité et limites connues

- Utiliser une valeur `SECRET_KEY` longue, aléatoire et privée dans l'environnement avant tout déploiement.
- Ne pas déployer l'application avec le serveur de développement Flask.
- L'application ne doit pas être utilisée avec des données fiscales réelles ou personnelles sans authentification, autorisations, politique de conservation, journalisation protégée et audit de sécurité.
- Les journaux d'audit applicatifs ne constituent pas, à eux seuls, un stockage inviolable.
- Une relance enregistrée dans l'application représente un suivi interne ; elle ne prouve pas qu'un SMS, un e-mail ou un courrier a réellement été envoyé.
- Les migrations de base de données doivent être initialisées et vérifiées dans le dépôt avant d'utiliser des commandes Flask-Migrate sur une nouvelle installation.

## État des tests

Le nombre de tests peut évoluer. Le résultat à jour est celui affiché par `python -m pytest` dans l'environnement local.
