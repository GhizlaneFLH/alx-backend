import PyPDF2
import pdfplumber
import re
import logging
from typing import Dict, Any, Optional

class PDFExtractorAgent:
    """Agent spécialisé dans l'extraction de texte des fichiers PDF"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Agent Extracteur PDF initialisé")
    
    def extract_text_from_pdf(self, pdf_path: str, method: str = "pdfplumber") -> Dict[str, Any]:
        """
        Extrait le texte d'un fichier PDF avec gestion d'erreurs
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            method: Méthode d'extraction ("pdfplumber" ou "pypdf2")
            
        Returns:
            Dict contenant le texte extrait et les métadonnées
        """
        try:
            if method == "pdfplumber":
                return self._extract_with_pdfplumber(pdf_path)
            else:
                return self._extract_with_pypdf2(pdf_path)
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction PDF: {e}")
            return {
                "success": False,
                "text": "",
                "error": str(e),
                "pages": 0
            }
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> Dict[str, Any]:
        """Extraction avec pdfplumber (meilleure qualité)"""
        text_content = ""
        pages_count = 0
        
        with pdfplumber.open(pdf_path) as pdf:
            pages_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
        
        return {
            "success": True,
            "text": self._clean_text(text_content),
            "pages": pages_count,
            "method": "pdfplumber"
        }
    
    def _extract_with_pypdf2(self, pdf_path: str) -> Dict[str, Any]:
        """Extraction avec PyPDF2 (fallback)"""
        text_content = ""
        pages_count = 0
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pages_count = len(pdf_reader.pages)
            
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
        
        return {
            "success": True,
            "text": self._clean_text(text_content),
            "pages": pages_count,
            "method": "pypdf2"
        }
    
    def _clean_text(self, text: str) -> str:
        """Nettoie et normalise le texte extrait"""
        if not text:
            return ""
        
        # Supprime les caractères de contrôle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
        
        # Normalise les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprime les espaces en début/fin
        text = text.strip()
        
        return text
    
    def extract_offer_content(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extrait et structure le contenu d'une offre d'emploi
        
        Returns:
            Dict avec le contenu structuré de l'offre
        """
        extraction_result = self.extract_text_from_pdf(pdf_path)
        
        if not extraction_result["success"]:
            return extraction_result
        
        text = extraction_result["text"]
        
        # Structure spécifique pour les offres d'emploi
        structured_content = {
            "success": True,
            "raw_text": text,
            "document_type": "offer",
            "metadata": {
                "pages": extraction_result["pages"],
                "method": extraction_result["method"],
                "text_length": len(text)
            }
        }
        
        return structured_content
    
    def extract_cv_content(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extrait et structure le contenu d'un CV
        
        Returns:
            Dict avec le contenu structuré du CV
        """
        extraction_result = self.extract_text_from_pdf(pdf_path)
        
        if not extraction_result["success"]:
            return extraction_result
        
        text = extraction_result["text"]
        
        # Structure spécifique pour les CVs
        structured_content = {
            "success": True,
            "raw_text": text,
            "document_type": "cv",
            "metadata": {
                "pages": extraction_result["pages"],
                "method": extraction_result["method"],
                "text_length": len(text)
            }
        }
        
        return structured_content
    
    def process_multiple_cvs(self, cv_paths: list) -> Dict[str, Any]:
        """
        Traite plusieurs CVs en parallèle
        
        Args:
            cv_paths: Liste des chemins vers les CVs
            
        Returns:
            Dict avec tous les CVs traités
        """
        results = {
            "success": True,
            "cvs": [],
            "total_processed": 0,
            "failed": []
        }
        
        for idx, cv_path in enumerate(cv_paths):
            self.logger.info(f"Traitement du CV {idx + 1}/{len(cv_paths)}: {cv_path}")
            
            cv_result = self.extract_cv_content(cv_path)
            
            if cv_result["success"]:
                cv_result["cv_id"] = f"cv_{idx + 1}"
                cv_result["file_path"] = cv_path
                results["cvs"].append(cv_result)
                results["total_processed"] += 1
            else:
                results["failed"].append({
                    "cv_path": cv_path,
                    "error": cv_result.get("error", "Erreur inconnue")
                })
        
        if results["total_processed"] == 0:
            results["success"] = False
        
        return results