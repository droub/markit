"""
Author: Derivation Bud
Date  : April 2014
Intro : 
        This is an atempt to create a new syntax to generate html
        html is not easy to read or write as a plain text.
        wiki syntax is good for short portions of doc but comes short
        to deal with complex documents. More over most documentation
        formats are not providing support for embedded drawings.

"""
import re
import itertools

def directives(doc):
    # Get plugins
    import importlib
    import glob,os.path
    import plugins
    rootDir =  os.path.dirname(os.path.abspath(__file__))
    candidates = glob.glob(rootDir+"/plugins/*.py")
    for candidate in candidates:
        module = os.path.basename(candidate)[:-3]
        importlib.import_module('plugins.'+module)

    # Recursively resolve includes
    while 1:
        tokens = re.split(r'(_\{include\s+.*?\}_)',doc,flags=re.S)
        if len(tokens)==1: 
            break
        else:
            build  = []
            for token in tokens:
                match=re.match(r'_\{include\s*(.*?)\s*\}_',token,flags=re.S)
                if match:
                    build.append( file(match.groups()[0]).read() )
                else:
                    build.append(token)
            doc = "".join(build)

    # Execute plugins
    tokens = re.split(r'(_\{.*?\}_)',doc,flags=re.S)
    build  = []
    for token in tokens:
        # In line python
        match=re.match(r'_\{py\s(.*)\}_',token,flags=re.S)
        if match:
            import sys,StringIO
            buffer = StringIO.StringIO()
            sys.stdout = buffer
            code_obj = compile(match.groups()[0],'<string>','exec') 
            exec code_obj
            sys.stdout = sys.__stdout__
            build.append(buffer.getvalue())
        else:
        # Modules
            match=re.match(r'_\{([\w.]+)(.*)\}_',token,flags=re.S)
            if match:
                nameToBeCalled,data=match.groups()
                callme = locals()['plugins']
                for package in nameToBeCalled.split('.'): 
                    callme = getattr(callme,package)
                if "." not in nameToBeCalled: 
                    callme = getattr(callme,nameToBeCalled)

                build.append(callme(data))
            else: 
                build.append(token)

    return "".join(build) 

def dos2unix(doc):
    doc=doc.replace('\r\n','\n')
    return doc

def wiki(doc):
    """ Map a wiki syntax onto markit tags"""
    syntax = {
"off":  [],
"on" :  [
        [r'^____*(.*)\n'          , '[article: \g<1>]\n'      ], # Article with attributes
        [r'^____* *\n'            , '[article:]\n'            ], # Article
        [r'^====*(.*)\n'          , '[section: \g<1>]\n'      ], # Section with attributes
        [r'^====* *\n'            , '[section:]\n'            ], # Section
        [r'^(.*)\n\^\^\^\^+'      , '[header:eol]\g<1>\n'     ], # Section's header
        [r'^vvvv* *\n(.*)\n'      , '[footer:eol]\g<1>\n'     ], # Section's footer
        [r'^_######'              , '[h6:eol]'                ], # Title 1
        [r'^_#####'               , '[h5:eol]'                ], # Title 2
        [r'^_####'                , '[h4:eol]'                ], # Title 3
        [r'^_###'                 , '[h3:eol]'                ], # Title 4
        [r'^_##'                  , '[h2:eol]'                ], # Title 5
        [r'^_#'                   , '[h1:eol]'                ], # Title 6
        [r'_/'                    , '[em:]'                   ], # italic
        [r'_\*'                   , '[b:]'                    ], # bold
        [r'_=='                   , '[pre:]'                  ], # code block
        [r'_='                    , '[code:]'                 ], # code in line
        [r'_"'                    , '[quote:]'                ], # quote
        [r'==_'                   , '[:]'                     ], # close code block
        [r'[.*#/="]_'             , '[:]'                     ], # close current
        [r'^([^*]*)(\s\*)'        , '\g<1>\n[ul:nol][li:]'    ], # Before First bullet
        [r'^\*'                   , '[li:]'                   ], # Any Bulleted line
        [r'^([^|]*)(\s\|\|+)'     , '\g<1>\n[table:nol]\g<2>' ], # Before first row
        [r'^\|\|\|'               , '[tr:][th:]'              ], # Header row
        [r'^\|\|'                 , '[tr:][td:]'              ], # Body row
        [r'\|\|+(\s*$)'           , '[:tr]\g<1>'              ], # Row ending (optional)
        [r'(.)\|\|\|'             , '\g<1>[th:]'              ], # Header cells
        [r'(.)\|\|'               , '\g<1>[td:]'              ], # Body cell
        [r'^\s*\n(^\w)'           , '\n[p:nol]\g<1>'          ], # Paragraph
        ],
    }
    tokens = re.split(r'(?<!\[)(\[wiki:[^\]]+\])',doc)
    engine = "on"
    build  = []
    for token in tokens:
        match = re.match(r'\[wiki:\s*(\w*)\s*]',token)
        if match:
            engine = match.groups()[0]
        else:
            for searchme,replacewith in syntax[engine]:
                token=re.sub(searchme,replacewith,token,0,re.M)
            build.append(token)

    return("".join(build))

