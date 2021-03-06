import random

import joblib
import nltk
from json_database import JsonStorageXDG

import biblioteca
from biblioteca.corpora.external import NILC

db = JsonStorageXDG("nltk_nilc_ngram_tagger", subfolder="ModelZoo/nltk")
MODEL_META = {
    "corpus": "NILC_taggers",
    "corpus_homepage": "http://www.nilc.icmc.usp.br/nilc/tools/nilctaggers.html",
    "model_id": "nltk_nilc_ngram_tagger",
    "tagset": "NILC",
    "tagset_homepage": "http://www.nilc.icmc.usp.br/nilc/download/tagsetcompleto.doc",
    "lang": "pt-br",
    "algo": "TrigramTagger",
    "backoff_taggers": ["AffixTagger", "UnigramTagger", "BigramTagger",
                        "TrigramTagger"],
    "required_packages": ["nltk"]
}
db.update(MODEL_META)
db.store()
model_path = db.path.replace(".json", ".pkl")

biblioteca.download("NILC_taggers")
nilc = NILC()

data = [s for s in nilc.tagged_sentences()]
random.shuffle(data)
cutoff = int(len(data) * 0.9)
train_data = data[:cutoff]
test_data = data[cutoff:]

affix_tagger = nltk.AffixTagger(train_data)
unitagger = nltk.UnigramTagger(train_data, backoff=affix_tagger
                               )

bitagger = nltk.BigramTagger(
    train_data, backoff=unitagger
)
tagger = nltk.TrigramTagger(
    train_data, backoff=bitagger
)

a = tagger.evaluate(test_data)

print("Accuracy of ngram tagger : ", a)  # 0.8661514978057623
db["accuracy"] = a
db.store()
joblib.dump(tagger, model_path)
