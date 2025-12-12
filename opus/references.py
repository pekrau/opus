"Reference database handler."

from pathlib import Path

import yaml

MAX_AUTHORS = 2


class References:
    "Reference database handler."

    def __init__(self, dirpath, formatter=None):
        self.dirpath = Path(dirpath).expanduser().resolve()
        self.formatter = formatter or DefaultReferenceFormatter()
        self.items = {}
        for filepath in self.dirpath.iterdir():
            if filepath.stem.startswith("template"):
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

    def output(self, document, items=None):
        "Output list of references; by default those that have been marked used."
        if not self.used:
            return
        with document.no_numbers():
            if items is None:
                items = [self[name] for name in sorted(self.used)]
            with document.new_section(document.references_title):
                for item in items:
                    self.formatter.add_full(document, item)
            document.flush()


class DefaultReferenceFormatter:

    def add_short(self, paragraph, name):
        with paragraph.bold():
            paragraph.add(name)

    def add_full(self, document, item):
        p = document.new_paragraph()
        authors = item.get("authors") or []
        p.add(", ".join([self.format_name(a) for a in authors[:MAX_AUTHORS]]))
        if len(authors) > MAX_AUTHORS:
            p.add_raw(",")
            with p.italic():
                p.add("et al.")
        p.add_raw(".")
        p.add(item["year"])
        if published := item.get("edition_published"):
            p.add(f"[{published}]")
        p.add_raw(".")

        match item["type"]:
            case "book":
                with p.italic():
                    p.add(f"{item['title'].rstrip('.')}.")
                    if subtitle := item.get("subtitle"):
                        p.add(f"{subtitle.rstrip('.')}.")
                if item.get("publisher"):
                    p.add(f"{item['publisher']}.")
            case "article":
                p.add(f"{item['title'].rstrip('.')}.")
                with p.italic():
                    p.add(item["journal"])
                if volume := item.get("volume"):
                    p.add_raw(f", {volume}")
                if number := item.get("number"):
                    p.add_raw(f"({number})")
                if pages := item.get("pages"):
                    p.add_raw(f", {pages.replace('--', '-')}.")
            case "website":
                p.add(f"{item['title'].rstrip('.')}.")
                p.add_link(item["url"])
                if accessed := item.get("accessed"):
                    p.add(f"({accessed})")

    def format_name(self, author):
        parts = [p.strip() for p in author.split(",")]
        name = parts[0]
        if len(parts) > 1:
            name += ", " + parts[1].split()[0]
            if len(parts) > 2:
                name += ", " + parts[2]
        return name


if __name__ == "__main__":
    refs = References("/home/pekrau/Dropbox/bok/referenser")
    print(len(refs))
