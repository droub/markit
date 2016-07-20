"""
Author: Derivation Bud
Date  : April 2014
Intro : 
        This is an atempt to create a new syntax to generate html
        html is not easy to read or write as a plain text.
        wiki syntax is good for short portions of doc but comes short
        to deal with complex documents. More over most documentation
        formats are not providing support for embedded drawings.

        Note on escaping:
        html: <xmp> any html here will be escaped </xmp>
        markit: [[tag:] this tag is not opened
        directives: _\{xxx ... }_ this directive is escaped and displayed
        directives: _{#xxx ... }_ this directive is escaped and not displayed
        wiki: [wiki:off] _*this is not bold*_ [wiki:on]
"""
import re
import itertools

def directives(doc,dirs,debug=None):
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
    while True:
        tokens = re.split(r'(_\{include\s+.*?\}_)',doc,flags=re.S)
        if len(tokens)==1: 
            break
        else:
            build  = []
            for token in tokens:
                match=re.match(r'_\{include\s*(.*?)\s*\}_',token,flags=re.S)
                if match:
                    if debug: print( "including:",match.groups()[0] )
                    build.append( open(match.groups()[0]%(dirs)).read() )
                else:
                    build.append(token)
            doc = "".join(build)

    # Execute plugins
    tokens = re.split(r'(?<!\\)(_\{.*?\}_)',doc,flags=re.S)
    build  = []
    for token in tokens:
        # In line python
        match=re.match(r'_\{py\s(.*)\}_',token,flags=re.S)
        if match:
            if debug: print("executing: in-line python")
            import sys
            try:    import StringIO as io # Python2
            except: import io             # Python3
            buffer = io.StringIO()
            sys.stdout = buffer
            code_obj = compile(match.groups()[0],'<string>','exec') 
            try:
                exec( code_obj)
            except:
                sys.stdout = sys.__stdout__
                print(token)
                raise 
            sys.stdout = sys.__stdout__
            build.append(buffer.getvalue())
        elif re.match(r'_\{\s*#.*\}_',token,flags=re.S):
            pass
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
                if debug: print( "executing:",match.groups()[0] )
                build.append(callme(data))
            else: 
                build.append(token)

    try:
        return "".join(build) 
    except:
        print(build)
        raise SystemError

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
        [r'^_######'              , '[h6:eol]'                ], # Title 7
        [r'^_#####'               , '[h5:eol]'                ], # Title 6
        [r'^_####'                , '[h4:eol]'                ], # Title 5
        [r'^_###'                 , '[h3:eol]'                ], # Title 4
        [r'^_##'                  , '[h2:eol]'                ], # Title 3
        [r'^_#'                   , '[h1:eol]'                ], # Title 2
        [r'_/'                    , '[em:]'                   ], # italic
        [r'_\*'                   , '[b:]'                    ], # bold
        [r'_=='                   , '[pre:]'                  ], # code block
        [r'_='                    , '[code:]'                 ], # code in line
        [r'_"'                    , '[blockquote:]'           ], # quote
        [r'\/_'                   , '[:em]'                   ], # close 
        [r'\*_'                   , '[:b]'                    ], # close 
        [r'==_'                   , '[:pre]'                  ], # close 
        [r'=_'                    , '[:code]'                 ], # close 
        [r'"_'                    , '[:blockquote]'           ], # close 
        [r'\._'                   , '[:]'                     ], # close current
        [r'^([^*]*)(\s\*)'        , '\g<1>\n[ul:nol][li:]'    ], # Before First bullet, list closed by nol
        [r'^\*\*\*\*'             , '[li: class="listlvl4"]'  ], # Sub bulleted line
        [r'^\*\*\*'               , '[li: class="listlvl3"]'  ], # "
        [r'^\*\*'                 , '[li: class="listlvl2"]'  ], # "
        [r'^\*'                   , '[li:]'                   ], # Any Bulleted line
        [r'^([^|]*)(\s\|\|+)'     , '\g<1>\n[table:nol]\g<2>' ], # Before first row, table close by nol
        [r'^\|\|\|'               , '[tr:][th:]'              ], # Header row
        [r'^\|\|'                 , '[tr:][td:]'              ], # Body row
        [r'\|\|+(\s*$)'           , '[:tr]\g<1>'              ], # Row ending (optional)
        [r'(.)\|\|\|'             , '\g<1>[th:]'              ], # Header cells
        [r'(.)\|\|'               , '\g<1>[td:]'              ], # Body cell
        [r'^\s*\n\s*\n'           , '[div. class="spacer"]'   ], # Give meaning to double empty lines, cast a shadow on some nol :(
       #[r'^\s*\n(^\w)'           , '\n[p:nol]\g<1>'          ], # Paragraph
        [r'_!{'                   , '_{'                      ], # Escaped directives
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

