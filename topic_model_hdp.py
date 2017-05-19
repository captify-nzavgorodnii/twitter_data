import csv
import os

import re
from gensim import corpora, models


class HDPModel:
    def __init__(self, account_name):
        self.account_name = account_name
        self.resources_path = 'resources'
        self.corpus_path = self.resources_path + '/' + self.account_name + '.mm'
        self.dictionary_path = self.resources_path + '/' + self.account_name + '.dict'
        self.model_path = self.resources_path + '/' + self.account_name + '.model'
        self.csv_path = self.resources_path + '/' + self.account_name + 'data.csv'

    def load_dict_and_corpus(self):
        """
        Method loads locally stored dictionary and corpus (gensim objects)
        :return: 
        """
        corpus = corpora.MmCorpus(self.corpus_path)
        dictionary = corpora.Dictionary.load(self.dictionary_path)
        return dictionary, corpus

    @staticmethod
    def get_model(dictionary, corpus):
        """
        Method returns trained topic-modelling model (Hierarchical Dierichlet Process).
        It requires gensim objects (dictionary and corpus)
        :param dictionary: gensim object
        :param corpus: gensim object
        :return: model object
        """
        return models.HdpModel(corpus, id2word=dictionary)

    def save_model(self, model):
        """
        Method can be used to save the model locally
        :param model: model gensim object
        :return: None
        """
        if not os.path.isfile(self.model_path):
            with open(self.model_path, 'wb') as fh:
                model.save(fh)

    def load_model(self):
        """
        Method can load the gensim object model from local storage
        :return: model gensim object
        """
        return models.HdpModel.load(self.model_path)

    @staticmethod
    def get_topics(model, num_words=12):
        """
        The method accepts model gensim object (HDP) and produces json of topics
        and main words that relate to the topic and describe it
        :param model: model gensim object
        :param num_words: number of words to return in json. The words are sorted in decreasing importance for the topic
        :return: json object with topics and words
        """
        topics = model.print_topics(num_words=num_words)

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

        return create_json(topics)

    def get_csv_of_topics(self, model, num_words=12):
        """ 
        Method accepts model and number of words to return and returns a csv of 
        words with their topics
        :param model: gensim model object
        :param num_words: number of descriptive words to return for each topic
        :return: 
        """
        out = list()
        regex = re.compile('[^a-zA-Z]')
        topics = model.print_topics(num_words=num_words)
        for t in topics:
            row = list()
            row.append('Topic ' + str(t[0] + 1))
            li = t[1].split('+')
            li = [x.strip() for x in li]
            li = [regex.sub('', x) for x in li]
            row.extend(li)
            out.append(row)
            # print(row) #  DEBUG
        f = open(self.csv_path, 'w')
        w = csv.writer(f)
        w.writerows(out)
        f.close()

