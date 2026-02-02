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
  <a href="https://vocesalviento.com">https://vocesalviento.com</a>
</p>

---

## Application en Ligne

L'application est **deployee et accessible publiquement** a l'adresse :

> **https://vocesalviento.com**

Vous pouvez la tester directement depuis votre navigateur, sans aucune installation locale necessaire.

---

## Utilisateur de Test

Un utilisateur est deja pre-configure avec les cles API et un profil complet :

| Champ | Valeur |
|-------|--------|
| **Nom d'utilisateur** | `pepe2012` |
| **Mot de passe** | `pepe2012` |
| **E-mail** | `annndriancito2012@gmail.com` |
| **Fournisseur LLM** | OpenAI |
| **Cle API LLM** | Configuree |
| **API Google Search** | Configuree |
| **Profil CV** | Complet avec competences, experience et preferences |

---

## Guide de Test Pas a Pas

Voici les etapes recommandees pour tester la plateforme de bout en bout :

### Etape 1 - Se connecter et configurer le profil

1. Accedez a **https://vocesalviento.com** et connectez-vous avec `pepe2012` / `pepe2012`.
2. Allez dans **Mon Profil** (icone utilisateur en haut a droite).
3. Renseignez votre **nom et prenom**, votre **localisation** (ex: Madrid, Barcelona, Paris).
4. Dans la section **Preferences de recherche**, configurez la **modalite de travail** sur **Indiferente** (ou laissez vide) pour obtenir un maximum d'offres dans les resultats.
5. Enregistrez le profil.

### Etape 2 - Telecharger et analyser le CV

1. Depuis votre profil, allez a la section **Mon Curriculum**.
2. Vous pouvez soit coller le texte de votre CV, soit telecharger un fichier PDF.
3. Si vous telechargez un **PDF**, le systeme utilise l'extraction de texte (PyPDF2) ou, si le PDF est une image scannee, **GPT-4 Vision (OCR)** pour lire le contenu.
4. Une fois le texte du CV charge, cliquez sur **Analyser le CV**. L'IA (OpenAI ou le fournisseur configure) analysera le contenu et extraira automatiquement :
   - Les **competences techniques** (langages, frameworks, outils)
   - L'**experience professionnelle** (postes, durees)
   - La **formation** (diplomes, certifications)
   - Les **langues parlees**
   - Un **resume professionnel** structure
5. Cliquez ensuite sur **Enregistrer le CV** pour sauvegarder le texte et le resume dans votre profil.

### Etape 3 - Consulter le ranking de postes recommandes

Apres l'analyse du CV, le systeme genere automatiquement un **ranking de postes recommandes** : une liste ordonnee des metiers les plus adaptes a votre profil, basee sur vos competences, votre experience et votre formation. Ce ranking est visible dans votre profil et sera utilise par l'agent IA pour personnaliser les recherches d'emploi.

### Etape 4 - Ouvrir un chat et chercher des offres

1. Allez dans **Chat IA** > **Nouvelle Conversation**.
2. Decrivez vos preferences en langage naturel. Par exemple :
   - *"Cherche des offres de developpeur Python a Madrid"*
   - *"Je veux des postes en teletravail dans la data science"*
   - *"Trouve des offres de marketing digital a Barcelona, contrat indefini"*
