#! /usr/bin/python
import re
import email
import sys
import os

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
            self.function = lambda mo : target

        if self.function:
            filters.append(self)
        else:
            pending.append(self)
            
    def __call__(self, function):
        assert self.function is None, "either use as decorator or call with three parameters"
        self.function = function
        filters.append(self)
        del pending[pending.index(self)]
        return function

def discard(header, value):
    filter(header, value)(lambda mo : None)

execfile(os.path.join(os.environ["HOME"], ".mailfilter"))

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

for filter in pending:
    print "missing filter function for", filter.header.pattern, filter.value.pattern

msg = email.message_from_file(sys.stdin)
del msg[MAILBOX_HEADER]
del msg[DISCARD_HEADER]
apply_filter(msg)
sys.stdout.write(msg.as_string())
