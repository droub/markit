"""
Author: Derivation Bud
Date  : Nov 2014
Intro : Embedding base64 encoded stuff in html
"""
import base64

templates = {"font": """\
[style: scoped]
@font-face {
	/* Imported from %s */
	font-family: '%s';
	src: url(data:font/woff;charset=utf-8;base64,%s) format('woff');
	font-weight: normal;
	font-style:  normal;
	} 
[:style] """,
"image": """\
<img alt=":(" src="data:image/png;base64,%s/>
""",
"background": """\
[style: scoped]
%s {
	background-image:url(data:image/png;base64,%s);
	}
[:style]
"""
,}

def font(doc):
	fontname,filename = doc.split()
	bin = open(filename, "rb").read()
	return templates["font"]%(filename,fontname,base64.b64encode(bin))

def image(doc):
	filename = doc
	bin = open(filename, "rb").read()
	return templates["image"]%(filename,base64.b64encode(bin))

def background(doc):
	selector,filename = doc
	bin = open(filename, "rb").read()
	return templates["image"]%(selector,base64.b64encode(bin))

