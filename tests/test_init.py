import unittest

class TestInit(unittest.TestCase):
    def test_init_file(self):
        # A simple smoke test ensuring the package imports
        import startq
        self.assertTrue(hasattr(startq, '__version__'))
        
if __name__ == "__main__":
    unittest.main()
