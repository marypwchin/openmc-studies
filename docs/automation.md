# Repository automation: step by step

## Files and how they fit together

This layout follows common Python and GitHub conventions. The configuration
formats are standard; the checks and helper scripts are tailored to this
repository. Paths in this table are relative to the repository root.

| File | Format | Purpose | Convention |
| --- | --- | --- | --- |
| [.github/workflows/notebooks.yml](../.github/workflows/notebooks.yml) | YAML | Defines push, pull-request, and manual triggers, then jobs and steps for repository validation. `run` executes shell commands; `uses` reuses GitHub Actions. | GitHub discovers workflow files in `.github/workflows/`; the filename is our choice. |
| [.github/workflows/links.yml](../.github/workflows/links.yml) | YAML | Schedules external-link checks and allows manual runs. Extracts URLs from prose and passes them to Lychee. | Same workflow convention; separating scheduled checks is common. |
| [.pre-commit-config.yaml](../.pre-commit-config.yaml) | YAML | Lists local hooks, commands, dependencies, and file filters. `repo: local` defines hooks within this repository. | Standard filename for pre-commit. Installing the Git hook activates it for this checkout. |
| [requirements-dev.txt](../requirements-dev.txt) | pip requirements text | Lists development tools. `ruff==0.11.13`, for example, pins that package to an exact version. | Common filename, explicitly read by `pip install -r requirements-dev.txt`; pip does not discover it automatically. |
| [pyproject.toml](../pyproject.toml) | TOML | Declares the package and build system. `[project]` contains package metadata; `[tool.setuptools]` selects the module to package. | Standard Python packaging file; enables `pip install -e .` here. |
| [openmc_studies_config.py](../openmc_studies_config.py) | Python | Defines `DATA_ROOT` and `ENDF_B81` for import by both notebooks and the setup script. | Custom module; supports the studies rather than implementing a CI check. |
| [scripts/update_structure.py](../scripts/update_structure.py) | Python | Reads notebook headings and the Git file inventory, then updates generated outline and README tree blocks. `--check` reports stale content without writing. | Custom script; `scripts/` is a common directory convention. |
| [scripts/check_notebooks.py](../scripts/check_notebooks.py) | Python | Uses `nbformat` to validate notebook schemas without executing cells. | Custom wrapper around a standard notebook library. |
| [scripts/check_links.py](../scripts/check_links.py) | Python | Parses Markdown, checks local file targets, and exports external prose URLs for Lychee. | Custom script shared by local hooks and CI. |
| [docs/automation.md](automation.md) | Markdown | Explains installation, checks, and troubleshooting. | `docs/` is conventional; this filename is our choice. |
| [.gitignore](../.gitignore) | Git ignore patterns | Excludes untracked environments, caches, checkpoints, and build artifacts from normal staging. It does not untrack files already committed. | Standard Git filename and pattern syntax. |

The connections are:

```text
Local commit
└── .pre-commit-config.yaml → helper scripts + Ruff

GitHub push or pull request
└── notebooks.yml → helper scripts + Ruff + configuration import check

Weekly or manual external-link check
└── links.yml → check_links.py → extracted URLs → Lychee

Both notebooks and the text-only setup script
└── openmc_studies_config.py → shared nuclear-data locations
```

**YAML** means *YAML Ain't Markup Language*. Both `.yml` and `.yaml` denote
the same format. Indentation expresses nesting; use spaces rather than tabs:

```yaml
jobs:
  validate:
    runs-on: ubuntu-latest
```

Here, `validate` names a job inside `jobs`, and `runs-on` selects its runner.

**TOML** means *Tom's Obvious, Minimal Language*. Named sections group explicit
key/value assignments:

```toml
[project]
name = "openmc-studies-config"
version = "0.1.0"
```

Configuration files describe what the tools should do. Python scripts implement
the repository-specific operations, and Markdown explains the system to people.
`.venv/` and `.ruff_cache/` are local tool-created directories, not workflow
source files; keep them out of commits.

