import logging
import re
from typing import Dict, List, Any, Tuple
import math
from fuzzywuzzy import fuzz

class MatcherAgent:
    """Agent spécialisé dans le calcul de scores de compatibilité CV-Offres (version simplifiée)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Poids pour les différents critères de matching
        self.weights = {
            'technical_skills': 0.30,
            'experience_level': 0.25,
            'education': 0.15,
            'languages': 0.10,
            'soft_skills': 0.10,
            'semantic_similarity': 0.10
        }
        
        self.logger.info("Agent Matcher initialisé (version simplifiée)")
    
    def calculate_compatibility_score(self, offer_analysis: Dict[str, Any], 
                                    cv_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule le score de compatibilité entre une offre et un CV
        
        Args:
            offer_analysis: Analyse structurée de l'offre
            cv_analysis: Analyse structurée du CV
            
        Returns:
            Dict avec le score global et les scores détaillés
        """
        scores = {}
        
        # 1. Score des compétences techniques
        scores['technical_skills'] = self._score_technical_skills(
            offer_analysis.get('technical_skills', {}),
            cv_analysis.get('technical_skills', {})
        )
        
        # 2. Score de l'expérience
        scores['experience_level'] = self._score_experience_level(
            offer_analysis.get('experience_level', {}),
            cv_analysis.get('total_experience_years', 0)
        )
        
        # 3. Score de la formation
        scores['education'] = self._score_education(
            offer_analysis.get('education_requirements', []),
            cv_analysis.get('education', [])
        )
        
        # 4. Score des langues
        scores['languages'] = self._score_languages(
            offer_analysis.get('languages', []),
            cv_analysis.get('languages', [])
        )
        
        # 5. Score des compétences comportementales
        scores['soft_skills'] = self._score_soft_skills(
            offer_analysis.get('soft_skills', []),
            cv_analysis.get('soft_skills', [])
        )
        
        # 6. Similarité sémantique simplifiée
        scores['semantic_similarity'] = self._score_semantic_similarity_simple(
            offer_analysis,
            cv_analysis
        )
        
        # Calcul du score global pondéré
        global_score = sum(scores[key] * self.weights[key] for key in scores.keys())
        
        # Analyse détaillée des correspondances
        detailed_analysis = self._generate_detailed_analysis(offer_analysis, cv_analysis, scores)
        
        return {
            'global_score': round(global_score, 2),
            'detailed_scores': scores,
            'match_level': self._get_match_level(global_score),
            'detailed_analysis': detailed_analysis,
            'strengths': self._identify_matching_strengths(offer_analysis, cv_analysis),
            'gaps': self._identify_gaps(offer_analysis, cv_analysis),
            'recommendations': self._generate_recommendations(offer_analysis, cv_analysis, scores)
        }
    
    def _score_technical_skills(self, offer_skills: Dict[str, List[str]], 
                               cv_skills: Dict[str, List[str]]) -> float:
        """Score les compétences techniques"""
        if not offer_skills:
            return 1.0  # Si pas d'exigences, score parfait
        
        total_offer_skills = sum(len(skills) for skills in offer_skills.values())
        if total_offer_skills == 0:
            return 1.0
        
        matched_skills = 0
        
        for category, required_skills in offer_skills.items():
            cv_category_skills = cv_skills.get(category, [])
            
            for required_skill in required_skills:
                # Correspondance exacte
                if required_skill in cv_category_skills:
                    matched_skills += 1
                else:
                    # Correspondance floue pour gérer les variantes
                    for cv_skill in cv_category_skills:
                        similarity = fuzz.ratio(required_skill.lower(), cv_skill.lower())
                        if similarity >= 80:  # 80% de similarité
                            matched_skills += 0.8
                            break
        
        return min(1.0, matched_skills / total_offer_skills)
    
    def _score_experience_level(self, offer_experience: Dict[str, Any], 
                               cv_experience_years: float) -> float:
        """Score le niveau d'expérience"""
        if not offer_experience or offer_experience.get('level') == 'non_specifie':
            return 1.0
        
        required_level = offer_experience.get('level')
        years_range = offer_experience.get('years_range')
        
        if years_range:
            min_years, max_years = years_range
            if cv_experience_years >= min_years:
                if cv_experience_years <= max_years:
                    return 1.0  # Dans la fourchette parfaite
                else:
                    # Surqualifié mais acceptable
                    excess = cv_experience_years - max_years
                    return max(0.7, 1.0 - (excess * 0.05))  # Pénalité légère pour surqualification
            else:
                # Sous-qualifié
                deficit = min_years - cv_experience_years
                return max(0.0, 1.0 - (deficit * 0.15))  # Pénalité plus forte
        
        # Correspondance par niveau
        level_scores = {
            'junior': (0, 3),
            'medior': (2, 6),
            'senior': (5, float('inf'))
        }
        
        if required_level in level_scores:
            min_exp, max_exp = level_scores[required_level]
            if cv_experience_years >= min_exp:
                if max_exp == float('inf') or cv_experience_years <= max_exp:
                    return 1.0
                else:
                    return 0.8  # Surqualifié
            else:
                return max(0.2, (cv_experience_years / min_exp) * 0.8)
        
        return 0.5  # Score neutre si impossible à évaluer
    
    def _score_education(self, offer_education: List[str], 
                        cv_education: List[Dict[str, Any]]) -> float:
        """Score la formation"""
        if not offer_education:
            return 1.0
        
        cv_degrees = [edu.get('degree', '').lower() for edu in cv_education]
        
        matched = 0
        for required_ed in offer_education:
            required_ed_lower = required_ed.lower()
            
            # Correspondance exacte
            if any(required_ed_lower in degree for degree in cv_degrees):
                matched += 1
            else:
                # Correspondance par niveau
                if self._education_level_match(required_ed_lower, cv_degrees):
                    matched += 0.8
        
        return min(1.0, matched / len(offer_education))
    
    def _education_level_match(self, required: str, cv_degrees: List[str]) -> bool:
        """Vérifie la correspondance par niveau d'éducation"""
        education_hierarchy = {
            'bac': 1, 'bac+2': 2, 'bac+3': 3, 'licence': 3,
            'bac+4': 4, 'bac+5': 5, 'master': 5, 'ingénieur': 5,
            'doctorat': 6, 'phd': 6
        }
        
        required_level = 0
        for key, level in education_hierarchy.items():
            if key in required:
                required_level = level
                break
        
        cv_max_level = 0
        for degree in cv_degrees:
            for key, level in education_hierarchy.items():
                if key in degree:
                    cv_max_level = max(cv_max_level, level)
        
        return cv_max_level >= required_level
    
    def _score_languages(self, offer_languages: List[Dict[str, str]], 
                        cv_languages: List[Dict[str, str]]) -> float:
        """Score les langues"""
        if not offer_languages:
            return 1.0
        
        total_score = 0
        for required_lang in offer_languages:
            req_language = required_lang.get('language', '').lower()
            req_level = required_lang.get('level', 'non_specifie')
            
            # Chercher cette langue dans le CV
            cv_lang_found = None
            for cv_lang in cv_languages:
                if cv_lang.get('language', '').lower() == req_language:
                    cv_lang_found = cv_lang
                    break
            
            if cv_lang_found:
                cv_level = cv_lang_found.get('level', 'non_specifie')
                level_score = self._compare_language_levels(req_level, cv_level)
                total_score += level_score
            else:
                total_score += 0  # Langue non trouvée
        
        return total_score / len(offer_languages)
    
    def _compare_language_levels(self, required_level: str, cv_level: str) -> float:
        """Compare les niveaux de langue"""
        level_hierarchy = {
            'non_specifie': 0,
            'débutant': 1,
            'intermédiaire': 2,
            'courant': 3,
            'bilingue': 4,
            'natif': 5
        }
        
        req_score = level_hierarchy.get(required_level, 0)
        cv_score = level_hierarchy.get(cv_level, 0)
        
        if cv_score >= req_score:
            return 1.0
        elif cv_score == req_score - 1:
            return 0.7  # Un niveau en dessous
        else:
            return 0.3  # Niveau insuffisant
    
    def _score_soft_skills(self, offer_soft_skills: List[str], 
                          cv_soft_skills: List[str]) -> float:
        """Score les compétences comportementales"""
        if not offer_soft_skills:
            return 1.0
        
        matched = 0
        for required_skill in offer_soft_skills:
            for cv_skill in cv_soft_skills:
                similarity = fuzz.ratio(required_skill.lower(), cv_skill.lower())
                if similarity >= 70:
                    matched += 1
                    break
        
        return min(1.0, matched / len(offer_soft_skills))
    
    def _score_semantic_similarity_simple(self, offer_analysis: Dict[str, Any], 
                                         cv_analysis: Dict[str, Any]) -> float:
        """Calcule une similarité sémantique simplifiée basée sur les mots-clés communs"""
        try:
            # Extraire les mots-clés pertinents
            offer_keywords = self._extract_keywords(offer_analysis)
            cv_keywords = self._extract_keywords(cv_analysis)
            
            if not offer_keywords or not cv_keywords:
                return 0.5
            
            # Calculer la similarité par intersection
            common_keywords = offer_keywords.intersection(cv_keywords)
            union_keywords = offer_keywords.union(cv_keywords)
            
            # Score de Jaccard
            jaccard_score = len(common_keywords) / len(union_keywords) if union_keywords else 0
            
            return jaccard_score
        
        except Exception as e:
            self.logger.warning(f"Erreur dans le calcul de similarité sémantique: {e}")
            return 0.5
    
    def _extract_keywords(self, analysis: Dict[str, Any]) -> set:
        """Extrait les mots-clés pertinents d'une analyse"""
        keywords = set()
        
        # Ajouter les compétences techniques
        if 'technical_skills' in analysis:
            for category, skills in analysis['technical_skills'].items():
                keywords.update(skill.lower() for skill in skills)
        
        # Ajouter les compétences comportementales
        if 'soft_skills' in analysis:
            keywords.update(skill.lower() for skill in analysis['soft_skills'])
        
        # Ajouter le titre du poste (pour les offres)
        if 'job_title' in analysis:
            keywords.update(word.lower() for word in analysis['job_title'].split() if len(word) > 3)
        
        # Ajouter les responsabilités (pour les offres)
        if 'responsibilities' in analysis:
            for resp in analysis['responsibilities']:
                keywords.update(word.lower() for word in resp.split() if len(word) > 3)
        
        return keywords
    
    def _get_match_level(self, score: float) -> str:
        """Détermine le niveau de correspondance"""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Bon"
        elif score >= 0.4:
            return "Moyen"
        else:
            return "Faible"
    
    def _generate_detailed_analysis(self, offer_analysis: Dict[str, Any], 
                                   cv_analysis: Dict[str, Any], 
                                   scores: Dict[str, float]) -> Dict[str, Any]:
        """Génère une analyse détaillée du matching"""
        return {
            'technical_match': {
                'score': scores['technical_skills'],
                'details': self._analyze_technical_match(
                    offer_analysis.get('technical_skills', {}),
                    cv_analysis.get('technical_skills', {})
                )
            },
            'experience_match': {
                'score': scores['experience_level'],
                'required': offer_analysis.get('experience_level', {}),
                'candidate': cv_analysis.get('total_experience_years', 0)
            },
            'education_match': {
                'score': scores['education'],
                'required': offer_analysis.get('education_requirements', []),
                'candidate': [edu.get('degree') for edu in cv_analysis.get('education', [])]
            }
        }
    
    def _analyze_technical_match(self, offer_skills: Dict[str, List[str]], 
                                cv_skills: Dict[str, List[str]]) -> Dict[str, Any]:
        """Analyse détaillée du matching technique"""
        matched = {}
        missing = {}
        
        for category, required_skills in offer_skills.items():
            cv_category_skills = cv_skills.get(category, [])
            matched[category] = []
            missing[category] = []
            
            for skill in required_skills:
                if skill in cv_category_skills:
                    matched[category].append(skill)
                else:
                    missing[category].append(skill)
        
        return {'matched': matched, 'missing': missing}
    
    def _identify_matching_strengths(self, offer_analysis: Dict[str, Any], 
                                   cv_analysis: Dict[str, Any]) -> List[str]:
        """Identifie les points forts du matching"""
        strengths = []
        
        # Compétences techniques communes
        offer_tech = offer_analysis.get('technical_skills', {})
        cv_tech = cv_analysis.get('technical_skills', {})
        
        common_skills = []
        for category, skills in offer_tech.items():
            cv_skills = cv_tech.get(category, [])
            common_skills.extend([skill for skill in skills if skill in cv_skills])
        
        if len(common_skills) >= 3:
            strengths.append(f"Maîtrise de {len(common_skills)} compétences requises")
        
        # Expérience
        cv_exp = cv_analysis.get('total_experience_years', 0)
        if cv_exp >= 5:
            strengths.append("Expérience professionnelle solide")
        
        return strengths
    
    def _identify_gaps(self, offer_analysis: Dict[str, Any], 
                      cv_analysis: Dict[str, Any]) -> List[str]:
        """Identifie les lacunes"""
        gaps = []
        
        # Compétences techniques manquantes
        offer_tech = offer_analysis.get('technical_skills', {})
        cv_tech = cv_analysis.get('technical_skills', {})
        
        missing_skills = []
        for category, skills in offer_tech.items():
            cv_skills = cv_tech.get(category, [])
            missing_skills.extend([skill for skill in skills if skill not in cv_skills])
        
        if missing_skills:
            gaps.append(f"Compétences manquantes: {', '.join(missing_skills[:3])}")
        
        return gaps
    
    def _generate_recommendations(self, offer_analysis: Dict[str, Any], 
                                cv_analysis: Dict[str, Any], 
                                scores: Dict[str, float]) -> List[str]:
        """Génère des recommandations"""
        recommendations = []
        
        if scores['technical_skills'] < 0.6:
            recommendations.append("Améliorer les compétences techniques requises")
        
        if scores['experience_level'] < 0.5:
            recommendations.append("Acquérir plus d'expérience dans le domaine")
        
        if scores['languages'] < 0.7:
            recommendations.append("Améliorer les compétences linguistiques")
        
        return recommendations
    
    def process_multiple_matches(self, offer_analysis: Dict[str, Any], 
                                cvs_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Traite le matching d'une offre avec plusieurs CVs"""
        results = []
        
        for cv_analysis in cvs_analyses:
            match_result = self.calculate_compatibility_score(offer_analysis, cv_analysis)
            
            # Ajouter les informations du CV
            match_result['cv_info'] = {
                'cv_id': cv_analysis.get('cv_id'),
                'name': cv_analysis.get('personal_info', {}).get('name', 'Nom non identifié'),
                'experience_years': cv_analysis.get('total_experience_years', 0),
                'completeness_score': cv_analysis.get('completeness_score', 0)
            }
            
            results.append(match_result)
        
        # Trier par score de compatibilité décroissant
        results.sort(key=lambda x: x['global_score'], reverse=True)
        
        return results