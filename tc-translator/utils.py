"""
Utility functions for API compatibility with googletrans
"""

from typing import Union, List, Optional
from .translator import Terminex, TranslationResult


# Global translator instance
_global_translator = None


def get_translator():
    """Get or create global translator instance"""
    global _global_translator
    if _global_translator is None:
        _global_translator = Terminex()
    return _global_translator


class TranslationWrapper:
    """Wrapper to mimic googletrans Translated object"""
    
    def __init__(self, result: TranslationResult):
        self.text = result.translated_text
        self.src = result.source_language
        self.dest = result.target_language
        self.origin = result.original_text
        self.pronunciation = None
        self.extra_data = {
            'domain': result.domain,
            'terms_used': result.terms_used
        }


def translate(
    text: Union[str, List[str]],
    dest: str,
    src: str = "auto",
    domain: Optional[str] = None
) -> Union[TranslationWrapper, List[TranslationWrapper]]:
    """
    Translate text using Terminex - API compatible with googletrans
    
    Args:
        text: Text or list of texts to translate
        dest: Destination language code
        src: Source language code (default: 'auto')
        domain: Domain for terminology
        
    Returns:
        Translation result(s) compatible with googletrans API
    """
    translator = get_translator()
    results = translator.translate(text, dest, src, domain)
    
    if isinstance(results, list):
        return [TranslationWrapper(r) for r in results]
    return TranslationWrapper(results)
