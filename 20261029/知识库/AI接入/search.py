"""Dependency-free lexical retrieval demo; emits context, not an AI answer."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

def tokenize(text):
    text = text.lower()
    words = re.findall(r'[a-z0-9_@.]+', text)
    for run in re.findall(r'[\u4e00-\u9fff]+', text):
        words.extend(run[i:i+2] for i in range(len(run)-1))
        if len(run) == 1:
            words.append(run)
    return words

def retrieve(query, limit=4):
    records = [json.loads(line) for line in (ROOT / 'chunks.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    bags = [Counter(tokenize(x['question'] + '\n' + x['text'])) for x in records]
    lengths = [sum(b.values()) for b in bags]
    average = sum(lengths) / len(lengths)
    ranked = []
    for record, bag, length in zip(records, bags, lengths):
        score = 0.0
        for term in set(tokenize(query)):
            df = sum(term in b for b in bags)
            tf = bag[term]
            score += math.log(1 + (len(bags)-df+0.5)/(df+0.5)) * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75*length/average))
        if score > 0:
            ranked.append({'id': record['id'], 'score': round(score, 4), 'text': record['text'], 'metadata': record['metadata']})
    return sorted(ranked, key=lambda x: x['score'], reverse=True)[:limit]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('question')
    parser.add_argument('--top-k', type=int, default=4)
    parser.add_argument('--messages', action='store_true', help='Emit generic role/content messages for an AI application')
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error('--top-k must be positive')
    context = retrieve(args.question, args.top_k)
    result = {'question': args.question, 'knowledge_context': context}
    if args.messages:
        result = [
            {'role': 'system', 'content': (ROOT / 'system_prompt.txt').read_text(encoding='utf-8')},
            {'role': 'user', 'content': json.dumps(result, ensure_ascii=False)},
        ]
    print(json.dumps(result, ensure_ascii=False, indent=2))
