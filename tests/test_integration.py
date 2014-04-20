from datetime import datetime, timedelta
import os
import sys
from unittest import TestCase

from pyaerobia import Aerobia

if sys.version_info >= (3, 0):
    basestring = str
    xrange = range
    unicode = str

class IntegrationTests(TestCase):

    @classmethod
    def setUpClass(cls):
        user = os.environ['PYAEROBIA_USER']
        password = os.environ['PYAEROBIA_PASS']
        cls.aerobia = Aerobia()
        cls.aerobia.auth(user, password)

    def test_auth(self):
        self.assertIsNotNone(self.aerobia.user_id())

    # TODO: test_workout(self): pass

    def test_workout_iterator_self(self):
        iter = self.aerobia.workout_iterator()
        self.assertIsNotNone(iter)
        workout = iter.next()
        self.assertIsNotNone(workout)
        self.assertIsInstance(workout.id, basestring)
        self.assertIsInstance(workout.name, basestring)
        self.assertIsInstance(workout.date, datetime)
        self.assertIsInstance(workout.duration, timedelta)
        self.assertIsInstance(workout.length, float)
        self.assertIsInstance(workout.type, basestring)

    def test_workout_iterator_foreign(self):
        iter = self.aerobia.workout_iterator(user_id=1)
        self.assertIsNotNone(iter)
        workout = iter.next()
        self.assertIsNotNone(workout)
        self.assertIsInstance(workout.id, basestring)
        self.assertIsInstance(workout.name, basestring)
        self.assertIsInstance(workout.date, datetime)
        self.assertIsInstance(workout.duration, timedelta)
        self.assertIsInstance(workout.length, float)
        self.assertIsInstance(workout.type, basestring)

    def test_import_export_workout(self):
        try:
            last_id = self.aerobia.workout_iterator().next().id
        except StopIteration:
            last_id = None
        file = open(os.path.join(os.path.dirname(__file__), "example.tcx"))
        void = self.aerobia.import_workout(file)
        self.assertIsNone(void)
        uploaded_id = self.aerobia.workout_iterator().next().id
        self.assertNotEqual(last_id, uploaded_id)
        tcx = self.aerobia.export_workout(uploaded_id)
        self.assertIsInstance(tcx, basestring)
