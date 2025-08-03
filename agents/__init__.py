"""
Package des agents spécialisés pour le système de matching CV-offres
"""

from .pdf_extractor_agent import PDFExtractorAgent

# Essayer d'importer les versions complètes, sinon utiliser les versions simplifiées
try:
    # Tester d'abord si spacy est disponible
    import spacy
    from .offer_analyzer_agent import OfferAnalyzerAgent
    from .cv_analyzer_agent import CVAnalyzerAgent
    from .matcher_agent import MatcherAgent
    print("✅ Utilisation des agents complets avec spaCy")
except ImportError as e:
    print(f"⚠️  spaCy non disponible ({e}), utilisation des agents simplifiés")
    # Utiliser les versions simplifiées
    from .offer_analyzer_agent_simple import OfferAnalyzerAgent
    from .cv_analyzer_agent_simple import CVAnalyzerAgent
    from .matcher_agent_simple import MatcherAgent

from .coordinator_agent import CoordinatorAgent

__all__ = [
    'PDFExtractorAgent',
    'OfferAnalyzerAgent',
    'CVAnalyzerAgent',
    'MatcherAgent',
    'CoordinatorAgent'
]