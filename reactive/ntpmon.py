
# Copyright (c) 2017-2018 Canonical Ltd
# Author: Paul Gear

from charms import layer
from charmhelpers.core import host

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

import charmhelpers.contrib.templating.jinja as templating
import os
import subprocess
import sys


#
# Module configuration
#

chrony_conf = '/etc/chrony/chrony.conf'
ntp_conf = '/etc/ntp.conf'
ntpmon_options = layer.options('ntpmon')


def get_config(option):
    if option in ntpmon_options:
        value = ntpmon_options[option]
        if value is not None and len(value) > 0:
            return value
    return None


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
    remove_state('ntpmon.installed')


#
# Reactive state handlers
#


@when_not('ntpmon.installed')
def install_ntpmon():
    """
    Install package dependencies, source files, and startup configuration.
    """
    install_dir = get_config('install-dir')
    if install_dir:
        log('installing ntpmon')
        host.rsync('src/', install_dir)

    service_name = get_config('service-name')
    using_systemd = host.init_is_systemd()
    if install_dir and service_name:
        if using_systemd:
            systemd_config = '/etc/systemd/system/' + service_name + '.service'
            log('installing systemd service: {}'.format(service_name))
            with open(systemd_config, 'w') as conffile:
                conffile.write(templating.render('src/' + service_name + '.systemd', ntpmon_options))
            subprocess.call(['systemd', 'daemon-reload'])
        else:
            upstart_config = '/etc/init/' + service_name + '.conf'
            log('installing upstart service: {}'.format(service_name))
            with open(upstart_config, 'w') as conffile:
                conffile.write(templating.render('src/' + service_name + '.upstart', ntpmon_options))
    else:
        if using_systemd:
            systemd_config = '/etc/systemd/system/' + service_name + '.service'
            log('removing systemd service: {}'.format(service_name))
            os.unlink(systemd_config)
            subprocess.call(['systemd', 'daemon-reload'])
        else:
            upstart_config = '/etc/init/' + service_name + '.conf'
            log('removing upstart service: {}'.format(service_name))
            host.rsync('src/' + service_name + '.upstart', upstart_config)

    set_state('ntpmon.installed')
    remove_state('ntpmon.configured')


@when('ntpmon.installed')
@when_not('ntpmon.configured')
def configure_ntpmon():
    """
    Reconfigure ntpmon - does nothing at present
    """
    log('configuring ntpmon')
    set_state('ntpmon.configured')
    remove_state('ntpmon.started')


@when('ntpmon.configured', 'telegraf.configured')
@when_not('ntpmon.started')
def start_ntpmon():
    """
    Start the ntpmon daemon process.
    If no NTP server is installed, do nothing.
    """
    service_name = get_config('service-name')
    started = False
    if service_name is not None and len(service_name):
        for f in (chrony_conf, ntp_conf):
            # TODO: set ntpmon mode based on config file presence?
            if os.path.exists(f):
                log('{} present; enabling and starting ntpmon'.format(f))
                host.service_resume(service_name)
                started = True
                break
        if not started:
            log('No supported NTP service present; disabling ntpmon')
            host.service_pause(service_name)
    set_state('ntpmon.started')


@when_file_changed([chrony_conf], hash_type='sha256')
def chrony_conf_updated():
    log('{} changed - checking if ntpmon needs starting'.format(chrony_conf))
    remove_state('ntpmon.started')


@when_file_changed([ntp_conf], hash_type='sha256')
def ntp_conf_updated():
    log('{} changed - checking if ntpmon needs starting'.format(ntp_conf))
    remove_state('ntpmon.started')


if __name__ == '__main__':
    main()
