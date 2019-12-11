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

        self.connect_after("delete-range", self.afterDeleteRange)
        self.connect_after("insert-text",  self.afterInsertText)

        if content:
            if type(content) == ET.Element:
                content = self.from_mawe(content)
            self.begin_not_undoable_action()
            self.insert(self.get_start_iter(), content)
            self.end_not_undoable_action()
            self.place_cursor(self.get_start_iter())

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

    def get_line_start_iter(self, at = None):
        if at is None:
            start = self.get_cursor_iter()
        else:
            start = at.copy()
        start.set_line_offset(0)
        return start
    
    def get_line_end_iter(self, at = None):
        if at is None:
            end = self.get_cursor_iter()
        else:
            end = at.copy()
        if not end.ends_line(): end.forward_to_line_end()
        return end
            
    def get_line_iter(self, at = None):
        return self.get_line_start_iter(at), self.get_line_end_iter(at)

    def get_line_and_offset(self, at = None):
        if at is None: at = self.get_cursor_iter()
        return at.get_line(), at.get_line_offset()

    #--------------------------------------------------------------------------

    def expect_forward(self, start, text):
        end = self.copy_iter(start, 0, len(text))
        return self.get_text(start, end, True) == text

    def expect_backward(self, end, text):
        start = self.copy_iter(end, 0, -len(text))
        return self.get_text(start, end, True) == text

    def line_starts_with(self, text, at = None):
        if at is None: at = self.get_cursor_iter()
        return self.expect_forward(self.get_line_start_iter(at), text)

    def line_ends_with(self, text, at = None):
        if at is None: at = self.get_cursor_iter()
        return self.expect_backward(self.get_line_end_iter(at), text)
        
    #--------------------------------------------------------------------------

    def afterInsertText(self, buffer, end, text, length, *args):
        start = self.copy_iter(end, 0, -length)
        #self.dump_range("Insert", start, end)
        self.remove_scene_marks(start, end)
        self.update_tags(start, end)
    
    def afterDeleteRange(self, buffer, start, end, *args):
        self.remove_scene_marks(start, end)
        self.update_tags(start, end)
    
    #--------------------------------------------------------------------------

    def has_scene_mark(self, at):
        marks = self.get_source_marks_at_iter(at, "scene")
        return len(marks) > 0

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

    def init_marks(self):
        self.marklist = Gtk.ListStore(object, str, int, int, int)
        self.markiter = {}

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
            self.apply_tag(self.tag_fold_prot, end, fold_end)
            #print("Scene hide: %d chars" % (fold_end.get_offset() - start.get_offset()))
            
        return mark

    def is_scenebreak(self, at):
        return self.line_starts_with("##", at)

    def remove_scene_mark(self, mark):
        start = self.get_iter_at_mark(mark)
        end   = self.scene_end_iter(start)
        self.remove_tag(self.tag_fold_hide, start, end)
        self.remove_tag(self.tag_fold_prot, start, end)
        
        if (start.starts_line()
            and len(self.get_source_marks_at_iter(start, "scene")) == 1
            and self.line_starts_with("##", start)): return

        self.delete_mark(mark)
        at = self.markiter[mark]
        self.marklist.remove(at)
        del self.markiter[mark]

        #self.dump_mark("Delete", mark)

    def remove_scene_marks(self, start, end):
        start = self.get_line_start_iter(start)
        end   = self.get_line_end_iter(end)

        for mark in self.get_marks("scene", start, end):
            self.remove_scene_mark(mark)

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
    # Updating text tags after changes (insert, delete)
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
    
    def update_tags(self, start, end):
        end  = self.get_line_end_iter(end)
        line = self.get_line_start_iter(start)
        
        while(line.compare(end) < 1):
            self.update_line_tags(line, self.get_line_end_iter(line))
            if line.is_end(): break
            line.forward_line()
        else:
            self.update_indent(*self.get_line_iter(line))

        #scene = self.scene_start_iter(start)
        #self.fold_off(scene)

        #self.mark_range("debug:update", start, end)
        #self.dump_source_marks(None, *self.get_bounds())
        #self.update_marklist()
        self.update_scene_stats(start, end)
        self.update_stats()

    def update_line_tags(self, start, end):
        self.remove_tags(start, end, *self.tag_reapplied)
        
        if self.line_starts_with("##", start):
            self.update_scene(start, end)
        else:
        
            if self.line_starts_with("//", start):
                self.apply_tag_by_name("comment", start, end)
            elif self.line_starts_with("<<", start):
                self.apply_tag_by_name("synopsis", start, end)
            elif self.line_starts_with("!!", start):
                self.apply_tag_by_name("missing", start, end)
            else:
                #self.apply_tag_by_name("text", start, end)
                pass
            self.update_spans(start, end)

        self.update_indent(start, end)
        
    def update_indent(self, start, end):
        self.remove_tags(start, end, "indent")

        if(start.is_start()): return
        if start.has_tag(self.tag_scenehdr): return 
        if start.has_tag(self.tag_scenefolded): return 
        
        prev_start = self.copy_iter(start, -1, 0)
        prev_end   = self.get_line_end_iter(prev_start)
        if(prev_start.equal(prev_end)): return

        if self.has_tags(prev_start, self.tag_scenehdr): return
        if self.has_tags(prev_start, "comment", "synopsis"):
            if not self.has_tags(prev_start, "indent"): return
        self.apply_tag_by_name("indent", start, end)
        #self.dump_range("Update indent", start, end)
    
    re_bold   = re.compile("(\*[^\*\s]\*)|(\*[^\*\s][^\*]*\*)")
    re_italic = re.compile("(\_[^\_\s]\_)|(\_[^\_\s][^\_]*\_)")
    re_wc     = re.compile("\w+")
    re_multispace = re.compile("\s+")

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
        end = self.get_line_end_iter(at)
        self.insert(end, self.fold_mark)
        
    def fold_off(self, at):
        if not self.is_folded(at): return
        end = self.get_line_end_iter(at)
        self.delete(self.copy_iter(end, 0, -len(self.fold_mark)), end)

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

    #--------------------------------------------------------------------------

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
    
    def to_mawe(self):
        pass

