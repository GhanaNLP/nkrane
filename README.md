# Nkrane

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Nkrane - Google Translate (nkrane-gt) is a Python library that enhances Google Translate with **custom terminology control** for low-resource languages, with a focus on Ghanaian languages.

It solves the problem of inconsistent translations for critical terms by allowing you to enforce specific translations for nouns and noun phrases while letting Google Translate handle the grammatical structure.

---

## 🌍 Why Nkrane?

Standard machine translation often struggles with:
- **Inconsistent terminology** - The same word translated differently in different contexts
- **Named entities** - People names, place names, cultural terms mistranslated
- **Domain-specific vocabulary** - Technical, medical, or legal terms poorly handled
- **Low-resource languages** - Limited training data for African languages

**Nkrane solves this by:**
1. **You provide a CSV file** with your preferred term translations (required)
2. Nkrane extracts noun phrases from source text using NLP (spaCy)
3. Matches them against your terminology dictionary
4. Replaces content words with placeholders (preserving articles like "a", "the")
5. Translates with Google Translate
6. Restores your terminology with proper case preservation and sentence capitalization

**You control the terminology. Google Translate handles the grammar.**

---

## 📦 Installation

### From Source

```bash
git clone https://github.com/ghananlp/nkrane-gt.git
cd nkrane-gt
pip install -e .
```

### Requirements

```bash
pip install pandas spacy requests
python -m spacy download en_core_web_sm
```

---

## 🎯 Quick Start

### Step 1: Create Your Terminology CSV

Create a CSV file with your preferred translations:

```bash
cat > my_terms.csv << EOF
text,text_translated
house,efie
car,kaa
market,gua
station,gyinabea
school,sukuu
teacher,okyerɛkyerɛfo
student,asuafo
EOF
```

### Step 2: Translate with Your Terminology

```python
from nkrane_gt import NkraneTranslator

# Initialize with your custom terminology
translator = NkraneTranslator(
    target_lang='ak',  # Akan/Twi
    terminology_source='my_terms.csv'
)

# Translate
result = translator.translate("I want to buy a house and a car.")
print(result['text'])
# Output: "Mepɛ sɛ metɔ efie ne kaa."

print(f"Terms replaced: {result['replacements_count']}")
# Output: Terms replaced: 2
```

### Batch Translation

```python
# Create terminology for batch translation
cat > batch_terms.csv << EOF
text,text_translated
house,efie
car,kaa
school,sukuu
student,asuafo
EOF

translator = NkraneTranslator(
    target_lang='ak',
    terminology_source='batch_terms.csv'
)

texts = [
    "I want to buy a house today.",
    "The car is very fast.",
    "The students go to school."
]

results = translator.batch_translate(texts)
for r in results:
    print(f"{r['original']}")
    print(f"  → {r['text']}")
    print(f"  (Replaced {r['replacements_count']} terms)\n")
```
```

---

## 📚 How It Works

### The Translation Pipeline

```
Input: "The station is in Accra."
         ↓
1. Noun Phrase Extraction (spaCy)
   → Finds: "The station" (noun chunk), "Accra" (proper noun)
   → Filters stopwords: "The station" → "station" (content word)
   → Keeps "The" as leading stopword
         ↓
2. Dictionary Matching (Your CSV)
   → "station" in CSV? ✓ → "gyinabea"
   → "Accra" in CSV? ✗ → Keep as is
         ↓
3. Preprocessing (Stopwords preserved)
   → "The <1> is in Accra."
         ↓
4. Google Translate
   → "The <1> is in Accra." → "<1> no wɔ Accra"
         ↓
5. Postprocessing (Case-matched + Sentence caps)
   → "<1> no wɔ Accra" → "Gyinabea no wɔ Accra"
   → (Capitalized because at sentence start)
         ↓
Output: "Gyinabea no wɔ Accra."
```

### Key Features

✅ **Stopword Preservation** - Articles like "a", "the" stay in place  
✅ **Case Matching** - Translations match original capitalization  
✅ **Sentence Capitalization** - First word of sentences auto-capitalized  
✅ **Multi-sentence Support** - Unique placeholders across all sentences  
✅ **Direct Translation** - Simple English → Target language translation

---

## 🛠️ Advanced Usage

### Custom Terminology Format

Your CSV can use various column headers (auto-detected):

**Option 1: Standard headers**
```csv
text,text_translated
house,efie
car,kaa
```

**Option 2: Alternative headers**
```csv
english,translation
house,efie
car,kaa
```

**Option 3: Any two columns**
```csv
source_term,target_term
house,efie
car,kaa
```

Supported header names:
- **Source**: `text`, `english`, `source`, `term`, `word`
- **Target**: `text_translated`, `translation`, `target`, `translated`

### Multi-word Terms and Phrases

```csv
text,text_translated
big house,efie kɛse
small car,kaa ketewa
middle lane,mfimfini kwan
trading space,aguadibea
```

### Detailed Translation Results

```python
result = translator.translate("The station is in Accra.")