## 1. Understand the two generated structures

`scripts/update_structure.py` reads Markdown ATX headings (`#` through `######`)
in every nonignored notebook. It skips fenced code examples, turns the heading
hierarchy into a text tree, and inserts a marked Markdown block immediately after
the first `#` title. Headings inside that first cell are included too. Use one
`#` title per notebook and `##`/`###` headings for its sections and subsections.
Setext headings (underlined titles) and HTML headings are not supported.

The same script updates only the marked structure section in README.md. The
default tree shows study content. Hidden paths and the top-level `docs/`,
`scripts/`, `requirements-dev.txt`, and `pyproject.toml` are reserved for an
expandable “Full repository tree, tooling, and CI” section with links to the CI
workflow, pre-commit configuration, and this guide. Adjust the `infrastructure`
set in `readme_text()` if more tooling directories are added.

Its file inventory
comes from Git: tracked files plus nonignored new files that exist on disk.
Empty directories, notebook checkpoints, virtual environments, and caches are
omitted. Add large data directories and other local artifacts to `.gitignore`
if they live inside this repository and should stay out of the tree.

The first update replaces the existing manual notebook outline. Notebook outputs,
code, execution counts, and metadata are preserved. JSON formatting may change
on that first update. Close notebooks or reload them after an external update
so an older editor buffer does not overwrite the generated outline.

## 2. Generate and inspect manually

From the repository root:

```sh
python3 scripts/update_structure.py
git diff --stat
git diff -- README.md
python3 scripts/update_structure.py --check
```

Open both notebooks and inspect the new trees. `--check` reports stale generated
content and exits nonzero without writing anything. A second normal run should
make no changes. Run again after adding or removing files or renaming headings.

