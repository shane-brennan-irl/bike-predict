import unittest
import math
from engine.BikePredictEngine import BikePredictEngine

class Test(unittest.TestCase):

	def test_Forecast_1(self):
		engine = BikePredictEngine()
		testList = [5,5,5,5,5,4,4,5]
		st, bt = engine.getExpSmthForecast(testList)
		result = st+bt
		self.assertTrue(result > 4.0 and result < 6.0 )

	def test_Forecast_2(self):
		engine = BikePredictEngine()
		testList = [8,8,7,6,5,4,3,2]
		st, bt = engine.getExpSmthForecast(testList)
		result = st+bt
		self.assertTrue(result < 2.0)

	def test_Forecast_3(self):
		engine = BikePredictEngine()
		testList = [8,8,6,5,5,4,4,2,1,1,1,1]
		st, bt = engine.getExpSmthForecast(testList)
		result = st+bt
		self.assertTrue(result < 1.0)

	def test_Forecast_4(self):
		engine = BikePredictEngine()
		testList = [8,8,7,8,8,8,8,8,9,8,8,8,8,8,8,8,8]
		st, bt = engine.getExpSmthForecast(testList)
		result = st+bt
		self.assertTrue(result > 7.5 and result < 8.5)

	def test_init_Forecast_1(self):
		engine = BikePredictEngine()
		testList = []
		st, bt = engine.getExpSmthForecast(testList)
		self.assertTrue(st is None)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
