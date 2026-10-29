from pathlib import Path
from pypdf import PdfReader
import json
out=Path('知识库'); r=PdfReader('hkust_canvas_student_guide.pdf')
pages=[p.extract_text() for p in r.pages]
(out/'原文逐页.md').write_text('# PDF 原文提取\n\n'+'\n\n'.join(f'## PDF 第 {i+1} 页\n\n{t}' for i,t in enumerate(pages)),encoding='utf-8')
links=[]
for i,p in enumerate(r.pages):
 for a in p.get('/Annots',[]):
  obj=a.get_object(); action=obj.get('/A',{})
  if action.get('/URI'): links.append({'pdf_page':i+1,'url':str(action['/URI'])})
(out/'来源链接.json').write_text(json.dumps(links,ensure_ascii=False,indent=2),encoding='utf-8')
