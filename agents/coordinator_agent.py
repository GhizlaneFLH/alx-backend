import logging
import os
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .pdf_extractor_agent import PDFExtractorAgent

# Importer les bonnes versions d'agents selon la disponibilité de spacy
try:
    import spacy
    from .offer_analyzer_agent import OfferAnalyzerAgent
    from .cv_analyzer_agent import CVAnalyzerAgent
    from .matcher_agent import MatcherAgent
except ImportError:
    from .offer_analyzer_agent_simple import OfferAnalyzerAgent
    from .cv_analyzer_agent_simple import CVAnalyzerAgent
    from .matcher_agent_simple import MatcherAgent

class CoordinatorAgent:
    """Agent coordinateur qui orchestre l'ensemble du système multi-agent"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialisation des agents spécialisés
        self.pdf_extractor = PDFExtractorAgent()
        self.offer_analyzer = OfferAnalyzerAgent()
        self.cv_analyzer = CVAnalyzerAgent()
        self.matcher = MatcherAgent()
        
        # Configuration
        self.max_workers = 4  # Pour le traitement parallèle des CVs
        
        # Stockage des résultats
        self.current_session = {
            "offer_analysis": None,
            "cvs_analyses": [],
            "matching_results": [],
            "session_id": None,
            "timestamp": None
        }
        
        self.logger.info("Agent Coordinateur initialisé avec tous les agents spécialisés")
    
    def process_matching_request(self, offer_pdf_path: str, 
                                cv_pdf_paths: List[str],
                                session_id: str = None) -> Dict[str, Any]:
        """
        Traite une demande complète de matching CV-offres
        
        Args:
            offer_pdf_path: Chemin vers l'offre d'emploi PDF
            cv_pdf_paths: Liste des chemins vers les CVs PDF
            session_id: Identifiant de session (optionnel)
            
        Returns:
            Dict avec tous les résultats du matching
        """
        start_time = time.time()
        
        # Initialiser la session
        self.current_session = {
            "session_id": session_id or f"session_{int(time.time())}",
            "timestamp": time.time(),
            "offer_analysis": None,
            "cvs_analyses": [],
            "matching_results": [],
            "processing_stats": {}
        }
        
        try:
            self.logger.info(f"Début du traitement - Session: {self.current_session['session_id']}")
            self.logger.info(f"Offre: {offer_pdf_path}")
            self.logger.info(f"Nombre de CVs: {len(cv_pdf_paths)}")
            
            # Étape 1: Traiter l'offre d'emploi
            offer_result = self._process_offer(offer_pdf_path)
            if not offer_result["success"]:
                return self._create_error_response("Erreur lors du traitement de l'offre", offer_result)
            
            # Étape 2: Traiter les CVs en parallèle
            cvs_result = self._process_cvs_parallel(cv_pdf_paths)
            if not cvs_result["success"]:
                return self._create_error_response("Erreur lors du traitement des CVs", cvs_result)
            
            # Étape 3: Calculer les scores de compatibilité
            matching_result = self._calculate_matching_scores()
            if not matching_result["success"]:
                return self._create_error_response("Erreur lors du calcul des scores", matching_result)
            
            # Statistiques de traitement
            processing_time = time.time() - start_time
            self.current_session["processing_stats"] = {
                "total_processing_time": round(processing_time, 2),
                "offer_processed": True,
                "cvs_processed": len(self.current_session["cvs_analyses"]),
                "cvs_failed": len(cv_pdf_paths) - len(self.current_session["cvs_analyses"]),
                "matches_calculated": len(self.current_session["matching_results"])
            }
            
            self.logger.info(f"Traitement terminé en {processing_time:.2f}s")
            
            return self._create_success_response()
            
        except Exception as e:
            self.logger.error(f"Erreur globale dans le coordinateur: {e}")
            return self._create_error_response("Erreur système", {"error": str(e)})
    
    def _process_offer(self, offer_pdf_path: str) -> Dict[str, Any]:
        """Traite l'offre d'emploi"""
        try:
            self.logger.info("Traitement de l'offre d'emploi...")
            
            # Vérifier l'existence du fichier
            if not os.path.exists(offer_pdf_path):
                return {"success": False, "error": f"Fichier offre non trouvé: {offer_pdf_path}"}
            
            # Extraction du texte
            extraction_result = self.pdf_extractor.extract_offer_content(offer_pdf_path)
            if not extraction_result["success"]:
                return {"success": False, "error": "Échec de l'extraction PDF", "details": extraction_result}
            
            # Analyse de l'offre
            offer_text = extraction_result["raw_text"]
            analysis_result = self.offer_analyzer.analyze_offer(offer_text)
            
            # Stocker le résultat
            self.current_session["offer_analysis"] = {
                "file_path": offer_pdf_path,
                "extraction": extraction_result,
                "analysis": analysis_result
            }
            
            self.logger.info(f"Offre analysée - Titre: {analysis_result.get('job_title', 'Non identifié')}")
            self.logger.info(f"Score de complétude: {analysis_result.get('completeness_score', 0):.2f}")
            
            return {"success": True, "analysis": analysis_result}
            
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement de l'offre: {e}")
            return {"success": False, "error": str(e)}
    
    def _process_cvs_parallel(self, cv_pdf_paths: List[str]) -> Dict[str, Any]:
        """Traite les CVs en parallèle"""
        try:
            self.logger.info(f"Traitement de {len(cv_pdf_paths)} CVs en parallèle...")
            
            # Filtrer les fichiers existants
            existing_paths = [path for path in cv_pdf_paths if os.path.exists(path)]
            missing_files = len(cv_pdf_paths) - len(existing_paths)
            
            if missing_files > 0:
                self.logger.warning(f"{missing_files} fichiers CV non trouvés")
            
            if not existing_paths:
                return {"success": False, "error": "Aucun fichier CV valide trouvé"}
            
            # Traitement parallèle
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Soumettre les tâches
                future_to_path = {
                    executor.submit(self._process_single_cv, path, idx): path 
                    for idx, path in enumerate(existing_paths)
                }
                
                processed_cvs = []
                failed_cvs = []
                
                # Récupérer les résultats
                for future in as_completed(future_to_path):
                    cv_path = future_to_path[future]
                    try:
                        result = future.result()
                        if result["success"]:
                            processed_cvs.append(result)
                        else:
                            failed_cvs.append({"path": cv_path, "error": result.get("error")})
                    except Exception as e:
                        failed_cvs.append({"path": cv_path, "error": str(e)})
            
            # Stocker les résultats
            self.current_session["cvs_analyses"] = processed_cvs
            
            self.logger.info(f"CVs traités avec succès: {len(processed_cvs)}")
            if failed_cvs:
                self.logger.warning(f"CVs échoués: {len(failed_cvs)}")
            
            return {
                "success": True, 
                "processed": len(processed_cvs),
                "failed": len(failed_cvs),
                "failed_details": failed_cvs
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement parallèle des CVs: {e}")
            return {"success": False, "error": str(e)}
    
    def _process_single_cv(self, cv_path: str, cv_index: int) -> Dict[str, Any]:
        """Traite un CV individuel"""
        try:
            cv_id = f"cv_{cv_index + 1}"
            self.logger.info(f"Traitement du CV {cv_id}: {os.path.basename(cv_path)}")
            
            # Extraction du texte
            extraction_result = self.pdf_extractor.extract_cv_content(cv_path)
            if not extraction_result["success"]:
                return {"success": False, "error": "Échec de l'extraction PDF", "details": extraction_result}
            
            # Analyse du CV
            cv_text = extraction_result["raw_text"]
            analysis_result = self.cv_analyzer.analyze_cv(cv_text, cv_id)
            
            result = {
                "success": True,
                "cv_id": cv_id,
                "file_path": cv_path,
                "file_name": os.path.basename(cv_path),
                "extraction": extraction_result,
                "analysis": analysis_result
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du CV {cv_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_matching_scores(self) -> Dict[str, Any]:
        """Calcule les scores de compatibilité pour tous les CVs"""
        try:
            self.logger.info("Calcul des scores de compatibilité...")
            
            if not self.current_session["offer_analysis"]:
                return {"success": False, "error": "Aucune offre analysée"}
            
            if not self.current_session["cvs_analyses"]:
                return {"success": False, "error": "Aucun CV analysé"}
            
            offer_analysis = self.current_session["offer_analysis"]["analysis"]
            
            # Préparer les analyses de CV pour le matcher
            cv_analyses = [cv["analysis"] for cv in self.current_session["cvs_analyses"]]
            
            # Calculer les scores de matching
            matching_results = self.matcher.process_multiple_matches(offer_analysis, cv_analyses)
            
            # Enrichir les résultats avec les informations des fichiers
            for i, match_result in enumerate(matching_results):
                cv_data = self.current_session["cvs_analyses"][i]
                match_result["file_info"] = {
                    "file_name": cv_data["file_name"],
                    "file_path": cv_data["file_path"]
                }
            
            # Stocker les résultats
            self.current_session["matching_results"] = matching_results
            
            # Statistiques des scores
            scores = [result["global_score"] for result in matching_results]
            score_stats = {
                "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "excellent_matches": len([s for s in scores if s >= 0.8]),
                "good_matches": len([s for s in scores if 0.6 <= s < 0.8]),
                "average_matches": len([s for s in scores if 0.4 <= s < 0.6]),
                "poor_matches": len([s for s in scores if s < 0.4])
            }
            
            self.logger.info(f"Scores calculés - Moyenne: {score_stats['average_score']}")
            self.logger.info(f"Excellents matchs: {score_stats['excellent_matches']}")
            
            return {"success": True, "score_stats": score_stats}
            
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul des scores: {e}")
            return {"success": False, "error": str(e)}
    
    def get_results_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des résultats"""
        if not self.current_session["matching_results"]:
            return {"error": "Aucun résultat disponible"}
        
        # Top 5 des meilleurs candidats
        top_candidates = self.current_session["matching_results"][:5]
        
        summary = {
            "session_id": self.current_session["session_id"],
            "offer_info": {
                "title": self.current_session["offer_analysis"]["analysis"].get("job_title", "Non identifié"),
                "completeness_score": self.current_session["offer_analysis"]["analysis"].get("completeness_score", 0)
            },
            "processing_stats": self.current_session.get("processing_stats", {}),
            "top_candidates": [
                {
                    "rank": i + 1,
                    "name": candidate["cv_info"]["name"],
                    "file_name": candidate["file_info"]["file_name"],
                    "global_score": candidate["global_score"],
                    "match_level": candidate["match_level"],
                    "experience_years": candidate["cv_info"]["experience_years"],
                    "key_strengths": candidate["strengths"][:3]  # Top 3 strengths
                }
                for i, candidate in enumerate(top_candidates)
            ]
        }
        
        return summary
    
    def get_detailed_results(self) -> Dict[str, Any]:
        """Retourne les résultats détaillés complets"""
        return {
            "session_info": {
                "session_id": self.current_session["session_id"],
                "timestamp": self.current_session["timestamp"],
                "processing_stats": self.current_session.get("processing_stats", {})
            },
            "offer_analysis": self.current_session["offer_analysis"],
            "cvs_analyses": self.current_session["cvs_analyses"],
            "matching_results": self.current_session["matching_results"]
        }
    
    def get_candidate_detail(self, cv_id: str) -> Optional[Dict[str, Any]]:
        """Retourne les détails d'un candidat spécifique"""
        for result in self.current_session["matching_results"]:
            if result["cv_info"]["cv_id"] == cv_id:
                return result
        return None
    
    def _create_success_response(self) -> Dict[str, Any]:
        """Crée une réponse de succès"""
        return {
            "success": True,
            "session_id": self.current_session["session_id"],
            "message": "Traitement terminé avec succès",
            "summary": self.get_results_summary(),
            "processing_stats": self.current_session.get("processing_stats", {})
        }
    
    def _create_error_response(self, message: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une réponse d'erreur"""
        return {
            "success": False,
            "error": message,
            "details": details,
            "session_id": self.current_session.get("session_id"),
            "timestamp": time.time()
        }

    def export_results_to_csv(self, output_path: str) -> bool:
        """Exporte les résultats vers un fichier CSV"""
        try:
            try:
                import pandas as pd
            except ImportError:
                self.logger.error("pandas non disponible pour l'export CSV")
                return False

            if not self.current_session["matching_results"]:
                return False
            
            # Préparer les données pour l'export
            export_data = []
            for result in self.current_session["matching_results"]:
                row = {
                    "Rang": result.get("rank", 0),
                    "Nom_Candidat": result["cv_info"]["name"],
                    "Fichier_CV": result["file_info"]["file_name"],
                    "Score_Global": result["global_score"],
                    "Niveau_Correspondance": result["match_level"],
                    "Années_Experience": result["cv_info"]["experience_years"],
                    "Score_Competences_Techniques": result["detailed_scores"]["technical_skills"],
                    "Score_Experience": result["detailed_scores"]["experience_level"],
                    "Score_Formation": result["detailed_scores"]["education"],
                    "Score_Langues": result["detailed_scores"]["languages"],
                    "Points_Forts": "; ".join(result["strengths"]),
                    "Lacunes": "; ".join(result["gaps"]),
                    "Recommandations": "; ".join(result["recommendations"])
                }
                export_data.append(row)
            
            # Créer le DataFrame et exporter
            df = pd.DataFrame(export_data)
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            self.logger.info(f"Résultats exportés vers: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'export CSV: {e}")
            return False