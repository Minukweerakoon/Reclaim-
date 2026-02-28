import spacy
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer

print("Downloading spaCy models...")
spacy.cli.download("en_core_web_md")
spacy.cli.download("xx_ent_wiki_sm")

print("Downloading BERT model...")
AutoTokenizer.from_pretrained('bert-base-multilingual-cased')
AutoModel.from_pretrained('bert-base-multilingual-cased')

print("Downloading sentence transformer model...")
SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

print("All models downloaded successfully.")
