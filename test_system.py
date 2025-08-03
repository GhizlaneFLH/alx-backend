#!/usr/bin/env python3
"""
Script de test pour le système multi-agent de matching CV-offres
"""

import os
import sys
import logging
import tempfile
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_imports():
    """Test l'import des modules principaux"""
    logger.info("📋 Test: Import des modules")
    
    try:
        # Importer le package principal
        import agents
        
        # Tester les imports individuels
        from agents import PDFExtractorAgent
        from agents import OfferAnalyzerAgent
        from agents import CVAnalyzerAgent
        from agents import MatcherAgent
        from agents import CoordinatorAgent
        
        logger.info("✅ Tous les modules importés avec succès")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Erreur d'import: {e}")
        return False

def test_agent_initialization():
    """Test l'initialisation des agents"""
    logger.info("📋 Test: Initialisation des agents")
    
    try:
        from agents import PDFExtractorAgent, OfferAnalyzerAgent, CVAnalyzerAgent, MatcherAgent, CoordinatorAgent
        
        # Initialiser chaque agent
        pdf_agent = PDFExtractorAgent()
        offer_agent = OfferAnalyzerAgent()
        cv_agent = CVAnalyzerAgent()
        matcher_agent = MatcherAgent()
        coordinator = CoordinatorAgent()
        
        logger.info("✅ Tous les agents initialisés avec succès")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")
        return False

