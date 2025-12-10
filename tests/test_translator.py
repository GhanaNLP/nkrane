"""
Unit tests for Terminex translator
"""

import unittest
import os
import tempfile
from pathlib import Path
import pandas as pd

from terminex import Terminex
from terminex.glossary_manager import GlossaryManager


class TestGlossaryManager(unittest.TestCase):
    """Test the glossary manager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test glossaries
        self.test_dir = tempfile.mkdtemp()
        
        # Create sample CSV files
        agric_data = pd.DataFrame({
            'id': [1, 2, 3],
            'term': ['abattoir', 'acaricide', 'acreage'],
            'translation': ['aboa kum fie', 'nkramamoadi kum aduro', 'asase dodoɔ']
        })
        agric_data.to_csv(Path(self.test_dir) / 'agric_terms_twi.csv', index=False)
        
        science_data = pd.DataFrame({
            'id': [10, 11],
            'term': ['molecule', 'atom'],
            'translation': ['molecule_twi', 'atom_twi']
        })
        science_data.to_csv(Path(self.test_dir) / 'science_terms_twi.csv', index=False)
        
        self.manager = GlossaryManager(self.test_dir)
    
    def test_load_glossaries(self):
        """Test that glossaries are loaded correctly"""
        self.assertIn('twi', self.manager.glossaries)
        self.assertIn('agric', self.manager.glossaries['twi'])
        self.assertIn('science', self.manager.glossaries['twi'])
    
    def test_available_languages(self):
        """Test getting available languages"""
        languages = self.manager.available_languages()
        self.assertIn('twi', languages)
    
    def test_available_domains(self):
        """Test getting available domains"""
        domains = self.manager.available_domains()
        self.assertIn('agric', domains)
        self.assertIn('science', domains)
        
        twi_domains = self.manager.available_domains('twi')
        self.assertEqual(len(twi_domains), 2)
    
    def test_find_terms_in_text(self):
        """Test finding terms in text"""
        text = "The abattoir processes livestock using acaricide"
        terms = self.manager.find_terms_in_text(text, 'twi', 'agric')
        
        self.assertEqual(len(terms), 2)
        term_names = [t[0] for t in terms]
        self.assertIn('abattoir', term_names)
        self.assertIn('acaricide', term_names)
    
    def test_get_glossary(self):
        """Test getting specific glossary"""
        glossary = self.manager.get_glossary('twi', 'agric')
        self.assertEqual(len(glossary), 3)
        
        # Test combined glossaries
        combined = self.manager.get_glossary('twi')
        self.assertEqual(len(combined), 5)


class TestTerminex(unittest.TestCase):
    """Test the main Terminex translator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create sample glossary
        agric_data = pd.DataFrame({
            'id': [1, 2],
            'term': ['abattoir', 'acaricide'],
            'translation': ['aboa kum fie', 'nkramamoadi kum aduro']
        })
        agric_data.to_csv(Path(self.test_dir) / 'agric_terms_twi.csv', index=False)
        
        self.translator = Terminex(self.test_dir)
    
    def test_term_substitution(self):
        """Test that terms are properly substituted"""
        result = self.translator.translate(
            "The abattoir uses acaricide",
            target_language='twi',
            domain='agric'
        )
        
        # Check that terms were found and used
        self.assertEqual(len(result.terms_used), 2)
        
        # Check that translations are present
        self.assertIn('aboa kum fie', result.translated_text)
        self.assertIn('nkramamoadi kum aduro', result.translated_text)
    
    def test_batch_translation(self):
        """Test batch translation"""
        texts = ["The abattoir is new", "Use acaricide carefully"]
        results = self.translator.translate(texts, target_language='twi', domain='agric')
        
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results, list)
    
    def test_case_insensitive_matching(self):
        """Test that term matching is case insensitive"""
        result = self.translator.translate(
            "The ABATTOIR uses Acaricide",
            target_language='twi',
            domain='agric'
        )
        
        self.assertEqual(len(result.terms_used), 2)


if __name__ == '__main__':
    unittest.main()
