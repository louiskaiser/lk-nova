# Publishing LK Nova

Use GitHub Pages for the product presentation and GitHub Releases for versioned downloads. Repository: https://github.com/louiskaiser/lk-nova

Product page: https://louiskaiser.github.io/lk-nova/

1. Create a repository in the intended account or organization.
2. Place this folder's contents at the repository root, including `.github/`, `docs/`, `source/`, `packaging/`, `dist/` and the documentation.
3. In Settings → Pages, select GitHub Actions as the publishing source.
4. Run Actions → Publish LK Nova → Run workflow. It publishes only `docs/`.
5. Check the published page, language selection, specimen and downloads.
6. Create release `v1.0.0` with `docs/downloads/LK-Nova-1.0.zip`, `LK-Nova-1.0-Source.zip` and `SHA256SUMS.txt` attached.

The workflow is manual. No account, domain or credentials are hardcoded. Relative download links work under a Pages project URL. A custom domain can be configured later.

## Update

Maintain English content in `packaging/site-template.html` and `packaging/locales/en.json`, update the translations, then run:

```sh
python3 packaging/build_site.py
python3 packaging/package.py
```

## References

- https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
