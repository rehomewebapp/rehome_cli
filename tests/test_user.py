import unittest


import user

class TestUser(unittest.TestCase):
    def setUp(self):
        self.me = user.User('data/users/NewUser.yaml')

    def test_purchase_valid(self):
        ''' Test if the the user has enough money'''
        investment_cost = 500
        self.assertTrue(self.me.check_solvency(investment_cost))

    def test_purchase_invalid(self):
        ''' Test if the the user has not enough money'''
        investment_cost = 5000
        self.assertFalse(self.me.check_solvency(investment_cost))


if __name__ == '__main__':
    unittest.main()

