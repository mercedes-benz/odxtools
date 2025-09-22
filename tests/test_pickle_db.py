# SPDX-License-Identifier: MIT
import pickle
import unittest

from odxtools.loadfile import load_pdx_file


class TestPickleDatabase(unittest.TestCase):

    def test_pickle(self) -> None:
        fresh_db = load_pdx_file("./examples/somersault.pdx")
        pickled_db = pickle.dumps(fresh_db)
        unpickled_db = pickle.loads(pickled_db)

        self.assertEqual(repr(fresh_db), repr(unpickled_db))


if __name__ == "__main__":
    unittest.main()
