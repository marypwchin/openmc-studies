"""Update heading trees and the README tree; --check makes no changes."""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- generated:structure -->'
END = '<!-- /generated:structure -->'


def source(cell):
    value = cell.get('source', '')
    return ''.join(value) if isinstance(value, list) else value


def headings(text):
    fence = None
    for line in text.splitlines():
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if match:
            token = match[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            match = re.match(r'^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$', line)
            if match:
                yield len(match[1]), match[2]


def tree_lines(node, prefix=''):
    lines = []
    for i, (name, children) in enumerate(node):
        last = i == len(node) - 1
        lines.append(prefix + ('└── ' if last else '├── ') + name)
        lines.extend(tree_lines(children, prefix + ('    ' if last else '│   ')))
    return lines


def block(lines):
    return START + '\n```text\n' + '\n'.join(lines) + '\n```\n' + END


def notebook_text(path):
    original = path.read_text()
    nb = json.loads(original)
    cells = nb['cells']
    # Remove our own block before collecting headings (no recursive outlines).
    for cell in cells:
        if cell['cell_type'] == 'markdown':
            text = source(cell)
            text = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n*', '', text, flags=re.S)
            # Migrate the existing hand-written outline in this repository.
            text = re.sub(r'\*\*Notebook outline\*\*\n```text\n.*?```\n*', '', text, flags=re.S)
            cell['source'] = text.splitlines(keepends=True)
    title_cell = None
    title = None
    items = []
    for cell in cells:
        if cell['cell_type'] != 'markdown':
            continue
        for level, label in headings(source(cell)):
            if title is None and level == 1:
                title_cell, title = cell, label
            else:
                items.append((level, label))
    if title_cell is None:
        raise ValueError(f'{path}: expected a Markdown # title')
    nodes = []
    stack = [(0, nodes)]
    for level, label in items:
        while stack[-1][0] >= level:
            stack.pop()
        children = []
        stack[-1][1].append((label, children))
        stack.append((level, children))
    text = source(title_cell)
    lines = text.splitlines(keepends=True)
    index = next(i for i, line in enumerate(lines) if re.match(r'^ {0,3}#\s+', line))
    lines[index] = lines[index].rstrip('\n') + '\n\n' + block([title] + tree_lines(nodes)) + '\n\n'
    title_cell['source'] = (''.join(lines[:index + 1]) + ''.join(lines[index + 1:]).lstrip('\n')).splitlines(keepends=True)
    # Preserve the original bytes if the JSON content already matches.
    if nb == json.loads(original):
        return original
    return json.dumps(nb, ensure_ascii=False, indent=1) + '\n'


def repository_paths():
    # Include tracked and nonignored new files; exclude local caches and environments.
    output = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT
    )
    excluded = {'.git', '.ipynb_checkpoints', '__pycache__', '.venv', 'venv', '.pytest_cache', '.ruff_cache'}
    return sorted({p for p in output.decode().split('\0') if p and
                   not excluded.intersection(Path(p).parts) and (ROOT / p).is_file()})


def readme_text(paths):
    def nodes(mapping):
        return [(name + ('/' if value else ''), nodes(value))
                for name, value in sorted(mapping.items(), key=lambda pair: (not bool(pair[1]), pair[0]))]

    def render_tree(selected):
        nested = {}
        for path in selected:
            node = nested
            for part in Path(path).parts:
                node = node.setdefault(part, {})
        return '```text\n' + '\n'.join(['.'] + tree_lines(nodes(nested))) + '\n```'

    # Keep infrastructure available on demand without crowding the study overview.
    infrastructure = {'docs', 'scripts', 'requirements-dev.txt', 'pyproject.toml'}
    visitor_paths = [p for p in paths if
                     not any(part.startswith('.') for part in Path(p).parts)
                     and Path(p).parts[0] not in infrastructure]
    generated = (
        START + '\n' + render_tree(visitor_paths) + '\n\n'
        '<details>\n<summary>Full repository tree, tooling, and CI</summary>\n\n'
        + render_tree(paths) + '\n\n'
        'See the [automation guide](docs/automation.md), '
        '[CI workflow](.github/workflows/notebooks.yml), and '
        '[pre-commit configuration](.pre-commit-config.yaml).\n\n'
        '</details>\n' + END
    )
    text = (ROOT / 'README.md').read_text()
    if START in text:
        return re.sub(re.escape(START) + r'.*?' + re.escape(END), lambda _: generated, text, flags=re.S)
    pattern = r'(## Repository structure\s*\n)```text\n.*?```'
    text, count = re.subn(pattern, lambda m: m[1] + generated, text, count=1, flags=re.S)
    if count != 1:
        raise ValueError('README needs a Repository structure heading followed by a text fence')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    paths = repository_paths()
    updates = [(ROOT / p, notebook_text(ROOT / p)) for p in paths if p.endswith('.ipynb')]
    updates.append((ROOT / 'README.md', readme_text(paths)))
    stale = False
    for path, text in updates:
        if path.read_text() != text:
            stale = True
            print(('Stale: ' if args.check else 'Updated: ') + str(path.relative_to(ROOT)))
            if not args.check:
                path.write_text(text)
    return int(args.check and stale)


if __name__ == '__main__':
    raise SystemExit(main())
