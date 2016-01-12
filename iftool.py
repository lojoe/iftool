#!/usr/bin/env python
'''
Network interface configuration control tool.

Usage:
    iftool [options] configure [--host=<host>] <template> [<destination>]

Options:
    -h, --help              display this message and exit.
    -V, --version           display version and exit.
    -v, --verbose           display extra output.
    -y, --yes               required for changes to take affect and files to
                            be written.
    --overwrite             required to replace existing files.

Commands:
    configure               Generate network configuration files described by
                            <template>. <destination> is where to place the
                            files [default: /etc/sysconfig/network-scripts] and
                            <host> is the server to write the files for
                            [default: `hostname`].
'''
__author__ = 'Joe Baldwin'
__author_email__ = 'joe@joebaldwin.com'
__credit__ = 'Adknowledge, Inc.'
__license__ = 'MIT'


import os
import socket
import sys

import docopt
import ipaddress
import jinja2
import yaml


VERBOSE = False
YES = False
OVERWRITE = False


def say(text='', newline=True, stream=None):
    '''
    Write text to stream with optional newline.
    '''
    if stream is None:
        stream = sys.stdout
    stream.write(str(text))
    if newline:
        stream.write(os.linesep)

    try: stream.flush()
    except AttributeError: pass


def verbose(text='', newline=True, stream=None):
    '''
    Call say() but only when --verbose switch has been supplied.
    '''
    if VERBOSE:
        say(text, newline, stream)


class CustomLoader(yaml.Loader):
    '''
    I am a YAML loader that supports !include.
    '''
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(CustomLoader, self).__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename) as file:
            return yaml.load(file, CustomLoader)
CustomLoader.add_constructor(u'!include', CustomLoader.include)


def configure(arguments):
    '''
    Generate network configuration files for a PowerMTA server.
    '''
    arguments['--host'] = arguments['--host'] or socket.gethostname()
    arguments['<destination>'] = arguments['<destination>'] or os.getcwd()

    with open(arguments['<template>']) as file:
        configuration = yaml.load(file, CustomLoader)

        if configuration['global']['vlan']:
            configure_device(configuration, arguments)
        configure_routes(configuration, arguments)
        configure_rules(configuration, arguments)
        configure_interfaces(configuration, arguments)


def configure_device(configuration, arguments):
    this_host = arguments['--host']
    for host in configuration['hosts']:
        if this_host == host or this_host.split('.')[0] == host.split('.')[0]:
            detail = configuration['hosts'][host]
            break
    else:
        say('ERROR: %s not found in template hosts section' % this_host)
        sys.exit(1)

    vlan = configuration['global']['vlan']
    device = detail['device']

    filename = jinja2.Template(configuration['templates']['device']['filename']).render(device=device)
    filename = os.path.join(arguments['<destination>'], filename)
    content = jinja2.Template(configuration['templates']['device']['content']).render(device=device, vlan=vlan)

    if YES:
        verbose('Writing %s' % os.path.join(arguments['<destination>'], filename))
        with open(filename, 'wt') as file:
            file.write(content)
    else:
        say('<DRY-RUN> not writing %s' % filename)
        for line in content.splitlines():
            say('> %s' % line)
        say('Use "--yes" option to write file.')


def configure_routes(configuration, arguments):
    this_host = arguments['--host']
    for host in configuration['hosts']:
        if this_host == host or this_host.split('.')[0] == host.split('.')[0]:
            detail = configuration['hosts'][host]
            break
    else:
        say('ERROR: %s not found in template hosts section' % this_host)
        sys.exit(1)

    device = detail['device']
    tables = []
    for table in sorted(configuration['tables']):
        d = configuration['tables'][table]
        tables.append({
            'table': table,
            'device': device,
            'ifname': d['primary ifname'],
            'subnet': d['subnet'],
            'gateway': d['default gateway']
        })

    filename = jinja2.Template(configuration['templates']['route']['filename']).render(device=device)
    filename = os.path.join(arguments['<destination>'], filename)
    content = jinja2.Template(configuration['templates']['route']['content']).render(tables=tables)

    if YES:
        verbose('Writing %s' % os.path.join(arguments['<destination>'], filename))
        with open(filename, 'wt') as file:
            file.write(content)
    else:
        say('<DRY-RUN> not writing %s' % filename)
        for line in content.splitlines():
            say('> %s' % line)
        say('Use "--yes" option to write file.')


def configure_rules(configuration, arguments):
    this_host = arguments['--host']
    for host in configuration['hosts']:
        if this_host == host or this_host.split('.')[0] == host.split('.')[0]:
            detail = configuration['hosts'][host]
            break
    else:
        say('ERROR: %s not found in template hosts section' % this_host)
        sys.exit(1)

    device = detail['device']
    tables = []
    for table in sorted(configuration['tables']):
        d = configuration['tables'][table]
        tables.append({
            'table': table,
            'device': device,
            'ifname': d['primary ifname'],
            'subnet': d['subnet'],
            'gateway': d['default gateway']
        })

    filename = jinja2.Template(configuration['templates']['rule']['filename']).render(device=device)
    filename = os.path.join(arguments['<destination>'], filename)
    content = jinja2.Template(configuration['templates']['rule']['content']).render(tables=tables)

    if YES:
        verbose('Writing %s' % os.path.join(arguments['<destination>'], filename))
        with open(filename, 'wt') as file:
            file.write(content)
    else:
        say('<DRY-RUN> not writing %s' % filename)
        for line in content.splitlines():
            say('> %s' % line)
        say('Use "--yes" option to write file.')


def configure_interfaces(configuration, arguments):
    this_host = arguments['--host']
    for host in configuration['hosts']:
        if this_host == host or this_host.split('.')[0] == host.split('.')[0]:
            detail = configuration['hosts'][host]
            break
    else:
        say('ERROR: %s not found in template hosts section' % this_host)
        sys.exit(1)

    vlan = configuration['global']['vlan']
    device = detail['device']
    ifnames = {}
    for table in sorted(configuration['tables']):
        d = configuration['tables'][table]
        ifnames[d['primary ifname']] = {
            'table': table,
            'device': device,
            'ifname': d['primary ifname'],
            'subnet': d['subnet'],
            'gateway': d['default gateway']
        }

    for ifname in sorted(ifnames.keys()):
        filename = jinja2.Template(configuration['templates']['interface']['filename']).render(
            device=device,
            ifname=ifname
        )
        filename = os.path.join(arguments['<destination>'], filename)

        address = configuration['hosts'][host]['addresses'][ifname]
        subnet = ipaddress.IPv4Network(unicode(ifnames[ifname]['subnet']))
        network_address = subnet.network_address
        netmask = subnet.netmask

        content = jinja2.Template(configuration['templates']['interface']['content']).render(
            device=device,
            ifname=ifname,
            address=address,
            network_address=network_address,
            netmask=netmask
        )

        if YES:
            verbose('Writing %s' % os.path.join(arguments['<destination>'], filename))
            with open(filename, 'wt') as file:
                file.write(content)
        else:
            say('<DRY-RUN> not writing %s' % filename)
            for line in content.splitlines():
                say('> %s' % line)
            say('Use "--yes" option to write file.')


def main(argv=None):
    '''
    Main program entry point.
    '''
    global VERBOSE
    global YES
    global OVERWRITE

    arguments = docopt.docopt(__doc__, argv)

    VERBOSE = arguments['--verbose']
    YES = arguments['--yes']
    OVERWRITE = arguments['--overwrite']

    if arguments['configure']:
        configure(arguments)


if __name__ == '__main__':
    main()