def markit(doc,debug=None):
    """ Converts markit tags such as [tag:]... 
        into html tags such as <tag> ...</tag>"""

    def closeTags(book,target,debug=None):
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
        if debug: trace=' data-dbg="%d_%s_%s"'%(nbClose,target[0],target[1])
        else    : trace=''
        while nbClose:
            nbClose -= 1
            tag,closure = book.pop()
            closed  += '</%s%s>'%(tag,trace)
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

            # Close targetted tag
            book,closed=closeTags(book,("*",tag),debug)
            if closed: build.append(closed)

            # Close previous sibling tag
            book,closed=closeTags(book,(tag,"*_but_noa"),debug)
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
            book,closed=closeTags(book,(tag,"*"),debug)
            if closed: build.append(closed)

        elif '\n' in token:    
            # Close tags before end of line
            book,closed_eol=closeTags(book,("*","eol"),debug)
            index_eol = token.find('\n')

            # Close tags before empty line
            match_nol =  re.search(r'\n\s*\n',token) 
            if  match_nol:
                book,closed_nol=closeTags(book,("*","nol"),debug)
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
            book,closed=closeTags(book,('*','*'),debug)
            if closed: build.append(closed)

        # Keep slice of document
        else:
            build.append(token)

    res = "".join(build)        
    res=res.replace("[[","[")

    return res

def sanitize(doc):
    # Remap forbidden characters
    remaps = [[r'<','&lt;'], [r'>','&gt;'], [r'&(?!\w+;)','&amp;']]
    for tag in ["pre","code"]:
        build = []
        tokens = re.split(r'(<\/?%s.*?>)'%(tag),doc)
        sanitizeNextToken = False
        for token in tokens:
            if re.match(r'<%s.*>'%(tag),token): 
                sanitizeNextToken = True
            elif sanitizeNextToken:
                for searchme,replacewith in remaps:
                    token=re.sub(searchme,replacewith,token,flags=re.M)
                sanitizeNextToken = False
            build.append(token)
        doc = "".join(build)        
    # Suppress xml stubs
    doc = re.sub(r'<\?xml.*?>',"",doc,flags=re.M|re.S)    
    doc = re.sub(r'<!DOCTYPE\s*svg.*?>',"",doc,flags=re.M|re.S)    
    return doc

def build(infile,outfile=None,debug=None):
    if not outfile :
        basename,extension = os.path.splitext(infile)
        if extension==".html":
            print("Sorry, input file should'nt have an extension .html:",infile)
        else:
            outfile = basename+".html"
    if outfile:
        global dirs
        dirs  = {
            "src":os.path.abspath(os.path.dirname(infile)),
            "sys":os.path.abspath(os.path.dirname(__file__)),
            }
        print(infile+" => "+outfile)
        doc   = open(infile).read()
        doc   = directives(doc,dirs,debug)
        doc   = dos2unix(doc)
        doc   = wiki(doc)
        doc   = markit(doc,debug)
        doc   = sanitize(doc)
        fo    = open(outfile,"w")
        fo.write(doc)
        fo.close()

if __name__=="__main__":
    import os,sys
    debug = None
    if "-d" in sys.argv:
        debug = True
        sys.argv.remove("-d")
    if   len(sys.argv)==2: build(sys.argv[1],debug=debug)
    elif len(sys.argv)==3: build(sys.argv[1],sys.argv[2],debug=debug)
    else :
        print("Usage: python markit.py infile.mi [ outfile.html ] [-d]")

