import sys
import json
import uuid
import keyring
import logging
import requests
from ics import Calendar

def setup(service_id):
	token = input("Please enter your API token: ")
	set_api_token(service_id, token)

def set_api_token(service_id, token):
	keyring.set_password(service_id, 'API_TOKEN', token)

def get_api_token(service_id):
	return keyring.get_password(service_id, 'API_TOKEN')

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

def add_task(api_token, title, due, label_ids):
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
			"Authorization": f"Bearer {api_token}"
		}).json()
	print("\tdone")

def get_all_projects(api_token):
	return requests.get(
		"https://api.todoist.com/rest/v1/projects",
		headers={
			"Authorization": f"Bearer {api_token}"
		}).json()

def get_all_sections(api_token):
	return requests.get(
		"https://api.todoist.com/rest/v1/sections",
		headers={
			"Authorization": f"Bearer {api_token}"
		}).json()

def get_all_labels(api_token):
	return requests.get(
		"https://api.todoist.com/rest/v1/labels",
		headers={
			"Authorization": f"Bearer {api_token}"
		}).json()

def main():
	service_id = 'JBROND_TODO'

	try:
		api_token = get_api_token(service_id)
		while not api_token:
			logging.warning(f"Todoist API token not find for {service_id} application.")
			setup(service_id)
			api_token = get_api_token(service_id)

		if len(sys.argv) < 2:
			print("\tPROJECTS:")
			print(get_all_projects(api_token))
			print("\tSECTIONS:")
			print(get_all_sections(api_token))
			print("\tLABELS:")
			print(get_all_labels(api_token))
		else:
			for event in read_calendar(sys.argv[1]):
				add_task(api_token, event['title'], event['date'], [2158774081])
		return 0
	except Exception as e:
		logging.error(e, exc_info=True)
		return 1

if __name__ == "__main__":
	sys.exit(main())

# ~@:-]