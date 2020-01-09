import unittest
import warnings
from quantastica.qconvert import convert, Format

class TestConvert(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_invalid_params(self):
        self.assertRaises(
            RuntimeError
            , convert, Format.PYQUIL, dict(), Format.TOASTER
            )

        self.assertRaises(
            RuntimeError
            , convert, Format.PYQUIL, dict(), Format.PYQUIL
            )


    def test_valid_params_empty_dict(self):
        ret = convert(Format.QOBJ, dict(), Format.TOASTER)
        self.assertEqual( None, ret )
        


if __name__ == '__main__':
    unittest.main()
