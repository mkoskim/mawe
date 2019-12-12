from gui.gtk import Gtk, Gdk, Pango, GtkSource
import os, re
from collections import namedtuple
from project.Document import ET, FormatError, Document
from tools import *

###############################################################################        
###############################################################################        
#
class SceneBuffer(GtkSource.Buffer):
#
###############################################################################        
###############################################################################        

    def __init__(self, content = None):
        super(SceneBuffer, self).__init__()

        self.create_tags()
        self.init_marks()

        self.stats = namedtuple("Stats", ["words", "chars"])
        self.stats.words = Gtk.Label()
        self.stats.chars = Gtk.Label()

        self.set_highlight_matching_brackets(False)

        if content: self.revert(content)
        self.update(*self.get_bounds())

        self.connect_after("delete-range", self.afterDeleteRange)
        self.connect_after("insert-text",  self.afterInsertText)

    #--------------------------------------------------------------------------
    
    def create_tags(self):

        # Span tags
        self.create_tag("bold",   weight = Pango.Weight.BOLD)
        self.create_tag("italic", style  = Pango.Style.ITALIC)

        # Block tags
        self.create_tag("indent", indent = 30)
        self.create_tag("text")
        self.create_tag("synopsis",
            paragraph_background = "#FFD",
        )
        self.create_tag("comment",
            #foreground = "#474",
            paragraph_background = "#DFD",
        )
        self.create_tag("missing",
            foreground = "#B22",
        )

        # Heading tags
        self.create_tag("title",
            foreground = "#444",
            scale = 1.5,
            justification = Gtk.Justification.CENTER,
            weight = Pango.Weight.BOLD,
            #pixels_above_lines = 20,
            pixels_below_lines = 10,
        )

        # Scene headers & folding
        self.create_tag("scene:heading",
            foreground = "#888",
            #justification = Gtk.Justification.CENTER,
            weight = Pango.Weight.BOLD,
            #pixels_above_lines = 20,
            pixels_below_lines = 5,
        )
        self.create_tag("scene:folded",
            #foreground = "#777",
            #justification = Gtk.Justification.LEFT,
            paragraph_background = "#EEE",
            #pixels_above_lines = 10,
            pixels_below_lines = 0,
            editable = False,
        )
        
        self.create_tag("fold:protect", editable = False),
        self.create_tag("fold:hidden",
            editable   = False,
            invisible  = True,
            paragraph_background = "#DDD",
            foreground = "#888",
            scale = 0.8,
        )

        self.create_tag("debug:update",
            background = "#DDD",
        )

        self.tagtbl = self.get_tag_table()
        self.tag_scenehdr    = self.tagtbl.lookup("scene:heading")
        self.tag_scenefolded = self.tagtbl.lookup("scene:folded")
        self.tag_fold_hide   = self.tagtbl.lookup("fold:hidden")
        self.tag_fold_prot   = self.tagtbl.lookup("fold:protect")

        self.tag_reapplied = [
            self.tag_scenehdr, self.tag_scenefolded,
            "comment", "synopsis", "missing",
            "bold", "italic",
        ]

    #--------------------------------------------------------------------------
    
    def get_cursor_iter(self):
        return self.get_iter_at_mark(self.get_insert())
    
    def copy_iter(self, at, line_delta, char_delta):
        at = at.copy()
        at.forward_lines(line_delta)
        at.forward_chars(char_delta)
        return at

    def get_line_start(self, at = None):
        if at is None:
            start = self.get_cursor_iter()
        else:
            start = at.copy()
        start.set_line_offset(0)
        return start
    
    def get_line_end(self, at = None):
        if at is None:
            end = self.get_cursor_iter()
        else:
            end = at.copy()
        if not end.ends_line(): end.forward_to_line_end()
        return end
            
    def get_line_iter(self, at = None):
        return self.get_line_start(at), self.get_line_end(at)

    def get_line_and_offset(self, at = None):
        if at is None: at = self.get_cursor_iter()
        return at.get_line(), at.get_line_offset()

    def make_iter_to_line(self, line, offset = 0):
        at = self.get_start_iter()
        at.set_line(line)
        at.set_line_offset(offset)
        return at

    #--------------------------------------------------------------------------

    def get_text_forward(self, start, count):
        end = self.copy_iter(start, 0, count)
        return self.get_text(start, end, True)

    def expect_forward(self, start, text):
        return self.get_text_forward(start, len(text)) == text

    def get_text_backward(self, end, count):
        start = self.copy_iter(end, 0, -count)
        return self.get_text(start, end, True)
        
    def expect_backward(self, end, text):
        return self.get_text_backward(end, len(text)) == text

    def line_starts_with(self, text, at = None):
        if at is None: at = self.get_cursor_iter()
        return self.expect_forward(self.get_line_start(at), text)

    def line_ends_with(self, text, at = None):
        if at is None: at = self.get_cursor_iter()
        return self.expect_backward(self.get_line_end(at), text)
        
    #--------------------------------------------------------------------------

    def scene_first_iter(self):
        at = self.get_start_iter()
        if self.has_scene_mark(at): return at
        return self.scene_next_iter(at)

    def scene_next_iter(self, at):
        at = at.copy()
        if not self.forward_iter_to_source_mark(at, "scene"):
            return None
        return at

    def scene_prev_iter(self, at):
        at = at.copy()
        if not self.backward_iter_to_source_mark(at, "scene"):
            return None
        return at

    def scene_start_iter(self, at = None):
        if at is None: at = self.get_cursor_iter()
        if self.has_scene_mark(at): return at.copy()
        return self.scene_prev_iter(at)
        
    def scene_end_iter(self, at = None):
        if at is None: at = self.get_cursor_iter()
        end = self.scene_next_iter(at)
        if end is None: return self.get_end_iter()
        return end

    #--------------------------------------------------------------------------

    def has_tags(self, at, *tags):
        for tag in tags:
            if type(tag) is str: tag = self.tagtbl.lookup(tag)
            if at.has_tag(tag): return True
        return False
    
    def remove_tags(self, start, end, *tags):
        for tag in tags:
            if type(tag) is str: tag = self.tagtbl.lookup(tag)
            self.remove_tag(tag, start, end)
    
    #--------------------------------------------------------------------------
    # Marks
    #--------------------------------------------------------------------------

    def init_marks(self):
        self.marklist = Gtk.ListStore(object, str, int, int, int)
        self.markiter = {}

    #def has_scene_mark(self, at):
    #    marks = self.get_source_marks_at_iter(at, "scene")
    #    return len(marks) > 0

    def get_marks(self, category, start, end):
        marks = []
        at = start.copy()
        while at.compare(end) < 1:
            marks = marks + self.get_source_marks_at_iter(at)
            if not self.forward_iter_to_source_mark(at, category): break
        return marks

    def create_scene_mark(self, at):
        start, end = self.get_line_iter(at)

        if len(self.get_source_marks_at_iter(start, "scene")) == 1:
            mark = self.get_source_marks_at_iter(start, "scene")[0]
            listiter = self.markiter[mark]
        else:
            previter = self.scene_prev_iter(at)
            if previter:
                prevmark = self.get_source_marks_at_iter(previter)[0]
                previter = self.markiter[prevmark]
            else:
                previter = None
            mark  = self.create_source_mark(None, "scene", start)
            listiter = self.marklist.insert_after(previter, [mark, "", 0, 0, 0])

        self.markiter[mark] = listiter
        name  = self.get_text(start, end, False)[2:].strip()        
        self.marklist.set_value(listiter, 1, name)

        #self.dump_mark("Created", mark)
        if self.is_folded(start):
            fold_start = end.copy()
            fold_start.forward_char()
            fold_end = self.scene_end_iter(end)
            self.apply_tag(self.tag_fold_hide, fold_start, fold_end)
            self.apply_tag(self.tag_fold_prot, start, fold_end)
            #print("Scene hide: %d chars" % (fold_end.get_offset() - start.get_offset()))
            
        return mark

    def remove_mark(self, mark, category = "scene"):
        start = self.get_iter_at_mark(mark)
        end   = self.scene_end_iter(start)
        self.remove_tag(self.tag_fold_hide, start, end)
        self.remove_tag(self.tag_fold_prot, start, end)
        
        if (start.starts_line()
            and len(self.get_source_marks_at_iter(start, category)) == 1
            and self.line_starts_with("##", start)): return

        self.delete_mark(mark)
        at = self.markiter[mark]
        self.marklist.remove(at)
        del self.markiter[mark]

        #self.dump_mark("Delete", mark)

    def remove_marks(self, start, end, category = "scene"):
        #start = self.get_line_start(start)
        #end   = self.get_line_end(end)

        for mark in self.get_marks(category, start, end):
            self.remove_mark(mark, category)

    #--------------------------------------------------------------------------
    # Improve update cycle
    #--------------------------------------------------------------------------

    def afterInsertText(self, buffer, end, text, length, *args):
        start = self.copy_iter(end, 0, -length)
        self.update(start, end)
    
    def afterDeleteRange(self, buffer, start, end, *args):
        self.update(start, end)
    
    #--------------------------------------------------------------------------

    def update(self, start, end):
        first_line = start.get_line()
        last_line  = end.get_line()

        def get_initial_mode(line):
            line_start = self.make_iter_to_line(line)
            starts_with = self.get_text_forward(line_start, 2)
            if starts_with == "##": return (False, False)
            if line == 0: return (False, True)
            if line_start.equal(self.get_line_end(line_start)): return (False, False)
            return (self.has_tags(line_start, "indent"), True)

        def apply_indent(start, end, mode, nextmode):
            if mode: self.apply_tag_by_name("indent", start, end)
            return (mode, nextmode)

        if first_line != 0:
            previndent, indentmode = get_initial_mode(first_line - 1)
        else:
            previndent, indentmode = (False, False)

        for line in range(first_line, last_line + 1):
            line_start = self.make_iter_to_line(line)
            line_end   = self.get_line_end(line_start)

            self.dump_range("Update %d (%d)" % (indentmode, previndent), line_start, line_end)

            self.remove_tags(line_start, line_end, *self.tag_reapplied, "indent")
            if line_start.equal(line_end):
                previndent, indentmode = apply_indent(line_start, line_end, False, True)
                continue

            starts_with = self.get_text_forward(line_start, 2)

            if starts_with == "##":
                previndent, indentmode = apply_indent(line_start, line_end, False, False)
            else:
                self.update_spans(line_start, line_end)
                
                if starts_with == "<<":
                    previndent, indentmode = apply_indent(line_start, line_end, previndent, previndent)
                    self.apply_tag_by_name("synopsis", line_start, line_end)
                elif starts_with == "//":
                    previndent, indentmode = apply_indent(line_start, line_end, previndent, previndent)
                    self.apply_tag_by_name("comment", line_start, line_end)
                elif starts_with == "!!":
                    previndent, indentmode = apply_indent(line_start, line_end, previndent, previndent)
                    self.apply_tag_by_name("missing", line_start, line_end)
                else:
                    previndent, indentmode = apply_indent(line_start, line_end, indentmode, True)
                    #self.dump_range("Update %d" % indentmode, line_start, line_end)

        def apply_next_indent(line, previndent, indentmode):
            line_start = self.make_iter_to_line(line)
            line_end   = self.get_line_end(line_start)

            if line_start.equal(self.get_start_iter()): return
            if line_start.equal(self.get_end_iter()): return

            self.remove_tags(line_start, line_end, "indent")
            if line_start.equal(line_end): return

            starts_with = self.get_text_forward(line_start, 2)
            if starts_with == "##": return
            if starts_with in ["!!", "//", "<<"]:
                if previndent: self.apply_tag_by_name("indent", line_start, line_end)
            if indentmode:
                self.apply_tag_by_name("indent", line_start, line_end)

        apply_next_indent(last_line + 1, previndent, indentmode)


            #print("Update line:", starts_with, line)

        #print("Update:", first_line, last_line)
        #self.remove_marks(start, end, "scene")

    #--------------------------------------------------------------------------

    re_bold   = re.compile(r"(\*[^\*\s]\*)|(\*[^\*\s][^\*]*\*)")
    re_italic = re.compile(r"(\_[^\_\s]\_)|(\_[^\_\s][^\_]*\_)")

    def update_spans(self, start, end):
        start = start.copy()
        end   = end.copy()
        text  = self.get_text(start, end, True)

        def set_tags(tagname, regex):
            for m in regex.finditer(text):
                start.set_line_offset(m.start())
                end.set_line_offset(m.end())
                self.apply_tag_by_name(tagname, start, end)
                #print(m.start(), m.end(), m.group())

        set_tags("bold",   SceneBuffer.re_bold)
        set_tags("italic", SceneBuffer.re_italic)

    def update_scene(self, start, end):
        self.apply_tag(self.tag_scenehdr, start, end)
        if self.is_folded(start):
            self.apply_tag(self.tag_scenefolded, start, end)

        self.create_scene_mark(start)

    def update_scene_stats(self, start, end):
        start = self.scene_prev_iter(start)
        if start is None: start = self.get_start_iter()
        end   = self.scene_end_iter(end)

        for mark in self.get_marks("scene", start, end):
            index = self.markiter[mark]
            start = self.get_iter_at_mark(mark)
            end   = self.scene_end_iter(start)
            
            words, _, comments, missing = self.wordcount(start, end, True)
            self.marklist.set_value(index, 2, words)
            self.marklist.set_value(index, 3, comments)
            self.marklist.set_value(index, 4, missing)

    #--------------------------------------------------------------------------
    # Folding:
    #--------------------------------------------------------------------------

    #fold_mark = " [folded]"
    #fold_mark = " [⋅⋅⋅]"
    #fold_mark = " ▶"
    #fold_mark = " ⋙"
    #fold_mark = " [•••]"
    fold_mark = " [+]"

    def is_folded(self, at):
        return self.line_ends_with(self.fold_mark, at)

    def fold_on(self, at):
        if self.is_folded(at): return
        end = self.get_line_end(at)
        self.insert(end, self.fold_mark)
        
    def fold_off(self, at):
        if not self.is_folded(at): return
        end = self.get_line_end(at)
        self.delete(self.copy_iter(end, 0, -len(self.fold_mark)), end)

    #--------------------------------------------------------------------------

    re_wc = re.compile(r"\w+")

    def wordcount(self, start, end, details = False):
        text  = self.get_text(start, end, True)
        text  = text.split("\n")

        if details:
            comments = filter(lambda s: s[:2] == "//", text)
            comments = "\n".join(list(comments))
            comments = len(SceneBuffer.re_wc.findall(comments))
            
            missing  = filter(lambda s: s[:2] == "!!", text)
            missing  = "\n".join(list(missing))
            missing  = len(SceneBuffer.re_wc.findall(missing))
        
        text  = filter(lambda s: s[:2] not in ["<<", "//", "!!", "##"], text)
        text  = "\n".join(list(text))
        chars = len(text)
        words = len(SceneBuffer.re_wc.findall(text))

        if details:
            return words, chars, comments, missing
        else:
            return words, chars
    
    def update_stats(self):
        words, chars = self.wordcount(*self.get_bounds())
        self.stats.words.set_text("Words: %d" % words)
        self.stats.chars.set_text("Chars: %d" % chars)

    #--------------------------------------------------------------------------

    def from_mawe(self, part):

        def strip(text):
            if text: return re.sub(self.re_multispace, " ", text).strip()
            return ""

        def parse_scene(scene):
            text = "## %s\n" % scene.get("name", "<Scene>")
            for paragraph in list(scene):
                if   paragraph.tag == "p":        text = text + strip(paragraph.text) + "\n"
                elif paragraph.tag == "br":       text = text + "\n"
                elif paragraph.tag == "comment":  text = text + "//" + strip(paragraph.text) + "\n"
                elif paragraph.tag == "synopsis": text = text + "<<" + strip(paragraph.text) + "\n"
                elif paragraph.tag == "missing":  text = text + "!!" + strip(paragraph.text) + "\n"
                else: log("Unknown paragraph type: %s" % paragraph.tag)
            return text

        text = ""
        for child in list(part):
            if child.tag == "scene": text = text + parse_scene(child) + "\n"
            else: log("Unknown element: %s" % child.tag)
        return text
    
    def revert(self, content):
        if type(content) == ET.Element:
            content = self.from_mawe(content)

        self.begin_not_undoable_action()
        start, end = self.get_bounds()
        self.remove_marks(start, end, None)
        self.delete(start, end)
        self.insert(self.get_start_iter(), content)
        self.end_not_undoable_action()

        self.set_modified(False)
        self.place_cursor(self.get_start_iter())

    re_scenes     = re.compile(r"^##", re.M)
    re_tripleLF   = re.compile(r"\n\n+", re.M)
    re_multispace = re.compile(r"\s+")

    def to_mawe(self):
        text   = self.get_text(*self.get_bounds(), True).lstrip()
        if text[:2] != "##": text = "##\n" + text

        scenes = SceneBuffer.re_scenes.split(text)[1:]

        part = ET.Element("part")

        for scene in scenes:
            name, *scene = *scene.rstrip().split("\n", 1), ""
            scene = "".join(scene)

            if name[-len(SceneBuffer.fold_mark):] == SceneBuffer.fold_mark:
                name = name[:-3]
            name  = name.strip()

            elem = ET.SubElement(part, "scene")
            elem.set("name", name)

            def addlines(subscene):
                for line in subscene.split("\n"): 
                    line = re.sub(SceneBuffer.re_multispace, " ", line.strip())
                    if   line[:2] == "<<": ET.SubElement(elem, "synopsis").text = line[2:]
                    elif line[:2] == "//": ET.SubElement(elem, "comment").text = line[2:]
                    elif line[:2] == "!!": ET.SubElement(elem, "missing").text = line[2:]
                    elif len(line): ET.SubElement(elem, "p").text = line
                    else: pass

            scene = scene.strip()
            scene = re.sub(SceneBuffer.re_tripleLF, "\n\n", scene)

            subscenes = scene.split("\n\n")

            for subscene in subscenes[:-1]:
                addlines(subscene)
                ET.SubElement(elem, "br")
            addlines(subscenes[-1])

            #ET.dump(elem)

        return part

    #--------------------------------------------------------------------------

    def dump_iter(self, prefix, at):
        print("%s: %d:%d" % (prefix, *self.get_line_and_offset(at)))
        
    def dump_range(self, prefix, start, end):
        print("%s: %d:%d - %d:%d" % (
            prefix,
            *self.get_line_and_offset(start),
            *self.get_line_and_offset(end)
        ))

    def dump_mark(self, prefix, mark):
        if mark in self.marks:
            text = self.marks[mark]
        else:
            text = None
        category = mark.get_category()
        name = mark.get_name()
        line, offset = self.get_line_and_offset(self.get_iter_at_mark(mark))
        print("%s %s.%s: %d:%d %s" % (
            prefix,
            category, name,
            line + 1, offset,
            text[:20]
        ))

    def dump_marks(self, category, start, end):
        print("Marks:")
        for mark in self.get_marks(category, start, end):
            self.dump_mark("-", mark)

