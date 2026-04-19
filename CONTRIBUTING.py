#!/usr/bin/env python3
"""
StartQ - Contributing Guide
==============================

Thank you for considering contributing to StartQ.

StartQ is a command-line utility for persisting agent session
context locally. The goal is a small, reliable tool that does
one thing well.


How to Contribute
-----------------

1. Report Bugs
   Use the GitHub issue tracker to report bugs.
   If your agent is hallucinating state, include the exact
   sequence of startq commands you executed.

2. Suggest Enhancements
   If you have an idea for a new feature, submit a GitHub
   issue before writing code. This ensures it aligns with
   the project scope.

3. Pull Requests
   - Fork the repository.
   - Ensure your code passes all lint checks.
   - Ensure unit tests pass locally before submitting.
   - Provide a clear PR description.
   - Do not bundle multiple unrelated features into one PR.

4. Development Setup

   git clone https://github.com/Phil-Hills/startq.git
   cd startq
   pip install -e .
   python -m pytest tests/


Thank you for helping make AI workflows reliable.
"""


if __name__ == "__main__":
    print(__doc__)
