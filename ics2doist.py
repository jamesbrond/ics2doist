import re
import sys
import json
import uuid
import keyring
import logging
import argparse
import requests
from ics import Calendar
from dateutil import parser

TODOIST_API_URL="https://api.todoist.com/rest/v1"

class RRule:
	def __init__(self, start, rule_string):
		self._freq_map = {
			"yearly": "year",
			"monthly": "month",
			"weekly": "week",
			"daily": "day",
			"hourly": "hour",
			"minutely": "minute",
			"secondly": "second"
		}
		self._month_list = ['months_start_at_1', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
		self._weekday_map = {
			"mo": "mon",
			"tu": "tue",
			"we": "wed",
			"th": "thu",
			"fr": "fri",
			"sa": "sat",
			"su": "sun"
		}
		self.dtstart = start
		self._parse(rule_string)

	def _handle_freq(self, rrkwargs, name, value):
		rrkwargs[name] = self._freq_map[value]

	def _handle_count(self, rrkwargs, name, value):
		rrkwargs[name] = value

	def _handle_until(self, rrkwargs, name, value):
		try:
			rrkwargs[name] = parser.parse(value)
		except ValueError:
			raise ValueError("invalid until date")

	def _handle_interval(self, rrkwargs, name, value):
		rrkwargs[name] = f"{value}"

	def _handle_bymonth(self, rrkwargs, name, value):
		# TODO rrkwargs[name] = [self._month_list[int(x)] for x in value.split(',')]
		pass

	def _handle_wkst(self, rrkwargs, name, value):
		# TODO rrkwargs[name] = self._weekday_map[value]
		pass

	def _handle_byday(self, rrkwargs, name, value):
		rrkwargs[name] = [self._weekday_map[x] for x in value.split(',')]

	def __str__(self):
		s = "every"

		if 'interval' in self.rrkwargs:
			s += f" {self.rrkwargs['interval']} {self.rrkwargs['freq']}s"
		elif 'byday' in self.rrkwargs:
			s += f" {','.join(self.rrkwargs['byday'])}"
		else:
			s += f" {self.rrkwargs['freq']}"

		if 'count' in self.rrkwargs:
			s += f" for {self.rrkwargs['count']} {self.rrkwargs['freq']}s"

		s += f" starting {self.dtstart.date().isoformat()}"

		if 'until' in self.rrkwargs:
			s += f" ending {self.rrkwargs['until'].date().isoformat()}"

		return s

	def _parse(self, rule_string):
		line = rule_string.split(':')[1]
		self.rrkwargs = {}
		for pair in line.split(';'):
			name, value = pair.split('=')
			name = name.lower()
			value = value.lower()
			try:
				getattr(self, "_handle_"+name)(self.rrkwargs, name, value)
			except AttributeError:
				raise ValueError("unknown parameter '%s'" % name)
			except (KeyError, ValueError):
				raise ValueError("invalid '%s': %s" % (name, value))

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

class ICS2Doist:
	def __init__(self, **options):
		self.todoist_api_url = options.pop('todoist_api_url', 'https://api.todoist.com/rest/v1')
		self.api_token = options['api_token']

	def _doist_api_get(self, action):
		return requests.get(
			f"{self.todoist_api_url}/{action}",
			headers={
				"Authorization": f"Bearer {self.api_token}"
			}).json()

	def _doist_api_post(self, action, data):
		return requests.post(
			f"{self.todoist_api_url}/{action}",
			data=json.dumps(data),
			headers={
				"Content-Type": "application/json",
				"X-Request-Id": str(uuid.uuid4()),
				"Authorization": f"Bearer {self.api_token}"
			}).json()

	def _strip_emoji(self, str):
		if str:
			emoji_pattern = re.compile("["
			u"\U0001F600-\U0001F64F"  # emoticons
			u"\U0001F300-\U0001F5FF"  # symbols & pictographs
			u"\U0001F680-\U0001F6FF"  # transport & map symbols
			u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
			"]+", flags=re.UNICODE)
			return emoji_pattern.sub(r'', str).strip()
		return None

	def _find_needle_in_haystack(self, needle, haystack):
		for straw in haystack:
			name = straw['name'].lower()
			if self._strip_emoji(name) == needle:
				return straw['id']
		return None


	def event_to_task(self, event, label_ids=None, project_id=None, section_id=None):
		task = {
			"content": event.name,
			"description": event.description,
			"completed": False
			# TODO priority
		}
		if project_id:
			task["project_id"] = project_id
		if section_id:
			task["section_id"] = section_id
		if label_ids:
			task["label_ids"] = label_ids

		rrules = None
		for line in event.extra:
			if str(line).startswith("RRULE"):
				rrules = str(line)
				break

		if rrules != None:
			task['due_string'] = str(RRule(event.begin, rrules))
		elif event.all_day:
			task['due_date'] = event.begin.format('YYYY-MM-DD')
		else:
			# TODO check timezone
			task['due_datetime'] = event.end.isoformat()

		return task

	def add_task(self, task):
		"""
		Creates a new task  and returns it as a JSON object
		"""
		return self._doist_api_post('tasks', task)

	def add_label(self, name):
		"""
		Creates a new label and returns its object as JSON
		"""
		return self._doist_api_post('labels', {"name": name})

	def get_all_projects(self):
		"""
		Returns JSON-encoded array containing all user projects
		"""
		return self._doist_api_get('projects')

	def get_all_sections(self):
		"""
		Returns a JSON array of all sections
		"""
		return self._doist_api_get('sections')

	def get_all_labels(self):
		"""
		Returns a JSON-encoded array containing all user labels
		"""
		return self._doist_api_get('labels')

	def get_label(self, name):
		"""
		Returns a label JSON-encoded object
		"""
		labels = self.get_all_labels()
		for label in labels:
			if label['name'] == name:
				return label
		return None

	def label_ids(self, label_name):
		"""
		Get label id. If label doesn't exitst it will create it
		"""
		l = None
		if label_name:
			l = self.get_label(label_name)
			if l is None:
				l = self.add_label(label_name)
		if l != None:
			l = [l['id']]
		return l

	def project_id(self, project_name):
		if project_name:
			return self._find_needle_in_haystack(project_name.lower(), self.get_all_projects())
		return None

	def section_id(self, section_name):
		if section_name:
			return self._find_needle_in_haystack(section_name.lower(), self.get_all_sections())
		return None

def parse_cmd_line():
	parser = argparse.ArgumentParser(prog="ics2doist.py", usage='%(prog)s [options]', description='Import ICS entries as Todoist tasks')

	parser.add_argument('-c', '--calendar',
		dest='ics_file',
		help='ICS calendar file')

	parser.add_argument('-l', '--label',
		dest='label',
		help='IDs of labels associated with all the events')

	parser.add_argument('-p', '--project',
		dest='project',
		help='events project name; if not set, events are put to user\'s Inbox')

	parser.add_argument('-s', '--section',
		dest='section',
		help='name of section to put all events into.')

	parser.add_argument('--projects',
    dest='projects',
    default=False, action='store_true',
    help='prints a JSON-encoded array containing all user projects and exit')

	parser.add_argument('--sections',
    dest='sections',
    default=False, action='store_true',
    help='prints a JSON array of all sections and exit')

	parser.add_argument('--labels',
    dest='labels',
    default=False, action='store_true',
    help='prints a JSON-encoded array containing all user labels and exit')

	parser.add_argument('--version',
		action='version',
		version='%(prog)s 1.4.0')

	return parser.parse_args()

def _dump_json(obj):
	print(json.dumps(obj, indent=3))

def set_api_token(service_id, token):
	keyring.set_password(service_id, 'API_TOKEN', token)

def get_api_token(service_id):
	return keyring.get_password(service_id, 'API_TOKEN')

def setup(service_id):
	token = input("Please enter your API token: ")
	set_api_token(service_id, token)

def main():
	service_id = "JBROND_ICS2DOIST"
	args = parse_cmd_line()

	try:
		api_token = get_api_token(service_id)
		while not api_token:
			logging.warning(f"Todoist API token not found for {service_id} application.")
			setup(service_id)
			api_token = get_api_token(service_id)

		ics2doist = ICS2Doist(api_token=api_token, todoist_api_url=TODOIST_API_URL)
		if args.ics_file:
			cal = ICSCalendar()
			for event in cal.read(args.ics_file):
				task = ics2doist.event_to_task(
					event = event,
					label_ids = ics2doist.label_ids(args.label),
					project_id = ics2doist.project_id(args.project),
					section_id = ics2doist.section_id(args.section))
				print(f"Add task {task['content']} ... ", end="")
				ics2doist.add_task(task)
				print("\tdone")

		elif args.projects:
			_dump_json(ics2doist.get_all_projects())
		elif args.sections:
			_dump_json(ics2doist.get_all_sections())
		elif args.labels:
			_dump_json(ics2doist.get_all_labels())

		return 0
	except Exception as e:
		logging.error(e, exc_info=True)
		return 1

if __name__ == "__main__":
	sys.exit(main())

# ~@:-]