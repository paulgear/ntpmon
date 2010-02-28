# This file is part of ntpmon 0.1 - see COPYING.txt for license.

ROOT=root
GROUP=root
WWW=www-data
PROG=ntpmon
VAR=/var/lib/$(PROG)
IMG=$(VAR)/images
SHARE=/usr/share/$(PROG)
DOC=/usr/share/doc/$(PROG)
SHARE_FILES=style.css
DOC_FILES=ChangeLog COPYING.txt README.txt THANKS.txt TODO.txt ntpmon-all
APACHE_CONF=$(PROG)-apache.conf
APACHE=/etc/apache2/conf.d
CRON_CONF=$(PROG)-cron.conf
CRON=/etc/cron.d
INSTALL=install
CGI=/usr/lib/cgi-bin
SOURCES=Makefile $(DOC_FILES) $(PROG) $(APACHE_CONF) $(CRON_CONF) $(SHARE_FILES)
VERSION=$(shell head -1 ChangeLog|awk '{print $$3}')

default:
	@echo To install $(PROG), run 'make install'.  This will install files into
	@for i in $(APACHE) $(CRON) $(CGI) $(DOC) $(SHARE) $(VAR); do \
	    echo "\t$$i"; \
	done

install:
	$(INSTALL) --directory --owner=$(WWW) --group=$(GROUP) $(VAR) $(IMG)
	$(INSTALL) --directory --owner=$(ROOT) --group=$(GROUP) $(SHARE) $(DOC)
	$(INSTALL) --owner=$(ROOT) --group=$(GROUP) $(PROG) $(CGI)/
	$(INSTALL) --owner=$(ROOT) --group=$(GROUP) -m 644 $(SHARE_FILES) $(SHARE)/
	$(INSTALL) --owner=$(ROOT) --group=$(GROUP) -m 644 $(DOC_FILES) $(DOC)/
	$(INSTALL) --owner=$(ROOT) --group=$(GROUP) -m 644 $(APACHE_CONF) $(APACHE)/
	$(INSTALL) --owner=$(ROOT) --group=$(GROUP) -m 644 $(CRON_CONF) $(CRON)/
	sed -ri -e 's/www-data/$(WWW)/' -e 's~/usr/lib/cgi-bin~$(CGI)~' -e 's~/var/lib/ntpmon~$(VAR)~' $(CRON)/$(CRON_CONF)

tarball:
	rm -rf $(PROG)-$(VERSION)
	mkdir $(PROG)-$(VERSION)
	cp -al $(SOURCES) $(PROG)-$(VERSION)/
	tar -czf tarballs/$(PROG)-$(VERSION).tar.gz $(PROG)-$(VERSION)/
	rm -rf $(PROG)-$(VERSION)/

