import re
import spacy
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

class CVAnalyzerAgent:
    """Agent spécialisé dans l'analyse et la structuration des CVs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            self.nlp = spacy.load("fr_core_news_sm")
        except OSError:
            self.logger.warning("Modèle spaCy français non trouvé, utilisation d'un modèle basique")
            self.nlp = None
        
        # Dictionnaires de compétences techniques (réutilisés de l'agent offres)
        self.technical_skills = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'scala'],
            'web': ['html', 'css', 'react', 'angular', 'vue', 'nodejs', 'express', 'django', 'flask'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible'],
            'data': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'spark', 'hadoop'],
            'tools': ['git', 'jenkins', 'jira', 'confluence', 'tableau', 'power bi', 'excel']
        }
        
        # Patterns pour extraire les informations personnelles
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'(?:\+33|0)[1-9](?:[0-9]{8})'
        
        # Diplômes et formations
        self.education_patterns = [
            r'bac\+?[0-9]', r'master', r'licence', r'doctorat', r'phd',
            r'ingénieur', r'école d\'ingénieur', r'grande école',
            r'dut', r'bts', r'iut', r'mba'
        ]
        
        # Mots-clés pour les sections
        self.section_keywords = {
            'experience': ['expérience', 'experience', 'emploi', 'poste', 'fonction', 'carrière'],
            'education': ['formation', 'éducation', 'diplôme', 'études', 'cursus', 'scolarité'],
            'skills': ['compétences', 'savoir-faire', 'expertise', 'aptitudes', 'capacités'],
            'languages': ['langues', 'language', 'idiomes'],
            'projects': ['projets', 'réalisations', 'achievements']
        }
        
        self.logger.info("Agent Analyseur CV initialisé")
    
    def analyze_cv(self, cv_content: str, cv_id: str = None) -> Dict[str, Any]:
        """
        Analyse complète d'un CV
        
        Args:
            cv_content: Texte du CV
            cv_id: Identifiant unique du CV
            
        Returns:
            Dict avec l'analyse structurée du CV
        """
        analysis = {
            "cv_id": cv_id,
            "personal_info": self._extract_personal_info(cv_content),
            "technical_skills": self._extract_technical_skills(cv_content),
            "soft_skills": self._extract_soft_skills(cv_content),
            "experience": self._extract_experience(cv_content),
            "education": self._extract_education(cv_content),
            "languages": self._extract_languages(cv_content),
            "projects": self._extract_projects(cv_content),
            "certifications": self._extract_certifications(cv_content),
            "total_experience_years": self._calculate_total_experience(cv_content),
            "profile_summary": self._extract_profile_summary(cv_content)
        }
        
        # Score de complétude du CV
        analysis["completeness_score"] = self._calculate_completeness_score(analysis)
        
        # Analyse des points forts
        analysis["strengths"] = self._identify_strengths(analysis)
        
        return analysis
    
    def _extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extrait les informations personnelles"""
        personal_info = {
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "location": self._extract_location(text)
        }
        return personal_info
    
    def _extract_name(self, text: str) -> str:
        """Extrait le nom du candidat"""
        lines = text.split('\n')
        
        # Le nom est souvent dans les premières lignes
        for line in lines[:5]:
            line = line.strip()
            # Éviter les lignes avec email, téléphone, etc.
            if (len(line) > 3 and len(line) < 50 and 
                not re.search(self.email_pattern, line) and
                not re.search(self.phone_pattern, line) and
                not any(keyword in line.lower() for keyword in ['cv', 'curriculum', 'vitae', 'résumé'])):
                
                # Vérifier si la ligne contient probablement un nom
                words = line.split()
                if len(words) >= 2 and all(word.isalpha() or word.replace('-', '').isalpha() for word in words):
                    return line
        
        return "Nom non identifié"
    
    def _extract_email(self, text: str) -> str:
        """Extrait l'adresse email"""
        match = re.search(self.email_pattern, text)
        return match.group(0) if match else "Email non trouvé"
    
    def _extract_phone(self, text: str) -> str:
        """Extrait le numéro de téléphone"""
        match = re.search(self.phone_pattern, text)
        return match.group(0) if match else "Téléphone non trouvé"
    
    def _extract_location(self, text: str) -> str:
        """Extrait la localisation"""
        # Villes françaises courantes
        cities = ['paris', 'lyon', 'marseille', 'toulouse', 'nice', 'nantes', 
                 'strasbourg', 'bordeaux', 'lille', 'rennes', 'reims', 'grenoble']
        
        text_lower = text.lower()
        for city in cities:
            if city in text_lower:
                return city.capitalize()
        
        # Patterns pour extraire la localisation
        location_patterns = [
            r'ville\s*:?\s*([^\n\r]+)',
            r'localisation\s*:?\s*([^\n\r]+)',
            r'adresse\s*:?\s*([^\n\r]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Localisation non spécifiée"
    
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
            'gestion du stress', 'esprit critique', 'initiative', 'polyvalence',
            'curiosité', 'persévérance', 'empathie', 'négociation'
        ]
        
        found_soft_skills = []
        text_lower = text.lower()
        
        for skill in soft_skills_keywords:
            if skill in text_lower:
                found_soft_skills.append(skill)
        
        return found_soft_skills
    
    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extrait l'expérience professionnelle"""
        experiences = []
        
        # Patterns pour identifier les expériences
        experience_patterns = [
            r'(\d{4})\s*-?\s*(\d{4}|\w+)?\s*:?\s*([^\n\r]+)',
            r'(\w+\s+\d{4})\s*-?\s*(\w+\s+\d{4}|\w+)?\s*:?\s*([^\n\r]+)'
        ]
        
        lines = text.split('\n')
        current_experience = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Chercher des dates dans la ligne
            date_match = re.search(r'(\d{4})', line)
            if date_match:
                # Possible début d'expérience
                year = int(date_match.group(1))
                if 1990 <= year <= datetime.now().year:
                    # Extraire le titre du poste et l'entreprise
                    job_info = self._parse_job_line(line)
                    if job_info:
                        experiences.append(job_info)
        
        return experiences
    
    def _parse_job_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse une ligne d'expérience professionnelle"""
        # Patterns courants pour les expériences
        patterns = [
            r'(\d{4})\s*-\s*(\d{4}|\w+)?\s*:?\s*(.+?)(?:\s+chez\s+(.+?))?$',
            r'(.+?)\s+chez\s+(.+?)\s+\((\d{4})\s*-\s*(\d{4}|\w+)?\)',
            r'(.+?)\s+-\s+(.+?)\s+\((\d{4})\s*-\s*(\d{4}|\w+)?\)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return {
                    "position": match.group(1).strip() if len(match.groups()) > 0 else "Poste non spécifié",
                    "company": match.group(2).strip() if len(match.groups()) > 1 else "Entreprise non spécifiée",
                    "start_year": match.group(3).strip() if len(match.groups()) > 2 else None,
                    "end_year": match.group(4).strip() if len(match.groups()) > 3 else "Présent",
                    "raw_text": line
                }
        
        return None
    
    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extrait la formation"""
        education = []
        text_lower = text.lower()
        
        for pattern in self.education_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                # Chercher la ligne complète contenant ce diplôme
                start_pos = match.start()
                # Trouver le début et la fin de la ligne
                line_start = text.rfind('\n', 0, start_pos) + 1
                line_end = text.find('\n', match.end())
                if line_end == -1:
                    line_end = len(text)
                
                line = text[line_start:line_end].strip()
                
                education.append({
                    "degree": match.group(0),
                    "institution": self._extract_institution_from_line(line),
                    "year": self._extract_year_from_line(line),
                    "raw_text": line
                })
        
        return education
    
    def _extract_institution_from_line(self, line: str) -> str:
        """Extrait l'institution d'une ligne de formation"""
        # Mots-clés d'institutions
        institution_keywords = ['université', 'école', 'institut', 'iut', 'lycée', 'collège']
        
        for keyword in institution_keywords:
            if keyword in line.lower():
                # Extraire le nom de l'institution autour du mot-clé
                words = line.split()
                for i, word in enumerate(words):
                    if keyword in word.lower():
                        # Prendre quelques mots autour
                        start = max(0, i-1)
                        end = min(len(words), i+3)
                        return ' '.join(words[start:end])
        
        return "Institution non spécifiée"
    
    def _extract_year_from_line(self, line: str) -> Optional[int]:
        """Extrait l'année d'une ligne de formation"""
        year_match = re.search(r'(\d{4})', line)
        if year_match:
            year = int(year_match.group(1))
            if 1990 <= year <= datetime.now().year:
                return year
        return None
    
    def _extract_languages(self, text: str) -> List[Dict[str, str]]:
        """Extrait les langues maîtrisées"""
        languages = []
        text_lower = text.lower()
        
        language_patterns = {
            'français': r'français|french',
            'anglais': r'anglais|english',
            'espagnol': r'espagnol|spanish',
            'allemand': r'allemand|german',
            'italien': r'italien|italian',
            'chinois': r'chinois|chinese',
            'japonais': r'japonais|japanese'
        }
        
        level_patterns = {
            'natif': r'natif|native|langue maternelle',
            'bilingue': r'bilingue|bilingual',
            'courant': r'courant|fluent',
            'intermédiaire': r'intermédiaire|intermediate',
            'débutant': r'débutant|beginner|notions'
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
    
    def _extract_projects(self, text: str) -> List[str]:
        """Extrait les projets mentionnés"""
        projects = []
        
        # Patterns pour identifier les projets
        project_patterns = [
            r'projet\s*:?\s*([^\n\r]+)',
            r'réalisation\s*:?\s*([^\n\r]+)',
            r'développement\s+de\s+([^\n\r]+)'
        ]
        
        for pattern in project_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                projects.append(match.group(1).strip())
        
        return projects
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extrait les certifications"""
        certifications = []
        
        cert_patterns = [
            r'certification\s*:?\s*([^\n\r]+)',
            r'certifié[e]?\s+([^\n\r]+)',
            r'aws\s+certified',
            r'microsoft\s+certified',
            r'google\s+certified'
        ]
        
        for pattern in cert_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                certifications.append(match.group(0).strip())
        
        return certifications
    
    def _calculate_total_experience(self, text: str) -> float:
        """Calcule le nombre total d'années d'expérience"""
        years = []
        
        # Chercher tous les patterns d'années d'expérience
        year_patterns = [
            r'(\d+)\s*ans?\s+d[\'']expérience',
            r'expérience\s+de\s+(\d+)\s*ans?',
            r'(\d+)\s*années?\s+d[\'']expérience'
        ]
        
        for pattern in year_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    years.append(float(match.group(1)))
                except ValueError:
                    continue
        
        # Si pas de mention explicite, essayer de calculer à partir des dates d'expérience
        if not years:
            experiences = self._extract_experience(text)
            total_years = 0
            for exp in experiences:
                if exp.get('start_year') and exp.get('end_year'):
                    try:
                        start = int(exp['start_year'])
                        end = int(exp['end_year']) if exp['end_year'] != 'Présent' else datetime.now().year
                        total_years += max(0, end - start)
                    except (ValueError, TypeError):
                        continue
            return total_years
        
        return max(years) if years else 0
    
    def _extract_profile_summary(self, text: str) -> str:
        """Extrait le résumé de profil/objectif"""
        summary_patterns = [
            r'profil\s*:?\s*([^\n\r]+(?:\n[^\n\r]+)*)',
            r'objectif\s*:?\s*([^\n\r]+(?:\n[^\n\r]+)*)',
            r'résumé\s*:?\s*([^\n\r]+(?:\n[^\n\r]+)*)',
            r'à propos\s*:?\s*([^\n\r]+(?:\n[^\n\r]+)*)'
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                summary = match.group(1).strip()
                # Limiter la longueur du résumé
                if len(summary) > 500:
                    summary = summary[:500] + "..."
                return summary
        
        # Si pas de section spécifique, prendre les premiers paragraphes significatifs
        lines = text.split('\n')
        summary_lines = []
        for line in lines[5:15]:  # Éviter les infos personnelles en début
            line = line.strip()
            if len(line) > 50 and not re.search(self.email_pattern, line):
                summary_lines.append(line)
                if len(' '.join(summary_lines)) > 300:
                    break
        
        return ' '.join(summary_lines) if summary_lines else "Résumé non disponible"
    
    def _calculate_completeness_score(self, analysis: Dict[str, Any]) -> float:
        """Calcule un score de complétude du CV (0-1)"""
        fields_to_check = [
            'personal_info', 'technical_skills', 'experience',
            'education', 'total_experience_years'
        ]
        
        filled_fields = 0
        total_fields = len(fields_to_check)
        
        for field in fields_to_check:
            if field in analysis and analysis[field]:
                if field == 'personal_info':
                    # Vérifier si au moins nom et email sont présents
                    personal = analysis[field]
                    if (personal.get('name') != "Nom non identifié" and 
                        personal.get('email') != "Email non trouvé"):
                        filled_fields += 1
                elif isinstance(analysis[field], (list, dict)):
                    if len(analysis[field]) > 0:
                        filled_fields += 1
                elif isinstance(analysis[field], (int, float)):
                    if analysis[field] > 0:
                        filled_fields += 1
                else:
                    filled_fields += 1
        
        return filled_fields / total_fields
    
    def _identify_strengths(self, analysis: Dict[str, Any]) -> List[str]:
        """Identifie les points forts du candidat"""
        strengths = []
        
        # Analyser l'expérience
        exp_years = analysis.get('total_experience_years', 0)
        if exp_years >= 5:
            strengths.append("Expérience solide")
        elif exp_years >= 2:
            strengths.append("Expérience significative")
        
        # Analyser les compétences techniques
        tech_skills = analysis.get('technical_skills', {})
        total_tech_skills = sum(len(skills) for skills in tech_skills.values())
        if total_tech_skills >= 10:
            strengths.append("Large palette de compétences techniques")
        elif total_tech_skills >= 5:
            strengths.append("Bonnes compétences techniques")
        
        # Analyser les langues
        languages = analysis.get('languages', [])
        if len(languages) >= 2:
            strengths.append("Compétences linguistiques")
        
        # Analyser la formation
        education = analysis.get('education', [])
        if any('master' in edu.get('degree', '').lower() or 'ingénieur' in edu.get('degree', '').lower() 
               for edu in education):
            strengths.append("Formation supérieure")
        
        return strengths