import os
import random

import joblib
from json_database import JsonStorageXDG
from nltk import AffixTagger
from nltk.tag import UnigramTagger, BigramTagger, TrigramTagger

db = JsonStorageXDG("nltk_onto5_ngram_tagger", subfolder="ModelZoo/nltk")
MODEL_META = {
    "corpus": "OntoNotes-5.0-NER-BIO",
    "lang": "en",
    "corpus_homepage": "https://github.com/yuchenlin/OntoNotes-5.0-NER-BIO",
    "model_id": "nltk_onto5_ngram_tagger",
    "tagset": "Penn Treebank",
    "algo": "TrigramTagger",
    "backoff_taggers": ["AffixTagger", "UnigramTagger", "BigramTagger",
                        "TrigramTagger"],
    "required_packages": ["nltk"]
}
db.update(MODEL_META)
db.store()
model_path = db.path.replace(".json", ".pkl")


# corpus handling
def read_ontonotes5(corpus_root):
    for root, dirs, files in os.walk(corpus_root):
        for filename in files:
            if filename.endswith(".ner"):
                with open(os.path.join(root, filename), 'r') as file_handle:
                    file_content = file_handle.read()
                    annotated_sentences = file_content.split('\n\n')
                    if not annotated_sentences:
                        continue

                    for annotated_sentence in annotated_sentences:
                        annotated_tokens = [seq for seq in
                                            annotated_sentence.split('\n') if
                                            seq]
                        if not annotated_tokens:
                            continue
                        toks = []
                        for idx, annotated_token in enumerate(
                                annotated_tokens):
                            annotations = annotated_token.split('\t')
                            if not annotations:
                                continue
                            word, tag = annotations[0], annotations[1]
                            toks.append((word, tag))
                        yield toks


corpus_root = "/home/user/PycharmProjects/nlp_workspace/biblioteca/corpora/OntoNotes-5.0-NER-BIO"
reader = read_ontonotes5(corpus_root)

data = list(reader)
random.shuffle(data)
train_data = data[:int(len(data) * 0.9)]
test_data = data[int(len(data) * 0.9):]

# create tagger
affix = AffixTagger(train_data)
uni = UnigramTagger(train_data, backoff=affix)
bi = BigramTagger(train_data, backoff=uni)
tagger = TrigramTagger(train_data, backoff=bi)

a = tagger.evaluate(test_data)

print("Accuracy: ", a)
db["accuracy"] = a
db.store()
joblib.dump(tagger, model_path)
