# Changes in nbdime

## 0.4

- Fixed issues with the diff filtering options.
- Added git diffdriver using web-diff.
- Added mercurial integration code and entry points.
- Added notebook extentions for integration into its web interface.
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

