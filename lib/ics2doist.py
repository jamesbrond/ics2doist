import logging
import lib.utils as utils
from lib.rrule import RRule
from todoist_api_python.api import TodoistAPI

class ICS2Doist:
	def __init__(self, **options):
		self.api = TodoistAPI(options['api_token'])

	def event_to_task(self, event, label_ids=None, project_id=None, section_id=None):
		task = {
			"description": event.description,
			"completed": False,
			"priority": 4
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
			task['due'] = {'date': event.begin.format('YYYY-MM-DD')}
		else:
			# TODO check timezone
			task['due'] = {'datetime': event.begin.isoformat()}

		return event.name, task

	def get_label(self, name):
		"""
		Returns a label JSON-encoded object
		"""
		labels = self.api.get_labels()
		for label in labels:
			if label.name == name:
				return label
		return None

	def label_ids(self, label_name):
		"""
		Get label id. If label doesn't exitst it will create it
		"""
		l = None
		if label_name:
			l = self.get_label(label_name)
			if l is None:
				logging.debug(f"create new label {label_name}")
				l = self.api.add_label( {"name": label_name})
		if l != None:
			l = [l.id]
		return l

	def project_id(self, project_name):
		if project_name:
			return utils.find_needle_in_haystack([project_name], self.api.get_projects())
		return None

	def section_id(self, section_name):
		if section_name:
			return utils.find_needle_in_haystack([section_name], self.api.get_sections())
		return None

# ~@:-]