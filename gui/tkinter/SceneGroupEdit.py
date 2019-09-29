###############################################################################
#
# Scene Group Editor is the hearth of mawe.
#
###############################################################################

from gui.tkinter.Tkinter import *
from tools.error import *

#------------------------------------------------------------------------------
#
# Text edit box:
#
# - TODO: Make it work also if editing single scene
# - TODO: Lots of quirks caused by Tkinter
# - TODO: Autoformat: When pressing enter, check the contents of the
#   line and format it, for example:
#
#   URL => clickable link
#   --- => Scene break
#
#   ...and so on.
#
# - TODO: Spellchecking
# - TODO: Search & Replace
# - TODO: Auto-tagging? Check the contents of the scenes and propose
#         tagging? Maybe writer can make some regular expressions for
#         autotagging?
#         
# - TODO: Make some sort of style library to move element/tag configs out.
#
#------------------------------------------------------------------------------

class SceneGroupText(ScrolledText):

    def __init__(self, parent, **kw):
        super(SceneGroupText, self).__init__(parent)

        self.config(
            wrap = WORD,
            
            font = ("Times New Roman", "12"),
            spacing1 = "4p",
            spacing2 = "4p",
            spacing3 = "4p",
            padx = "1c",
            pady = "1c",
            undo = True,
        )

        self.config(kw)
        
        self.bind_tags()
        self.bind_keys()

        self.pack(fill = "both", expand = "yes")

    #--------------------------------------------------------------------------

    def bind_tags(self):

        self.tag_config("scene", 
            font = ("Times New Roman", "12", "bold"),
            background = "#FAFAFA",
            foreground = "#BBBBBB",
            spacing1 = "12p",
            justify = CENTER,
        )

        self.tag_config("comment", 
            font = ("Times New Roman", "12"),
            background = "#DDEEDD",
            spacing1 = "6p",
            spacing2 = "4p",
            spacing3 = "6p",
            lmargin1 = "2c",
            lmargin2 = "2c",
            rmargin  = "1c",
        )

        self.tag_config("synopsis", 
            font = ("Times New Roman", "12"),
            background = "#FFFFCC",
            spacing1 = "8p",
            spacing2 = "4p",
            spacing3 = "8p",
            lmargin1 = "2c",
            lmargin2 = "2c",
            rmargin  = "1c",
            #elide = True,
        )

        self.tag_config("bold",
            font = ("Times New Roman", "12", "bold"),
        )

        self.tag_config("italic",
            font = ("Times New Roman", "12", "italic"),
        )

        self.tag_config("hidden", elide = True)
        self.tag_config("folded", elide = True)

        self.tag_raise("sel")

    #--------------------------------------------------------------------------

    def bind_keys(self):
        
        self.bind("<Prior>", lambda e: self.key_pgup(e))
        self.bind("<Next>", lambda e: self.key_pgdn(e))
        self.bind("<BackSpace>", lambda e: self.key_bksp(e))
        self.bind("<Delete>", lambda e: self.key_delete(e))
        self.bind("<Return>", lambda e: self.key_enter(e))

        self.bind("<Control-x>", lambda e: self.cut(e))
        self.bind("<Control-c>", lambda e: self.copy(e))
        self.bind("<Control-v>", lambda e: self.paste(e))

        #----------------------------------------------------------------------

        #self.bind("<Alt-x>", lambda e: self.toggle_scene(e))
        self.bind("<Alt-x>", lambda e: self.block_toggle(e, "scene", "comment synopsis"))
        self.bind("<Alt-c>", lambda e: self.block_toggle(e, "comment", "scene synopsis"))
        self.bind("<Alt-s>", lambda e: self.block_toggle(e, "synopsis", "scene comment"))
        self.bind("<Alt-h>", lambda e: self.block_fold(e, "comment synopsis"))
        self.bind("<Alt-f>", lambda e: self.scene_fold(e))

        self.bind("<Control-b>", lambda e: self.style_toggle(e, "bold"))
        self.bind("<Control-i>", lambda e: self.style_toggle(e, "italic"))

        #----------------------------------------------------------------------

        self.bind("<Alt-l>", lambda e: self.insert_lorem(e))
        self.bind("<Alt-L>", lambda e: self.insert_lorem(e))
        self.bind("<Control-r>", lambda e: self.report(e))        
        #self.bind("<Key>", lambda e: self.trace_key(e))

    #--------------------------------------------------------------------------

    def trace_key(self, event):
        print("Key:", event.keycode, event.state)
        
    def tag_ranges(self, tag):
        ranges = super(SceneGroupText, self).tag_ranges(tag)
        return tuple(zip(ranges[0::2], ranges[1::2]))
        
    def report(self, event):
        print("Report:")
        for tag in self.tag_names():
            ranges = self.tag_ranges(tag)
            if ranges: print(tag, ranges)
        pass

    #--------------------------------------------------------------------------

    modifiers = {
        "Shift":    0x0001,
        "Control":  0x0004,
    }

    def key_modifiers(self, event):
        mods = modifiers.keys()
        return filter(lambda m: event.state & modifiers[m], mods)

    def hasModifier(self, event, modifier):
        return modifier in key_modifiers(event)

    def addModifiers(self, event, *mods):
        state = event.state
        for m in mods: state = state | self.modifiers[m]
        return state

    #--------------------------------------------------------------------------

    def Position(self, mark = INSERT):

        class _Position:
            def __init__(self, text, mark = INSERT):
                self.text = text
                self.line, self.column = tuple(map(int, self.text.index(mark).split(".")))
            
            def __str__(self):
                return "%s.%s" % (str(self.line), str(self.column))
            
            def isVisible(self):
                return self.text.dlineinfo(str(self)) != None
            
            def apply(self, mark):
                self.text.mark_set(mark, self.asString())

        return _Position(self, mark)

    #--------------------------------------------------------------------------

    def Range(self, start = SEL_FIRST, end = SEL_LAST):

        class _Range:
        
            def __init__(self, text, start, end):

                def get(index):
                    try:
                        return text.index(index)
                    except TclError:
                        return None

                if not end: end = start
                self.start, self.end = (get(start), get(end))

            def range(self):
                return (self.start, self.end)
                
            def valid(self):
                return self.range() != (None, None)

        return _Range(self, start, end)

    #--------------------------------------------------------------------------

    def emit(self, text = None, tag = None):
        start = self.index(INSERT)
        if text:
            self.insert(INSERT, text)
            if tag: self.tag_add(tag, start, INSERT)
        self.see(INSERT)
        return self.index(INSERT)

    #--------------------------------------------------------------------------

    def hasTag(self, tags, index = INSERT):
        tags = tags.split()
        return tuple(filter(lambda t: t in tags, self.tag_names(index)))

    #--------------------------------------------------------------------------
    # Fixing page up & down.
    #--------------------------------------------------------------------------
    
    def key_pgup(self, event):
        vbpos = self.vbar.get()
        
        if(vbpos[0] == 0.0):
            self.event_generate("<Key-Home>", state = self.addModifiers(event, "Control"))
            return "break"

    def key_pgdn(self, event):
        endat = self.Position("end -1 char")

        if(endat.isVisible()):
            self.event_generate("<Key-End>", state = self.addModifiers(event, "Control"))
            return "break"

    #--------------------------------------------------------------------------

    def block_range(self, block, index = INSERT):

        class _Block:

            def __init__(self, hdr, content):
                self.header  = hdr
                self.content = content

            def __str__(self):
                return "Block: (%s - %s) + (%s - %s)" % (
                    self.header.start, self.header.end,
                    self.content.start, self.content.end
                )

        prev = self.tag_prevrange("scene", index)
        if not prev: return None

        next = self.tag_nextrange("scene", prev[1])
        if not next: next = (END, END)

        return _Block(
            self.Range(prev[0], prev[1]),
            self.Range(prev[1], next[0])
        )

    #--------------------------------------------------------------------------

    def key_bksp(self, event):
        current = self.hasTag("scene comment synopsis hidden")
        next    = self.hasTag("scene comment synopsis hidden", "insert -1 char")
        
        if current != next:
            self.event_generate("<Key-Left>")
            return "break"

    def key_delete(self, event):
        current = self.hasTag("scene comment synopsis hidden")
        next    = self.hasTag("scene comment synopsis hidden", "insert +1 char")
        
        if current != next:
            self.event_generate("<Key-Right>")
            return "break"

    def key_enter(self, event):
        if(self.hasTag("scene")):
            scene = self.block_range("scene", "insert lineend")
            self.tag_remove("folded", scene.content.start, scene.content.end)
            self.mark_set("insert", scene.content.start)
            return "break"

    #--------------------------------------------------------------------------

    def cut(self, event):
        #log("Cut")
        pass
        
    def copy(self, event):
        #log("Copy")
        pass
        
    def paste(self, event):
        #log("Paste")
        pass

    #--------------------------------------------------------------------------

    def block_toggle(self, event, block, override = ""):
        for tag in override.split():
            self.tag_remove(tag, "insert linestart", "insert lineend+1c")
            
        isblock = self.hasTag(block, "insert linestart")
        print(isblock)
        if isblock:
            self.tag_remove(block, "insert linestart", "insert lineend+1c")
        else:
            self.tag_add(block, "insert linestart", "insert lineend+1c")

    def block_fold(self, event, blocks):
        for tag in blocks.split():
            hide = self.tag_cget(tag, "elide")
            if not hide: hide = 0
            hide = int(hide)
            self.tag_config(tag, elide = not hide)
        
    def scene_fold(self, event):
        scene = self.block_range("scene", "insert lineend")
        #print(self.index(INSERT), self.index("insert lineend"), str(scene))

        if scene:
            start, end = scene.content.start, scene.content.end
            if self.hasTag("folded", start):
                self.tag_remove("folded", start, end)
            else:
                self.tag_add("folded", start, end)
                self.mark_set("insert", scene.header.start)
        pass

    #--------------------------------------------------------------------------

    def style_toggle(self, event, style):
        sel = self.Range()
        if sel.valid():
            if self.hasTag(style, sel.start):
                self.tag_remove(style, sel.start, sel.end)
            else:
                self.tag_add(style, sel.start, sel.end)
        return "break"

    #--------------------------------------------------------------------------

    def insert_lorem(self, event):
        self.emit(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit, " +
            "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. " +
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris " +
            "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in " +
            "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla " +
            "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in " +
            "culpa qui officia deserunt mollit anim id est laborum.\n"
        )
        self.edit_separator()

###############################################################################
#
# SceneGroupEditor
#
###############################################################################

class SceneGroupEditor(Frame):

    def __init__(self, parent, **kw):
        super(SceneGroupEditor, self).__init__(parent)
        self.configure(kw)
    
        self.filename  = Label(self, text = "Filename:")
        self.filename.pack()
        self.groupname = Label(self, text = "Group:")
        self.groupname.pack()
        self.textbox   = SceneGroupText(self)
        self.textbox.pack()
        self.textbox.focus()

        self.pack()

