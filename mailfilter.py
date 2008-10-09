#!/usr/bin/env python
#
# Copyright (C) 2008 Alexander Bernauer (alex at ulm dot ccc dot de)
# Copyright (C) 2008 Rico Schiekel (fire at downgra dot de)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
#
# vim:syntax=python:sw=4:ts=4:expandtab

__version__ = '0.1'

import sys
import os
import re
import email

DISCARD_HEADER = 'x-mailfilter-discard'
MAILBOX_HEADER = 'x-mailfilter-mailbox'

filters = []
pending = []


def esc(s):
    return s.replace(".", "-")


class filter(object):

    def __init__(self, header, value, target=None):
        self.header = re.compile(header)
        self.value = re.compile(value)
        if target is None:
            self.function = None
        elif callable(target):
            self.function = target
        else:
            self.function = lambda mo: target

        if self.function:
            filters.append(self)
        else:
            pending.append(self)

    def __call__(self, function):
        assert self.function is None, "either use as decorator or call with " \
                                      "three parameters"
        self.function = function
        filters.append(self)
        del pending[pending.index(self)]
        return function


def discard(header, value):
    filter(header, value)(lambda mo: None)


def apply_filter(msg):
    for filter in filters:
        for header, value in msg.items():
            if filter.header.match(header):
                mo = filter.value.search(value)
                if mo:
                    mailbox = filter.function(mo)
                    if mailbox is None:
                        msg[DISCARD_HEADER] = "True"
                    else:
                        msg[MAILBOX_HEADER] = mailbox
                    return


execfile(os.path.join(os.environ.get("HOME", ''), ".mailfilter"))

for filter in pending:
    print "missing filter function for '%s' '%s'" % (filter.header.pattern,
                                                     filter.value.pattern)

msg = email.message_from_file(sys.stdin)
del msg[MAILBOX_HEADER]
del msg[DISCARD_HEADER]
apply_filter(msg)
sys.stdout.write(msg.as_string())
