# Changes in nbdime

## 3.2

###  3.2.1 - 2023-04

- Fixed incorrect exit code submission when succesfully closing web tools.

###  3.2.0 - 2023-04

- Jupyter server 2.0 support
- Removed ipython_genutils code.
- Make INFO text more readable in dark terminal
- Compatible with asynchronous contentsmanager
- Update cell marker format to use bold correctly

## 3.1

###  3.1.0 - 2021-05

- Removed py2 compatibility code.
- Fixed issue with certain output diffs in web view.

## 3.0

###  3.0.0 - 2021-04

- Added support for JupyterLab 3. This includes compatibility with jupyter_server (notebook is still supported as well).
- Basic functionality for working with cell ids introduced in notebook format spec 4.5. Full utilization of this for diffing/merging functionality is planned for a later release.
- Fixed some issues with inline merging

## 2.0

###  2.1.0 - 2020-10

- Dropped Python 3.5 support.
- Optimize comparison of large stream outputs.
- Fixed an error when merging a file that were concurrently added in two branches with git.
- Fixed a config bug where ignore configs written in a file was not taken into account.
- Fixed compatibility with JupyterLab 2.2
- Various other fixes and adjustments.

###  2.0.0 - 2020-03

- Dropped Python 2 support, and Python 3.4 support.
- Fix support for Python 3.8 on Windows.
- Various improvements to lab/notebook extensions.
- Made web apps (e.g. nbdiff-web) work properly offline.
- Fix for git driver with renamed files.
- Various other fixes and adjustments.


## 1.1

###  1.1.0 - 2019-08

- Add rest API for server extension for handling pure git diffs of notebooks. This allows for a cleaner call without prefixing the filename etc. This is currently only available on the server extension, but can be moved to the main server if there is demand.


## 1.0

###  1.0.7 - 2019-07
- Fixes an issue using config files (PR #476).
- Upgrades to using lab 1.0 components, which also allows lab extension to support lab 1.0.

###  1.0.6 - 2019-05
- Fixed a styling regression from 1.0.5, where the web text panes
had incorrect styling (most notably incorrect widths).

###  1.0.5 - 2019-03
- Fixed filename encoding issue with git diff on Python 2.
- Fixes for deploying nbdime on a non-localhost server.
- Web: Fixed issue where unchanged cells would not show correctly if unhidden.
- Various other fixes and adjustments.

###  1.0.4 - 2018-12

- Fix git diffing failure with older versions of git. Now, an older version of git will simply prevent integration with git filters.
- Allow for two-way merge by making the base notebook argument to `nbmerge` optional. It will now default to an empty notebook.

###  1.0.3 - 2018-10

- Web: Fix issues with hiding unchanged cells. Make hiding unchanged cells configurable and on by default.
- Options of the console printing can now be configured. Mainly the `--no-color` flag disables ANSI color escapes.
- Web: Fixed MathJax math rendering.
- Various other fixes and adjustments.

###  1.0.2 - 2018-08

- Diff: Optimized diffing of large texts (e.g. big cells).
- Config: Fixed several issues with the config system.
- Lab extension: Updated to latest jupyterlab. All npm packages are now using ES6 features.
- Web: Fixed keyboard tabbing / focusing issues.

###  1.0.1 - 2018-06

- Web: Fix output rendering of outputs with a period in MIME type name.
- Config: Add configuration option for front-end extensions.
- Merging: Fix handling of corner case for inline merge strategy.
- Various other fixes and adjustments.

###  1.0.0 - 2018-05

- Added ability for git diff driver to integrate with git filters.
- Improved/fixed merge resolution for similar cell insertions.
- Added config system to allow for configuring the various entrypoints. Especially useful for customizing which keys to ignore when diffing.
- Added control to web view of outputs to select which MIME type to render, and to enable trusting of outputs for full rendering.
- Added jupyterlab extension. Frontend/server extensions are now enabled by default on installation.
- Various fixes and adjustments.


## 0.4

###  0.4.1 - 2017-12

- Fixed layout issue in web diff for cells added/removed/patched in the same location.
- Dropped support for Python 3.3.
- Ensure Ctrl+C will shut down the nbdime web server on Windows.
- Ensure server extension works with 4.x version of notebook server.
- Various fixes and adjustments.

###  0.4.0 - 2017-11

- Fixed issues with the diff filtering options.
- Added git diffdriver using web-diff.
- Added mercurial integration code and entry points.
- Added notebook extensions for integration into its web interface.
- Changed layout for web diff such that chunks of added/removed cells or outputs are shown side-by-side. For small monitors, they will still be shown below each other.
- In the web-diff, relative images in rendered markdown will now show a placeholder image instead of broken images.
- Various fixes and performance improvements.


## 0.3

- Handle git refs directly in nbdime, so you can `nbdiff HEAD notebook.ipynb`, etc. in git repos. This replaces the never-quite-working git difftool
- Support filtering options on all entrypoints, e.g. `nbdiff -s` to only show diff of sources. See `nbdiff -h` for details
- Fix MathJax CDN URL, now that cdn.mathjax.org has shutdown
- Use `jupyter-packaging` to build javascript sources in `setup.py`
- Various fixes and performance improvements

## 0.2

- Support ip, base-url arguments to web entrypoints
- Enable export of web diff to static HTML
- Various fixes and improvements

## 0.1

###  0.1.2 - 2017-01

- Fix inclusion of webapp sources in wheels

###  0.1.1 - 2017-01

- Fix default location of `--global` git attributes file
- Support `--system` argument for git configuration, allowing easy setup of nbdime system-wide
- Render tracebacks and colors in stream output in web view
- Render output as long as one MIME-type is safe in web view
- Improve styling of web view
- Fix a bug in inline-merge

### 0.1.0 - 2016-12

First release of nbdime!

