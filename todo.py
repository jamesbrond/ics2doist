import sys
import json
import uuid
import logging
import requests
from ics import Calendar

API_TOKEN="fe520c257103a0239972e112e1f766d23869389c"

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

def add_task(title, due, label_ids):
	print(f"Add task {title} on {due}...", end="")
	requests.post(
		"https://api.todoist.com/rest/v1/tasks",
		data=json.dumps({
			"content": title,
			"due_date": due,
			"label_ids": label_ids
		}),
		headers={
			"Content-Type": "application/json",
			"X-Request-Id": str(uuid.uuid4()),
			"Authorization": f"Bearer {API_TOKEN}"
		}).json()
	print("\tdone")

def get_all_projects():
	return requests.get(
		"https://api.todoist.com/rest/v1/projects",
		headers={
			"Authorization": f"Bearer {API_TOKEN}"
		}).json()

def get_all_sections():
	return requests.get(
		"https://api.todoist.com/rest/v1/sections",
		headers={
			"Authorization": f"Bearer {API_TOKEN}"
		}).json()

def get_all_labels():
	return requests.get(
		"https://api.todoist.com/rest/v1/labels",
		headers={
			"Authorization": f"Bearer {API_TOKEN}"
		}).json()

def main():
	try:
		if len(sys.argv) < 2:
			print("\tPROJECTS:")
			print(get_all_projects())
			print("\tSECTIONS:")
			print(get_all_sections())
			print("\tLABELS:")
			print(get_all_labels())
		else:
			for event in read_calendar(sys.argv[1]):
				add_task(event['title'], event['date'], [2158774081])
		return 0
	except Exception as e:
		logging.error(e, exc_info=True)
		return 1

if __name__ == "__main__":
	sys.exit(main())

# ~@:-]