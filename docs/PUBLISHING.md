# Publishing checklist (maintainer only)

**English** | [Русский](PUBLISHING.ru.md)

This folder is a **new repository**, not a branch or a fork of the private commercial codebase. Never use the private repository's `.git` directory or history.

1. Check README claims, screenshots, and the code before publication. Make sure the commissioned shop's branding and images may be showcased and you own the published algorithm/source.
2. Create a **new, empty public repository** named `flora-sense` on GitHub. Do **not** initialize it with a README or a `.gitignore`; both already exist here.
3. On your Mac, unzip the package to its own directory, separate from `diploma-project`.
4. From the new `flora-sense` directory, run:

   ```bash
   git init -b main
   git add README.md README.ru.md .gitignore docs recommender session-reranking
   git status --short
   git commit -m "docs: publish Flora Sense technical showcase"
   git remote add origin https://github.com/Evme22/flora-sense.git
   git push -u origin main
   ```

5. Verify that the public repository shows the English and Russian READMEs, 4 screenshots, Python recommender, JavaScript reranker, and tests. Check the repository's file list for anything private. This package does **not** contain `.env` or actual customer data.
6. To publish the original video **without quality loss**, open the new repository's **Releases** tab, choose *Draft a new release*, create the tag `demo-2026-11`, and upload your **original `.mov` file**, renamed `flora-sense-demo.mov`. Publish the release. The README link is prepared for that tag.
7. Keep `Evme22/diploma-project` private. Never click **Change visibility** on it.

If a different GitHub account or repository name is used, replace the URLs in this package before publishing.
