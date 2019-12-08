from gui.gtk import Gtk, Gdk, Pango, GtkSource
import os

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

        self.marklist = Gtk.TextBuffer()
        self.marks = {}

        self.set_highlight_matching_brackets(False)

        self.connect_after("delete-range", self.afterDeleteRange)
        self.connect_after("insert-text",  self.afterInsertText)

        if content:
            print("Loading")
            self.begin_not_undoable_action()
            self.insert(self.get_start_iter(), content)
            self.end_not_undoable_action()
            self.place_cursor(self.get_start_iter())
        else:
            print("Empty")

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
            at = self.get_cursor_iter()
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

    def get_source_marks(self, category, start, end):
        marks = []
        at = start.copy()
        while at.compare(end) < 1:
            marks = marks + self.get_source_marks_at_iter(at)
            if not self.forward_iter_to_source_mark(at, category): break
        return marks

    def create_scene_mark(self, at):
        start, end = self.get_line_iter(at)
        mark = self.create_source_mark(None, "scene", start)
        self.marks[mark] = self.get_text(start, end, False)[2:].strip()

        #self.dump_mark("Created", mark)
        if self.is_folded(start):
            fold_start = end.copy()
            fold_start.forward_char()
            fold_end = self.scene_end_iter(end)
            self.apply_tag(self.tag_fold_hide, fold_start, fold_end)
            self.apply_tag(self.tag_fold_prot, end, fold_end)
            #print("Scene hide: %d chars" % (fold_end.get_offset() - start.get_offset()))
            
        return mark

    def remove_scene_mark(self, mark):
        #self.dump_mark("Delete", mark)

        start = self.get_iter_at_mark(mark)
        end   = self.scene_end_iter(start)
        self.remove_tag(self.tag_fold_hide, start, end)
        self.remove_tag(self.tag_fold_prot, start, end)
        
        self.delete_mark(mark)
        del self.marks[mark]

    def remove_scene_marks(self, start, end):
        start = self.get_line_start_iter(start)
        end   = self.get_line_end_iter(end)

        for mark in self.get_source_marks("scene", start, end):
            self.remove_scene_mark(mark)

    def update_scene(self, start, end):
        self.apply_tag(self.tag_scenehdr, start, end)
        if self.is_folded(start):
            self.apply_tag(self.tag_scenefolded,
                self.copy_iter(start, 0, -1),
                end
            )

        self.create_scene_mark(start)

    def update_marklist(self):
        text = ""
        for mark in self.get_source_marks("scene", *self.get_bounds()):
            name = self.marks[mark]
            if len(name) > 40: name = name[:37] + "..."
            text = text + name + "\n"
        self.marklist.delete(*self.marklist.get_bounds())
        self.marklist.insert_at_cursor(text)
        
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
        self.update_marklist()

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
    
    import re
    re_bold   = re.compile("(\*[^\*\s]\*)|(\*[^\*\s][^\*]*\*)")
    re_italic = re.compile("(\_[^\_\s]\_)|(\_[^\_\s][^\_]*\_)")
    
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

        set_tags("bold",   self.re_bold)
        set_tags("italic", self.re_italic)

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

    def dump_source_marks(self, category, start, end):
        print("Marks:")
        for mark in self.get_source_marks(category, start, end):
            self.dump_mark("-", mark)

