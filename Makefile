# This file is part of ntpmon - see COPYING.txt for license.

BINDIR=bin
BUILDROOT=buildroot
CONFDIR=/etc/default
DESTDIR=/
GROUP=$(NAME)
NAME=ntpmon
PREFIX=/usr/local
SHAREDIR=share/$(NAME)
SYSTEMD_SERVICE_DIR=/lib/systemd/system
USER=$(NAME)
VERSION=3.0.1
RELEASE=1

TESTS=\
  unit_tests/test_peer_stats.py \
  unit_tests/test_tailer.py \
  unit_tests/test_classifier.py \
  unit_tests/test_peers.py

test: pytest datatest

pytest:
	PYTHONPATH=$(PWD)/src python3 -m pytest $(TESTS)

datatest:
	PYTHONPATH=$(PWD)/src ./testdata/testdata.sh

format:
	black --line-length=128 --target-version=py39 src/ unit_tests/

push:
	git push github

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

install:
	install -d $(DESTDIR)/$(PREFIX)/ \
		$(DESTDIR)/$(CONFDIR)/ \
		$(DESTDIR)/$(PREFIX)/$(BINDIR)/ \
		$(DESTDIR)/$(PREFIX)/$(SHAREDIR)/ \
		$(DESTDIR)/$(SYSTEMD_SERVICE_DIR)/
	install -m 0644 src/*.py $(DESTDIR)/$(PREFIX)/$(SHAREDIR)/
	chmod 0755 $(DESTDIR)/$(PREFIX)/$(SHAREDIR)/*ntpmon.py
	cd $(DESTDIR)/$(PREFIX)/$(BINDIR); \
		ln -s ../$(SHAREDIR)/ntpmon.py $(NAME); \
		ln -s ../$(SHAREDIR)/check_ntpmon.py check_$(NAME)
	BINDIR=$(PREFIX)/$(BINDIR) CONFDIR=$(CONFDIR) GROUP=$(GROUP) NAME=$(NAME) USER=$(USER) python3 \
		src/jinja2_render.py src/ntpmon.service > $(DESTDIR)/$(SYSTEMD_SERVICE_DIR)/$(NAME).service
	BINDIR=$(PREFIX)/$(BINDIR) CONFDIR=$(CONFDIR) GROUP=$(GROUP) NAME=$(NAME) USER=$(USER) python3 \
		src/jinja2_render.py src/ntpmon.env > $(DESTDIR)/$(CONFDIR)/$(NAME)

release:
	dch --newversion $(VERSION)-$(RELEASE)
	dch --release --distribution focal
	for i in CHANGELOG.md debian/changelog debian/*.rst; do \
		grep -qw "$(VERSION)" $$i || exit 1; \
	done
	git commit -m'Prepare $(VERSION) release' -a
	git tag --sign v$(VERSION)
	git push --tags

$(BUILDROOT):
	mkdir $@

orig:	$(BUILDROOT)
	git archive --format=tar.gz --prefix=$(NAME)-$(VERSION)/ v$(VERSION) > $(BUILDROOT)/$(NAME)_$(VERSION).orig.tar.gz
	if [ ! -f tarballs/$(NAME)_$(VERSION).orig.tar.gz ]; then \
		cp $(BUILDROOT)/$(NAME)_$(VERSION).orig.tar.gz tarballs/; \
	fi
	cd $(BUILDROOT) && tar -xf $(NAME)_$(VERSION).orig.tar.gz

package:	$(BUILDROOT)
	cd $(BUILDROOT)/$(NAME)-$(VERSION)/ && debuild

srcpackage:	$(BUILDROOT)
	cd $(BUILDROOT)/$(NAME)-$(VERSION)/ && debuild -S
