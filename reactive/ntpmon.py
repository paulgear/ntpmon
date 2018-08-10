#!/usr/bin/env python3
# Copyright (c) 2017 Canonical Ltd

from charmhelpers.fetch import apt_install
from charmhelpers.core import hookenv, host

from charms.reactive import (
    main,
    remove_state,
    set_state,
)

from charms.reactive.decorators import (
    hook,
    when,
    when_file_changed,
    when_not,
)

import os
import subprocess


#
# Module configuration - these shouldn't need adjusting
#

ntp_conf = '/etc/ntp.conf'
ntpmon_dir = '/opt/ntpmon'
service_name = 'ntpmon-telegraf'
systemd_config = '/etc/systemd/system/' + service_name + '.service'
upstart_config = '/etc/init/' + service_name + '.conf'

#
# Hooks
#


# layer-basic does not fire config.changed unconditionally on charm
# upgrade, which means we need to make that happen ourselves, in
# case there is a configuration-affecting change.

@hook('upgrade-charm')
def upgrade_charm():
    hookenv.log('Forcing NTPmon upgrade on upgrade-charm')
    remove_state('ntpmon.installed')


#
# Reactive state handlers
#


@when_not('ntpmon.installed')
def install_ntpmon():
    """
    Install package dependencies, source files, and startup configuration.
    """
    hookenv.log('installing ntpmon dependencies')
    apt_install(['python3-psutil'])

    hookenv.log('installing ntpmon')
    host.mkdir(os.path.dirname(ntpmon_dir))
    host.rsync('src/', '{}/'.format(ntpmon_dir))

    if host.init_is_systemd():
        hookenv.log('installing ntpmon systemd configuration')
        host.rsync('src/' + service_name + '.systemd', systemd_config)
        subprocess.call(['systemd', 'daemon-reload'])
    else:
        hookenv.log('installing ntpmon upstart configuration')
        host.rsync('src/' + service_name + '.upstart', upstart_config)
    set_state('ntpmon.installed')
    remove_state('ntpmon.configured')


@when('ntpmon.installed')
@when_not('ntpmon.configured')
def configure_ntpmon():
    """
    Reconfigure ntpmon - does nothing at present
    """
    hookenv.log('configuring ntpmon')
    set_state('ntpmon.configured')
    remove_state('ntpmon.started')


@when('ntpmon.configured', 'telegraf.configured')
@when_not('ntpmon.started')
def start_ntpmon():
    """
    Start the ntpmon daemon process.
    If ntp is not installed, do nothing.
    """
    if os.path.exists(ntp_conf):
        hookenv.log(ntp_conf + ' present; enabling and starting ntpmon')
        host.service_resume(service_name)
    else:
        hookenv.log(ntp_conf + ' not present; disabling ntpmon')
        host.service_pause(service_name)
    set_state('ntpmon.started')


@when_file_changed([ntp_conf], hash_type='sha256')
def ntp_conf_updated():
    remove_state('ntpmon.started')


if __name__ == '__main__':
    main()
