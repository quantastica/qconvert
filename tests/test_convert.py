# This code is part of quantastica.qconvert
#
# (C) Copyright Quantastica 2019.
# https://quantastica.com/
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import unittest
import json
import os
from quantastica.qconvert import convert, Format


class TestConvert(unittest.TestCase):
    @staticmethod
    def abspath(relativepath):
        return os.path.join(os.path.dirname(__file__), relativepath)

    @staticmethod
    def dict_from_file(relativepath):
        abspath = TestConvert.abspath(relativepath)
        ret = None
        with open(abspath) as f:
            ret = json.load(f)

        return ret

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_invalid_params(self):
        self.assertRaises(
            RuntimeError, convert, Format.PYQUIL, dict(), Format.TOASTER
        )

        self.assertRaises(
            RuntimeError, convert, Format.PYQUIL, dict(), Format.PYQUIL
        )

    def test_valid_params_empty_dict(self):
        ret = convert(Format.QOBJ, dict(), Format.TOASTER)
        self.assertEqual(len(ret), 0)
        ret = convert(Format.QOBJ, dict(), Format.PYQUIL)
        self.assertEqual(len(ret), 0)

    def test_bell_simple(self):
        bell_dict = self.dict_from_file("files/qobj_bell.json")
        ret = convert(Format.QOBJ, bell_dict, Format.PYQUIL)
        self.assertIs(type(ret), str)
        self.assertTrue(len(ret) > 0)
        ret = convert(Format.QOBJ, bell_dict, Format.TOASTER)
        self.assertIs(type(ret), str)
        self.assertTrue(len(ret) > 0)

    def test_bell_pyquil(self):
        # TODO: check for different outputs with different input options
        bell_dict = self.dict_from_file("files/qobj_bell.json")
        ret = convert(Format.QOBJ, bell_dict, Format.PYQUIL)
        self.assertTrue("qc.run" in ret)


if __name__ == "__main__":
    unittest.main()
