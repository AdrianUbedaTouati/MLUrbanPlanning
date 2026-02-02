# MLUrbanPlanning - Plateforme IA de Recherche d'Emploi

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.1.6-092E20?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/LangChain-0.3+-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" />
  <img src="https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" />
  <img src="https://img.shields.io/badge/Version-3.8.0-blue?style=for-the-badge" />
</p>

<p align="center">
  <b>Plateforme intelligente de recherche d'emploi propulsee par des agents IA avec Function Calling</b>
</p>

<p align="center">
  <a href="https://vocesalviento.com">vocesalviento.com</a>
</p>

---

## Description Generale

MLUrbanPlanning est une plateforme web qui aide les candidats a trouver des offres d'emploi grace a des **agents d'intelligence artificielle** qui analysent le CV de l'utilisateur, recherchent des offres sur le web et generent des recommandations personnalisees. Le systeme utilise le **Function Calling** avec jusqu'a 15 iterations automatiques pour resoudre des requetes complexes.

### Fonctionnalites principales

- **Analyse de CV avec IA** - Extraction automatique des competences, experience, formation et langues depuis un PDF ou texte
- **Recherche intelligente d'emploi** - Agent qui recherche des offres sur le web et les filtre selon le profil du candidat
- **Chat interactif avec Function Calling** - Conversation naturelle avec l'agent qui execute des outils automatiquement
- **Multi-fournisseur LLM** - Support pour Google Gemini, OpenAI, NVIDIA et Ollama (100% local et prive)
- **Analyse de compatibilite** - Score de compatibilite entre le profil du candidat et les offres trouvees
- **Navigation web interactive** - Playwright pour naviguer sur des portails d'emploi complexes
- **Bilingue** - Interface disponible en francais et en espagnol

---

## URL Publique

L'application est deployee et accessible a l'adresse :

**https://vocesalviento.com**

---

## Utilisateur de Test

La plateforme dispose d'un utilisateur pre-configure avec les APIs et un profil complet pret a tester :

| Champ | Valeur |
|-------|--------|
| **Nom d'utilisateur** | `pepe2012` |
| **Mot de passe** | `pepe2012` |
| **E-mail** | `annndriancito2012@gmail.com` |
| **Fournisseur LLM** | OpenAI |
| **Cle API LLM** | Configuree |
| **API Google Search** | Configuree |
| **Profil CV** | Complet avec competences, experience et preferences |

> L'utilisateur dispose deja des cles API OpenAI et Google Search configurees, ainsi qu'un profil de candidat avec un CV analyse et des preferences de recherche definies.

---

## Stack Technologique

| Composant | Technologie |
|-----------|-------------|
| **Backend** | Django 5.1.6, Python 3.12 |
| **IA / Agents** | LangChain 0.3+, Function Calling Agent |
| **LLMs** | Google Gemini 2.5 Flash, OpenAI GPT-4o, NVIDIA NIM, Ollama |
| **Frontend** | Bootstrap 5, JavaScript (AJAX) |
| **Base de donnees** | SQLite (developpement) / PostgreSQL (production) |
| **Web Scraping** | Playwright (navigation interactive) |
| **Serveur** | Nginx + HTTPS (Let's Encrypt) |

---

## Architecture de l'Agent

Le systeme utilise un **Function Calling Agent** qui decide de maniere autonome quels outils executer :

```
Utilisateur : "Cherche des offres de data science a Paris"

  -> L'agent analyse la requete
  -> Execute : get_user_profile() -> obtient le CV et les preferences
  -> Execute : search_jobs(query="data science", location="Paris")
  -> Analyse ~60 offres, selectionne le top 15
  -> Genere une analyse de compatibilite avec un score
  -> Reponse finale avec les offres classees
```

### Outils disponibles

| Categorie | Outils | Description |
|-----------|--------|-------------|
| **Profil** | `get_user_profile`, `get_full_cv` | Contexte du candidat |
| **Recherche** | `search_jobs`, `web_search` | Recherche d'offres et web |
| **Analyse** | `analyze_cv`, `recommend_companies` | Analyse de CV et recommandations |
| **Navigation** | `browse_webpage`, `browse_interactive` | Extraction web et Playwright |

---

## Structure du Projet

```
MLUrbanPlanning/
├── config/                     # Settings et URLs Django
├── apps/
│   ├── authentication/         # Utilisateurs, connexion, cles API
│   ├── company/                # Profil candidat, CV, preferences
│   ├── chat/                   # Sessions de chat et messages
│   └── core/                   # Tableau de bord, accueil, profil
├── agent_ia_core/              # Moteur IA
│   ├── agent_function_calling.py   # Agent principal
│   ├── config.py                   # Configuration
│   ├── tools/
│   │   ├── agent_tools/            # Outils de l'agent
│   │   └── core/                   # Registry et classes de base
│   └── schema/                     # Validation des donnees
├── templates/                  # Templates HTML
├── static/                     # CSS, JS (design inspire d'Apple)
├── data/                       # Base de donnees et registres
├── media/                      # CVs telecharges par les utilisateurs
└── manage.py
```

---

## Installation Locale

```bash
# Cloner le depot
git clone https://github.com/AdrianUbedaTouati/MLUrbanPlanning.git
cd MLUrbanPlanning

# Environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Dependances
pip install -r requirements.txt

# Variables d'environnement
cp .env.example .env   # Editer avec vos cles API

# Migrations et serveur
python manage.py migrate
python manage.py runserver
```

Accedez a `http://127.0.0.1:8000`

---

## Configuration du LLM

Chaque utilisateur configure son fournisseur d'IA depuis **Mon Profil > Modifier le Profil** :

| Fournisseur | Modele par defaut | Cle API | Cout |
|-------------|-------------------|---------|------|
| **Ollama** | qwen2.5:7b | Non requise | Gratuit (local) |
| **Google Gemini** | gemini-2.5-flash | Oui | Payant |
| **OpenAI** | gpt-4o-mini | Oui | Payant |
| **NVIDIA** | llama-3.1-8b | Oui | Payant |

---

## Interface

L'interface suit un design minimaliste inspire d'Apple avec :

- Chat interactif avec AJAX (sans rechargement)
- Indicateur de saisie anime pendant que l'IA repond
- Metadonnees visibles : tokens utilises, outils executes
- Design responsive pour mobile et desktop
- Support du mode sombre

---

## Licence

Projet academique - Tous droits reserves.
