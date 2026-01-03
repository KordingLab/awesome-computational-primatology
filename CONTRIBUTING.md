# Contributing to Awesome Computational Primatology

Thank you for your interest in contributing! This document explains how to add papers and improve the project.

## 🚀 Quick Start

### Preview Your Changes Locally
```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/awesome-computational-primatology.git
cd awesome-computational-primatology

# 2. Make your changes to README.md

# 3. Preview the website (auto-generates index.html and opens browser)
python scripts/dev-preview.py

# 4. Commit BOTH README.md and index.html, then create a pull request
```

**Important:** Always commit `index.html` along with your `README.md` changes. The CI will fail if they're out of sync.

### Automatic PR Previews
When you submit a PR, our automation will:
- ✅ Generate a preview website with your changes
- ✅ Post a comment with the preview link
- ✅ Validate table formatting and links
- ✅ Check that `index.html` is in sync with `README.md`

### 1. Branch Protocol
- Fork the repository
- Create a branch with format: `add-paper/YYYY-AuthorName` (e.g., `add-paper/2024-Smith`)
- For multiple papers or other changes: `update/brief-description`
- Add your paper in the correct section following the format below
- Verify all links are working

### 2. Pull Request Process
1. Create a draft PR first
2. Use title format: "Add: YYYY AuthorName paper" or "Update: brief description"
3. Fill out the PR template
4. Mark as ready for review when complete

### 3. Review Process
- Maintainers will review within 1-2 weeks
- Automated checks will verify table formatting and links
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
- **Year**: Publication year
- **Paper**: `[Title](link)` or just Title if preprint
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
See the full [Topic Categories](docs/TOPIC_LEGEND.md) for abbreviations (PD, BPE, FD, FLE, FR, FAC, HD, HPE, BR, AM, SI, RL, AV, O).

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