import csv
import os

import re
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


def pretty_output(ts):

    def save_to_csv(ts):
        out = list()
        regex = re.compile('[^a-zA-Z]')
        for t in ts:
            row = list()
            row.append('Topic ' +str(t[0]+1))
            li = t[1].split('+')
            li = [x.strip() for x in li]
            li = [regex.sub('', x) for x in li]
            row.extend(li)
            out.append(row)
            # print(row) #  DEBUG
        f = open('resources/data.csv', 'w')
        w = csv.writer(f)
        w.writerows(out)
        f.close()

    save_to_csv(ts)

    def create_json(ts):
        out = dict()
        regex = re.compile('[^a-zA-Z]')
        for t in ts:
            key = 'Topic ' + str(t[0] + 1)
            li = t[1].split('+')
            li = [x.strip() for x in li]
            li = [regex.sub('', x) for x in li]
            out[key] = li
        return out

    print(create_json(ts))


pretty_output(topics)
