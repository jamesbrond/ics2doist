import sys
import json
import uuid
import keyring
import logging
import argparse
import requests
from ics import Calendar

TODOIST_API_URL="https://api.todoist.com/rest/v1"

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

def read_calendar(in_file):
	events = []
	with open(in_file, 'r') as file:
		ics_text = file.read()
		c = Calendar(ics_text)
		for e in c.events:
			events.append({
				"title": e.name,
				"date": e.begin.format('YYYY-MM-DD')
			})
		return events

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

def add_task(api_token, title, due, label_ids):
	"""
	Creates a new task  and returns it as a JSON object
	"""
	return _doist_api_post(api_token, 'tasks', {
		"content": title,
		"due_date": due,
		"label_ids": label_ids
	})

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
			labels = None
			if args.label:
				label = get_label(api_token, args.label)
				if label is None:
					label = add_label(api_token, args.label)
			if label != None:
				labels = [label['id']]
			for event in read_calendar(args.ics_file):
				print(f"Add task {event['title']} on {event['date']}...", end="")
				add_task(api_token, event['title'], event['date'], labels)
				print("\tdone")

		elif args.projects:
			print(json.dumps(get_all_projects(api_token), indent=3))
		elif args.sections:
			print(json.dumps(get_all_sections(api_token), indent=3))
		elif args.labels:
			print(json.dumps(get_all_labels(api_token), indent=3))

		return 0
	except Exception as e:
		logging.error(e, exc_info=True)
		return 1

if __name__ == "__main__":
	sys.exit(main())

# ~@:-]