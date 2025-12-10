# TC Translator - Terminology Controlled Translation System

A translation system that preserves domain-specific terminology during translation by using controlled glossaries.

## Overview

Terminex wraps Google Translate API with terminology substitution capabilities. It ensures that specialized terms (medical, agricultural, scientific, etc.) are translated consistently using predefined glossaries rather than relying on generic machine translation.

## Features

- **Domain-specific terminology preservation**: Uses CSV glossaries to maintain accurate translations
- **Multi-domain support**: Separate glossaries for different domains (agriculture, science, medical, etc.)
- **Multi-language support**: Automatically detects available languages from CSV filenames
- **Google Translate API compatible**: Mimics the same API interface for easy integration
- **Automatic fallback**: Falls back to standard translation for terms not in glossaries

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/tc-translator.git
cd tc-translator

# Install dependencies
pip install -r requirements.txt
```

## CSV Glossary Format

Place your glossary CSV files in the `glossaries/` directory with the naming convention:
```
{domain}_terms_{language}.csv
```

Examples:
- `agric_terms_twi.csv`
- `science_terms_ga.csv`
- `medical_terms_ewe.csv`

CSV structure:
```csv
id,term,translation
1,abattoir,aboa kum fie
2,acaricide,nkramamoadi kum aduro
```

## Usage

### Basic Usage

```python
from tc-translator import Terminex

# Initialize translator
translator = Terminex()

# Translate with terminology preservation
result = translator.translate(
    "The abattoir uses acaricide for pest control",
    target_language="twi",
    domain="agric"
)

print(result.translated_text)
print(f"Terms substituted: {result.terms_used}")
```

### Available Languages and Domains

```python
# Check available languages
print(translator.available_languages())

# Check available domains
print(translator.available_domains())

# Check domains for specific language
print(translator.available_domains(language="twi"))
```

### Advanced Usage

```python
# Translate without domain (uses all available glossaries for that language)
result = translator.translate(
    "Plant the seeds in the acre-foot area",
    target_language="twi"
)

# Translate with source language specification
result = translator.translate(
    "Text to translate",
    source_language="en",
    target_language="twi",
    domain="science"
)

# Get detailed information
print(result.original_text)
print(result.translated_text)
print(result.terms_used)  # List of terms that were substituted
print(result.source_language)
print(result.target_language)
```

### API-Compatible Interface

For compatibility with existing Google Translate code:

```python
from tc-translator import translate

# Simple translation
result = translate("The abattoir processes livestock", dest="twi", domain="agric")
print(result.text)

# Batch translation
texts = ["abattoir management", "acaricide application"]
results = translate(texts, dest="twi", domain="agric")
for r in results:
    print(r.text)
```

## How It Works

1. **Preprocessing**: Scans input text for terms in the glossary and replaces them with unique placeholders `<1>`, `<2>`, etc.
2. **Translation**: Sends the placeholder-filled text to Google Translate
3. **Post-processing**: Replaces placeholders in the translated text with the corresponding terminology translations from the CSV

## Directory Structure

```
tc-translator/
├── tc-translator/
│   ├── __init__.py
│   ├── translator.py
│   ├── glossary_manager.py
│   └── utils.py
├── glossaries/
│   ├── agric_terms_twi.csv
│   ├── science_terms_twi.csv
│   └── ...
├── tests/
│   └── test_translator.py
├── examples/
│   └── basic_usage.py
├── requirements.txt
├── setup.py
└── README.md
```

## Requirements

- Python 3.7+
- googletrans==4.0.0rc1 (or googletrans-py==4.0.0)
- pandas

## Contributing

Contributions are welcome! Please feel free to submit glossary files for additional languages and domains.

## License

MIT License
