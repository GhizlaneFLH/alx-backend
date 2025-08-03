import re
import spacy
import logging
from typing import Dict, List, Any, Optional
import pandas as pd

class OfferAnalyzerAgent:
    """Agent spécialisé dans l'analyse et la structuration des offres d'emploi"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            self.nlp = spacy.load("fr_core_news_sm")
        except OSError:
            self.logger.warning("Modèle spaCy français non trouvé, utilisation d'un modèle basique")
            self.nlp = None
        
        # Dictionnaires de compétences techniques
        self.technical_skills = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'scala'],
            'web': ['html', 'css', 'react', 'angular', 'vue', 'nodejs', 'express', 'django', 'flask'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible'],
            'data': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'spark', 'hadoop'],
            'tools': ['git', 'jenkins', 'jira', 'confluence', 'tableau', 'power bi', 'excel']
        }
        
        # Niveaux d'expérience
        self.experience_patterns = {
            'junior': r'(?:junior|débutant|0-2\s*ans?|moins de 3 ans)',
            'medior': r'(?:médior|intermédiaire|2-5\s*ans?|3-6\s*ans?)',
            'senior': r'(?:senior|expérimenté|5\+?\s*ans?|plus de 5 ans|6\+?\s*ans?)'
        }
        
        # Diplômes et formations
        self.education_patterns = [
            r'bac\+?[0-9]', r'master', r'licence', r'doctorat', r'phd',
            r'ingénieur', r'école d\'ingénieur', r'grande école',
            r'dut', r'bts', r'iut'
        ]
        
        self.logger.info("Agent Analyseur d'Offres initialisé")
    
    def analyze_offer(self, offer_content: str) -> Dict[str, Any]:
        """
        Analyse complète d'une offre d'emploi
        
        Args:
            offer_content: Texte de l'offre d'emploi
            
        Returns:
            Dict avec l'analyse structurée de l'offre
        """
        analysis = {
            "job_title": self._extract_job_title(offer_content),
            "technical_skills": self._extract_technical_skills(offer_content),
            "soft_skills": self._extract_soft_skills(offer_content),
            "experience_level": self._extract_experience_level(offer_content),
            "education_requirements": self._extract_education_requirements(offer_content),
            "languages": self._extract_languages(offer_content),
            "location": self._extract_location(offer_content),
            "contract_type": self._extract_contract_type(offer_content),
            "salary_range": self._extract_salary_info(offer_content),
            "company_info": self._extract_company_info(offer_content),
            "must_have_skills": self._extract_must_have_skills(offer_content),
            "nice_to_have_skills": self._extract_nice_to_have_skills(offer_content),
            "responsibilities": self._extract_responsibilities(offer_content),
            "benefits": self._extract_benefits(offer_content)
        }
        
        # Score de complétude de l'offre
        analysis["completeness_score"] = self._calculate_completeness_score(analysis)
        
        return analysis
    
    def _extract_job_title(self, text: str) -> str:
        """Extrait le titre du poste"""
        # Patterns courants pour les titres de poste
        title_patterns = [
            r'poste\s*:?\s*([^\n\r]+)',
            r'titre\s*:?\s*([^\n\r]+)',
            r'recherchons?\s+un[e]?\s+([^\n\r]+)',
            r'recrute\s+un[e]?\s+([^\n\r]+)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Si aucun pattern trouvé, prendre les premiers mots significatifs
        lines = text.split('\n')
        for line in lines[:5]:  # Chercher dans les 5 premières lignes
            if len(line.strip()) > 10 and len(line.strip()) < 100:
                return line.strip()
        
        return "Titre non identifié"
    
    def _extract_technical_skills(self, text: str) -> Dict[str, List[str]]:
        """Extrait les compétences techniques par catégorie"""
        text_lower = text.lower()
        found_skills = {}
        
        for category, skills in self.technical_skills.items():
            found_skills[category] = []
            for skill in skills:
                if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                    found_skills[category].append(skill)
        
        return found_skills
    
    def _extract_soft_skills(self, text: str) -> List[str]:
        """Extrait les compétences comportementales"""
        soft_skills_keywords = [
            'communication', 'leadership', 'travail en équipe', 'autonomie',
            'créativité', 'adaptabilité', 'rigueur', 'organisation',
            'gestion du stress', 'esprit critique', 'initiative'
        ]
        
        found_soft_skills = []
        text_lower = text.lower()
        
        for skill in soft_skills_keywords:
            if skill in text_lower:
                found_soft_skills.append(skill)
        
        return found_soft_skills
    
    def _extract_experience_level(self, text: str) -> Dict[str, Any]:
        """Extrait le niveau d'expérience requis"""
        text_lower = text.lower()
        
        for level, pattern in self.experience_patterns.items():
            if re.search(pattern, text_lower):
                # Extraire le nombre d'années si possible
                years_match = re.search(r'(\d+)(?:-(\d+))?\s*ans?', text_lower)
                years_range = None
                if years_match:
                    min_years = int(years_match.group(1))
                    max_years = int(years_match.group(2)) if years_match.group(2) else min_years
                    years_range = (min_years, max_years)
                
                return {
                    "level": level,
                    "years_range": years_range,
                    "raw_text": years_match.group(0) if years_match else None
                }
        
        return {"level": "non_specifie", "years_range": None, "raw_text": None}
    
    def _extract_education_requirements(self, text: str) -> List[str]:
        """Extrait les exigences de formation/diplômes"""
        found_education = []
        text_lower = text.lower()
        
        for pattern in self.education_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                found_education.append(match.group(0))
        
        return list(set(found_education))  # Supprimer les doublons
    
    def _extract_languages(self, text: str) -> List[Dict[str, str]]:
        """Extrait les langues requises"""
        languages = []
        text_lower = text.lower()
        
        language_patterns = {
            'français': r'français|french',
            'anglais': r'anglais|english',
            'espagnol': r'espagnol|spanish',
            'allemand': r'allemand|german',
            'italien': r'italien|italian'
        }
        
        level_patterns = {
            'courant': r'courant|fluent',
            'bilingue': r'bilingue|bilingual',
            'natif': r'natif|native',
            'intermédiaire': r'intermédiaire|intermediate',
            'débutant': r'débutant|beginner'
        }
        
        for lang, pattern in language_patterns.items():
            if re.search(pattern, text_lower):
                # Chercher le niveau
                level = "non_specifie"
                for level_name, level_pattern in level_patterns.items():
                    if re.search(level_pattern, text_lower):
                        level = level_name
                        break
                
                languages.append({"language": lang, "level": level})
        
        return languages
    
    def _extract_location(self, text: str) -> str:
        """Extrait la localisation du poste"""
        location_patterns = [
            r'lieu\s*:?\s*([^\n\r]+)',
            r'localisation\s*:?\s*([^\n\r]+)',
            r'ville\s*:?\s*([^\n\r]+)',
            r'région\s*:?\s*([^\n\r]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Villes françaises courantes
        cities = ['paris', 'lyon', 'marseille', 'toulouse', 'nice', 'nantes', 'strasbourg', 'bordeaux']
        text_lower = text.lower()
        
        for city in cities:
            if city in text_lower:
                return city.capitalize()
        
        return "Non spécifié"
    
    def _extract_contract_type(self, text: str) -> str:
        """Extrait le type de contrat"""
        contract_patterns = {
            'CDI': r'\bcdi\b',
            'CDD': r'\bcdd\b',
            'Stage': r'\bstage\b',
            'Freelance': r'\bfreelance\b|\bindépendant\b',
            'Interim': r'\bintérim\b|\bintérimaire\b'
        }
        
        text_lower = text.lower()
        for contract_type, pattern in contract_patterns.items():
            if re.search(pattern, text_lower):
                return contract_type
        
        return "Non spécifié"
    
    def _extract_salary_info(self, text: str) -> Dict[str, Any]:
        """Extrait les informations de salaire"""
        salary_patterns = [
            r'(\d+(?:\s*\d+)*)\s*(?:€|euros?)\s*(?:par\s*an|annuel)',
            r'(\d+(?:\s*\d+)*)\s*k€?\s*(?:par\s*an|annuel)?',
            r'salaire\s*:?\s*(\d+(?:\s*\d+)*)\s*(?:€|k€?)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(' ', '')
                try:
                    amount = int(amount_str)
                    # Si le montant est en milliers (k€)
                    if 'k' in match.group(0).lower():
                        amount *= 1000
                    return {
                        "amount": amount,
                        "raw_text": match.group(0),
                        "currency": "EUR"
                    }
                except ValueError:
                    continue
        
        return {"amount": None, "raw_text": None, "currency": None}
    
    def _extract_company_info(self, text: str) -> Dict[str, str]:
        """Extrait les informations sur l'entreprise"""
        company_patterns = [
            r'entreprise\s*:?\s*([^\n\r]+)',
            r'société\s*:?\s*([^\n\r]+)',
            r'compagnie\s*:?\s*([^\n\r]+)'
        ]
        
        company_name = "Non spécifié"
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                break
        
        return {"name": company_name}
    
    def _extract_must_have_skills(self, text: str) -> List[str]:
        """Extrait les compétences obligatoires"""
        must_have_patterns = [
            r'exigé[es]?\s*:?\s*([^\n\r]+)',
            r'obligatoire[s]?\s*:?\s*([^\n\r]+)',
            r'requis[es]?\s*:?\s*([^\n\r]+)',
            r'indispensable[s]?\s*:?\s*([^\n\r]+)'
        ]
        
        must_have_skills = []
        for pattern in must_have_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skills_text = match.group(1)
                # Diviser par virgules ou points
                skills = re.split(r'[,;]', skills_text)
                must_have_skills.extend([skill.strip() for skill in skills if skill.strip()])
        
        return must_have_skills
    
    def _extract_nice_to_have_skills(self, text: str) -> List[str]:
        """Extrait les compétences souhaitées mais non obligatoires"""
        nice_to_have_patterns = [
            r'souhaité[es]?\s*:?\s*([^\n\r]+)',
            r'apprécié[es]?\s*:?\s*([^\n\r]+)',
            r'un plus\s*:?\s*([^\n\r]+)',
            r'bonus\s*:?\s*([^\n\r]+)'
        ]
        
        nice_to_have_skills = []
        for pattern in nice_to_have_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skills_text = match.group(1)
                skills = re.split(r'[,;]', skills_text)
                nice_to_have_skills.extend([skill.strip() for skill in skills if skill.strip()])
        
        return nice_to_have_skills
    
    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extrait les responsabilités du poste"""
        responsibility_patterns = [
            r'missions?\s*:?\s*([^\n\r]+)',
            r'responsabilités?\s*:?\s*([^\n\r]+)',
            r'tâches?\s*:?\s*([^\n\r]+)',
            r'activités?\s*:?\s*([^\n\r]+)'
        ]
        
        responsibilities = []
        for pattern in responsibility_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                resp_text = match.group(1)
                responsibilities.append(resp_text.strip())
        
        return responsibilities
    
    def _extract_benefits(self, text: str) -> List[str]:
        """Extrait les avantages proposés"""
        benefits_patterns = [
            r'avantages?\s*:?\s*([^\n\r]+)',
            r'bénéfices?\s*:?\s*([^\n\r]+)',
            r'nous proposons\s*:?\s*([^\n\r]+)'
        ]
        
        benefits = []
        for pattern in benefits_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                benefit_text = match.group(1)
                benefit_items = re.split(r'[,;]', benefit_text)
                benefits.extend([item.strip() for item in benefit_items if item.strip()])
        
        return benefits
    
    def _calculate_completeness_score(self, analysis: Dict[str, Any]) -> float:
        """Calcule un score de complétude de l'offre (0-1)"""
        fields_to_check = [
            'job_title', 'technical_skills', 'experience_level',
            'education_requirements', 'location', 'contract_type'
        ]
        
        filled_fields = 0
        for field in fields_to_check:
            if field in analysis and analysis[field]:
                if isinstance(analysis[field], (list, dict)):
                    if len(analysis[field]) > 0:
                        filled_fields += 1
                elif isinstance(analysis[field], str):
                    if analysis[field] != "Non spécifié" and analysis[field] != "Non identifié":
                        filled_fields += 1
                else:
                    filled_fields += 1
        
        return filled_fields / len(fields_to_check)