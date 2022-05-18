import unittest

import user
import building
import system
import events


class TestEvents(unittest.TestCase):
    def setUp(self):
        self.year = 2022
        self.me = user.User('data/users/NewUser.yaml')
        self.my_building = building.Building('data/buildings/NewBuilding.yaml')
        self.my_system = system.System('data/systems/NewSystem.yaml')
        self.event_states = {}

    def test_inherit(self):
        ''' Test if the money gets added to the event_economic_balance when you inherit'''
        inital_event_economic_balance = self.me.event_economic_balance
        events.inherit(self.year, self.me, self.my_building, self.my_system, self.event_states)
        new_event_economic_balance = self.me.event_economic_balance
        self.assertGreater(new_event_economic_balance, inital_event_economic_balance)

if __name__ == '__main__':
    unittest.main()