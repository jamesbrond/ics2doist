import logging
from ics import Calendar

class ICSCalendar:
	def __init__(self):
		self.events = []

	def __sizeof__(self):
		return len(self.events)

	def read(self, in_file):
		"""
		Gets all events from ICS file
		"""
		self.events = []
		try:
			with open(in_file, 'r') as file:
				ics_text = file.read()
			c = Calendar(ics_text)
			self.events = c.events
		except Exception as e:
			logging.error(e)
		return self.events

	def get_events(self):
		return self.events

# ~@:-]