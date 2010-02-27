# This file is part of ntpmon 0.1 - see COPYING.txt for license.

ROOT=root
GROUP=root
WWW=www-data
PROG=ntpmon
VAR=/var/lib/$(PROG)
IMG=$(VAR)/images
SHARE=/usr/share/$(PROG)
SHARE_FILES=style.css
APACHE_CONF=$(PROG)-apache.conf
APACHE=/etc/apache2/conf.d
CRON_CONF=$(PROG)-cron.conf
CRON=/etc/cron.d
INSTALL=install
CGI=/usr/lib/cgi-bin
SOURCES=ChangeLog COPYING.txt Makefile ntpmon ntpmon-all ntpmon-apache.conf ntpmon-cron.conf README.txt style.css THANKS.txt TODO.txt

default:
	@echo To install $(PROG) into $(CGI), $(SHARE), and $(VAR), run 'make install'

install:
	@$(INSTALL) --directory --owner=$(WWW) --group=$(GROUP) $(VAR) $(IMAGES)
	@$(INSTALL) --directory --owner=$(ROOT) --group=$(GROUP) $(SHARE)
	@$(INSTALL) --owner=$(ROOT) --group=$(GROUP) $(PROG) $(CGI)/
	@$(INSTALL) --owner=$(ROOT) --group=$(GROUP) $(SHARE_FILES) $(SHARE)/
	@$(INSTALL) --owner=$(ROOT) --group=$(GROUP) $(APACHE_CONF) $(APACHE)/
	@$(INSTALL) --owner=$(ROOT) --group=$(GROUP) $(CRON_CONF) $(CRON)/

tarball:
	rm -rf $(PROG)-$(VERSION)
	mkdir $(PROG)-$(VERSION)
	cp -al $(SOURCES) $(PROG)-$(VERSION)/
	tar -czf $(PROG)-$(VERSION).tar.gz $(PROG)-$(VERSION)/
	rm -rf $(PROG)-$(VERSION)/

