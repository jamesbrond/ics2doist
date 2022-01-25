import sys
import logging
import argparse
import lib.key_ring as keyring
from lib.doistbackup import DoistBackup
from lib.doistrestore import DoistRestore

def parse_cmd_line():
	parser = argparse.ArgumentParser(prog="doistbackup.py", usage='%(prog)s [options]', description='Backup and restore utility for Todoist')

	parser.add_argument('-b', '--backup',
		dest='is_backup',
		action='store_true',
		default=True,
		help='Backup flag')

	parser.add_argument('-r', '--restore',
		dest='is_restore',
		action='store_true',
		default=False,
		help='Restore flag')

	parser.add_argument('-f', '--file',
		dest='filename',
		required=True)

	parser.add_argument('--version',
		action='version',
		version='%(prog)s 1.0.0')

	parser.add_argument('-d', '--debug',
    dest='loglevel',
    default=logging.INFO, action='store_const', const=logging.DEBUG,
    help='More verbose output')

	return parser.parse_args()


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

		if args.is_restore:
			rest = DoistRestore(args.filename, api_token)
			rest.restore()
		elif args.is_backup:
			bkg = DoistBackup(args.filename, api_token)
			bkg.backup()

		return 0
	except Exception as e:
		logging.error(e, exc_info=True)
		return 1

if __name__ == "__main__":
	sys.exit(main())

# ~@:-]