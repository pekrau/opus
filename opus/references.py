"Reference database handler."

from pathlib import Path
import unicodedata

import yaml


def to_stem(s):
    """- Convert all non-ASCII characters to closest ASCII
    - Lowercase
    - Replace blank with dash
    """
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    return s.lower().replace(" ", "-")


class References:
    "Reference database handler."

    def __init__(self, dirpath, formatter=None):
        self.dirpath = Path(dirpath).expanduser().resolve()
        self.formatter = DefaultReferenceFormatter()
        self.items = {}
        for filepath in self.dirpath.iterdir():
            if filepath.stem.startswith("template"):
                continue
            if filepath.suffix != ".yaml":
                continue
            with open(filepath) as infile:
                try:
                    item = yaml.safe_load(infile)
                except yaml.parser.ParserError as error:
                    raise ValueError(f"Invalid YAML in {filepath}")
                else:
                    try:
                        name = item["name"]
                    except KeyError:
                        raise KeyError(f"missing 'name' in {filepath}")
                    name = name.casefold()
                    if to_stem(name) != filepath.stem:
                        raise ValueError(f"name/filename mismatch for {filepath}")
                    if name in self.items:
                        raise KeyError(f"reference name {name} already defined")
                    self.items[name] = item
        self.used = set()

    def reset_used(self):
        self.used = set()

    def __iter__(self):
        return (self[name] for name in sorted(self.used))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, name):
        return self.items[name.casefold()]

    def __contains__(self, name):
        return name.casefold() in self.items

    def add(self, paragraph, name, raw=False):
        "Output the short form of the named reference, and mark as used."
        try:
            item = self[name]
        except KeyError:
            paragraph += f"[ref? {name}]"
            print(f"Missing reference {name}")
        else:
            self.used.add(name)
            self.formatter.add_short(paragraph, item, raw=raw)


class DefaultReferenceFormatter:
    "Default reference formatter."

    def add_short(self, paragraph, item, raw=False):
        with paragraph.italic():
            paragraph.add(item["name"], raw=raw)

    def add_full(self, document, item, raw=False, max_authors=4):
        p = document.new_paragraph()
        authors = item.get("authors") or []
        p.add(", ".join([self.format_name(a) for a in authors[:max_authors]]), raw=raw)
        if len(authors) > max_authors:
            p.raw(",")
            with p.italic():
                p.add("et al")
        p.raw(".")
        p.add(item["year"])
        if published := item.get("edition_published"):
            p.add(f"[{published}]")
        p.raw(".")

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
                    p.raw(f", {volume}")
                elif year := item.get("year"):
                    p.raw(f", {year}")
                if issue := item.get("issue"):
                    p.raw(f" ({issue})")
                if pages := item.get("pages"):
                    p.raw(f", {pages.replace('--', '-')}.")
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
    refs = References("~/references")
    print(f"{len(refs)} references")
