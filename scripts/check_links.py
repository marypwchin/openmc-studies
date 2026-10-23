"""Check local file links, or export external prose URLs for Lychee.

Reads Markdown files and notebook Markdown cells; never executes notebooks.
Local checks validate file existence, not heading fragments or notebook attachments.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

from update_structure import ROOT, repository_paths


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(value for key, value in attrs
                          if key in {'href', 'src'} and value)


def links(text):
    parser = MarkdownIt('commonmark')

    def walk(tokens):
        for token in tokens:
            if token.type == 'link_open':
                yield token.attrGet('href')
            elif token.type == 'image':
                yield token.attrGet('src')
            elif token.type in {'html_inline', 'html_block'}:
                html = HTMLLinks()
                html.feed(token.content)
                yield from html.links
            elif token.type == 'text':
                # Include bare prose URLs; leave code examples and outputs alone.
                for match in re.finditer(r'https?://[^\s<>]+', token.content):
                    yield match[0].rstrip('.,;:!?')
            if token.children:
                yield from walk(token.children)

    yield from walk(parser.parse(text))


def documents(paths):
    for filename in paths:
        path = ROOT / filename
        if path.suffix == '.md':
            yield path, filename, path.read_text()
        elif path.suffix == '.ipynb':
            notebook = json.loads(path.read_text())
            for i, cell in enumerate(notebook['cells'], 1):
                if cell['cell_type'] == 'markdown':
                    source = cell.get('source', '')
                    text = ''.join(source) if isinstance(source, list) else source
                    yield path, f'{filename}:cell {i}', text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--external-output', type=Path,
                        help='Export unique HTTP(S) URLs instead of checking local files')
    args = parser.parse_args()
    paths = repository_paths()
    known = set(paths)
    external = set()
    broken = []
    count = 0
    for path, label, text in documents(paths):
        for target in links(text):
            url = urlsplit(target)
            if url.scheme in {'http', 'https'}:
                external.add(target)
                continue
            if url.scheme or url.netloc or not url.path:
                continue
            count += 1
            decoded = unquote(url.path)
            candidate = ((ROOT / decoded.lstrip('/')) if decoded.startswith('/')
                         else path.parent / decoded).resolve()
            try:
                relative = candidate.relative_to(ROOT).as_posix()
            except ValueError:
                relative = None
            exists = relative in known or (candidate.is_dir() and relative is not None
                      and any(p.startswith(relative.rstrip('/') + '/') for p in known))
            if candidate == ROOT:
                exists = True
            if not exists:
                broken.append(f'{label}: missing repository target: {target}')
    if args.external_output:
        args.external_output.write_text('\n'.join(sorted(external)) + '\n')
        print(f'Exported {len(external)} external URLs to {args.external_output}')
        return 0
    for diagnostic in broken:
        print(diagnostic)
    print(f'Checked {count} local file links; {len(broken)} broken.')
    return int(bool(broken))


if __name__ == '__main__':
    raise SystemExit(main())
