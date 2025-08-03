# 🤖 Système Multi-Agent de Matching CV-Offres

Un système intelligent utilisant plusieurs agents spécialisés pour analyser et matcher des CVs avec des offres d'emploi. Ce système utilise des agents simplifiés qui fonctionnent sans dépendances externes complexes.

## ✨ Fonctionnalités

- ✅ **Extraction automatique** du texte des PDFs (offres et CVs)
- ✅ **Analyse intelligente** des exigences des offres d'emploi
- ✅ **Analyse des compétences** et expériences des candidats
- ✅ **Calcul de scores** de compatibilité précis
- ✅ **Interface web moderne** et intuitive
- ✅ **Architecture multi-agent** modulaire
- ✅ **Export des résultats** en CSV
- ✅ **Traitement parallèle** des CVs pour de meilleures performances

## 🏗️ Architecture

Le système est composé de **5 agents spécialisés** :

### 1. 📄 Agent Extracteur PDF
- Extraction du texte des documents PDF
- Support de `pdfplumber` (principal) et `PyPDF2` (fallback)
- Nettoyage et normalisation du texte

### 2. 💼 Agent Analyseur d'Offres
- Analyse et structuration des exigences
- Extraction des compétences techniques et comportementales
- Détection du niveau d'expérience et des formations requises
- Identification des langues, localisation, type de contrat

### 3. 👤 Agent Analyseur de CVs
- Analyse des profils candidats
- Extraction des informations personnelles
- Analyse de l'expérience professionnelle et formation
- Calcul automatique des années d'expérience

### 4. 🎯 Agent Matcher
- Calcul des scores de compatibilité
- Analyse multicritères pondérée
- Génération de recommandations
- Identification des points forts et lacunes

### 5. 🎭 Agent Coordinateur
- Orchestration du processus complet
- Traitement parallèle des CVs
- Gestion des sessions et résultats

## 🚀 Installation

### Prérequis
- Python 3.7+
- pip

### Installation rapide

```bash
# Cloner le projet (si applicable)
git clone <repository-url>
cd workspace

# Installer les dépendances
pip install -r requirements_simple.txt

# Vérifier l'installation
python3 test_system.py
```

### Dépendances principales
- `flask` : Serveur web
- `flask-cors` : Support CORS
- `PyPDF2` & `pdfplumber` : Extraction PDF
- `fuzzywuzzy` : Correspondance floue de texte

## 💻 Utilisation

### 1. Lancer l'application

```bash
python3 app.py
```

L'application sera disponible sur : **http://localhost:5000**

### 2. Interface Web

1. **📤 Upload de l'offre d'emploi** (PDF)
2. **📂 Upload des CVs** (PDFs multiples)
3. **⚙️ Analyse automatique** par les agents
4. **📊 Consultation des résultats** avec scores et recommandations
5. **💾 Export CSV** des résultats détaillés

### 3. API REST

#### Endpoints disponibles :

- `GET /api/health` - État de l'API
- `POST /api/upload-offer` - Upload offre d'emploi
- `POST /api/upload-cvs` - Upload CVs multiples
- `POST /api/process-matching` - Lancer l'analyse
- `GET /api/results/{session_id}` - Récupérer les résultats
- `GET /api/export/{session_id}` - Exporter en CSV

#### Exemple d'utilisation :

```bash
# Vérifier l'état
curl http://localhost:5000/api/health

# Upload d'une offre
curl -X POST -F "offer=@offre.pdf" http://localhost:5000/api/upload-offer

# Upload de CVs
curl -X POST -F "session_id=SESSION_ID" -F "cvs=@cv1.pdf" -F "cvs=@cv2.pdf" http://localhost:5000/api/upload-cvs
```

## 📊 Système de Scoring

Le système utilise un **scoring multicritères pondéré** :

- **Compétences techniques** (30%) : Correspondance des technologies
- **Niveau d'expérience** (25%) : Années d'expérience vs requis
- **Formation** (15%) : Diplômes et certifications
- **Langues** (10%) : Maîtrise des langues requises
- **Compétences comportementales** (10%) : Soft skills
- **Similarité sémantique** (10%) : Analyse globale du contenu

### Niveaux de correspondance :
- 🟢 **Excellent** : 80-100%
- 🔵 **Bon** : 60-79%
- 🟡 **Moyen** : 40-59%
- 🔴 **Faible** : 0-39%

## 📁 Structure du Projet

```
workspace/
├── agents/                     # Agents spécialisés
│   ├── __init__.py            # Imports conditionnels
│   ├── pdf_extractor_agent.py # Extraction PDF
│   ├── offer_analyzer_agent_simple.py # Analyse offres
│   ├── cv_analyzer_agent_simple.py    # Analyse CVs
│   ├── matcher_agent_simple.py        # Matching
│   └── coordinator_agent.py           # Coordination
├── templates/
│   └── index.html             # Interface web
├── uploads/                   # Fichiers uploadés
├── results/                   # Résultats exportés
├── examples/                  # Fichiers d'exemple
├── app.py                     # Application Flask
├── test_system.py            # Tests du système
├── requirements_simple.txt   # Dépendances
└── README.md                 # Documentation
```

## 🧪 Tests

Le système inclut une suite de tests complète :

```bash
python3 test_system.py
```

**Tests inclus :**
- ✅ Import des modules
- ✅ Initialisation des agents
- ✅ Analyse de texte (offres et CVs)
- ✅ Calcul de matching
- ✅ Création des dossiers d'exemple

## 🎯 Fonctionnalités Avancées

### Traitement Parallèle
- Analyse simultanée de plusieurs CVs
- Optimisation des performances
- Gestion d'erreurs robuste

### Gestion de Sessions
- Sessions uniques par analyse
- Stockage temporaire des résultats
- Récupération des données

### Export de Données
- Export CSV détaillé
- Scores par critère
- Recommandations personnalisées

## 🔧 Configuration

### Variables d'environnement
- `FLASK_ENV` : Environnement (development/production)
- `MAX_CONTENT_LENGTH` : Taille max des fichiers (défaut: 50MB)

### Personnalisation
- Modifier les poids dans `matcher_agent_simple.py`
- Ajouter des compétences dans les dictionnaires
- Personnaliser l'interface dans `templates/index.html`

## 🐛 Dépannage

### Problèmes courants

1. **Erreur d'import spaCy** : Normal, le système utilise les versions simplifiées
2. **Fichiers non trouvés** : Vérifier les chemins et permissions
3. **Erreur de parsing PDF** : Essayer avec des PDFs moins complexes

### Logs
Les logs détaillés sont disponibles dans la console pour le débogage.

## 🚧 Limitations Actuelles

- Analyse basée sur des expressions régulières (pas de NLP avancé)
- Support des PDFs simples uniquement
- Interface en français principalement
- Pas de persistance de données (sessions en mémoire)

## 🔮 Améliorations Futures

- [ ] Intégration d'un modèle NLP avancé
- [ ] Support de formats multiples (DOCX, TXT)
- [ ] Base de données pour la persistance
- [ ] API d'authentification
- [ ] Analyses statistiques avancées
- [ ] Interface multilingue

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

---

**🎉 Système prêt à l'emploi !** 

Pour démarrer : `python3 app.py` puis rendez-vous sur http://localhost:5000