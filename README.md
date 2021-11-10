# ics2doist

## Usage

    ics2doist.py [options]
    Import ICS entries as Todoist tasks

    optional arguments:
      -h, --help            show this help message and exit
      -c ICS_FILE, --calendar ICS_FILE
                            ICS calendar file
      -l LABEL, --label LABEL
                            IDs of labels associated with all the events
      -p PROJECT, --project PROJECT
                            events project name; if not set, events are put to user's Inbox
      -s SECTION, --section SECTION
                            name of section to put all events into.
      --projects            prints a JSON-encoded array containing all user projects and exit
      --sections            prints a JSON array of all sections and exit
      --labels              prints a JSON-encoded array containing all user labels and exit
      --version             show program's version number and exit

## Install

    python -m venv venv
    ./venv/Script/activate
    pip install -r requirements.txt