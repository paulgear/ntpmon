# This file is part of ntpmon - see COPYING.txt for license.

BUILDROOT=buildroot
DESTDIR=/
NAME=ntpmon
PREFIX=/usr/local
SHAREDIR=share/$(NAME)
VERSION=2.0.0

test: pytest datatest

pytest:
	PYTHONPATH=./src python3 -m unittest -b unit_tests/test_classifier.py unit_tests/test_peers.py

datatest:
	PYTHONPATH=./src ./testdata/testdata.sh

push:
	git push github

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

install:
	install -d $(DESTDIR)/$(PREFIX)/ $(DESTDIR)/$(PREFIX)/$(SHAREDIR)/
	install -m 0644 src/*.py $(DESTDIR)/$(PREFIX)/$(SHAREDIR)/
	chmod 0755 $(DESTDIR)/$(PREFIX)/$(SHAREDIR)/*ntpmon.py
	install -d -m 0755 $(DESTDIR)/$(PREFIX)/bin
	cd $(DESTDIR)/$(PREFIX)/bin; \
		ln -s ../$(SHAREDIR)/ntpmon.py $(NAME); \
		ln -s ../$(SHAREDIR)/check_ntpmon.py check_$(NAME)

buildenv:
	mkdir -p $(BUILDROOT)
	git archive --format=tar.gz --prefix=$(NAME)-$(VERSION)/ HEAD > $(BUILDROOT)/$(NAME)_$(VERSION).orig.tar.gz

package:	buildenv
	cd $(BUILDROOT); \
		tar -xf $(NAME)_$(VERSION).orig.tar.gz; \
		cd $(NAME)-$(VERSION)/; \
		debuild

srcpackage:	buildenv
	cd $(BUILDROOT); \
		tar -xf $(NAME)_$(VERSION).orig.tar.gz; \
		cd $(NAME)-$(VERSION)/; \
		debuild -S