## 3. Install pre-commit in a local development environment

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt -e .
pre-commit validate-config
pre-commit install
```

This installs a Git pre-commit hook for this checkout. Each new clone needs the
installation step. Hook environments are managed by pre-commit; the notebook
validator uses the pinned nbformat dependency in the configuration. First use
requires internet access to prepare those environments.

## 4. Run the configured checks

```sh
pre-commit run --all-files
```

Four hooks are configured (the configuration file defines their order):

1. Generate outlines and README structure. It runs on every commit because a
   change to any repository filename can change the README tree.
2. Validate notebook schemas with nbformat. This checks notebook structure,
   required fields, cell types, and metadata format. It does not validate the
   scientific results or execute cells.
3. Check local file links in Markdown files and notebook Markdown cells.
   No internet is used for this check. It validates repository file/directory
   targets, including reference links, images, and HTML `href`/`src` attributes.
   Heading fragments and notebook attachments are not validated. Notebook code,
   outputs, and fenced/inline code examples are excluded.
4. Check Python files and notebook code cells with Ruff's `E9,F63,F7,F82,F401`
   rules, matching the earlier CI proposal. These catch syntax errors, invalid
   control flow, undefined names, and unused imports. This is a focused check, not full style
   linting, formatting, or proof that the code will run successfully.

To run each check individually:

```sh
pre-commit run update-structure --all-files
pre-commit run notebook-schema --all-files
pre-commit run fatal-python-errors --all-files
pre-commit run local-links --all-files
```

Read each diagnostic's filename, cell/line, and rule code; fix the source,
save the notebook, and rerun the failed hook. Ruff is configured without
automatic fixes so that you can review each correction.

The first hook deliberately updates files. If it changes anything, pre-commit
stops the commit for review. Review the changes, stage them, and run again.
It never stages files automatically.

## 5. Review and stage the intended changes

```sh
git status --short
git diff --check
git diff
git add .pre-commit-config.yaml .gitignore .github requirements-dev.txt scripts docs README.md 0_nuclear_data/*.ipynb
pre-commit run --all-files
git diff --cached --check
git diff --cached --stat
git diff --cached
```

`git diff --check` checks whitespace problems in unstaged changes; the cached
version checks the staged patch. Review the staged diff for accidental data,
private paths, unwanted outputs, and unrelated edits. When satisfied, commit
with your chosen message. If a hook updates files again, review and re-stage
those files, then retry the commit.

## 6. Keep slower or policy-dependent checks separate

The earlier proposal includes selective notebook execution, synthetic XML tests,
and optional later publishing. These are separate from the fast checks above:

- **Clean-kernel execution:** run the analysis notebook from top to bottom in
  the intended OpenMC environment after checking its data paths. Inspect the
  results and assertions. This catches execution-order and dependency problems.
  Install the shared module into that environment with `python -m pip install -e .`
  from the repository root. Both notebooks use `openmc_studies_config` to locate
  the installation; change `DATA_ROOT` there if your libraries are outside `~/data`.
- **Installation notebook:** inspect `APPLY` and local archive paths before any
  execution. Run the preview first. Full execution can download and install
  many GB of nuclear data, so do not execute it in a commit hook.
- **Outputs:** decide whether committed plots and tables are part of the study.
  Do not automatically strip them until that policy is chosen.
- **XML auditing unit tests:** extract reusable index-validation functions,
  then test them against temporary, synthetic XML/HDF5 paths. Cover a valid
  index, missing referenced files, malformed XML, and relative path resolution.
  Run those tests with `python -m pytest` once the functions and tests exist.
  No such test suite has been added here; it needs a defined validation API.
- **Broader linting/formatting:** the fatal Ruff rules are configured. Style
  formatting and broader rule sets can be added separately.
- **Scientific validation:** check library provenance, data-path assumptions,
  and physical comparisons independently. Schema validation cannot establish
  scientific correctness.

## 7. Run the same checks on GitHub

`.github/workflows/notebooks.yml` runs on pushes, pull requests, and manual
dispatch. After reviewing, committing, and pushing these files, open the
repository's **Actions** tab and select **Validate notebooks**. Open each step
to see diagnostics. For a manual rerun, select **Run workflow** after the
workflow is on the default branch.

CI uses `--check` for structures: it fails on stale documentation without
changing it. Fix locally with `python scripts/update_structure.py`, review and
commit the updated files, then push again. To reproduce the other CI steps:

```sh
python scripts/check_notebooks.py 0_nuclear_data/*.ipynb
ruff check --select E9,F63,F7,F82,F401 .
```

CI does not install OpenMC, execute notebooks, download nuclear data, or run
transport simulations. Publishing rendered notebooks remains optional future
work. This is CI; no deployment has been configured. Local hooks can be
bypassed; GitHub checks provide an independent check on the pushed revision.
CI also installs the shared configuration module and checks that it imports
from outside the checkout, with an absolute data root and the ENDF/B-VIII.1 path.

References: https://pre-commit.com/ and https://nbformat.readthedocs.io/

## 8. Check external links weekly

`.github/workflows/links.yml` runs separately each Monday at 13:23 UTC, or
manually via **Actions → Check external links → Run workflow**. Scheduled
workflows run from the default branch, so merge and push the workflow there
to activate it. GitHub may delay scheduled runs.

The workflow extracts unique HTTP/HTTPS links from Markdown and notebook
Markdown cells, then sends the list to Lychee. Bare URLs in prose are included;
links in code cells, outputs, and code examples are excluded. It does not
download the nuclear-data archives referenced only in setup code.

Failures appear in that workflow's log and job summary, independently of the
Notebook CI badge. A failed HTTP check is a signal to investigate: open the URL
in your browser before changing it. A 403 can indicate bot blocking and a 429
can indicate rate limiting; neither proves the page has disappeared. Requests
are limited to four concurrent checks with retries, but blocking can still occur.
No 403/429 responses are silently treated as successes.

To reproduce extraction locally (the output alone does not check the internet):

```sh
python scripts/check_links.py
python scripts/check_links.py --external-output /tmp/openmc-external-links.txt
```

Lychee reference: https://github.com/lycheeverse/lychee-action
