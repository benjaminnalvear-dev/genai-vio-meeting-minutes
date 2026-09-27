"""Retrieval léxico BM25 sobre las intervenciones (sin modelos adicionales)."""

from __future__ import annotations

import math
import re
from collections import Counter

from .temporal import fold

STOPWORDS = set("""
a al algo alguien ante antes aqui asi aun aunque bien bueno cada como con contra cual cuando de del desde
donde dos el ella ellas ellos en entonces entre era eres es esa esas ese eso esos esta estaba estamos estan
estar este esto estos estoy fue ha habia hay hace hacer la las le les lo los mas me mi mis mucho muy nada ni
no nos nosotros o otra otro para pero poco por porque que quien se sea segun ser si sin sobre solo son su sus
tal tambien tampoco te tenemos tengo tiene todo todos tu tus un una uno unos unas usted va vamos y ya yo
ahi eso esa igual cierto claro perdon listo ok vale
""".split())


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", fold(text))
    out = []
    for tok in tokens:
        if tok in STOPWORDS or len(tok) < 2:
            continue
        if len(tok) > 4 and tok.endswith("es"):
            tok = tok[:-2]
        elif len(tok) > 3 and tok.endswith("s"):
            tok = tok[:-1]
        out.append(tok)
    return out


# Stemmer español liviano: quita sufijos verbales y nominales comunes ("abrimos"/"abrir" -> "abr",
# "tentativo"/"tentativa" -> "tentativ"). Sin dependencias; no es Snowball completo.
SUFFIXES = sorted("iendo ando aron ieron amos emos imos aban ados idas idos adas aba ado ido ada ida "
                  "ar er ir an en as es os a e o".split(), key=len, reverse=True)


def stem(token: str) -> str:
    for suf in SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 3:
            return token[: -len(suf)]
    return token


def tokenize_stem(text: str) -> list[str]:
    return [stem(t) for t in re.findall(r"[a-z0-9]+", fold(text)) if t not in STOPWORDS and len(t) >= 2]


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75, tokenizer=None):
        self.tokenizer = tokenizer or tokenize
        self.tokens = [self.tokenizer(d) for d in docs]
        self.k1, self.b = k1, b
        self.avgdl = sum(len(t) for t in self.tokens) / max(len(self.tokens), 1)
        df = Counter(tok for toks in self.tokens for tok in set(toks))
        n = len(self.tokens)
        self.idf = {tok: math.log(1 + (n - f + 0.5) / (f + 0.5)) for tok, f in df.items()}
        self.tf = [Counter(t) for t in self.tokens]

    def scores(self, query: str) -> list[float]:
        q = self.tokenizer(query)
        out = []
        for tf, toks in zip(self.tf, self.tokens):
            s = 0.0
            for tok in q:
                if tok not in tf:
                    continue
                f = tf[tok]
                s += self.idf.get(tok, 0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(toks) / self.avgdl))
            out.append(s)
        return out

    def top(self, query: str, k: int, allowed: set[int] | None = None, min_score: float = 0.5) -> list[int]:
        s = self.scores(query)
        idx = [i for i in range(len(s)) if (allowed is None or i in allowed) and s[i] >= min_score]
        return sorted(idx, key=lambda i: s[i], reverse=True)[:k]
