import unittest
from DataObjects.PointEnumeration import PointEnumeration
import jsonpickle


class TestPointEnumeration(unittest.TestCase):

    def setUp(self):
        self.point = PointEnumeration(
            name="feed_state",
            description="Pump System State",
            hmi_writeable=True,
            requestable=True,
            states=["OFF", "RUN", "DEPRESSURIZE", "FLUSH"])

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point.__dict__, unpickled_point.__dict__)


if __name__ == '__main__':
    unittest.main()