3. L'agent IA va automatiquement :
   - Charger votre profil et votre CV
   - Rechercher des offres sur le web (Google, portails d'emploi)
   - Filtrer et classer les resultats selon votre profil
   - Verifier que les offres sont **actives** en naviguant sur les pages
   - Generer une **analyse de compatibilite** (fit analysis) pour chaque offre
4. Les resultats incluent : titre du poste, entreprise, localisation, lien direct, score de compatibilite et details specifiques.

---

## Fonctionnement de l'Agent IA

### Architecture Function Calling

Le coeur du systeme est un **agent a Function Calling** base sur LangChain. Contrairement a un simple chatbot, l'agent peut **executer des outils de maniere autonome** en boucle, jusqu'a 15 iterations par requete.

Le cycle de fonctionnement est le suivant :

```
1. L'utilisateur envoie un message
2. L'agent charge automatiquement le profil utilisateur (1ere iteration)
3. Le LLM analyse le message et decide quel outil appeler
4. L'outil s'execute et retourne un resultat
5. Le LLM analyse le resultat et decide :
   - Appeler un autre outil (retour a l'etape 3)
   - Ou generer la reponse finale
6. Reponse envoyee a l'utilisateur
```

L'agent utilise un **raisonnement en chaine** : a chaque iteration, le LLM voit tout l'historique (messages + resultats d'outils) et decide de la prochaine action. Il n'y a pas de script fixe : l'agent s'adapte a la requete.

### Outils (Tools) de l'Agent

L'agent dispose de **8 outils** qu'il peut combiner librement :

| Outil | Fonction |
|-------|----------|
| `get_user_profile` | Recupere le profil complet du candidat (CV, competences, preferences, ranking) |
| `get_full_cv` | Retourne le texte integral du curriculum |
| `search_jobs` | Recherche d'offres d'emploi via le web. Analyse ~60 offres, retourne les 15 meilleures avec verification et score de compatibilite |
| `search_recent_jobs` | Recherche d'offres publiees dans les dernieres 24-48h |
| `search_jobs_by_ranking` | Recherche 10 offres pour chaque poste du ranking CV, retourne le top 3 de chaque |
| `recommend_companies` | Recommande des entreprises par secteur/localisation, inclut les contacts recruteurs |
| `web_search` | Recherche Google Custom Search pour des requetes generiques |
| `browse_webpage` | Extrait le contenu d'une page web pour verifier qu'une offre est active et extraire les details |

### Systeme de Scoring et Compatibilite

Chaque offre trouvee est evaluee selon un **algorithme de scoring sur 100 points** :

| Critere | Points | Description |
|---------|--------|-------------|
| **Correspondance technique** | 35 pts | Alignement entre les competences du candidat et les technologies demandees |
| **Localisation et modalite** | 25 pts | Filtre strict : la ville et le mode de travail (remote/presentiel/hybride) doivent correspondre |
| **Salaire et avantages** | 20 pts | Salaire mentionne et competitif par rapport aux attentes |
| **Qualite de l'offre** | 10 pts | Clarte de la description, reputation de l'entreprise |
| **Type de contrat** | 10 pts | Indefini > stable > temporaire |

De plus, chaque offre inclut un **fit_analysis** : une analyse specifique qui detaille les technologies mentionnees, les annees d'experience requises, les responsabilites concretes et la correspondance avec le profil du candidat.

### Verification des Offres

L'agent ne se contente pas de lister des resultats de recherche. Il **navigue sur les pages des offres** (via `browse_webpage`) pour :
- Verifier que l'offre est **encore active**
- Extraire les **details reels** du poste (technologies, salaire, modalite)
- Generer l'analyse de compatibilite basee sur le contenu reel
- Attribuer un **niveau de confiance** (haute/moyenne/basse) a la verification

### Cycle de Revision (optionnel)

Apres la generation de la reponse initiale, le systeme peut executer un **cycle de revision** :
1. Un `ResponseReviewer` evalue la qualite de la reponse (score 0-100)
2. Si la qualite est insuffisante, une deuxieme requete est lancee avec du feedback
3. La reponse amelioree est fusionnee et renvoyee a l'utilisateur

### Multi-Fournisseur LLM

Chaque utilisateur configure son fournisseur d'IA depuis son profil :

| Fournisseur | Modele par defaut | Cle API | Cout |
|-------------|-------------------|---------|------|
| **Ollama** | qwen2.5:7b | Non requise | Gratuit (local) |
| **Google Gemini** | gemini-2.5-flash | Oui | Payant |
| **OpenAI** | gpt-4o-mini | Oui | Payant |
| **NVIDIA** | llama-3.1-8b | Oui | Payant |

---

## Description Generale

MLUrbanPlanning est une plateforme web qui aide les candidats a trouver des offres d'emploi grace a des **agents d'intelligence artificielle** qui analysent le CV de l'utilisateur, recherchent des offres sur le web et generent des recommandations personnalisees. Le systeme utilise le **Function Calling** avec jusqu'a 15 iterations automatiques pour resoudre des requetes complexes.

### Fonctionnalites principales

- **Analyse de CV avec IA** - Extraction automatique des competences, experience, formation et langues depuis un PDF ou texte. Support OCR via GPT-4 Vision pour les PDF scannes.
- **Ranking de postes** - Classification automatique des metiers les plus adaptes au profil du candidat.
- **Recherche intelligente d'emploi** - Agent qui recherche des offres sur le web, les filtre, les verifie et les classe selon le profil.
- **Chat interactif avec Function Calling** - Conversation naturelle avec l'agent qui execute des outils automatiquement (jusqu'a 15 iterations).
- **Multi-fournisseur LLM** - Support pour Google Gemini, OpenAI, NVIDIA et Ollama (100% local et prive).
- **Analyse de compatibilite** - Score sur 100 et analyse detaillee pour chaque offre.
- **Navigation web interactive** - Verification des offres en temps reel via Playwright.
- **Bilingue** - Interface disponible en francais et en espagnol.

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
| **Serveur** | Nginx + Gunicorn + HTTPS (Let's Encrypt) |

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
│   ├── agent_function_calling.py   # Agent principal (boucle FC)
│   ├── config.py                   # Configuration et prompts
│   ├── tools/
│   │   ├── agent_tools/            # 8 outils de l'agent
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

## Interface

L'interface suit un design minimaliste inspire d'Apple avec :

- Chat interactif avec AJAX (sans rechargement de page)
- Indicateur de saisie anime pendant que l'IA repond
- Metadonnees visibles par message : tokens utilises, outils executes, cout
- Design responsive pour mobile et desktop

---

## Licence

Projet academique - Tous droits reserves.
