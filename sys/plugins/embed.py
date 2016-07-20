"""
Author: Derivation Bud
Date  : Nov 2014
Intro : Embedding base64 encoded stuff in html
"""
import base64
import sys
dirs = sys.modules["__main__"].dirs

templates = {"font": """\
[style: ]
@font-face {
	/* Imported from %s */
	font-family: '%s';
	src: url(data:font/woff;charset=utf-8;base64,%s) format('woff');
	font-weight: normal;
	font-style:  normal;
	} 
[:style] """,
"image": """\
<img alt=":(" src="data:%s;base64,%s"/>
""",
"background": """\
[style: ]
%s {
	background-image:url('data:%s;base64,%s');
	}
[:style]
"""
,}
mimeTypes = {
	"jpg" :"image/jpeg",
	"jpeg":"image/jpeg",
	"svg" :"image/svg+xml",
	"png" :"image/png",
	}
def font(doc):
	fontname,filename = doc.split()
	bin = open(filename%(dirs), "rb").read()
	return templates["font"]%(filename,fontname,base64.b64encode(bin).decode('utf-8'))

def image(doc):
	filename = doc.split()[0]%(dirs)
	fmt = mimeTypes[filename.split(".")[-1]]
	if fmt=="image/svg+xml":
		return open(filename).read()
	else:
		bin = open(filename, "rb").read()
		return templates["image"]%(fmt,base64.b64encode(bin).decode('utf-8'))

def background(doc):
	selector,filename = doc.split()
	fmt = mimeTypes[filename.split(".")[-1]]
	bin = open(filename%(dirs), "rb").read()
	return templates["background"]%(selector,fmt,base64.b64encode(bin).decode('utf-8'))

