.PHONY:  install uninstall
install:
	cp -f ec4Linux.py $(DESTDIR)/usr/bin/ec4Linux.py
	cp -f exec4Linux.sh $(DESTDIR)/usr/bin/ec4Linux
	cp -f data/polkit-1/actions/io.itch.odintdh.extremecooling4linux.policy $(DESTDIR)/usr/share/polkit-1/actions/
	cp -f locale/es/LC_MESSAGES/extremecooling4linux.mo $(DESTDIR)/usr/share/locale/es/LC_MESSAGES/extremecooling4linux.mo
	mkdir -p $(DESTDIR)/usr/share/extremecooling4linux
	cp -rf data $(DESTDIR)/usr/share/extremecooling4linux/
	cp -f data/io.itch.odintdh.extremecooling4linux.desktop $(DESTDIR)/usr/share/applications/
	cp -f data/img/extremecooling4linux.png $(DESTDIR)/usr/share/pixmaps/extremecooling4linux.png
	cp -f metainfo/io.itch.odintdh.extremecooling4linux.appdata.xml $(DESTDIR)/usr/share/metainfo/
	chmod 0755 $(DESTDIR)/usr/bin/ec4Linux.py
	chmod 0755 $(DESTDIR)/usr/bin/ec4Linux

uninstall:
	rm -f $(DESTDIR)/usr/bin/ec4Linux.py
	rm -f $(DESTDIR)/usr/bin/ec4Linux
	rm -f $(DESTDIR)/usr/share/polkit-1/actions/io.itch.odintdh.extremecooling4linux.policy
	rm -f $(DESTDIR)/usr/share/locale/es/LC_MESSAGES/extremecooling4linux.mo
	rm -f $(DESTDIR)/usr/share/applications/io.itch.odintdh.extremecooling4linux.desktop
	rm -f $(DESTDIR)/usr/share/pixmaps/extremecooling4linux.png
	rm -rf $(DESTDIR)/usr/share/extremecooling4linux
	rm -f $(DESTDIR)/usr/share/metainfo/io.itch.odintdh.extremecooling4linux.appdata.xml
