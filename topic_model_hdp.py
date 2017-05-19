import os

from gensim import corpora, models

path = 'resources'
parent_name = 'Honda'
corpus_path = path + '/' + parent_name + '.mm'
dictionary_path = path + '/' + parent_name + '.dict'
model_path = path + '/' + parent_name + '.model'

corpus = corpora.MmCorpus(corpus_path)
dictionary = corpora.Dictionary.load(dictionary_path)

hdp = models.HdpModel(corpus, id2word=dictionary)


def save_model(model):
    if not os.path.isfile(model_path):
        with open(model_path, 'wb') as fh:
            model.save(fh)


save_model(hdp)


def load_model():
    return models.HdpModel.load(model_path)

hdp = load_model()

topics = hdp.print_topics(num_words=12)
for topic in topics:
    print(topic)
