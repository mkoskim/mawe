MAWE
====

MAWE - My Advanced Writer's Editor - for Linux, written with Python/GTK.

Mawe is successor for Moe (https://github.com/mkoskim/moe). Moe itself is very usable editor for writers, and it has been my workhorse for years. Even that it handles certain things better than e.g. Scrivener (in my opinion), it has certain drawbacks from its fundamental design decisions.

Mawe tries to fix the problems in moe by taking a different approach at very basic level.

---

As most of the writer's editors nowadays in the market (scrivener, manuskript, ywriter, ...), moe is also based on the hierarchial tree of "scenes". All these editors are like mail clients - on your left hand, you have scene hierarchy, and on right hand you have one scene opened.

The idea sounds good at first, BUT a story, a book, is not like that. A book is a sequence of scenes and chapters. That is what you want to create - you don't want to create a hierarchy of scenes, groups, parts, lots of interconnected metatext, links, tags and such. No, you want to create a sequence of chapters.

Very coarsely speaking, the fundamental difference between unstructured editors (like Notepad, Microsoft Word and googledocs) compared to structured ones is: in unstructured editors you write the draft and it can generate Table of Content, while in structured editors you create ToC and it generates the draft.

Structured editors are way better for story writing, true, but you might have hard times to see the actual result, and you keep generating "drafts", reading them and going back to scene hierarchy to edit the story and print out next draft.

I fought against this problem when developing Moe editor. It has half-working "draft" view to edit the story, but because of the underlying structure it is close impossible to give the writer free hands to modify the draft.

Mawe tries to tackle the problems by creating an editor in between these two lands. Very simply speaking, it is meant to be a text editor, which (1) maintains the ToC while you write your story like Word and googledocs, and (2) where you can modify the story by modifying the ToC like with Scrivener and yWriter.
