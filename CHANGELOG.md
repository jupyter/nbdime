# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

## 4.0.2

([Full Changelog](https://github.com/jupyter/nbdime/compare/4.0.1...cafe00c44746cb9831ea2052a7666b898f36fae8))

### Bugs fixed

- Allow unauthenticated access to jupyter server [#761](https://github.com/jupyter/nbdime/pull/761) ([@krassowski](https://github.com/krassowski))

### Maintenance and upkeep improvements

- Update release scripts to use trusted publisher [#768](https://github.com/jupyter/nbdime/pull/768) ([@krassowski](https://github.com/krassowski))
- Bump express and verdaccio [#765](https://github.com/jupyter/nbdime/pull/765) ([@dependabot](https://github.com/dependabot))
- Bump braces from 3.0.2 to 3.0.3 [#764](https://github.com/jupyter/nbdime/pull/764) ([@dependabot](https://github.com/dependabot))
- Bump ejs from 3.1.9 to 3.1.10 [#763](https://github.com/jupyter/nbdime/pull/763) ([@dependabot](https://github.com/dependabot))
- Bump webpack from 5.86.0 to 5.94.0 [#762](https://github.com/jupyter/nbdime/pull/762) ([@dependabot](https://github.com/dependabot))
- Bump axios to version 1.7.4 [#760](https://github.com/jupyter/nbdime/pull/760) ([@tiltingpenguin](https://github.com/tiltingpenguin))
- Update integration tests workflow [#758](https://github.com/jupyter/nbdime/pull/758) ([@krassowski](https://github.com/krassowski))
- Bump follow-redirects from 1.15.3 to 1.15.6 [#750](https://github.com/jupyter/nbdime/pull/750) ([@dependabot](https://github.com/dependabot))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/nbdime/graphs/contributors?from=2023-11-21&to=2024-09-05&type=c))

[@dependabot](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Adependabot+updated%3A2023-11-21..2024-09-05&type=Issues) | [@krassowski](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Akrassowski+updated%3A2023-11-21..2024-09-05&type=Issues) | [@tiltingpenguin](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Atiltingpenguin+updated%3A2023-11-21..2024-09-05&type=Issues)

<!-- <END NEW CHANGELOG ENTRY> -->

## 4.0.1

([Full Changelog](https://github.com/jupyter/nbdime/compare/4.0.0...89548a7f688c31d86138371eb610c74e4810486a))

### Bugs fixed

- Fix version parsing [#739](https://github.com/jupyter/nbdime/pull/739) ([@fcollonval](https://github.com/fcollonval))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/nbdime/graphs/contributors?from=2023-11-20&to=2023-11-21&type=c))

[@fcollonval](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Afcollonval+updated%3A2023-11-20..2023-11-21&type=Issues)

## 4.0.0

([Full Changelog](https://github.com/jupyter/nbdime/compare/3.2.1...d02956e0e24a0e00160ca912f90261858528a39b))

### Enhancements made

- Change header for unchanged notebook meta [#736](https://github.com/jupyter/nbdime/pull/736) ([@vidartf](https://github.com/vidartf))
- Ensure collapsed mergepane border [#731](https://github.com/jupyter/nbdime/pull/731) ([@vidartf](https://github.com/vidartf))
- Add translation for the frontend in Lab [#709](https://github.com/jupyter/nbdime/pull/709) ([@fcollonval](https://github.com/fcollonval))
- Make collapseIdentical margin configurable [#707](https://github.com/jupyter/nbdime/pull/707) ([@fcollonval](https://github.com/fcollonval))
- Support hiding base editor [#705](https://github.com/jupyter/nbdime/pull/705) ([@fcollonval](https://github.com/fcollonval))
- Restore collapsers [#701](https://github.com/jupyter/nbdime/pull/701) ([@fcollonval](https://github.com/fcollonval))
- Add support for using cell ID in diffing and merging [#639](https://github.com/jupyter/nbdime/pull/639) ([@vidartf](https://github.com/vidartf))

### Bugs fixed

- Fix duplicate pickers [#735](https://github.com/jupyter/nbdime/pull/735) ([@vidartf](https://github.com/vidartf))
- CM6: Fix spacing between editors [#728](https://github.com/jupyter/nbdime/pull/728) ([@HaudinFlorence](https://github.com/HaudinFlorence))
- Fix drag and drop [#723](https://github.com/jupyter/nbdime/pull/723) ([@fcollonval](https://github.com/fcollonval))
- Do not collapse editor lines in single editor [#719](https://github.com/jupyter/nbdime/pull/719) ([@fcollonval](https://github.com/fcollonval))
- Improve alignment [#717](https://github.com/jupyter/nbdime/pull/717) ([@fcollonval](https://github.com/fcollonval))
- Add CSS files in nbdime package [#715](https://github.com/jupyter/nbdime/pull/715) ([@fcollonval](https://github.com/fcollonval))
- Apply post-mortem review comments [#711](https://github.com/jupyter/nbdime/pull/711) ([@fcollonval](https://github.com/fcollonval))
- Improve `findAlignedLines` [#706](https://github.com/jupyter/nbdime/pull/706) ([@fcollonval](https://github.com/fcollonval))
- Improve diff view [#696](https://github.com/jupyter/nbdime/pull/696) ([@fcollonval](https://github.com/fcollonval))
- Fix wrong picker marker (a typo during lab 4.0 migration) [#688](https://github.com/jupyter/nbdime/pull/688) ([@krassowski](https://github.com/krassowski))
- Use pseudo-elements instead of border to preserve line height [#687](https://github.com/jupyter/nbdime/pull/687) ([@krassowski](https://github.com/krassowski))

### Maintenance and upkeep improvements

- Test the releaser fix for tag format [#737](https://github.com/jupyter/nbdime/pull/737) ([@fcollonval](https://github.com/fcollonval))
- Bump axios from 1.5.1 to 1.6.1 [#734](https://github.com/jupyter/nbdime/pull/734) ([@dependabot](https://github.com/dependabot))
- Bump JS packages to rc.0 [#730](https://github.com/jupyter/nbdime/pull/730) ([@fcollonval](https://github.com/fcollonval))
- Bump @babel/traverse from 7.22.5 to 7.23.2 [#713](https://github.com/jupyter/nbdime/pull/713) ([@dependabot](https://github.com/dependabot))
- Set up releaser [#710](https://github.com/jupyter/nbdime/pull/710) ([@fcollonval](https://github.com/fcollonval))
- Upgrade devdependencies and clean up the configuration [#708](https://github.com/jupyter/nbdime/pull/708) ([@fcollonval](https://github.com/fcollonval))
- Don't trigger CI jobs twice [#704](https://github.com/jupyter/nbdime/pull/704) ([@fcollonval](https://github.com/fcollonval))
- Bump postcss from 8.4.24 to 8.4.31 [#703](https://github.com/jupyter/nbdime/pull/703) ([@dependabot](https://github.com/dependabot))
- Switch from hub to gh CLI [#702](https://github.com/jupyter/nbdime/pull/702) ([@fcollonval](https://github.com/fcollonval))
- RTD: make sure nodejs is present [#698](https://github.com/jupyter/nbdime/pull/698) ([@minrk](https://github.com/minrk))
- Add src for sourcemap [#692](https://github.com/jupyter/nbdime/pull/692) ([@fcollonval](https://github.com/fcollonval))
- Chore: use jupyter packaging [#600](https://github.com/jupyter/nbdime/pull/600) ([@agoose77](https://github.com/agoose77))

### Documentation improvements

- Update test badge [#725](https://github.com/jupyter/nbdime/pull/725) ([@fcollonval](https://github.com/fcollonval))
- Bump version [#712](https://github.com/jupyter/nbdime/pull/712) ([@fcollonval](https://github.com/fcollonval))
- Add `.readthedocs.yml` config file [#686](https://github.com/jupyter/nbdime/pull/686) ([@krassowski](https://github.com/krassowski))
- Remove debug console.log [#684](https://github.com/jupyter/nbdime/pull/684) ([@fcollonval](https://github.com/fcollonval))

### Other merged PRs

- Fix editor background color [#714](https://github.com/jupyter/nbdime/pull/714) ([@HaudinFlorence](https://github.com/HaudinFlorence))
- Fix pickers for empty chunks [#691](https://github.com/jupyter/nbdime/pull/691) ([@krassowski](https://github.com/krassowski))
- Fix syntax highlighting issue in diffchunks. [#689](https://github.com/jupyter/nbdime/pull/689) ([@HaudinFlorence](https://github.com/HaudinFlorence))
- Support JupyterLab 4.0, port to Lumino 2 [#673](https://github.com/jupyter/nbdime/pull/673) ([@HaudinFlorence](https://github.com/HaudinFlorence))
- Bump semver from 5.7.1 to 5.7.2 [#671](https://github.com/jupyter/nbdime/pull/671) ([@dependabot](https://github.com/dependabot))
- Update files with prettier formatting [#668](https://github.com/jupyter/nbdime/pull/668) ([@HaudinFlorence](https://github.com/HaudinFlorence))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/nbdime/graphs/contributors?from=2023-04-30&to=2023-11-20&type=c))

[@agoose77](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Aagoose77+updated%3A2023-04-30..2023-11-20&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Adependabot+updated%3A2023-04-30..2023-11-20&type=Issues) | [@fcollonval](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Afcollonval+updated%3A2023-04-30..2023-11-20&type=Issues) | [@github-actions](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Agithub-actions+updated%3A2023-04-30..2023-11-20&type=Issues) | [@HaudinFlorence](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3AHaudinFlorence+updated%3A2023-04-30..2023-11-20&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Ajtpio+updated%3A2023-04-30..2023-11-20&type=Issues) | [@krassowski](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Akrassowski+updated%3A2023-04-30..2023-11-20&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Aminrk+updated%3A2023-04-30..2023-11-20&type=Issues) | [@SylvainCorlay](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3ASylvainCorlay+updated%3A2023-04-30..2023-11-20&type=Issues) | [@vidartf](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Avidartf+updated%3A2023-04-30..2023-11-20&type=Issues)

## 4.0.0rc1

([Full Changelog](https://github.com/jupyter/nbdime/compare/nbdime-jupyterlab@3.0.0-rc.1...d02956e0e24a0e00160ca912f90261858528a39b))

### Enhancements made

- Change header for unchanged notebook meta [#736](https://github.com/jupyter/nbdime/pull/736) ([@vidartf](https://github.com/vidartf))
- Ensure collapsed mergepane border [#731](https://github.com/jupyter/nbdime/pull/731) ([@vidartf](https://github.com/vidartf))

### Bugs fixed

- Fix duplicate pickers [#735](https://github.com/jupyter/nbdime/pull/735) ([@vidartf](https://github.com/vidartf))

### Maintenance and upkeep improvements

- Test the releaser fix for tag format [#737](https://github.com/jupyter/nbdime/pull/737) ([@fcollonval](https://github.com/fcollonval))
- Bump axios from 1.5.1 to 1.6.1 [#734](https://github.com/jupyter/nbdime/pull/734) ([@dependabot](https://github.com/dependabot))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/nbdime/graphs/contributors?from=2023-11-06&to=2023-11-20&type=c))

[@dependabot](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Adependabot+updated%3A2023-11-06..2023-11-20&type=Issues) | [@fcollonval](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Afcollonval+updated%3A2023-11-06..2023-11-20&type=Issues) | [@github-actions](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Agithub-actions+updated%3A2023-11-06..2023-11-20&type=Issues) | [@vidartf](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Avidartf+updated%3A2023-11-06..2023-11-20&type=Issues)

## 4.0.0rc0

([Full Changelog](https://github.com/jupyter/nbdime/compare/4.0.0a1...4349d9477f2dba374bca7355779c94071431b64b))

### Enhancements made

- Add translation for the frontend in Lab [#709](https://github.com/jupyter/nbdime/pull/709) ([@fcollonval](https://github.com/fcollonval))
- Add support for using cell ID in diffing and merging [#639](https://github.com/jupyter/nbdime/pull/639) ([@vidartf](https://github.com/vidartf))

### Bugs fixed

- CM6: Fix spacing between editors [#728](https://github.com/jupyter/nbdime/pull/728) ([@HaudinFlorence](https://github.com/HaudinFlorence))
- Fix drag and drop [#723](https://github.com/jupyter/nbdime/pull/723) ([@fcollonval](https://github.com/fcollonval))
- Do not collapse editor lines in single editor [#719](https://github.com/jupyter/nbdime/pull/719) ([@fcollonval](https://github.com/fcollonval))
- Improve alignment [#717](https://github.com/jupyter/nbdime/pull/717) ([@fcollonval](https://github.com/fcollonval))
- Add CSS files in nbdime package [#715](https://github.com/jupyter/nbdime/pull/715) ([@fcollonval](https://github.com/fcollonval))

### Maintenance and upkeep improvements

- Bump JS packages to rc.0 [#730](https://github.com/jupyter/nbdime/pull/730) ([@fcollonval](https://github.com/fcollonval))
- Bump @babel/traverse from 7.22.5 to 7.23.2 [#713](https://github.com/jupyter/nbdime/pull/713) ([@dependabot](https://github.com/dependabot))
- Set up releaser [#710](https://github.com/jupyter/nbdime/pull/710) ([@fcollonval](https://github.com/fcollonval))

### Documentation improvements

- Update test badge [#725](https://github.com/jupyter/nbdime/pull/725) ([@fcollonval](https://github.com/fcollonval))
- Bump version [#712](https://github.com/jupyter/nbdime/pull/712) ([@fcollonval](https://github.com/fcollonval))

### Other merged PRs

- Fix editor background color [#714](https://github.com/jupyter/nbdime/pull/714) ([@HaudinFlorence](https://github.com/HaudinFlorence))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/nbdime/graphs/contributors?from=2023-10-16&to=2023-11-06&type=c))

[@dependabot](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Adependabot+updated%3A2023-10-16..2023-11-06&type=Issues) | [@fcollonval](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Afcollonval+updated%3A2023-10-16..2023-11-06&type=Issues) | [@github-actions](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Agithub-actions+updated%3A2023-10-16..2023-11-06&type=Issues) | [@HaudinFlorence](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3AHaudinFlorence+updated%3A2023-10-16..2023-11-06&type=Issues) | [@krassowski](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Akrassowski+updated%3A2023-10-16..2023-11-06&type=Issues) | [@vidartf](https://github.com/search?q=repo%3Ajupyter%2Fnbdime+involves%3Avidartf+updated%3A2023-10-16..2023-11-06&type=Issues)