print("Original:", result['original'])
print("Preprocessed:", result['preprocessed'])
print("Google output:", result['google_translation'])
print("Final:", result['text'])
print("Terms replaced:", result['replacements_count'])
```

**Output:**
```
Original: The station is in Accra.
Preprocessed: The <1> is in Accra.
Google output: <1> no wɔ Accra
Final: Gyinabea no wɔ Accra.
Terms replaced: 1
```

---

## 🌐 Supported Languages

### Target Languages
- **ak** - Akan/Twi (Ghana)
- **ee** - Ewe (Ghana, Togo)
- **gaa** - Ga (Ghana)
- Plus any language supported by Google Translate

### Source Languages
- **en** - English (default)
- Any language supported by Google Translate

---

## 📋 Best Practices

### 1. Focus on Key Terms
Don't translate everything - focus on:
- Domain-specific vocabulary
- Proper nouns (names, places)
- Technical terms
- Words with multiple meanings

### 2. Use Multi-word Phrases
```csv
text,text_translated
high school,ntoaso sukuu
emergency room,ntɛm ayaresabea
trading space,aguadibea
```

### 3. Test Your Terminology
```python
# Check what terms were actually replaced
result = translator.translate("The student goes to high school.")
print("Replaced:", result['replaced_terms'])
print("Count:", result['replacements_count'])
```

### 4. Preserve Natural Language
Let Google Translate handle:
- Grammar and sentence structure
- Verb conjugations
- Pronouns and function words
- Context-dependent translations

---

## 🎓 Example Use Cases

### News Translation
```python
# Create terminology for your news domain
cat > news_terms.csv << EOF
text,text_translated
parliament,mmarahyɛ bagua
minister,ɔsoafoɔ
president,ɔmampanyin
election,abatoɔ
government,aban
EOF

translator = NkraneTranslator(
    target_lang='ak',
    terminology_source='news_terms.csv'
)
```

### Educational Content
```python
# School-related terminology
cat > education_terms.csv << EOF
text,text_translated
teacher,okyerɛkyerɛfo
student,asuafo
classroom,adesuadan
homework,fie adwuma
examination,sɔhwɛ
EOF
```

### Medical Documentation
```python
# Medical terminology
cat > medical_terms.csv << EOF
text,text_translated
hospital,ayaresabea
doctor,dɔkota
patient,ɔyarefo
medicine,aduro
treatment,ayaresa
EOF
```

---

## 🔍 Troubleshooting

### Terms Not Being Replaced?

**Check if spaCy recognizes it as a noun:**
```python
import spacy
nlp = spacy.load("en_core_web_sm")
doc = nlp("The big house is red.")
for chunk in doc.noun_chunks:
    print(f"Chunk: '{chunk.text}'")
# Output: Chunk: 'The big house'
```

**Make sure your CSV has the exact content words:**
```csv
# Correct - uses content words
text,text_translated
big house,efie kɛse

# Won't match "the big house" because "the" is filtered out
```

### Case Issues?

The system automatically handles:
- ✅ Sentence-initial capitalization
- ✅ Title Case preservation
- ✅ ALL CAPS preservation

```python
# All of these work correctly:
"The house" → "Efie"  (capitalized)
"the house" → "efie"  (lowercase)
"THE HOUSE" → "EFIE"  (all caps)
```

---

## 📖 Citation

If you use Nkrane in your research, please cite:

```bibtex
@software{nkrane_gt,
  title={Nkrane: Enhanced Machine Translation with Custom Terminology Control},
  author={GhanaNLP},
  year={2026},
  url={https://github.com/ghananlp/nkrane-gt}
}
```

---

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Additional language support
- Improved noun phrase extraction
- Domain-specific terminology packs
- Performance optimizations

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- Built on [Google Translate](https://translate.google.com/) for base translation
- Uses [spaCy](https://spacy.io/) for NLP processing
- Created for better African language translation tools

**"Nkrane"** means "termites" in Akan/Twi - small but powerful workers, just like this library working to improve translation quality term by term.

---

## 📧 Contact

- Issues: [GitHub Issues](https://github.com/ghananlp/nkrane-gt/issues)
- Email: natural.language.processing.gh@gmail.com
- Website: [GhanaNLP](https://ghananlp.org)

---

## ⚡ Quick Reference

```python
# Basic usage with terminology
translator = NkraneTranslator(
    target_lang='ak',
    terminology_source='my_terms.csv'
)

# Different source language
translator = NkraneTranslator(
    target_lang='ak',
    src_lang='fr',  # French to Akan
    terminology_source='my_terms.csv'
)

# Translate and see what was replaced
result = translator.translate("Your text here")
print(result['text'])
print(f"Replaced {result['replacements_count']} terms")
```
