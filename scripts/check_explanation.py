"""Structural checks complement the separately completed visual review."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from docx import Document
from pypdf import PdfReader

root=Path(__file__).resolve().parents[1]
path=root/'reports/Customer_Churn_Project_Explanation.docx'
doc=Document(path)
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(path) as archive:
    styles=etree.fromstring(archive.read('word/styles.xml'))
    xml=etree.fromstring(archive.read('word/document.xml'))
    title=next(s for s in styles if s.get('{'+ns['w']+'}styleId')=='Title')
    assert not title.xpath('.//w:pBdr',namespaces=ns)
    assert len(xml.xpath('//w:hyperlink[@w:anchor]',namespaces=ns))==23
    assert len(xml.xpath('//w:bookmarkStart',namespaces=ns))==23
assert len(doc.inline_shapes)==7
pdf=PdfReader(root/'tmp/docx_review/guide.pdf')
assert len(pdf.pages)==26
assert all(len(page.extract_text().strip())>100 for page in pdf.pages)
contents=' '.join(pdf.pages[1].extract_text().split())
assert 'Sources and project references 26' in contents
assert '[[TOC]]' not in '\n'.join(p.text for p in doc.paragraphs)
print('PASS: DOCX package, 23 internal contents links, seven images, clean title, 26 rendered pages and matching final contents entry.')
