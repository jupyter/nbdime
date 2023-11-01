# Making a new release of nbdime

The extension can be published to `PyPI` and `npm` manually or using the [Jupyter Releaser](https://github.com/jupyter-server/jupyter_releaser).

## Manual release

### Python package

This extension can be distributed as Python packages. All of the Python
packaging instructions are in the `pyproject.toml` file to wrap your extension in a
Python package. Before generating a package, you first need to install some tools:

```bash
pip install build twine hatch
```

Bump the version using the custom script:

```bash
python scripts/bump_version.py <new-version>
```

> _\<new-version\>_ can be a segment like `major`, `minor`, `patch`, `alpha`,...

Make sure to clean up all the development files before building the package:

```bash
jlpm clean:all
```

You could also clean up the local git repository:

```bash
git clean -dfX
```

To create a Python source package (`.tar.gz`) and the binary package (`.whl`) in the `dist/` directory, do:

```bash
python -m build
```

> `python setup.py sdist bdist_wheel` is deprecated and will not work for this package.

Then to upload the package to PyPI, do:

```bash
twine upload dist/*
```

### NPM package

To publish the frontend part of the extension as a NPM package, do:

```bash
npm login
npm publish --access public
```

## Automated releases with the Jupyter Releaser

The extension repository should already be compatible with the Jupyter Releaser.

Check out the [workflow documentation](https://jupyter-releaser.readthedocs.io/en/latest/get_started/making_release_from_repo.html) for more information.

Here is a summary of the steps to cut a new release:

- Add tokens to the [Github Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets) in the repository:
  - `ADMIN_GITHUB_TOKEN` (with "public_repo" and "repo:status" permissions); see the [documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
  - `NPM_TOKEN` (with "automation" permission); see the [documentation](https://docs.npmjs.com/creating-and-viewing-access-tokens)
- Set up PyPI

<details><summary>Using PyPI trusted publisher (modern way)</summary>

- Set up your PyPI project by [adding a trusted publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
  - The _workflow name_ is `publish-release.yml` and the _environment_ should be left blank.
- Ensure the publish release job as `permissions`: `id-token : write` (see the [documentation](https://docs.pypi.org/trusted-publishers/using-a-publisher/))

</details>

<details><summary>Using PyPI token (legacy way)</summary>

- If the repo generates PyPI release(s), create a scoped PyPI [token](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/#saving-credentials-on-github). We recommend using a scoped token for security reasons.

- You can store the token as `PYPI_TOKEN` in your fork's `Secrets`.

  - Advanced usage: if you are releasing multiple repos, you can create a secret named `PYPI_TOKEN_MAP` instead of `PYPI_TOKEN` that is formatted as follows:

    ```text
    owner1/repo1,token1
    owner2/repo2,token2
    ```

    If you have multiple Python packages in the same repository, you can point to them as follows:

    ```text
    owner1/repo1/path/to/package1,token1
    owner1/repo1/path/to/package2,token2
    ```

</details>

- Go to the Actions panel
- Run the "Step 1: Prep Release" workflow
- Check the draft changelog
- Run the "Step 2: Publish Release" workflow

## Publishing to `conda-forge`

If the package is not on conda forge yet, check the documentation to learn how to add it: https://conda-forge.org/docs/maintainer/adding_pkgs.html

Otherwise a bot should pick up the new version publish to PyPI, and open a new PR on the feedstock repository automatically.
