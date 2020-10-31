# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -rf build/html/
	rm source/lena.*.rst source/modules.rst source/lena.rst

## Create Russian documentation ##
# sphinx-build -b gettext source _build/gettext
# Update it later:
# sphinx-intl update -p _build/gettext -l ru
# Build Russian documentation (after updating po files):
# sphinx-build -b html -D language=ru source _build/html/ru
# From https://docs.readthedocs.io/en/stable/guides/manage-translations.html
#
# To add another language, create a different project on Readthedocs
# https://docs.readthedocs.io/en/stable/localization.html#project-with-multiple-translations
# Update its versions (otherwise only latest will be shown).

## Create Russian RST ##
# python2 /usr/local/bin/xml2rst.py _build/xml/ru/tutorial/1-introduction.xml > 1-intro.rst
# Probably, manually substitute excessive spaces.
