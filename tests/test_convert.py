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
import logging
import time
import sys

#!!!
#sys.path.append("../")
#!!!


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

    @classmethod
    def setUpClass(cls):
        cls.bell_dict = cls.dict_from_file("files/qobj_bell.json")
        cls.qaoa_dict = cls.dict_from_file("files/qobj_qaoa.json")
        pass

    def setUp(self):
        logging.basicConfig(
            format='%(levelname)s %(asctime)s %(pathname)s - %(message)s',
            level=os.environ.get("LOGLEVEL", "CRITICAL"),
        )
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        sys.stderr.write(" took %.3fs ... " % (t))

    def test_qaoa_speed(self):
        for i in range(0,10):
            ret = convert(Format.QOBJ, self.qaoa_dict, Format.PYQUIL)
        self.assertIs(type(ret), str)
        self.assertTrue(len(ret) > 0)

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
        ret = convert(Format.QOBJ, self.bell_dict, Format.PYQUIL)
        self.assertIs(type(ret), str)
        self.assertTrue(len(ret) > 0)
        ret = convert(Format.QOBJ, self.bell_dict, Format.TOASTER)
        self.assertIs(type(ret), str)
        self.assertTrue(len(ret) > 0)

    # check that qc.run is added by default (create_exec_code == True)
    def test_pyquil_qc_run(self):
        ret = convert(
            Format.QOBJ, self.bell_dict, Format.PYQUIL, options=dict()
        )
        self.assertTrue("qc.run" in ret)
        self.assertFalse("WavefunctionSimulator" in ret)

    def test_pyquil_seed(self):
        ret = convert(
            Format.QOBJ, self.bell_dict, Format.PYQUIL, options=dict(seed=1)
        )
        self.assertTrue(".random_seed" in ret)
        ret = convert(
            Format.QOBJ, self.bell_dict, Format.PYQUIL, options=dict()
        )
        self.assertFalse(".random_seed" in ret)

    # check that qc.run is omited when create_exec_code is set to False
    def test_pyquil_without_qc_run(self):
        ret = convert(
            Format.QOBJ,
            self.bell_dict,
            Format.PYQUIL,
            options={"create_exec_code": False},
        )
        self.assertFalse("qc.run" in ret)

    # check that WavefunctionSimulator is used for statevector_simulator
    # check that shots is not considered for statevector_simulator
    def test_pyquil_state_vector(self):
        ret = convert(
            Format.QOBJ,
            self.bell_dict,
            Format.PYQUIL,
            options={
                "lattice": "statevector_simulator",
                "create_exec_code": False,
                "shots": 10,
            },
        )
        self.assertFalse("wrap_in_numshots_loop" in ret)
        self.assertFalse("qc.run" in ret)
        self.assertTrue("WavefunctionSimulator" in ret)

    # check that wrap_in_numshots_loop exists when shots is larger than 1
    def test_pyquil_custom_lattice_and_shots(self):
        lattice = "aspen"
        ret = convert(
            Format.QOBJ,
            self.bell_dict,
            Format.PYQUIL,
            options={
                "lattice": lattice,
                "create_exec_code": False,
                "shots": 10,
            },
        )
        self.assertTrue("wrap_in_numshots_loop" in ret)
        self.assertFalse("qc.run" in ret)
        self.assertTrue(lattice in ret)


if __name__ == "__main__":
    unittest.main()
