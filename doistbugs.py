import re
import sys
import argparse
import logging
import lib.utils as utils
import lib.key_ring as keyring
from lib.doistemplate import DoistTemplate

REGEXP_LINE = r"^\d+"
PROJECT_NAME = 'Work'
SECTION_NAME = 'ris11'

def parse_cmd_line():
	parser = argparse.ArgumentParser(prog="ics2doist.py", usage='%(prog)s [options]', description='Import ICS entries as Todoist tasks')
	parser.add_argument('-d', '--debug',
		dest='loglevel',
		default=logging.INFO, action='store_const', const=logging.DEBUG,
		help='More verbose output')

	return parser.parse_args()

def parse_input_row(line):
	logging.debug(line)
	if re.search(REGEXP_LINE, line):
		t = line.split('\t')
		return {
			"content": f"#{t[0]}: {t[3]}",
			"description": t[5],
			"priority": 2,
			"labels": [t[2]]
		}
	return None

def main():
	service_id = "JBROND_ICS2DOIST"
	args = parse_cmd_line()
	logging.basicConfig(level=args.loglevel, format="[%(levelname)s] %(message)s")

	try:
		api_token = keyring.get_api_token(service_id)
		while not api_token:
			logging.warning(f"Todoist API token not found for {service_id} application.")
			keyring.setup(service_id)
			api_token = keyring.get_api_token(service_id)

		tmpl = DoistTemplate(api_token)
		project_id = utils.find_needle_in_haystack([PROJECT_NAME], tmpl.projects)
		logging.debug(f"project id: {project_id}")
		section_id = utils.find_needle_in_haystack([SECTION_NAME], tmpl.sections)
		logging.debug(f"section id: {section_id}")

		print("Paste bug list and press ctrl+z, enter when done:")
		msg = sys.stdin.readlines()
		for line in msg:
			task = parse_input_row(line)
			if task:
				logging.debug(f"Add task {task}")
				tmpl._task(project_id, section_id, None, task, None)

		return 0
	except Exception as e:
		logging.error(e, exc_info=True)
		return 1

if __name__ == "__main__":
	sys.exit(main())