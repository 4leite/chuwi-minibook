PREFIX ?= /usr/local
LIBEXECDIR ?= $(PREFIX)/libexec
SYSTEMD_USER_UNIT_DIR ?= $(PREFIX)/lib/systemd/user

SCRIPT = gnome-tablet-exit-orientation.py
SERVICE = gnome-tablet-exit-orientation.service

all:

check:
	python3 -m unittest -v test_gnome_tablet_exit_orientation.py

install:
	install -Dm755 $(SCRIPT) \
		$(DESTDIR)$(LIBEXECDIR)/gnome-tablet-exit-orientation
	install -d $(DESTDIR)$(SYSTEMD_USER_UNIT_DIR)
	sed 's|@libexecdir@|$(LIBEXECDIR)|g' $(SERVICE).in \
		> $(DESTDIR)$(SYSTEMD_USER_UNIT_DIR)/$(SERVICE)
	chmod 644 $(DESTDIR)$(SYSTEMD_USER_UNIT_DIR)/$(SERVICE)

uninstall:
	rm -f $(DESTDIR)$(LIBEXECDIR)/gnome-tablet-exit-orientation
	rm -f $(DESTDIR)$(SYSTEMD_USER_UNIT_DIR)/$(SERVICE)

.PHONY: all check install uninstall
