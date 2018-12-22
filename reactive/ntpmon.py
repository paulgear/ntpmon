
# Copyright (c) 2017-2018 Canonical Ltd
# Author: Paul Gear

from charms import layer
from charmhelpers.core import host

from charms.reactive import (
    clear_flag,
    set_flag,
)

from charms.reactive.decorators import (
    hook,
    when,
    when_file_changed,
    when_not,
)

import charmhelpers.contrib.templating.jinja as templating
import os
import subprocess
import sys


#
# Module configuration
#

CHRONY_CONF = '/etc/chrony/chrony.conf'
NTP_CONF = '/etc/ntp.conf'


#
# hookenv.log is expensive; use stderr instead
#
def log(msg):
    print(msg, file=sys.stderr)


#
# Hooks
#


# layer-basic does not fire config.changed unconditionally on charm
# upgrade, which means we need to make that happen ourselves, in
# case there is a configuration-affecting change.

@hook('upgrade-charm')
def upgrade_charm():
    log('Forcing NTPmon upgrade on upgrade-charm')
    clear_flag('ntpmon.installed')


#
# Reactive state handlers
#


@when_not('ntpmon.installed')
def install_ntpmon():
    """
    Install package dependencies, source files, and startup configuration.
    """
    install_dir = layer.options.get('ntpmon', 'install-dir')
    service_name = layer.options.get('ntpmon', 'service-name')
    using_systemd = host.init_is_systemd()
    if install_dir:
        log('installing ntpmon')
        host.mkdir(os.path.dirname(install_dir))
        host.rsync('src/', '{}/'.format(install_dir))

        if service_name:
            if using_systemd:
                systemd_config = '/etc/systemd/system/' + service_name + '.service'
                log('installing systemd service: {}'.format(service_name))
                with open(systemd_config, 'w') as conffile:
                    conffile.write(templating.render('src/' + service_name + '.systemd', layer.options.get('ntpmon')))
                subprocess.call(['systemd', 'daemon-reload'])
            else:
                upstart_config = '/etc/init/' + service_name + '.conf'
                log('installing upstart service: {}'.format(service_name))
                with open(upstart_config, 'w') as conffile:
                    conffile.write(templating.render('src/' + service_name + '.upstart', layer.options.get('ntpmon')))

    set_flag('ntpmon.installed')
    clear_flag('ntpmon.configured')


# TODO: implement removal


@when('ntpmon.installed')
@when_not('ntpmon.configured')
def configure_ntpmon():
    """
    Reconfigure ntpmon - does nothing at present
    """
    log('configuring ntpmon')
    set_flag('ntpmon.configured')
    clear_flag('ntpmon.started')


@when('ntpmon.configured')
@when_not('ntpmon.started')
def start_ntpmon():
    """
    Start the ntpmon daemon process.
    If no NTP server is installed, do nothing.
    """
    started = False
    service_name = layer.options.get('ntpmon', 'service-name')
    if service_name:
        for f in (CHRONY_CONF, NTP_CONF):
            if os.path.exists(f):
                log('{} present; enabling and starting ntpmon'.format(f))
                host.service_resume(service_name)
                started = True
                break
        if not started:
            log('No supported NTP service present; disabling ntpmon')
            host.service_pause(service_name)
    set_flag('ntpmon.started')


# TODO: implement stop


@when_file_changed([CHRONY_CONF], hash_type='sha256')
def chrony_conf_updated():
    log('{} changed - checking if ntpmon needs starting'.format(CHRONY_CONF))
    clear_flag('ntpmon.started')


@when_file_changed([NTP_CONF], hash_type='sha256')
def ntp_conf_updated():
    log('{} changed - checking if ntpmon needs starting'.format(NTP_CONF))
    clear_flag('ntpmon.started')
