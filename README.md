MAWE
====

MAWE - My Advanced Writer's Editor - written with Python.

Keep in mind, that this is also sketching for web version.

---

Mawe is based on Moe (https://github.com/mkoskim/moe). Moe itself is very usable editor for writers, and it has been my workhorse for years. Even that it handles certain things better than e.g. Scrivener (in my opinion), it has certain drawbacks, which come from the very fundamental design principles.

Mawe is a text editor project for writers, which tries to fix the problems in moe by taking a different approach at very basic level.

Moe, as well as most of the writer's editors - scrivener, storybook, ywriter, ... - nowadays in the market, is based on the hierarchial list of "scenes", an undividable piece of text. All these editors are like mail clients - on the left hand, you have list of mails, and on the right hand you have one mail opened.

The idea sounds good, BUT a story, a book, is not like that. A book is a sequence of characters, a sequence of scenes and chapters. That is what you want to create - you don't want to create a hierarchy of scenes, groups, parts, lots of interconnected metatext, links, tags and such, no. You want to create a sequence of chapters. That is why I decided to start develop mawe.

It can be hard to explain this fundamental difference here shortly, but I try. Shortly speaking, unstructured editors like word and googledocs are meant to write drafts and generate ToCs (Table of Content), while in structured editors like scrivener, ywriter, storybook and moe you create the ToC and generate drafts.

Structured editors are way better for story writing, true, but you might have hard times to see how the actual result looks like - you keep generating "drafts", reading them and going back to scene hierarchy to edit the story and print out next draft.

I fought against this problem when developing Moe editor. It has half-working "draft" view to edit the story, but because of the underlying structure it is close impossible to give the writer free hands to modify the draft.

Mawe tries to tackle the problems by creating an editor in between these two lands. Very simply speaking, it is meant to be a text editor, which (1) maintains the ToC when you write your story like Word and googledocs, and (2) where you can modify the story by modifying the ToC like with Scrivener and yWriter.
