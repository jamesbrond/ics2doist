import sys
import logging
import argparse
import lib.key_ring as keyring
from lib.doistemplate import DoistTemplate

#######################################################################

class StoreDictKeyPair(argparse.Action):
	def __call__(self, parser, namespace, values, option_string=None):
		my_dict = {}
		for kv in values.split(","):
			k,v = kv.split("=")
			my_dict[k] = v
		setattr(namespace, self.dest, my_dict)

def parse_cmd_line():
	parser = argparse.ArgumentParser(prog="doistemplate.py", usage='%(prog)s [options]', description='Create a new task from a template')

	parser.add_argument(
		'template',
		type=argparse.FileType('r'))

	parser.add_argument("-D",
		dest="placeholders",
		action=StoreDictKeyPair,
		metavar="PLACEHOLDER0=VALUE0,PLACEHOLDER1=VALUE1...")

	parser.add_argument('--version',
		action='version',
		version='%(prog)s 1.0.0')

	return parser.parse_args()

def main():
	service_id = "JBROND_ICS2DOIST"
	args = parse_cmd_line()

	try:
		api_token = keyring.get_api_token(service_id)
		while not api_token:
			logging.warning(f"Todoist API token not found for {service_id} application.")
			keyring.setup(service_id)
			api_token = keyring.get_api_token(service_id)

		tmpl = DoistTemplate(api_token)
		with args.template as file:
			tmpl.parse(file, args.placeholders)

		return 0
	except Exception as e:
		logging.error(e, exc_info=True)
		return 1

if __name__ == "__main__":
	sys.exit(main())