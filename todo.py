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

def setup(service_id):
	token = input("Please enter your API token: ")
	set_api_token(service_id, token)

def set_api_token(service_id, token):
	keyring.set_password(service_id, 'API_TOKEN', token)

def get_api_token(service_id):
	return keyring.get_password(service_id, 'API_TOKEN')

def parse_cmd_line():
	parser = argparse.ArgumentParser(prog="todo.py", usage='%(prog)s [options]', description='Import ICS entries as Todoist tasks')

	# input ICS
	parser.add_argument('-c', '--calendar',
		dest='ics_file',
		help='ICS calendar file')

	# label name assigned to all events
	# if the label is not found in the label will be created
	parser.add_argument('-l', '--label',
		dest='label',
		help='Label assigned to all calendar events')

	# get projects list
	parser.add_argument('--projects',
    dest='projects',
    default=False, action='store_true',
    help='Get all projects')

	# get sections list
	parser.add_argument('--sections',
    dest='sections',
    default=False, action='store_true',
    help='Get all sections')

	# get label list
	parser.add_argument('--labels',
    dest='labels',
    default=False, action='store_true',
    help='Get all labels')

	# version
	parser.add_argument('--version',
		action='version',
		version='%(prog)s 1.3.0')

	return parser.parse_args()

def _doist_api_get(api_token, action):
	return requests.get(
		f"{TODOIST_API_URL}/{action}",
		headers={
			"Authorization": f"Bearer {api_token}"
		}).json()

def _doist_api_post(api_token, action, data):
	return requests.post(
		f"{TODOIST_API_URL}/{action}",
		data=json.dumps(data),
		headers={
			"Content-Type": "application/json",
			"X-Request-Id": str(uuid.uuid4()),
			"Authorization": f"Bearer {api_token}"
		}).json()

def _dump_json(obj):
	print(json.dumps(obj, indent=3))

def event_to_task(event, label_ids=None, project_id=None, section_id=None):
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

def read_calendar(in_file):
	"""
	Gets all events from ICS file
	"""
	with open(in_file, 'r') as file:
		ics_text = file.read()
	c = Calendar(ics_text)
	return c.events

def add_task(api_token, task):
	"""
	Creates a new task  and returns it as a JSON object
	"""
	return _doist_api_post(api_token, 'tasks', task)

def add_label(api_token, name):
	"""
	Creates a new label and returns its object as JSON
	"""
	return _doist_api_post(api_token, 'labels', {"name": name})

def get_all_projects(api_token):
	"""
	Returns JSON-encoded array containing all user projects
	"""
	return _doist_api_get(api_token, 'projects')

def get_all_sections(api_token):
	"""
	Returns a JSON array of all sections
	"""
	return _doist_api_get(api_token, 'sections')

def get_all_labels(api_token):
	"""
	Returns a JSON-encoded array containing all user labels
	"""
	return _doist_api_get(api_token, 'labels')

def get_label(api_token, name):
	"""
	Returns a label JSON-encoded object
	"""
	labels = get_all_labels(api_token)
	for label in labels:
		if label['name'] == name:
			return label
	return None

def main():
	service_id = 'JBROND_TODO'
	args = parse_cmd_line()

	try:
		api_token = get_api_token(service_id)
		while not api_token:
			logging.warning(f"Todoist API token not found for {service_id} application.")
			setup(service_id)
			api_token = get_api_token(service_id)

		if args.ics_file:
			label = None
			if args.label:
				label = get_label(api_token, args.label)
				if label is None:
					label = add_label(api_token, args.label)
			if label != None:
				label = [label['id']]
			for event in read_calendar(args.ics_file):
				task = event_to_task(event, label)
				print(f"Add task {task['content']} ... ", end="")
				add_task(api_token, task)
				print("\tdone")

		elif args.projects:
			_dump_json(get_all_projects(api_token))
		elif args.sections:
			_dump_json(get_all_sections(api_token))
		elif args.labels:
			_dump_json(get_all_labels(api_token))

		return 0
	except Exception as e:
		logging.error(e, exc_info=True)
		return 1

if __name__ == "__main__":
	sys.exit(main())

# ~@:-]