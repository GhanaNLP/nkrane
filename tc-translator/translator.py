"""
Main Translator - Handles the translation with terminology substitution
"""

import re
from typing import List, Optional, Union
from dataclasses import dataclass
from googletrans import Translator as GoogleTranslator

from .glossary_manager import GlossaryManager


@dataclass
class TranslationResult:
    """Result of a translation operation"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    domain: Optional[str]
    terms_used: List[dict]  # List of {term, translation, id}


class Terminex:
    """Main translator class with terminology awareness"""
    
    def __init__(self, glossary_dir: str = "glossaries"):
        """
        Initialize the Terminex translator
        
        Args:
            glossary_dir: Directory containing glossary CSV files
        """
        self.glossary_manager = GlossaryManager(glossary_dir)
        self.google_translator = GoogleTranslator()
    
    def translate(
        self,
        text: Union[str, List[str]],
        target_language: str,
        source_language: str = "auto",
        domain: Optional[str] = None
    ) -> Union[TranslationResult, List[TranslationResult]]:
        """
        Translate text with terminology preservation
        
        Args:
            text: Text or list of texts to translate
            target_language: Target language code (e.g., 'twi', 'ga')
            source_language: Source language code (default: 'auto')
            domain: Domain for terminology (e.g., 'agric', 'science')
            
        Returns:
            TranslationResult or list of TranslationResult objects
        """
        # Handle list of texts
        if isinstance(text, list):
            return [self.translate(t, target_language, source_language, domain) for t in text]
        
        # Single text translation
        original_text = text
        
        # Step 1: Find and substitute terms
        terms_found = self.glossary_manager.find_terms_in_text(
            text, target_language, domain
        )
        
        # Create mapping of placeholders to terms
        term_mapping = {}
        processed_text = text
        
        for idx, (term, term_id, translation) in enumerate(terms_found):
            placeholder = f"<{term_id}>"
            # Replace term with placeholder (case-insensitive)
            pattern = r'\b' + re.escape(term) + r'\b'
            processed_text = re.sub(pattern, placeholder, processed_text, flags=re.IGNORECASE)
            term_mapping[placeholder] = {
                'term': term,
                'translation': translation,
                'id': term_id
            }
        
        # Step 2: Translate with Google Translate
        try:
            translation = self.google_translator.translate(
                processed_text,
                src=source_language,
                dest=self._map_language_code(target_language)
            )
            translated_text = translation.text
            detected_src = translation.src
        except Exception as e:
            print(f"Translation error: {e}")
            # Fallback: return original text
            translated_text = processed_text
            detected_src = source_language
        
        # Step 3: Replace placeholders with terminology translations
        for placeholder, term_info in term_mapping.items():
            translated_text = translated_text.replace(placeholder, term_info['translation'])
        
        # Build terms used list
        terms_used = [
            {
                'term': info['term'],
                'translation': info['translation'],
                'id': info['id']
            }
            for info in term_mapping.values()
        ]
        
        return TranslationResult(
            original_text=original_text,
            translated_text=translated_text,
            source_language=detected_src,
            target_language=target_language,
            domain=domain,
            terms_used=terms_used
        )
    
    def _map_language_code(self, code: str) -> str:
        """
        Map custom language codes to Google Translate codes if needed
        
        Args:
            code: Language code from CSV filename
            
        Returns:
            Google Translate compatible language code
        """
        # Add custom mappings here if needed
        # For now, pass through as-is
        # Example: {'twi': 'tw', 'ga': 'gaa'}
        code_mapping = {
            'twi': 'tw',  # Twi (Akan)
            # Add more mappings as needed
        }
        return code_mapping.get(code.lower(), code.lower())
    
    def available_languages(self) -> List[str]:
        """Get list of available languages"""
        return self.glossary_manager.available_languages()
    
    def available_domains(self, language: Optional[str] = None) -> List[str]:
        """
        Get list of available domains
        
        Args:
            language: If specified, returns domains for that language only
            
        Returns:
            List of domain names
        """
        return self.glossary_manager.available_domains(language)
