# Truss microsite

Hugo site built by `.github/workflows/pages.yml`. The version in the header and footer comes from
`packages/python/pyproject.toml` (`HUGO_PARAMS_version`); pull requests build the site, `main` and
published releases deploy it.

    HUGO_PARAMS_version=$(python3 -c 'import tomllib;print(tomllib.load(open("packages/python/pyproject.toml","rb"))["project"]["version"])') \
      hugo --source website --destination public --panicOnWarning
