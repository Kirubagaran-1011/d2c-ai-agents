"""Offline text embedder (hashing trick, no API key, no downloads).

Turns text into a fixed-size unit vector from word and word-pair counts, so similar
wording gives similar vectors. Swap in a neural embedding model later by keeping the
same `embed(text) -> list[float]` method.
"""
import hashlib
import math
import re

STOPWORDS = {"a", "an", "the", "for", "to", "of", "and", "or", "in", "on", "with", "is", "are", "i", "me", "my", "ke", "ki", "ka", "ko", "hai", "se", "that", "you", "it", "this", "some", "something", "want", "need", "looking", "chahiye"}
# Tiny Hindi/Hinglish to English map so common Hinglish queries match English product text.
SYNONYMS = {"chai": "tea", "kadak": "strong", "thanda": "cold", "garmi": "summer", "meetha": "sweet", "neend": "sleep", "raat": "night", "tohfa": "gift", "uphaar": "gift"}


def tokenize(text: str) -> list:
    words = re.findall(r"[a-z0-9]+", text.lower())
    out = []
    for word in words:
        word = SYNONYMS.get(word, word)
        if word in STOPWORDS:
            continue
        if len(word) > 3 and word.endswith("s"):
            word = word[:-1]
        out.append(word)
    return out


class HashingEmbedder:
    def __init__(self, dim: int = 512):
        self.dim = dim

    def _bucket(self, feature: str):
        digest = hashlib.md5(feature.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % self.dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        return index, sign

    def embed(self, text: str) -> list:
        words = tokenize(text)
        features = words + [f"{a}_{b}" for a, b in zip(words, words[1:])]
        vector = [0.0] * self.dim
        for feature in features:
            index, sign = self._bucket(feature)
            vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector))
        return [v / norm for v in vector] if norm else vector
