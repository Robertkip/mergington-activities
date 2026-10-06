# Security policy

## Supported versions

Only the latest commit on `main` is supported. Security fixes are made there.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

- If the repository's **Security** tab shows a **Report a vulnerability** button under **Advisories**, use it. That sends a private report to the maintainers.
- Otherwise, email security@mergington-high-school.example.

Include what you found, where you found it, and the steps to reproduce it if you can.

## What to expect

- We acknowledge your report within 3 business days.
- We keep you informed while we work on a fix, and tell you when it is released.

## How security updates are handled

1. **Version updates.** Dependabot checks the Python dependencies in `requirements.txt` every week and opens a pull request for each available update (see `.github/dependabot.yml`).
2. **Security updates.** When a dependency has a known vulnerability and a fix is available, Dependabot security updates open a pull request automatically. This is a repository setting; see [docs/github-setup.md](docs/github-setup.md).
3. **Review.** These pull requests follow the same rules as every other change. The repository ruleset applies, and the maintainers team reviews them because it owns `requirements.txt`.
4. **Testing.** There is no automated CI, so the reviewer checks out the Dependabot branch, runs `python -m pytest`, and merges only if the tests pass.
5. **Timing.** Security update pull requests are reviewed within 5 business days.
