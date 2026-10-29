"""Rebuild portable AI knowledge files from the reviewed Markdown. No dependencies."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'AI接入'
OUT.mkdir(exist_ok=True)
source = ROOT.parent / 'hkust_canvas_student_guide.pdf'
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
links = json.loads((ROOT / '来源链接.json').read_text(encoding='utf-8-sig'))
md = (ROOT / 'README.md').read_text(encoding='utf-8-sig')
records = []
for section in re.split(r'^## ', md, flags=re.M)[2:]:
    topic, _, rest = section.partition('\n')
    for entry in re.split(r'^### ', rest, flags=re.M)[1:]:
        question, _, body = entry.partition('\n')
        answer, sep, provenance = body.rpartition('来源：')
        if not sep:
            raise ValueError(f'Missing provenance: {question}')
        locator = provenance.split('页')[0]
        pages = set()
        for first, last in re.findall(r'(\d+)(?:[–-](\d+))?', locator):
            pages.update(range(int(first), int(last or first) + 1))
        if not pages or not pages <= set(range(1, 10)):
            raise ValueError(f'Invalid pages: {question}')
        answer = answer.strip()
        # Make cross-file references usable when a chunk is retrieved on its own.
        answer = answer.replace('来源链接.json', '本条 metadata.related_links（同页链接，未逐项匹配）')
        uid = 'hkust-canvas-' + hashlib.sha256(question.encode()).hexdigest()[:16]
        citation = f'HKUST Canvas Student Guide，PDF 第 {"、".join(map(str, sorted(pages)))} 页'
        records.append({
            'id': uid,
            'text': f'主题：{topic.strip()}\n问题：{question.strip()}\n回答：{answer}\n来源：{citation}',
            'question': question.strip(), 'answer': answer,
            'metadata': {
                'document_id': 'hkust_canvas_student_guide',
                'source_file': source.name, 'source_sha256': source_hash,
                'source_title': 'HKUST Canvas Student Guide',
                'topic': topic.strip(), 'language': 'zh-CN',
                'pdf_pages': sorted(pages), 'citation': citation,
                'transformed_on': '2026-10-29', 'source_published_on': None,
                'currentness_verified': False,
                'content_type': 'rewritten_qa',
                'related_links': list(dict.fromkeys(x['url'] for x in links if x['pdf_page'] in pages)),
                'related_links_scope': 'same_pdf_pages_not_individually_matched',
            },
        })
with (OUT / 'chunks.jsonl').open('w', encoding='utf-8') as f:
    for record in records:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
(OUT / 'knowledge.txt').write_text('\n\n---\n\n'.join(x['text'] for x in records), encoding='utf-8')
manifest = {'schema_version': '1.0', 'record_count': len(records),
            'source_file': source.name, 'source_sha256': source_hash,
            'embedding_field': 'text', 'primary_key': 'id',
            'metadata_field': 'metadata', 'embeddings_included': False,
            'note': 'Question-answer chunks; PDF pages are 1-based including the contents page.'}
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
assert len(records) == len(set(x['id'] for x in records)) == md.count('\n### ')
print(f'Validated {len(records)} records; all questions covered; source pages and IDs checked.')
