# Contributing to Awesome Computational Primatology

Thank you for your interest in contributing! This document explains how to add papers and improve the project.

## 🚀 Quick Start

**Edit `README.md` only.** Add one row per paper, at the top of its year in the Projects table, and open a pull request. Everything else is derived from the README and rebuilt by CI on every merge: the website, the paper-count badge, the stats and the growth figure. Don't commit generated files.

When you open a PR, CI will:
- lint the table (column count, year, link in the Paper cell; topic codes and Model?/Data? values against the legends)
- check the links your PR adds
- build the site and attach it as the `site` artifact on the run page (download it and open `index.html`)

### Preview locally (optional)
```bash
uv run --no-project --with-requirements requirements.txt python scripts/dev-preview.py
# or: pip install -r requirements.txt && python scripts/dev-preview.py
```
This lints the README, builds into `_site/`, and serves it at http://localhost:8000.

### Pull requests
- Title: "Add: YYYY AuthorName" or "Update: brief description"
- Fill out the PR template

### Review Process
- Maintainers will review within 1-2 weeks
- Reviews focus on:
  - Correct formatting
  - Working links
  - Appropriate categorization
  - Complete information

### Eligibility Criteria
- Papers must be at the intersection of deep learning and non-human primatology
- Published from 2012 onwards (around AlexNet era)
- Must provide novel approaches or applications in computational primatology
- Cross-species datasets including primates are acceptable

### Table Format
Add your paper to the appropriate table section using this format:
| Year | Paper | Topic | Animal | Model? | Data? | Image/Video Count |

Where:
- **Year**: Publication year (of the published version, if there is one)
- **Paper**: `[Short name](link)`; prefer a DOI link (`https://doi.org/...`), arXiv DOIs for preprints
- **Topic**: Use abbreviations from Topic Legend (PD, BPE, FD, etc.)
- **Animal**: Specific primate species or "Cross-species"
- **Model?**:
  - `[Yes](link)` if code + pretrained models available
  - `[Code only](link)` if repository available but no pretrained models
  - `[No](link)` if repository with information but no functional code
  - "N/A" if neither available
- **Data?**:
  - `[Yes](link)` if publicly available
  - "Upon request" if available through contact
  - "N/A" if not available
- **Image/Video Count**: Number or "N/A" if not applicable

### Topic Legend
See the full [Topic Categories](docs/TOPIC_LEGEND.md) for abbreviations (PD, BPE / 2D BPE / 3D BPE, FD, FLE, FR, FAC, HD, HPE, BR, AM, SI, RL, AV, O).

## Verification Steps
Before submitting your PR:
1. Verify all links are accessible
2. Check table formatting matches existing entries
3. Ensure topic abbreviations are correct
4. Confirm model/data availability is accurately represented
5. Test any code repository links

## Questions or Issues?
- Open an issue for:
  - Clarification on guidelines
  - Suggesting improvements
  - Reporting broken links
  - Discussing paper categorization
- Expect response within 1 week

## Additional Resources
- [GitHub Fork & Pull Request Workflow](https://github.com/susam/gitpr)
- [Markdown Table Format](https://www.markdownguide.org/extended-syntax/#tables)