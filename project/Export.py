###############################################################################
#
# Document exporting
#
###############################################################################

#------------------------------------------------------------------------------
# Escape sequences
#------------------------------------------------------------------------------

def doEscape(s):
    escaped = {
        "å": r"\'e5",
        "Å": r"\'c5",
        "ä": r"\'e4",
        "Ä": r"\'c4",
        "ö": r"\'f6",
        "Ö": r"\'d6",
        '"': r"\'94",
        '~': r"\~",
    }

    #s = s.encode("utf-8")
    for char in escaped.keys():
        s = s.replace(char, escaped[char])
    return s

#------------------------------------------------------------------------------
# Element formatting
#------------------------------------------------------------------------------

class Wrap:
    def __init__(self, prefix, postfix):
        self.prefix = prefix
        self.postfix = postfix

    def __call__(self, text, args = {}):
        return (self.prefix % args) + text + (self.postfix % args) + "\n"

#------------------------------------------------------------------------------

wrapDoc = Wrap("\n".join([
    r"{\rtf1\ansi",
    r"{\fonttbl\f0\froman\fcharset0 Times New Roman;}",
    r"{\info{\title %(title)s}{\author %(author)s}}",
    r"\deflang1035",
    r"\paperh16837\paperw11905",
    r"\margl1701\margr1701\margt851\margb1701",
    r"\sectd\sbknone",
    r"\pgwsxn11905\pghsxn16837",
    r"\marglsxn1701\margrsxn1701\margtsxn1701\margbsxn1701",
    r"\gutter0\ltrsect",
    r"\headery851",
    r"\lang1035\f0\fs24\fi0\li0\ri0\rin0\lin0"
    r"{\header\lang1035",
        r"\sl-440\tqr\tx8496 %(header)s",
        r"\tab Sivu %s (%s)" % (
            r"{\field{\*\fldinst PAGE}}",
            r"{\field{\*\fldinst NUMPAGES}}"
        ),
        r"\par}",
    r"{\qc{\sa480\b\fs34 %(title)s\par}}",
    ""]),
    "\n".join([
        r"}",
    ])
)

wrapPara1 = Wrap(r"{\lang1035\sl-440\sb480 ", "\par}\n\n")
wrapPara  = Wrap(r"{\lang1035\sl-440\fi567 ", "\par}\n\n")

#------------------------------------------------------------------------------

def fmtParagraph(p, first = False):
    if not p.text: return ""
    if first: return wrapPara1(p.text)
    return wrapPara(p.text)

def fmtScene(scene):
    content = ""
    first = True
    for p in list(scene):
        if p.tag == "br":
            first = True
        elif p.tag == "p":
            content = content + fmtParagraph(p, first)
            first = False
        else:
            pass
    return content

def fmtContent(body):
    content = ""

    for scene in list(body):
        name = scene.get("name")

        if content and len(name) > 0 and name[0] == "*":
            content = content + r"{\sb480\qc * * *\par}" + "\n\n"

        if name[0:5] != "skip:":
            text = fmtScene(scene)
            if text:
                content = content + text

    return content

def fmtDoc(doc):
    root = doc.root

    title    = root.find("./body/head/title").text
    subtitle = root.find("./body/head/subtitle").text

    author = root.find("./body/head/nickname")
    if author is None or not author.text:
        author = root.find("./body/head/author").text
    else:
        author = author.text

    if author:
        header = "%s: %s" % (author, title)
    else:
        header = "%s" % (title)

    content = wrapDoc(
        fmtContent(root.find(".body/part")),
        {
            "title": title,
            "subtitle": subtitle,
            "author": author,
            "header": header,
        }
    )
    content = doEscape(content)
    return content

#------------------------------------------------------------------------------

def RTF(doc, filename):
    content = fmtDoc(doc)
    f = open(filename, "w")
    f.write(content)
    f.close()

