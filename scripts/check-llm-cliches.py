#!/usr/bin/env python3
"""Subset of https://tools.simonwillison.net/llm-cliche-highlighter regexes."""
from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("no-chain", re.compile(r"\bno[-\s]+\w+,\s+no[-\s]+\w+", re.I)),
    ("whole", re.compile(r"\b(?:that|this)(?:'s|\s+(?:is|was))\s+the\s+whole\b", re.I)),
    ("did-not-chain", re.compile(r"\b(?:did\s+not|didn't)\s+\w+[^.!?\n]{0,40},\s+(?:did\s+not|didn't)\s+", re.I)),
    ("sit-with", re.compile(r"\bsit(?:s|ting)?\s+with\s+(?:that|this|it)\b", re.I)),
    ("already-know", re.compile(r"\byou\s+already\s+know", re.I)),
    ("is-the-entire", re.compile(r"(?:\b(?:is|was|are|were)|'s)\s+the\s+entire\b", re.I)),
    ("the-entire-is", re.compile(r"\bthe\s+entire\s+[\w'-]+(?:\s+[\w'-]+){0,4}?\s+(?:is|was|are|were)\b", re.I)),
    ("punchline", re.compile(r"\bthe\s+punchline(?:\s+(?:is|was|being)\b|\s*[:?])", re.I)),
    ("worth-naming", re.compile(r"\bworth\s+naming\b", re.I)),
    ("not-nothing", re.compile(r"\b(?:that|this|it|which)(?:'s|\s+(?:is|was))\s+not\s+nothing\b", re.I)),
    ("is-the-whole", re.compile(r"(?:\b(?:is|was|are|were)|'s)\s+the\s+whole\b|\bhere(?:'s|\s+is)\s+the\s+whole\b", re.I)),
    ("performative-honesty", re.compile(r"\bI\s+(?:will\s+not|won't)\s+pretend\b|\b(?:I'll|let's|to)\s+be\s+(?:honest|clear|blunt|real)\b", re.I)),
    ("thats-the-part", re.compile(r"\b(?:that|this|it)(?:'s|\s+(?:is|was))\s+the\s+part\b|\bmy\s+favou?rite\s+part\s+of\b", re.I)),
    ("the-only-i-trust", re.compile(r"\bthe\s+only\s+[\w'-]+\s+that\s+(?:matters|counts|works|survives)\b", re.I)),
    ("take-my-word", re.compile(r"\btake\s+my\s+word\s+for\s+", re.I)),
    ("turns-out", re.compile(r"(?:^|[.!?]\s+)Turns\s+out\b|\bit\s+turns\s+out\s+that\b", re.I | re.M)),
    ("fits-in-your-head", re.compile(r"\bin\s+your\s+head\b|\bbatteries[-\s]included\b|\bit\s+just\s+works\b|\bzero[-\s]config|\bsane\s+defaults\b", re.I)),
    ("heres-the-twist", re.compile(r"\bhere(?:'s|\s+is)\s+(?:the|a)\s+(?:twist|thing|catch|kicker|rub)\b", re.I)),
    ("x-is-dead", re.compile(r"\b(?:is|are)\s+dead\b|\blong\s+live\s+\w+", re.I)),
    ("thats-why-mattered", re.compile(r"\b(?:that|this)(?:'s|\s+(?:is|was))\s+why\b.{0,80}?\b(?:matter(?:s|ed)?|count(?:s|ed)?)\b", re.I | re.S)),
    ("ai-vocab", re.compile(r"\b(?:delv(?:e|es|ed|ing)|tapestr(?:y|ies)|meticulous(?:ly)?|pivotal|intricate(?:ly)?|intricacies|interplay|underscor(?:e|es|ed|ing)|garner(?:s|ed|ing)?|bolster(?:s|ed|ing)?|vibrant|bustling|multifaceted|seamless(?:ly)?|commendable|ever-evolving)\b", re.I)),
    ("not-just", re.compile(r"\bnot\s+(?:just|only|merely|simply)\s+[^.!?\n;]*?\bbut(?:\s+also)?\b", re.I)),
    ("note-that", re.compile(r"\bit(?:'s|\s+(?:is|was))\s+(?:also\s+)?(?:important|worth|crucial|essential|vital)\s+(?:to\s+|noting|mentioning)", re.I)),
    ("testament", re.compile(r"\b(?:stands?|stood|serves?|served)\s+as\s+(?:a|an)\s+(?:\w+\s+)?(?:testament|reminder)\b|\bis\s+a\s+(?:\w+\s+)?testament\s+to\b", re.I)),
    ("crucial-role", re.compile(r"\bplay(?:s|ed|ing)?\s+(?:a|an)\s+(?:\w+\s+)?(?:crucial|pivotal|vital|key|significant|central|critical|important)\s+role\b", re.I)),
    ("landscape", re.compile(r"\b(?:ever-)?(?:evolving|changing|shifting)\s+landscape\b|\bin\s+today's\s+(?:fast-paced|ever-changing|digital|modern)\s+", re.I)),
    ("vague-experts", re.compile(r"\b(?:experts|critics|observers|scholars|analysts|commentators)\s+(?:have\s+)?(?:argu|note|suggest|believe|agree|contend)", re.I)),
    ("despite-challenges", re.compile(r"\bdespite\s+(?:these|those|such)\s+(?:\w+\s+)?challenges\b|\bchallenges\s+remain\b|\bremains\s+to\s+be\s+seen\b|\btime\s+will\s+tell\b", re.I)),
    ("participle-tail", re.compile(r",\s+(?:highlighting|underscoring|emphasizing|showcasing|reflecting|demonstrating|illustrating|signaling|solidifying|cementing|reinforcing|underlining)\s+(?:its|his|her|their|our|the|a|an|how|that|what|both)\b", re.I)),
    ("promo", re.compile(r"\bnestled\s+(?:in|on)\b|\bin\s+the\s+heart\s+of\b|\brich\s+(?:cultural\s+)?(?:heritage|history|tapestry)\b|\bhidden\s+gem\b|\bbreathtaking\b", re.I)),
    ("ai-leftovers", re.compile(r"\bas\s+an\s+ai(?:\s+language)?\s+model\b|\bknowledge\s+cutoff\b", re.I)),
    ("colon-triple", re.compile(r":\s+[^.!?;:\n]{2,40},\s+[^.!?;:\n]{2,40},\s+(?:and\s+|or\s+)?[^.!?;:\n]{2,40}(?=[.!?\n])")),
]


def anaphora(text: str) -> list[str]:
    sents = re.split(r"(?<=[.!?])\s+", text)
    hits = []
    run = 1
    prev = ""
    for s in sents:
        w = re.match(r"([A-Za-z]+)", s)
        if not w:
            run = 1
            prev = ""
            continue
        word = w.group(1).lower()
        if word in {"the", "a", "an", "this", "that", "these", "those", "it", "its", "he", "she", "they", "we", "i"}:
            run = 1
            prev = ""
            continue
        if word == prev:
            run += 1
            if run >= 3:
                hits.append(s[:80])
        else:
            run = 1
            prev = word
    return hits


def main() -> int:
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    bad: list[str] = []
    for name, rx in PATTERNS:
        for m in rx.finditer(text):
            bad.append(f"{name}: {m.group(0)!r}")
    for h in anaphora(text):
        bad.append(f"sentence-anaphora: {h!r}")
    if bad:
        print(f"{len(bad)} hit(s) in {path}")
        for b in bad:
            print(" ", b)
        return 1
    print(f"0 hits in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
