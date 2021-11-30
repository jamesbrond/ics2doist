import sys
import keyring
import logging
import argparse
from lib.ics2doist import ICS2Doist
from lib.icscalendar import ICSCalendar

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

def _dump_json(obj_list):
	for obj in  obj_list:
		print(obj)

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

		ics2doist = ICS2Doist(api_token=api_token)
		if args.ics_file:
			cal = ICSCalendar()
			for event in cal.read(args.ics_file):
				(task_content, task) = ics2doist.event_to_task(
					event = event,
					label_ids = ics2doist.label_ids(args.label),
					project_id = ics2doist.project_id(args.project),
					section_id = ics2doist.section_id(args.section))
				print(f"Add task {task_content} ... ", end="")
				ics2doist.api.add_task(content=task_content, **task)
				print("\tdone")

		elif args.projects:
			_dump_json(ics2doist.api.get_projects())
		elif args.sections:
			_dump_json(ics2doist.api.get_sections())
		elif args.labels:
			_dump_json(ics2doist.api.get_labels())

		return 0
	except Exception as e:
		logging.error(e, exc_info=True)
		return 1

if __name__ == "__main__":
	sys.exit(main())

# ~@:-]