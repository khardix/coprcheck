# Automated quality checking of COPR repositories

`coprcheck` is a CLI tool, written in Python 3, designed to automate running of
various tests on provided [COPR][copr] repository.

## Status

This project is work in progress, in alpha/development stage. The user should
not assume that any feature or functionality is final.

Travis CI status: [![Build Status](https://travis-ci.org/khardix/coprcheck.svg?branch=master)](https://travis-ci.org/khardix/coprcheck)

## Collaboration and testing

If you want to contribute, please submit a pull request. Please provide tests
for any new functionality and assure that the test suite passes with your changes
applied. The project is tested using [pytest][].

## Legal

The source code is freely available under the [GNU AGPL v3][agpl] license. For
details, see the link or the LICENSE file in the repository.

[agpl]: https://www.gnu.org/licenses/agpl.html "GNU Affero General Public License, Version 3"
[copr]: https://copr.fedorainfracloud.org/ "COPR – Fedora build system"
[pytest]: http://pytest.org/ "pytest: a mature full-featured Python testing tool"
