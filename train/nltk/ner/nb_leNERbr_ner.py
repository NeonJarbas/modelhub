import os
import random

import joblib
from json_database import JsonStorageXDG
from nltk.tag import ClassifierBasedTagger

from neon_classic_modelhub import load_model
from neon_classic_modelhub.chunkers.nltk_chunkers import NamedEntityChunker, \
    conlltags2tree
from neon_classic_modelhub.features.nltk_feats import NltkFeatures

db = JsonStorageXDG("nltk_leNERbr_nb_NER", subfolder="ModelZoo/nltk")
MODEL_META = {
    "corpus": "leNER-Br",
    "lang": "pt-br",
    "corpus_homepage": "https://cic.unb.br/~teodecampos/LeNER-Br/",
    "model_id": "nltk_leNERbr_nb_NER",
    "tagset": "conll_iob",
    "algo": "NaiveBayes",
    "entitíes": ['PESSOA', 'JURISPRUDENCIA', 'LEGISLACAO', 'ORGANIZACAO',
                 'LOCAL', 'TEMPO'],
    "required_packages": ["nltk", "JarbasModelZoo"]

}
db.update(MODEL_META)
db.store()
model_path = db.path.replace(".json", ".pkl")


# corpus handling
def to_conll_iob(annotated_sentence):
    """
    `annotated_sentence` = list of triplets [(w1, t1, iob1), ...]
    Transform a pseudo-IOB notation: O, PERSON, PERSON, O, O, LOCATION, O
    to proper IOB notation: O, B-PERSON, I-PERSON, O, O, B-LOCATION, O
    """
    proper_iob_tokens = []
    for idx, annotated_token in enumerate(annotated_sentence):
        tag, word, ner = annotated_token

        if ner != 'O':
            if idx == 0:
                ner = "B-" + ner
            elif annotated_sentence[idx - 1][2] == ner:
                ner = "I-" + ner
            else:
                ner = "B-" + ner
        proper_iob_tokens.append((tag, word, ner))
    return proper_iob_tokens


def postag_corpus(corpus_root, postagger="nltk_floresta_macmorpho_perceptron_tagger"):
    tagger = load_model(postagger)
    for root, dirs, files in os.walk(corpus_root):
        for filename in files:
            if filename.endswith(".conll"):
                with open(os.path.join(root, filename), 'r') as file_handle:
                    file_content = file_handle.read()
                    annotated_sentences = file_content.split('\n\n')
                    for annotated_sentence in annotated_sentences:
                        annotated_tokens = [seq for seq in
                                            annotated_sentence.split('\n') if
                                            seq]
                        words = [w.split(' ')[0] for w in annotated_tokens]
                        tagged = tagger.tag(words)
                        standard_form_tokens = []
                        for idx, annotated_token in enumerate(
                                annotated_tokens):
                            annotations = annotated_token.split(' ')
                            word, ner = annotations[0], annotations[1]
                            tag = tagged[idx][1]

                            standard_form_tokens.append((word, tag, ner))

                        conll_tokens = to_conll_iob(standard_form_tokens)

                        # Make it NLTK Classifier compatible - [(w1, t1, iob1), ...] to [((w1, t1), iob1), ...]
                        # Because the classfier expects a tuple as input, first item input, second the class
                        if conll_tokens:
                            yield [((w, t), iob) for w, t, iob in conll_tokens]


# Download the corpus here:
# https://github.com/davidsbatista/NER-datasets/blob/master/Portuguese/Paramopama
corpus_root = "/home/user/PycharmProjects/nlp_workspace/biblioteca/corpora/NER-datasets/Portuguese/leNER-Br"
reader = postag_corpus(corpus_root)

data = list(reader)
random.shuffle(data)
training_samples = data[:int(len(data) * 0.9)]
test_samples = data[int(len(data) * 0.9):]


def train():
    # training
    tagger = ClassifierBasedTagger(
        train=training_samples,
        feature_detector=NltkFeatures.extract_iob_features)

    joblib.dump(tagger, model_path)


def accuracy_test():
    chunker = NamedEntityChunker(model_id=MODEL_META["model_id"])

    # accuracy test
    score = chunker.evaluate(
        [conlltags2tree([(w, t, iob) for (w, t), iob in iobs])
         for iobs in test_samples])
    a = score.accuracy()
    print("Accuracy : ", a)
    db["accuracy"] = a
    db.store()


train()
accuracy_test()
