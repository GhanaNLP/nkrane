# nkrane_gt/terminology_manager.py
import os
import csv
import pickle
import re
import spacy
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import importlib.resources

# Load spaCy model for English
try:
    nlp = spacy.load("en_core_web_sm")
    STOPWORDS = nlp.Defaults.stop_words
    SPACY_AVAILABLE = True
except:
    print("Warning: spaCy model not found. Please install: python -m spacy download en_core_web_sm")
    SPACY_AVAILABLE = False
    STOPWORDS = set()

@dataclass
class Term:
    term: str
    translation: str
    source: str  # 'builtin' or 'user'

class TerminologyManager:
    def __init__(self, target_lang: str, user_csv_path: str = None, use_builtin: bool = True):
        """
        Initialize terminology manager.

        Args:
            target_lang: Target language code (ak, ee, gaa)
            user_csv_path: Path to user's CSV file (optional)
            use_builtin: Whether to use built-in dictionary (default: True)
        """
        self.target_lang = target_lang
        self.terms = {}  # Dictionary: english_term -> translation
        self.sources = {}  # Dictionary: english_term -> source

        if use_builtin:
            self._load_builtin_terms()

        if user_csv_path:
            self._load_user_terms(user_csv_path)

    def _load_builtin_terms(self):
        """Load built-in terms from pickle file."""
        try:
            # Determine which built-in file to load
            if self.target_lang == 'ak':
                pkl_name = 'nouns_ak.pkl'
            elif self.target_lang == 'ee':
                pkl_name = 'nouns_ee.pkl'
            elif self.target_lang == 'gaa':
                pkl_name = 'nouns_gaa.pkl'
            else:
                print(f"Warning: No built-in dictionary for language '{self.target_lang}'")
                return

            # Load from package data using importlib.resources
            try:
                # First try to load as package resource
                with importlib.resources.files('nkrane_gt.data').joinpath(pkl_name).open('rb') as f:
                    builtin_dict = pickle.load(f)
                    print(f"Loaded {len(builtin_dict)} built-in terms for {self.target_lang}")

                    # Add built-in terms
                    for english_term, translation in builtin_dict.items():
                        english_term_lower = english_term.lower()
                        self.terms[english_term_lower] = translation
                        self.sources[english_term_lower] = 'builtin'

            except (FileNotFoundError, ModuleNotFoundError):
                # Fallback to direct file path
                current_dir = os.path.dirname(__file__)
                pkl_path = os.path.join(current_dir, 'data', pkl_name)

                if os.path.exists(pkl_path):
                    with open(pkl_path, 'rb') as f:
                        builtin_dict = pickle.load(f)
                    print(f"Loaded {len(builtin_dict)} built-in terms for {self.target_lang}")

                    # Add built-in terms
                    for english_term, translation in builtin_dict.items():
                        english_term_lower = english_term.lower()
                        self.terms[english_term_lower] = translation
                        self.sources[english_term_lower] = 'builtin'
                else:
                    print(f"Warning: Built-in dictionary not found: {pkl_path}")
                    # Create empty dictionary if file doesn't exist
                    with open(pkl_path, 'wb') as f:
                        pickle.dump({}, f)
                    print(f"Created empty dictionary at: {pkl_path}")

        except Exception as e:
            print(f"Error loading built-in dictionary: {e}")

    def _load_user_terms(self, csv_path: str):
        """Load user terms from CSV file."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Try to detect the delimiter
                sample = f.read(1024)
                f.seek(0)

                # Check for common delimiters
                if ',' in sample:
                    delimiter = ','
                elif ';' in sample:
                    delimiter = ';'
                elif '\t' in sample:
                    delimiter = '\t'
                else:
                    delimiter = ','  # default

                reader = csv.DictReader(f, delimiter=delimiter)
                fieldnames = [f.lower() for f in reader.fieldnames] if reader.fieldnames else []

                # Determine which columns to use
                text_col = None
                trans_col = None

                # Look for text column
                for col in ['text', 'english', 'source', 'term', 'word']:
                    if col in fieldnames:
                        text_col = col
                        break

                # Look for translation column
                for col in ['text_translated', 'translation', 'target', 'translated']:
                    if col in fieldnames:
                        trans_col = col
                        break

                # If not found, use first two columns
                if not text_col or not trans_col:
                    if len(fieldnames) >= 2:
                        text_col = reader.fieldnames[0]
                        trans_col = reader.fieldnames[1]
                    else:
                        print(f"Error: CSV needs at least 2 columns")
                        return

                # Read terms
                user_terms_count = 0
                for row in reader:
                    english_term = row.get(text_col, '').strip().lower()
                    translation = row.get(trans_col, '').strip()

                    if english_term and translation:
                        self.terms[english_term] = translation
                        self.sources[english_term] = 'user'
                        user_terms_count += 1

                print(f"Loaded {user_terms_count} user terms from {csv_path}")

        except Exception as e:
            print(f"Error loading user CSV: {e}")

    def _remove_stopwords(self, phrase: str) -> str:
        """Remove stopwords from a phrase."""
        if not SPACY_AVAILABLE:
            # Simple fallback
            words = phrase.lower().split()
            filtered_words = [w for w in words if w not in STOPWORDS]
            return ' '.join(filtered_words)

        doc = nlp(phrase.lower())
        cleaned_tokens = [token.text for token in doc if not token.is_stop]
        return ' '.join(cleaned_tokens).strip()

    def _extract_noun_phrases(self, text: str) -> List[Dict]:
        """Extract noun phrases from text using spaCy, filtering stopwords."""
        if not SPACY_AVAILABLE:
            # Fallback: extract words that are in our dictionary
            words = re.findall(r'\b\w+\b', text.lower())
            result = []
            for word in words:
                if word in self.terms:
                    # Find position in original text
                    start = text.lower().find(word)
                    if start != -1:
                        result.append({
                            'text': word,
                            'chunk_start': start,
                            'chunk_end': start + len(word),
                            'start': start,
                            'end': start + len(word),
                            'leading_stopwords': '',
                            'trailing_stopwords': ''
                        })
            return result

        doc = nlp(text)
        noun_phrases = []

        # Extract noun chunks and filter stopwords
        for chunk in doc.noun_chunks:
            # Get all tokens in this chunk
            tokens = [token for token in chunk]

            # Check if ALL tokens are stopwords - if so, skip this chunk entirely
            if all(token.is_stop for token in tokens):
                continue

            # Filter out stopwords to get content words
            content_tokens = [token for token in tokens if not token.is_stop]

            # If no content words left (shouldn't happen due to check above, but safety)
            if not content_tokens:
                continue

            # Get the text of content words only
            content_text = ' '.join(token.text for token in content_tokens)

            # Calculate start and end positions for content words only
            first_content = content_tokens[0]
            last_content = content_tokens[-1]
            
            # Extract leading stopwords (between chunk start and first content word)
            leading_stopwords = []
            for token in tokens:
                if token.idx < first_content.idx:
                    leading_stopwords.append(token.text_with_ws)
                else:
                    break
            
            # Extract trailing stopwords (between last content word and chunk end)
            trailing_stopwords = []
            for token in reversed(tokens):
                if token.idx > last_content.idx:
                    trailing_stopwords.insert(0, token.text_with_ws)
                else:
                    break

            noun_phrases.append({
                'text': content_text,  # Only content words, no stopwords
                'full_text': chunk.text,  # Original full phrase with stopwords
                'chunk_start': chunk.start_char,  # Start of the entire chunk (including leading stopwords)
                'chunk_end': chunk.end_char,  # End of the entire chunk (including trailing stopwords)
                'start': first_content.idx,  # Start of first content word
                'end': last_content.idx + len(last_content.text),  # End of last content word
                'root': chunk.root.text,
                'has_stopwords': len(tokens) != len(content_tokens),  # Flag if stopwords were removed
                'leading_stopwords': ''.join(leading_stopwords),  # Stopwords before content
                'trailing_stopwords': ''.join(trailing_stopwords)  # Stopwords after content
            })

        # Also extract standalone proper nouns that weren't in chunks
        covered_spans = set()
        for np in noun_phrases:
            for i in range(np['start'], np['end']):
                covered_spans.add(i)

        for token in doc:
            if token.pos_ in ["PROPN", "NOUN"] and token.idx not in covered_spans:
                # EXTRA CHECK: Skip pronouns like "I" even if tagged as PROPN/NOUN
                # Also skip if it's a stopword
                if not token.is_stop and token.pos_ != "PRON":
                    noun_phrases.append({
                        'text': token.text,
                        'full_text': token.text,
                        'chunk_start': token.idx,
                        'chunk_end': token.idx + len(token.text),
                        'start': token.idx,
                        'end': token.idx + len(token.text),
                        'root': token.text,
                        'has_stopwords': False,
                        'leading_stopwords': '',
                        'trailing_stopwords': ''
                    })

        return noun_phrases

    def preprocess_text(self, text: str) -> Tuple[str, Dict[str, str], Dict[str, str]]:
        """
        Replace noun phrases in text with placeholders.
        Only replaces content words (non-stopwords) from phrases that are found in terminology.
        Stopwords within noun phrases are left in place and not replaced.

        Args:
            text: Input text

        Returns:
            Tuple of (preprocessed_text, placeholder_to_translation, original_cases)
        """
        if not self.terms:
            return text, {}, {}

        # Split text into sentences
        if SPACY_AVAILABLE:
            doc = nlp(text)
            sentences = [sent.text for sent in doc.sents]
            sentence_spans = [(sent.start_char, sent.end_char) for sent in doc.sents]
        else:
            # Simple sentence splitting
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            sentence_spans = []

        all_replacements = {}
        all_original_cases = {}
        processed_sentences = []
        placeholder_counter = 1  # MOVED OUTSIDE - shared across all sentences

        for sent_idx, sentence in enumerate(sentences):
            if not sentence.strip():
                processed_sentences.append(sentence)
                continue

            # Extract noun phrases from this sentence
            noun_phrases = self._extract_noun_phrases(sentence)

            # Filter to only phrases found in our dictionary (using content words)
            matching_phrases = []
            for phrase in noun_phrases:
                phrase_lower = phrase['text'].lower()
                # Try exact match with content words
                if phrase_lower in self.terms:
                    matching_phrases.append(phrase)
                else:
                    # Try without any remaining stopwords (should already be clean, but double-check)
                    cleaned = self._remove_stopwords(phrase_lower)
                    if cleaned and cleaned in self.terms:
                        # Update the phrase info with cleaned version
                        phrase_copy = phrase.copy()
                        phrase_copy['text'] = cleaned
                        matching_phrases.append(phrase_copy)

            # Sort by position (end to start) to avoid replacement issues
            matching_phrases.sort(key=lambda x: x.get('chunk_start', x['start']), reverse=True)

            preprocessed_sentence = sentence
            sentence_replacements = {}
            sentence_original_cases = {}
            # placeholder_counter removed from here - now shared across sentences

            for phrase in matching_phrases:
                phrase_lower = phrase['text'].lower()
                translation = self.terms.get(phrase_lower)

                if translation:
                    placeholder = f"<{placeholder_counter}>"
                    placeholder_counter += 1

                    # Get leading and trailing stopwords
                    leading = phrase.get('leading_stopwords', '')
                    trailing = phrase.get('trailing_stopwords', '')
                    
                    # Replace the ENTIRE chunk (from chunk_start to chunk_end)
                    # with: leading_stopwords + placeholder + trailing_stopwords
                    # This ensures stopwords are preserved in their correct positions
                    chunk_start_pos = phrase.get('chunk_start', phrase['start'])
                    chunk_end_pos = phrase.get('chunk_end', phrase['end'])

                    # Build the replacement: leading stopwords + placeholder + trailing stopwords
                    replacement = leading + placeholder + trailing

                    # Replace the entire chunk
                    preprocessed_sentence = (
                        preprocessed_sentence[:chunk_start_pos] + 
                        replacement + 
                        preprocessed_sentence[chunk_end_pos:]
                    )

                    sentence_replacements[placeholder] = translation
                    # Store both the content words and the full phrase for case preservation
                    sentence_original_cases[placeholder] = {
                        'content': phrase['text'],  # Just "station"
                        'full': phrase.get('full_text', phrase['text']),  # "the station"
                        'leading': leading  # "the "
                    }

            processed_sentences.append(preprocessed_sentence)
            all_replacements.update(sentence_replacements)
            all_original_cases.update(sentence_original_cases)

        # Reconstruct text with processed sentences
        if SPACY_AVAILABLE:
            # Join preserving original structure
            preprocessed_text = ''.join(
                processed_sentences[i] + (text[sentence_spans[i][1]:sentence_spans[i+1][0]] if i < len(sentence_spans) - 1 else '')
                for i in range(len(processed_sentences))
            ) if sentence_spans else ' '.join(processed_sentences)
        else:
            # Simple join
            preprocessed_text = '. '.join(processed_sentences)
            if not preprocessed_text.endswith('.'):
                preprocessed_text += '.'

        return preprocessed_text, all_replacements, all_original_cases

    def postprocess_text(self, text: str, replacements: Dict[str, str], 
                        original_cases: Dict[str, str]) -> str:
        """
        Replace placeholders with translations, preserving case of the ORIGINAL phrase
        and ensuring proper sentence capitalization.

        Args:
            text: Translated text with placeholders
            replacements: Mapping from placeholders to translations
            original_cases: Mapping from placeholders to original case info (can be string or dict)

        Returns:
            Postprocessed text with actual translations
        """
        result = text

        for placeholder, translation in replacements.items():
            case_info = original_cases.get(placeholder, '')
            
            # Handle both old format (string) and new format (dict)
            if isinstance(case_info, dict):
                original_content = case_info.get('content', '')
                original_full = case_info.get('full', '')
                leading_stopword = case_info.get('leading', '')
            else:
                # Old format - just a string
                original_content = case_info
                original_full = case_info
                leading_stopword = ''
            
            # Determine the case to apply based on the full phrase (including leading stopword)
            # This is important for cases like "The station" where "The" is capitalized
            original_to_check = original_full if original_full else original_content
            
            # Find the placeholder in the text to check if it's at sentence start
            import re
            placeholder_pattern = re.escape(placeholder)
            match = re.search(placeholder_pattern, result)
            
            is_sentence_start = False
            if match:
                pos = match.start()
                if pos == 0:
                    is_sentence_start = True
                elif pos >= 2:
                    # Check if preceded by sentence-ending punctuation + space
                    preceding = result[max(0, pos-2):pos]
                    if preceding in ['. ', '! ', '? ']:
                        is_sentence_start = True
            
            # Apply case based on the original phrase
            if original_to_check:
                # Check if the leading stopword (if any) was capitalized
                leading_was_capitalized = False
                if leading_stopword.strip() and leading_stopword.strip()[0].isupper():
                    leading_was_capitalized = True
                
                # Now apply appropriate casing
                if original_to_check.isupper():
                    # Original was ALL UPPERCASE (e.g., "THE HOUSE")
                    translation = translation.upper()
                elif original_content.istitle() or (len(original_content.split()) > 1 and all(word[0].isupper() for word in original_content.split() if word)):
                    # Original content was Title Case (e.g., "Big House")
                    translation = translation.title()
                elif original_content[0].isupper() or leading_was_capitalized:
                    # Original started with uppercase - either the content word itself or the leading stopword
                    # Capitalize first letter of translation
                    if len(translation) > 0:
                        translation = translation[0].upper() + translation[1:].lower()
                else:
                    # Original was all lowercase
                    translation = translation.lower()
            else:
                # Default to lowercase if no case info
                translation = translation.lower()
            
            # If at sentence start, ensure first letter is capitalized (override previous logic)
            if is_sentence_start and len(translation) > 0:
                translation = translation[0].upper() + translation[1:]

            result = result.replace(placeholder, translation)

        # Final pass: ensure sentences start with capital letters
        result = self._ensure_sentence_capitalization(result)
        
        return result
    
    def _ensure_sentence_capitalization(self, text: str) -> str:
        """Ensure that sentences start with capital letters."""
        if not text:
            return text
        
        # Capitalize first character
        result = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        # Capitalize after sentence-ending punctuation
        import re
        # Pattern: sentence-ending punctuation followed by space(s) and a lowercase letter
        pattern = r'([.!?])\s+([a-z])'
        
        def capitalize_match(match):
            return match.group(1) + ' ' + match.group(2).upper()
        
        result = re.sub(pattern, capitalize_match, result)
        
        return result

    def get_terms_count(self) -> Dict[str, int]:
        """Get count of terms by source."""
        counts = {'total': len(self.terms), 'builtin': 0, 'user': 0}
        for source in self.sources.values():
            counts[source] += 1
        return counts