def markit(doc):
    """ Converts markit tags such as [tag:]... 
        into html tags such as <tag> ...</tag>"""

    def closeTags(book,target):
        """Close a tail of open tags. Tags are closed progressing backward 
        until a tag with the right name or waiting for the right event is
        found."""
        closed  = ''
        if target == ('*','*'): 
            # Schedule Close all tags
            match   = True
            nbClose = len(book)
        else:
            # Schedule Close trailing tags 
            nbClose = 0
            targetTag,targetClosure=target
            flipped_book = book[:]
            flipped_book.reverse()
            match   = False
            index   = 0
            for tag,closure in flipped_book:
                index += 1
                if closure+targetTag+targetClosure == "noa"+tag+"*_but_noa":
                    continue  # Avoiding autoclose

                elif targetTag in ["*",tag] and targetClosure in ["*","*_but_noa",closure]:
                    nbClose = index # Autoclose to at least this position
        # Close here
        while nbClose:
            nbClose -= 1
            tag,closure = book.pop()
            closed  += '</%s>'%(tag)
        return book,closed

    book  = [] # Keeps track of tags still open 
    build = [] # Accumulates html converted doc

    # isolate   : [tag:auclose blabla] and [:tag] tokens
    tokens    = re.split(r'(?<!\[)(\[:?\w*[:\.]?[^\]]*\])',doc)
    doMarkit  = True
    for token in tokens+['eof']:
        if  re.match(r'\[markit:\s*off\s*\]',token):
            doMarkit = None
        elif re.match(r'\[markit:\s*on\s*\]',token):
            doMarkit = True
        # Forward document untouched
        elif not doMarkit:
            build.append(token)
        # Open close
        elif  re.match(r'\[(\w+)\.\s+([^\]]*)\]',token): 
            tag,attr=re.match(r'\[(\w+)\.\s+([^\]]*)\]',token).groups()
            build.append("<%s %s></%s>"%(tag,attr,tag))
        # Open tag
        elif  re.match(r'\[\w+:',token): 
            tag,closure,attr = re.match(r'\[(\w+):(\w*)\s*([^\]]*)\]',token).groups()

            # Close previous sibling tag
            book,closed=closeTags(book,(tag,"*_but_noa"))
            if closed: build.append(closed)

            # Close targetted tag
            book,closed=closeTags(book,("*",tag))
            if closed: build.append(closed)

            # Open tag
            book.append((tag,closure))
            if attr: build.append("<%s %s>"%(tag,attr))
            else   : build.append("<%s>"%(tag))

        # Manual Close current tag
        elif re.match(r'\[:\]',token):    
            tag,closure = book.pop()
            build.append("</%s>"%(tag))

        # Manual Close parent tag
        elif re.match(r'\[:\w',token):    
            tag = re.match(r'\[:(\w*)',token).groups()[0]
            book,closed=closeTags(book,(tag,"*"))
            if closed: build.append(closed)

        elif '\n' in token:    
            # Close tags before end of line
            book,closed_eol=closeTags(book,("*","eol"))
            index_eol = token.find('\n')

            # Close tags before empty line
            match_nol =  re.search(r'\n\s*\n',token) 
            if  match_nol:
                book,closed_nol=closeTags(book,("*","nol"))
                index_nol = match_nol.start()

                if index_nol==index_eol:
                    closed = token[:index_eol]          +\
                             closed_eol                 +\
                             closed_nol                 +\
                             token[index_eol:]
                else: 
                    closed = token[:index_eol]          +\
                             closed_eol                 +\
                             token[index_eol:index_nol] +\
                             closed_nol                 +\
                             token[index_nol:]
            else: 
                closed = token[:index_eol]              +\
                         closed_eol                     +\
                         token[index_eol:]

            build.append(closed)

        # Close tags before end of file
        elif token == 'eof':    
            book,closed=closeTags(book,('*','*'))
            if closed: build.append(closed)

        # Keep slice of document
        else:
            build.append(token)

    res = "".join(build)        
    res=res.replace("[[","[")

    return res

def build(infile,outfile=None):
    if not outfile :
        basename,extension = os.path.splitext(infile)
        if extension==".html":
            print "Sorry, input file should'nt have an extension .html:",infile
        else:
            outfile = basename+".html"
    if outfile:
        print infile,"=>",outfile
        doc   = file(infile).read()
        doc   = directives(doc)
        doc   = dos2unix(doc)
        doc   = wiki(doc)
        doc   = markit(doc)
        fo    = file(outfile,"w")
        fo.write(doc)
        fo.close()

if __name__=="__main__":
    import os,sys
    if   len(sys.argv)==2: build(sys.argv[1])
    elif len(sys.argv)==3: build(sys.argv[1],sys.argv[2])
    else :
        print "Usage: python markit.py infile.mi [ outfile.html ]"

