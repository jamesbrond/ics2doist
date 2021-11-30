import re
from lib.rrule import RRule
from todoist_api_python.api import TodoistAPI

class ICS2Doist:
	def __init__(self, **options):
		self.api = TodoistAPI(options['api_token'])

	def _strip_emoji(self, str):
		if str:
			emoji_pattern = re.compile("["
			u"\U0001F600-\U0001F64F"  # emoticons
			u"\U0001F300-\U0001F5FF"  # symbols & pictographs
			u"\U0001F680-\U0001F6FF"  # transport & map symbols
			u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
			"]+", flags=re.UNICODE)
			return emoji_pattern.sub(r'', str).strip()
		return None

	def _find_needle_in_haystack(self, needle, haystack):
		for straw in haystack:
			name = straw.name.lower()
			if self._strip_emoji(name) == needle:
				return straw.id
		return None

	def event_to_task(self, event, label_ids=None, project_id=None, section_id=None):
		task = {
			"description": event.description,
			"completed": False
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
			task['due_date'] = event.begin.format('YYYY-MM-DD')
		else:
			# TODO check timezone
			task['due_datetime'] = event.end.isoformat()

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
				l = self.api.add_label( {"name": label_name})
		if l != None:
			l = [l.id]
		return l

	def project_id(self, project_name):
		if project_name:
			return self._find_needle_in_haystack(project_name.lower(), self.api.get_projects())
		return None

	def section_id(self, section_name):
		if section_name:
			return self._find_needle_in_haystack(section_name.lower(), self.api.get_sections())
		return None