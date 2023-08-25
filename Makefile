install:
	cp -r piaware-configurator/* /var/www/piaware_configurator
	cp debian/piaware-configurator.service /lib/systemd/system/
	cp sudoers/piaware-configurator /etc/sudoers.d/
