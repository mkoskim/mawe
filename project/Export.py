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

class ElemFmt:
    def __init__(self, prefix, postfix):
        self.prefix = prefix
        self.postfix = postfix

    def wrap(self, text, args = {}):
        return (self.prefix % args) + text + (self.postfix % args) + "\n"
    
#------------------------------------------------------------------------------

docFmt = ElemFmt("\n".join([
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
        r"\sl-440\tqr\tx8496 %(author)s: %(title)s",
        r"\tab Sivu %s (%s)" % (
            r"{\field{\*\fldinst PAGE}}",
            r"{\field{\*\fldinst NUMPAGES}}"
        ),
        r"\par}",
    ""]),
    "\n".join([
        r"}",
    ])
)

paraFirstFmt = ElemFmt(r"{\lang1035\sl-440\sb480 ", "\par}\n\n")
paraFmt      = ElemFmt(r"{\lang1035\sl-440\fi567 ", "\par}\n\n")

#------------------------------------------------------------------------------

def fmtBreak(p):
    return breakFmt.wrap("")

def fmtParagraph(p, first = False):
    if not p.text: return ""
    if first: return paraFirstFmt.wrap(p.text)
    return paraFmt.wrap(p.text)

def fmtContent(body):
    content = ""
    for scene in list(body):
        paras = list(scene)
        first = True
        for p in list(scene):
            if p.tag == "br":
                first = True
            else:
                content = content + fmtParagraph(p, first)
                first = False
    return content

#------------------------------------------------------------------------------

def RTF(doc, filename):
    root = doc.root

    #--------------------------------------------------------------------------
    # Get info
    #--------------------------------------------------------------------------

    title    = root.find("./body/head/title").text
    subtitle = root.find("./body/head/subtitle").text

    nickname = root.find("./body/head/nickname")
    if nickname is None:
        nickname = root.find("./body/head/author").text
    else:
        nickname = nickname.text

    #--------------------------------------------------------------------------
    # do content
    #--------------------------------------------------------------------------

    content = docFmt.wrap(
        fmtContent(root.find(".body/part")),
        {
            "title": title,
            "subtitle": subtitle,
            "author": nickname,
        }
    )
    content = doEscape(content)

    #--------------------------------------------------------------------------
    # Write file
    #--------------------------------------------------------------------------

    f = open(filename, "w")
    f.write(content)
    f.close()

