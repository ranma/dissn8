# Copyright (C) 2019  Vincent Pelletier <plr.vincent@gmail.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import absolute_import
from io import BytesIO
import unittest
from .assn8 import assemble
from . import simsn8

EQUAL = object()

def _diffDict(a, b):
    result = {}
    key_set = set(a)
    unique_key_set = key_set.symmetric_difference(b)
    if unique_key_set:
        raise ValueError(a.keys(), b.keys())
    for key in key_set:
        value_diff = diff(a[key], b[key])
        if value_diff is not EQUAL:
            result[key] = value_diff
    if result:
        return result
    return EQUAL

def _diffVector(a, b):
    result = {}
    if len(a) != len(b):
        raise ValueError(len(a), len(b))
    for index, (item_a, item_b) in enumerate(zip(a, b)):
        item_diff = diff(item_a, item_b)
        if item_diff is not EQUAL:
            result[index] = item_b
    if result:
        return result
    return EQUAL

def _diffValue(a, b):
    return EQUAL if a == b else b

_type_diff = {
    dict: _diffDict,
    list: _diffVector,
    tuple: _diffVector,
    int: _diffValue,
    type(None): _diffValue,
}

# XXX: A limitation of this is that it only detects actual changes. If an item
# is written to with the same value (ex: clearing an already cleared FZ), it
# will not be detected.
def diff(a, b):
    diff_a = _type_diff[type(a)]
    diff_b = _type_diff[type(b)]
    if diff_a is not diff_b:
        raise TypeError(type(a), type(b))
    return diff_a(a, b)

class SimSN8F2288TestBase(unittest.TestCase):
    @staticmethod
    def _getSimulator(source, watchdog=False):
        return simsn8.SN8F2288(BytesIO(assemble(
            # Boilerplate stuff.
            u'CHIP SN8F2288\n'
            u'//{{SONIX_CODE_OPTION\n'
            u'    .Code_Option Watch_Dog "' + (
                u'Enable' if watchdog else u'Disable'
            ) + u'"\n'
            u'    .Code_Option LVD "LVD_M"\n'
            u'//}}SONIX_CODE_OPTION\n'
            u'.CODE\n'
            u'ORG 0\n' +
            source + '\n'
        )))

    @staticmethod
    def _stripStateTiming(state):
        return {
            x: y
            for x, y in state.iteritems()
            if x not in ('run_time', 'cycle_count', 'slow_clock')
        }

    def assertStrippedDifferenceEqual(self, state0, state1, expected):
        self.assertEqual(
            diff(
                self._stripStateTiming(state0),
                self._stripStateTiming(state1),
            ),
            expected,
        )