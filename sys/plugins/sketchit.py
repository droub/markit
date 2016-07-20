"""
Author: Derivation Bud
Date  : May 2014
Intro : Ascii Art Block Diagrams To SVG converter
"""
import re
import itertools

def sketchit(doc):
    """ Block diagram converter """
    def svgline(x1,y1,x2,y2):  
        return '<line x1="%d" y1="%d" x2="%d" y2="%d"/>'%(x1,y1,x2,y2)
    def svgtext(x,y,txt):      
        return '<text x="%d" y="%d" dy=".3em">%s</text>'%(x,y,txt)
    def svgrect(x,y,w,h):  
        return '<rect x="%d" y="%d" width="%d" height="%d"/>'%(x,y,w,h)
    def svgarrow():            
        return '<path id="arrow" d="M -0.3,0 l 0,0.3,0.6,-0.3,-0.6,-0.3 z"/>'
    def svgbubble():           
        return '<circle id="bubble" cx="0" cy="0" r="0.3" />'
    def svgobj(x,y,a,id):      
        return '<use x="%d" y="%d" xlink:href="#%s" '%(x,y,id)+\
                'transform="rotate(%0.2f,%d,%d)"/>'%(a,x,y)
    def svgring(cx,cy,rx,ry):           
        return '<ellipse cx="%0.2f" cy="%0.2f" rx="%0.2f" ry="%0.2f"/>'%(cx,cy,rx,ry)
    def svggone(vertices):
        d,cmd = "M "," L "
        for x,y in vertices:
            d += "%d %d%s"%(x,y,cmd)  
            cmd = " "
        return '<path d="%s z"/>'%(d)

    shapes = {"lines":[],"rects":[],"texts":[],"terms":[],"gones":[],"rings":[]}

    # unpack args
    match=re.match('\s*([\d.]+)',doc)
    if match: scale=float(match.groups()[0])
    else:     scale=1.0

    rows = doc.split("\n")[1:]
    nbrows = len(rows)
    # justify width
    nbcols = max([ len(row) for row in rows ])
    rows = [("%%-%ds"%(nbcols))%(row) for row in rows]
    # transpose
    cols=["".join([row[x] for row in rows]) for x in range(nbcols)]
    # detect horizontal shapes
    for y,row in enumerate(rows):
        # horizontal lines
        for match in re.finditer(r'[-.+<>@v^]{2,}',row):
            shapes["lines"].append( [match.start(),y,match.end()-1,y] )
        # bubble arrows
        for match in re.finditer(r'@',row):
            shapes["terms"].append( [match.start(),y,0,"bubble"] )
        # right arrows
        for match in re.finditer(r'[.+-]>',row):
            shapes["terms"].append( [match.end()-1,y,0,"arrow"] )
        # left arrows
        for match in re.finditer(r'<[.+-]',row):
            shapes["terms"].append( [match.start(),y,180,"arrow"] )
        # labels
        textOnly = re.sub(r'[|+^<>-]','@',row)      # Mask lines
        textOnly = re.sub(r'(\W)\.','\1@',textOnly) # Preserve . when in text
        textOnly = re.sub(r'\bv\b','@',textOnly)    # Mask v when alone
        textOnly = re.sub(r'  ','@@',textOnly)      # Mask blanks
        for match in re.finditer(r'[^@]+',textOnly):
            ztext = match.group().strip()
            if ztext not in ['v','']:
                shapes["texts"].append( [match.start(),y,ztext] )
    # detect vertical shapes
    for x,col in enumerate(cols):
        # vertical lines
        for match in re.finditer(r'[.|+<@>v^]{2,}',col):
            shapes["lines"].append( [x,match.start(),x,match.end()-1] )
        # down arrows
        for match in re.finditer(r'[.|@+]v',col):
            shapes["terms"].append( [x,match.end()-1,90,"arrow"] )
        # up arrows
        for match in re.finditer(r'\^[.|+]',col):
            shapes["terms"].append( [x,match.start(),270,"arrow"] )
    # detect boxes
    colines = {} # are matching hlines
    for x1,y1,x2,y2 in shapes["lines"]:
        if y1==y2 and (x1,x2) not in colines:
            catch = []
            for line in shapes["lines"]:
                if (line[0],line[2])==(x1,x2) : catch.append(line)
            if len(catch)>=2: colines[(x1,x2)]=catch
    for group in colines.values():
        for hline1,hline2 in itertools.combinations(group,2):
            vline1,vline2=False,False
            for line in shapes["lines"]:
                if   line==[hline1[0],hline1[1],hline2[0],hline2[1]]: vline1 = line
                elif line==[hline1[2],hline1[3],hline2[2],hline2[3]]: vline2 = line
            if vline1 and vline2:
                vertices = [] 
                for x in range(hline1[0],hline1[2]): 
                    if rows[hline1[1]][x]=="." : vertices.append([x,hline1[1]]) 
                for y in range(vline2[1],vline2[3]): 
                    if cols[vline2[0]][y]=="." : vertices.append([vline2[0],y]) 
                for x in range(hline2[2],hline2[0],-1): 
                    if rows[hline2[1]][x]=="." : vertices.append([x,hline2[1]]) 
                for y in range(vline1[3],vline1[1],-1): 
                    if cols[vline1[0]][y]=="." : vertices.append([vline1[0],y]) 
                if len(vertices)==1:
                    shapes["rings"].append([1.0*(hline1[0]+hline1[2])/2,
                                            1.0*(vline1[1]+vline1[3])/2,
                                            1.0*(hline1[2]-hline1[0])/2,
                                            1.0*(vline1[3]-vline1[1])/2,])
                elif len(vertices)>1:
                    shapes["gones"].append(vertices)

                else:
                    shapes["rects"].append([hline1[0],hline1[1],
                                            hline2[2]-hline1[0],
                                            hline2[3]-hline1[1]])

                for line in [hline1,hline2,vline1,vline2]:
                    shapes["lines"].remove(line)

    svg = []        
    w=str(nbcols*scale)+"em"
    h=str(nbrows*scale)+"em"
    svg.append('<svg width="%s" height="%s" viewbox="0 0 %d %d">'%(w,h,nbcols,nbrows)) 
    svg.append('<defs>')
    svg.append(svgarrow())
    svg.append(svgbubble())
    svg.append('</defs>')
    svg.append('<g font-size="1">')

    for rect in shapes["rects"]: svg.append(svgrect(*rect))
    for gone in shapes["gones"]: svg.append(svggone(gone))
    for ring in shapes["rings"]: svg.append(svgring(*ring))
    for line in shapes["lines"]: svg.append(svgline(*line))
    for text in shapes["texts"]: svg.append(svgtext(*text))
    for term in shapes["terms"]: svg.append(svgobj(*term))

    svg.append('</g>')
    svg.append('</svg>')

    return "\n".join(svg)
