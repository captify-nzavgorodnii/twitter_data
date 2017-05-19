import math


class TextProcessing:

    def __init__(self):
        pass

    def tf(self, word, blob):
        return blob.words.count(word) / len(blob.words)

    def n_containing(self, word, bloblist):
        return sum(1 for blob in bloblist if word in blob.words)

    def idf(self, word, bloblist):
        return math.log(len(bloblist) / (1 + self.n_containing(word, bloblist)))

    def tfidf(self, word, blob, bloblist):
        return self.tf(word, blob) * self.idf(word, bloblist)

    # def clean_tweets(self, text):
    #     from nltk.corpus import stopwords
    #     import string
    #     import preprocessor as p
    #
    #     punctuation = list(string.punctuation)
    #     stop = stopwords.words('english') + punctuation + ['rt', 'via']
    #     return [term for term in p.clean(text).split(' ') if term not in stop]