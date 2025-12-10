"""
Glossary Manager - Handles loading and managing terminology glossaries
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import pandas as pd


class GlossaryManager:
    """Manages terminology glossaries from CSV files"""
    
    def __init__(self, glossary_dir: str = "glossaries"):
        """
        Initialize the glossary manager
        
        Args:
            glossary_dir: Directory containing glossary CSV files
        """
        self.glossary_dir = Path(glossary_dir)
        self.glossaries: Dict[str, Dict[str, pd.DataFrame]] = {}
        self._load_glossaries()
    
    def _load_glossaries(self):
        """Load all glossary files from the directory"""
        if not self.glossary_dir.exists():
            self.glossary_dir.mkdir(parents=True, exist_ok=True)
            return
        
        # Pattern: {domain}_terms_{language}.csv
        pattern = re.compile(r'^(.+?)_terms_(.+?)\.csv$')
        
        for file_path in self.glossary_dir.glob("*.csv"):
            match = pattern.match(file_path.name)
            if match:
                domain, language = match.groups()
                
                try:
                    df = pd.read_csv(file_path)
                    
                    # Validate required columns
                    if not all(col in df.columns for col in ['id', 'term', 'translation']):
                        print(f"Warning: {file_path.name} missing required columns. Skipping.")
                        continue
                    
                    # Strip whitespace from headers and values
                    df.columns = df.columns.str.strip()
                    df['term'] = df['term'].str.strip()
                    df['translation'] = df['translation'].str.strip()
                    
                    # Store by language then domain
                    if language not in self.glossaries:
                        self.glossaries[language] = {}
                    self.glossaries[language][domain] = df
                    
                    print(f"Loaded glossary: {domain} ({language}) - {len(df)} terms")
                    
                except Exception as e:
                    print(f"Error loading {file_path.name}: {e}")
    
    def get_glossary(self, language: str, domain: str = None) -> pd.DataFrame:
        """
        Get glossary for a specific language and domain
        
        Args:
            language: Target language code
            domain: Domain name (if None, combines all domains for that language)
            
        Returns:
            DataFrame with glossary terms
        """
        if language not in self.glossaries:
            return pd.DataFrame(columns=['id', 'term', 'translation'])
        
        if domain:
            return self.glossaries[language].get(domain, pd.DataFrame(columns=['id', 'term', 'translation']))
        
        # Combine all domains for this language
        all_dfs = list(self.glossaries[language].values())
        if not all_dfs:
            return pd.DataFrame(columns=['id', 'term', 'translation'])
        
        return pd.concat(all_dfs, ignore_index=True)
    
    def available_languages(self) -> List[str]:
        """Get list of available languages"""
        return sorted(list(self.glossaries.keys()))
    
    def available_domains(self, language: str = None) -> List[str]:
        """
        Get list of available domains
        
        Args:
            language: If specified, returns domains for that language only
            
        Returns:
            List of domain names
        """
        if language:
            return sorted(list(self.glossaries.get(language, {}).keys()))
        
        # Get all unique domains across all languages
        domains = set()
        for lang_glossaries in self.glossaries.values():
            domains.update(lang_glossaries.keys())
        return sorted(list(domains))
    
    def find_terms_in_text(self, text: str, language: str, domain: str = None) -> List[Tuple[str, int, str]]:
        """
        Find all glossary terms in the text
        
        Args:
            text: Input text to search
            language: Target language
            domain: Domain to search in (None for all domains)
            
        Returns:
            List of tuples (term, id, translation)
        """
        glossary = self.get_glossary(language, domain)
        if glossary.empty:
            return []
        
        found_terms = []
        text_lower = text.lower()
        
        # Sort by term length (longest first) to match longer terms first
        sorted_glossary = glossary.sort_values(by='term', key=lambda x: x.str.len(), ascending=False)
        
        for _, row in sorted_glossary.iterrows():
            term = row['term'].lower()
            # Use word boundaries for whole word matching
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                found_terms.append((row['term'], row['id'], row['translation']))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in found_terms:
            if term[1] not in seen:  # Check by ID
                seen.add(term[1])
                unique_terms.append(term)
        
        return unique_terms
