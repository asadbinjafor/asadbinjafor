# Profile maintenance

This profile uses GitHub Flavored Markdown and repository-hosted SVG assets. It does not depend on an external stats-image service or JavaScript running inside a README.

## Edit content

- Edit `README.md` for the biography, project links, training and community activities.
- Edit the information rows in `scripts/build_profile.py` for the terminal hero.
- `assets/asad.png` is the supplied, unmodified portrait. The SVG embeds it directly; the ASCII scene is deterministic text sampled from that image.
- Run `python scripts/build_profile.py` after changing the portrait or SVG content. The generator requires Pillow. The mobile hero is generated at the same time.
- The animations honor `prefers-reduced-motion`. The portrait and all key information remain visible when animations are disabled.

## Refresh GitHub activity

GitHub Actions runs `.github/workflows/refresh-profile.yml` every six hours, at 00:17, 06:17, 12:17 and 18:17 Bangladesh time (UTC+6). GitHub's scheduling may run later during busy periods. Updates to the renderer or workflow also trigger a refresh. Use **Actions → Refresh profile stats → Run workflow** for an immediate refresh.

The job fetches public repository counts, languages and the rolling contribution history, then publishes the data, desktop/mobile stats, grid and README labels together. It uses GitHub's built-in, repository-scoped token; no personal access token is needed. Month labels advance with the rolling graph. Content-based image URLs refresh the browser's cache when an SVG changes.

The contribution graph and stats are periodically refreshed snapshots, not per-commit live counters. Language distribution counts non-fork public repositories by their primary language, rather than claiming percentages of code or personal expertise. The snake is decorative; the underlying cells retain the actual contribution levels and per-day counts.

For a local refresh, run `python -m pip install -r requirements.txt` and `python scripts/refresh_stats.py`. Review and commit the README, data and generated assets together. Run `python -m unittest discover -s tests -v` to check date rollover, source parsing and README updates.

Malformed or incomplete source data fails the job before publishing, preserving the last valid profile. Concurrent refreshes are serialized. The publication step rebases onto the current `main` and never force-pushes. Only generated stats files and README metadata are staged by the job.

If GitHub disables a schedule after a long period without repository activity, re-enable it on the Actions page. The README always shows the last successful refresh time.

## Content sources

- Owner-supplied CV and portrait.
- Owner's portfolio: https://github.com/asadbinjafor/Asad_Portfolio
- Public GitHub endpoints listed in `data/github-snapshot.json`.
- The full-stack mobile-shop project is marked ongoing as stated in the CV. Research is explicitly ongoing. Courses and workshops are described as training, not professional certifications or employment.
- The supplied CV is not duplicated in this repository; the resume button retains the owner's existing public portfolio resume link.

## Design

The terminal frame, cyan/violet color scheme, animated portrait-to-code panel, stats, contribution animation and grouped skill icons are an original implementation inspired by the reel the owner supplied:
https://www.facebook.com/reel/1748981069508297

The desktop hero uses two columns; the mobile `<picture>` source stacks the portrait and information panel. README links are real HTML anchors outside the images, since SVG content shown as an image is not an interactive page.

Skill icons are from https://github.com/tandpfun/skill-icons under the MIT license; see `skill-icons-LICENSE.txt`. Individual source SVGs are kept in `assets/icons/`. All other generated UI artwork is maintained by the Python generator.
