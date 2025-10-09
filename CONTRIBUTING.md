# Contributing

We follow the [IPython Contributing Guide](https://github.com/ipython/ipython/blob/master/CONTRIBUTING.md).

# Contributing with codespaces

Opening this repository in Codespaces will pre-install the environment you need to develop with.

## Updating Javascript packages.

This project uses lerna to manage the multiple packages inside the packages folder. If you run an npm command at the root it will run the command for each subpackage. This is good for working across packages, however more commonly we want to work with an individual package. To do this change directories into the package you wish to alter, then npm will run only for that package.

### Adding npm dependency

This should be done inside the directory of the package which requires the dependency.

### Testing changes to the webapp

The python setup.py script will built the entirety of the project and place it inside the build folder. Run `python setup.py build` once you are ready to test a change. Then the nbdime module can be invoked to test changes by running `python -m nbdime service` for example diff web can be started at `python -m nbdime diff-web testnotebookpath testnotebookpath2` there are test notebooks in the `nbdime/webapp/testnotebook` folder.


### Testing Changes to The Jupyter Lab Extension

The `python setup.py build` script will again update the extension. In order to see changes to in the Jupyter Lab interface you will need it to be setup. Running these commands will setup the environment:

```bash
jupyter server extension enable nbdime
jupyter labextension develop . --overwrite
```
(Note if you are using Codespace the above setup should have already happened for you.)

Every time you make a change you can re-run the build script and overwrite the lab extension to see the update.

### Running npm tests

The project uses jest to test the javascript, a typescript compile step occurs before the test suite runs. You can run the tests for the entire project with `npm run test` in the root, or change directories to the package you are working on and run `npm run test` to test just that package.
