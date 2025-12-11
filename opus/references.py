"Reference database handler."

from pathlib import Path

import yaml


class References:
    "Reference database handler."

    def __init__(self, dirpath, formatter=None):
        self.formatter = formatter or DefaultReferenceFormatter()
        self.items = {}
        for filepath in Path(dirpath).iterdir():
            if filepath.stem == "template":
                continue
            if filepath.suffix != ".yaml":
                continue
            with open(filepath) as infile:
                item = yaml.safe_load(infile)
                name = item["name"].casefold()
                if name in self.items:
                    raise KeyError(f"reference name {name} already defined")
                self.items[name] = item
        self.used = set()

    def reset_used(self):
        self.used = set()

    def __len__(self):
        return len(self.items)

    def __getitem__(self, name):
        return self.items[name.casefold()]

    def __contains__(self, name):
        return name.casefold() in self.items

    def add(self, paragraph, name):
        "Output the short form of the named reference, and mark as used."
        if name in self:
            self.used.add(name)
        else:
            name = f"[ref? {name}]"
        self.formatter.add_short(paragraph, name)

    def write(self, document, items=None):
        "Write out list of references; by default those that have been marked used."
        if items is None:
            items = [self[name] for name in sorted(self.used)]
        with document.new_section(document.references_title):
            for item in items:
                self.formatter.add_full(document, item)


class DefaultReferenceFormatter:

    def add_short(self, paragraph, name):
        paragraph.add(name)

    def add_full(self, document, item):
        p = document.new_paragraph()
        p.add(f"{item['name']}. {item['title']}.")


if __name__ == "__main__":
    refs = References("/home/pekrau/Dropbox/bok/referenser")
    print(len(refs))
