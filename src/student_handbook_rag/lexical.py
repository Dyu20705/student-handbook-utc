"""Small in-memory BM25 index for the local handbook, preserving Vietnamese accents."""
from collections import Counter
import math
import re
import unicodedata


def tokenize(text):
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())


class LexicalIndex:
    def __init__(self, documents):
        self.documents = documents
        self.terms = [Counter(tokenize(doc.page_content)) for doc in documents]
        self.lengths = [sum(terms.values()) for terms in self.terms]
        self.average_length = sum(self.lengths) / max(1, len(documents))
        self.frequencies = Counter(term for terms in self.terms for term in terms)

    def search(self, query, k):
        scored = []
        for index, terms in enumerate(self.terms):
            score = 0.0
            for term in set(tokenize(query)):
                frequency = terms.get(term, 0)
                if not frequency:
                    continue
                df = self.frequencies[term]
                idf = math.log(1 + (len(self.documents) - df + .5) / (df + .5))
                denominator = frequency + 1.5 * (.25 + .75 * self.lengths[index] / self.average_length)
                score += idf * frequency * 2.5 / denominator
            if score:
                scored.append((index, score))
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        return [(self.documents[index], score) for index, score in scored[:k]]