def test_text_analysis():
    """Test l'analyse de texte"""
    logger.info("📋 Test: Analyse de texte")
    
    try:
        from agents import OfferAnalyzerAgent, CVAnalyzerAgent
        
        # Test d'analyse d'offre
        offer_agent = OfferAnalyzerAgent()
        offer_text = """
        Poste: Développeur Python Senior
        Nous recherchons un développeur Python expérimenté avec 5+ années d'expérience.
        Compétences requises: Python, Django, Flask, PostgreSQL, Git
        Formation: Master en informatique ou équivalent
        Lieu: Paris
        Contrat: CDI
        Salaire: 55k€ par an
        """
        
        offer_analysis = offer_agent.analyze_offer(offer_text)
        
        if offer_analysis and 'job_title' in offer_analysis:
            logger.info("✅ Analyse d'offre fonctionnelle")
        else:
            logger.warning("⚠️  Analyse d'offre partielle")
        
        # Test d'analyse de CV
        cv_agent = CVAnalyzerAgent()
        cv_text = """
        Jean Dupont
        jean.dupont@email.com
        06 12 34 56 78
        Paris
        
        Développeur Python Senior
        
        Expérience:
        2019-2024: Développeur Python - TechCorp
        2017-2019: Développeur Junior - StartupXYZ
        
        Compétences:
        Python, Django, Flask, PostgreSQL, Git, Docker
        
        Formation:
        2017: Master Informatique - Université Paris
        """
        
        logger.info(f"CV text type: {type(cv_text)}, length: {len(cv_text) if cv_text else 'None'}")
        
        try:
            cv_analysis = cv_agent.analyze_cv(cv_text, "cv_test")
        except Exception as e:
            logger.error(f"Specific CV analysis error: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        if cv_analysis and 'personal_info' in cv_analysis:
            logger.info("✅ Analyse de CV fonctionnelle")
        else:
            logger.warning("⚠️  Analyse de CV partielle")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse de texte: {e}")
        return False

def test_matching():
    """Test le calcul de matching"""
    logger.info("📋 Test: Calcul de matching")
    
    try:
        from agents import MatcherAgent
        
        matcher = MatcherAgent()
        
        # Données de test simplifiées
        offer_analysis = {
            'job_title': 'Développeur Python Senior',
            'technical_skills': {
                'programming': ['python'],
                'web': ['django', 'flask'],
                'database': ['postgresql']
            },
            'experience_level': {'level': 'senior', 'years_range': (5, 10)},
            'education_requirements': ['master'],
            'languages': [{'language': 'français', 'level': 'natif'}],
            'soft_skills': ['autonomie', 'travail en équipe']
        }
        
        cv_analysis = {
            'cv_id': 'cv_test',
            'personal_info': {'name': 'Jean Dupont', 'email': 'jean@email.com'},
            'technical_skills': {
                'programming': ['python'],
                'web': ['django', 'flask'],
                'database': ['postgresql']
            },
            'total_experience_years': 7,
            'education': [{'degree': 'master informatique'}],
            'languages': [{'language': 'français', 'level': 'natif'}],
            'soft_skills': ['autonomie', 'travail en équipe'],
            'profile_summary': 'Développeur expérimenté'
        }
        
        match_result = matcher.calculate_compatibility_score(offer_analysis, cv_analysis)
        
        if match_result and 'global_score' in match_result:
            score = match_result['global_score']
            logger.info(f"✅ Matching fonctionnel - Score: {score}")
            return True
        else:
            logger.error("❌ Résultat de matching invalide")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du matching: {e}")
        return False

def create_example_files():
    """Crée des fichiers d'exemple pour les tests"""
    try:
        # Créer les dossiers
        os.makedirs("examples", exist_ok=True)
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("results", exist_ok=True)
        
        # Créer un fichier d'exemple d'offre
        offer_example = """
# Exemple d'Offre d'Emploi

**Poste:** Développeur Full-Stack Senior

**Description:**
Nous recherchons un développeur full-stack expérimenté pour rejoindre notre équipe technique.

**Compétences requises:**
- Python (Django/Flask)
- JavaScript (React/Vue.js)
- Base de données (PostgreSQL, MongoDB)
- Git, Docker
- 5+ années d'expérience

**Formation:** Master en informatique ou équivalent
**Lieu:** Paris, France
**Contrat:** CDI
**Salaire:** 50-60k€ par an
        """
        
        with open("examples/exemple_offre.txt", "w", encoding="utf-8") as f:
            f.write(offer_example)
        
        # Créer un fichier d'exemple de CV
        cv_example = """
# CV - Marie Martin

**Contact:**
- Email: marie.martin@email.com
- Téléphone: 06 12 34 56 78
- Localisation: Paris

**Expérience Professionnelle:**

**2020-2024: Développeuse Full-Stack Senior - TechCorp**
- Développement d'applications web avec Python/Django
- Frontend avec React.js
- Gestion de bases de données PostgreSQL
- Travail en équipe agile

**2018-2020: Développeuse Web - StartupXYZ**
- Développement avec Python/Flask
- JavaScript/Vue.js
- MongoDB

**Formation:**
- 2018: Master Informatique - Université Paris Diderot

**Compétences Techniques:**
- Python, Django, Flask
- JavaScript, React, Vue.js
- PostgreSQL, MongoDB
- Git, Docker, AWS

**Langues:**
- Français (natif)
- Anglais (courant)
        """
        
        with open("examples/exemple_cv.txt", "w", encoding="utf-8") as f:
            f.write(cv_example)
        
        logger.info("✅ Dossiers d'exemple créés")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création des exemples: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🚀 Démarrage des tests du système multi-agent")
    
    tests = [
        ("Import des modules", test_imports),
        ("Initialisation des agents", test_agent_initialization),
        ("Analyse de texte", test_text_analysis),
        ("Calcul de matching", test_matching),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Test: {test_name}")
        try:
            result = test_func()
            results.append(result)
            if result:
                logger.info(f"✅ Test réussi: {test_name}")
            else:
                logger.error(f"❌ Test échoué: {test_name}")
        except Exception as e:
            logger.error(f"❌ Erreur lors du test '{test_name}': {e}")
            results.append(False)
    
    # Créer les fichiers d'exemple
    create_example_files()
    
    # Résumé des résultats
    passed = sum(results)
    total = len(results)
    
    logger.info(f"\n📊 Résultats des tests: {passed}/{total} réussis")
    
    if passed == total:
        logger.info("🎉 Tous les tests sont réussis!")
        logger.info("👉 Vous pouvez maintenant lancer l'application avec: python app.py")
        sys.exit(0)
    else:
        logger.error("❌ Certains tests ont échoué. Vérifiez la configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()