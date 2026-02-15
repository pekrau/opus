"Reference database handler."

from pathlib import Path
import unicodedata

import yaml


def normalize(reference):
    """Normalize the reference for part of a URL.
    - Normalize non-ASCII characters.
    - Convert the string to ASCII.
    - Lowercase.
    - Replace blank with dash.
    """
    return (
        unicodedata.normalize("NFKD", reference)
        .replace("æ", "a")
        .replace("Æ", "A")
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .lower()
        .replace(" ", "-")
    )


class References:
    "Reference database handler."

    def __init__(self, dirpath, formatter=None):
        self.dirpath = Path(dirpath).expanduser().resolve()
        self.formatter = DefaultReferenceFormatter()
        self.items = {}
        for filepath in self.dirpath.glob("*.yaml"):
            if filepath.stem.startswith("template"):
                continue
            with open(filepath) as infile:
                try:
                    item = yaml.safe_load(infile)
                except yaml.parser.ParserError as error:
                    raise ValueError(f"Invalid YAML in {filepath}")
                else:
                    try:
                        reference = item["reference"]
                    except KeyError:
                        raise KeyError(f"missing 'reference' in {filepath}")
                    reference = reference.casefold()
                    if normalize(reference) != filepath.stem:
                        raise ValueError(f"reference/filename mismatch for {filepath}")
                    if reference in self.items:
                        raise KeyError(f"reference {reference} already defined")
                    self.items[reference] = item
        self.used = set()

    def reset_used(self):
        self.used = set()

    def __iter__(self):
        return (self[reference] for reference in sorted(self.used))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, reference):
        return self.items[reference.casefold()]

    def __contains__(self, reference):
        return reference.casefold() in self.items

    def add(self, paragraph, reference, raw=False):
        "Output the short form of the given reference, and mark as used."
        try:
            item = self[reference]
        except KeyError:
            paragraph += f"[ref? {reference}]"
            print(f"Missing reference {reference}")
        else:
            self.used.add(reference)
            self.formatter.add_short(paragraph, item, raw=raw)


class DefaultReferenceFormatter:
    "Default reference formatter. Outputs the reference and the title."

    def add_short(self, paragraph, item, raw=False):
        with paragraph.italic():
            paragraph.add(item["reference"], raw=raw)
        paragraph.add(f', "{item["title"]}"')

    def add_full(self, document, item, raw=False, max_authors=4):
        p = document.paragraph()
        authors = item.get("authors") or []
        p.add(", ".join([self.format_name(a) for a in authors[:max_authors]]), raw=raw)
        if len(authors) > max_authors:
            p.raw(",")
            with p.italic():
                p.add("et al")
        p.raw(".")
        p.add(str(item["year"]))
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
                    p.add(f"{pages.replace('--', '-')}.")
            case "link":
                p.add(f"{item['title'].rstrip('.')}.")
                p.link(item["href"])
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
    refs = References("~/Dropbox/pekrau.github.io/references")
    print(f"{len(refs)} references")
