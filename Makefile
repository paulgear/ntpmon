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
		src/jinja2_render.py src/ntpmon-prometheus.systemd > $(DESTDIR)/$(SYSTEMD_SERVICE_DIR)/$(NAME)-prometheus.service
	BINDIR=$(PREFIX)/$(BINDIR) CONFDIR=$(CONFDIR) GROUP=$(GROUP) NAME=$(NAME) USER=$(USER) python3 \
		src/jinja2_render.py src/ntpmon-telegraf.systemd > $(DESTDIR)/$(SYSTEMD_SERVICE_DIR)/$(NAME)-telegraf.service
	BINDIR=$(PREFIX)/$(BINDIR) CONFDIR=$(CONFDIR) GROUP=$(GROUP) NAME=$(NAME) USER=$(USER) python3 \
		src/jinja2_render.py src/ntpmon.env > $(DESTDIR)/$(CONFDIR)/$(NAME)

$(BUILDROOT):
	mkdir $@
	git archive --format=tar.gz --prefix=$(NAME)-$(VERSION)/ HEAD > $(BUILDROOT)/$(NAME)_$(VERSION).orig.tar.gz

package:	$(BUILDROOT)
	cd $(BUILDROOT); \
		tar -xf $(NAME)_$(VERSION).orig.tar.gz; \
		cd $(NAME)-$(VERSION)/; \
		debuild

srcpackage:	$(BUILDROOT)
	cd $(BUILDROOT); \
		tar -xf $(NAME)_$(VERSION).orig.tar.gz; \
		cd $(NAME)-$(VERSION)/; \
		debuild -S
