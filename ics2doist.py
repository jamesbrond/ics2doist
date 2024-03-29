"""ICS file to todoist task"""

import sys
import logging
import argparse
import lib.utils as utils
import lib.key_ring as keyring
from lib.ics2doist import ICS2Doist
from lib.icscalendar import ICSCalendar

def _parse_cmd_line():
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
        help='name of section to put all events into')

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

    parser.add_argument('-d', '--debug',
        dest='loglevel',
        default=logging.INFO, action='store_const', const=logging.DEBUG,
        help='More verbose output')

    return parser.parse_args()

def main():
    """Main"""
    service_id = "JBROND_ICS2DOIST"
    args = _parse_cmd_line()
    logging.basicConfig(level=args.loglevel, format="[%(levelname)s] %(message)s")

    try:
        api_token = keyring.get_api_token(service_id)
        while not api_token:
            logging.warning(f"Todoist API token not found for {service_id} application.")
            keyring.setup(service_id)
            api_token = keyring.get_api_token(service_id)

        ics2doist = ICS2Doist(api_token=api_token)
        if args.ics_file:
            cal = ICSCalendar()
            for event in cal.read(args.ics_file):
                (task_content, task) = ics2doist.event_to_task(
                    event = event,
                    label_ids = ics2doist.label_ids(args.label),
                    project_id = ics2doist.project_id(args.project),
                    section_id = ics2doist.section_id(args.section))
                logging.info(f"Adding task {task_content}:")
                logging.debug(task)
                ics2doist.api.add_task(content=task_content, **task)

        elif args.projects:
            utils.dump_json(ics2doist.api.get_projects())
        elif args.sections:
            utils.dump_json(ics2doist.api.get_sections())
        elif args.labels:
            utils.dump_json(ics2doist.api.get_labels())

        return 0
    except Exception as e:
        logging.error(e, exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())

# ~@:-]
