import json
from typing import Dict, List
from .terminology_manager import TerminologyManager

def list_available_options(terminologies_dir: str = None) -> Dict:
    """List all available domains and languages."""
    manager = TerminologyManager(terminologies_dir)
    
    domains = manager.get_domains()
    languages = manager.get_languages()
    domain_lang_pairs = manager.get_available_domains_languages()
    
    # Group languages by domain
    domains_dict = {}
    for domain, lang in domain_lang_pairs:
        if domain not in domains_dict:
            domains_dict[domain] = []
        domains_dict[domain].append(lang)
    
    return {
        'domains': domains,
        'languages': languages,
        'domain_language_pairs': domain_lang_pairs,
        'domains_with_languages': domains_dict
    }

def export_terminology(domain: str, language: str, output_format: str = 'json',
                      terminologies_dir: str = None):
    """Export terminology for a domain and language."""
    manager = TerminologyManager(terminologies_dir)
    terms_dict = manager.get_terms_for_domain_lang(domain, language)
    
    if not terms_dict:
        raise ValueError(f"No terminology found for {domain}/{language}")
    
    terms_list = [
        {
            'id': term.id,
            'term': term.term,
            'translation': term.translation
        }
        for term in terms_dict.values()
    ]
    
    if output_format == 'json':
        return json.dumps(terms_list, indent=2, ensure_ascii=False)
    elif output_format == 'csv':
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['id', 'term', 'translation'])
        writer.writeheader()
        writer.writerows(terms_list)
        return output.getvalue()
    
    return terms_list

def validate_terminology_file(filepath: str) -> bool:
    """Validate a terminology CSV file."""
    import pandas as pd
    try:
        df = pd.read_csv(filepath)
        
        # Check required columns
        required_columns = ['id', 'term', 'translation']
        if not all(col in df.columns for col in required_columns):
            return False, f"Missing required columns. Required: {required_columns}"
        
        # Check for duplicates
        if df['term'].duplicated().any():
            return False, "Duplicate terms found"
        
        if df['id'].duplicated().any():
            return False, "Duplicate IDs found"
        
        return True, "File is valid"
        
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
