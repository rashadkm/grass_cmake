# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 18:39:21 2013

@author: pietro
"""
from __future__ import (nested_scopes, generators, division, absolute_import,
                        with_statement, print_function, unicode_literals)
from . import read


class Flag(object):
    def __init__(self, xflag=None, diz=None):
        self.value = False
        diz = read.element2dict(xflag) if xflag is not None else diz
        self.name = diz['name']
        self.special = True if self.name in (
            'verbose', 'overwrite', 'quiet', 'run') else False
        self.description = diz['description']
        self.default = diz.get('default', None)
        self.guisection = diz.get('guisection', None)

    def get_bash(self):
        if self.value:
            if self.special:
                return '--%s' % self.name[0]
            else:
                return '-%s' % self.name
        else:
            return ''

    def get_python(self):
        if self.value:
            if self.special:
                return '%s=True' % self.name
            else:
                return self.name
        else:
            return ''

    def __str__(self):
        return self.get_bash()

    def __repr__(self):
        return "Flag <%s> (%s)" % (self.name, self.description)

    @property
    def __doc__(self):
        """
        {name}: {default}
            {description}"""
        return read.DOC['flag'].format(name=self.name,
                                       default=repr(self.default),
                                       description=self.description)
