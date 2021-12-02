import sys
import logging
import argparse
import lib.utils as utils
import lib.key_ring as keyring
from yaml import load
try:
  from yaml import CLoader as Loader
except ImportError:
  from yaml import Loader
from todoist_api_python.api import TodoistAPI

def parse_cmd_line():
	parser = argparse.ArgumentParser(prog="doistemplate.py", usage='%(prog)s [options]', description='Create a new task from a template')

	parser.add_argument(
		'template',
		type=argparse.FileType('r'))

	parser.add_argument('--version',
		action='version',
		version='%(prog)s 1.0.0')

	return parser.parse_args()

class DoistTemplate:
	"""
	Import YAML template file into Todoist application
	"""
	def __init__(self, api_token):
		self.api = TodoistAPI(api_token)
		self.projects = self.api.get_projects()
		self.sections = self.api.get_sections()
		self.labels = self.api.get_labels()

	def _parse(self, obj, list_keys):
		item = {}
		for k in list_keys:
			if k in obj:
				item[k] = obj[k]
		return item

	def _project(self, name, outer):
		inner = outer[name]
		project_id = utils.find_needle_in_haystack([name], self.projects)
		if project_id is None:
			prj = self._parse(inner, ["color", "favorite"])
			prj["name"] = name
			project = self.api.add_project(**prj)
			self.projects.append(project)
			project_id = project.id

		print(f"Project: {name} ({project_id})")

		if "sections" in inner:
			for section in inner["sections"]:
				self._section(project_id, section)
		if "tasks" in inner:
			for task in inner["tasks"]:
				self._task(project_id=project_id, section_id=None, parent_id=None, task=task)

	def _section(self, project_id, section):
		section_id = utils.find_needle_in_haystack([section["name"], project_id], self.sections, ["name", "project_id"])
		if section_id is None:
			sec = {
				"name": section["name"],
				"project_id": project_id
			}
			section_object = self.api.add_section(**sec)
			self.sections.append(section_object)
			section_id = section_object.id

		print(f"Section: {section['name']} ({section_id})")

		if "tasks" in section:
			for task in section["tasks"]:
				self._task(project_id=None, section_id=section_id, parent_id=None, task=task)

	def _task(self, project_id, section_id, parent_id, task):
		tsk = self._parse(task, ["content", "description", "completed", "priority", "due_string"])

		if section_id is not None:
			tsk["section_id"] = section_id
		elif project_id is not None:
			tsk["project_id"] = project_id
		elif parent_id is not None:
			tsk["parent_id"] = parent_id

		if "labels" in task:
			label_ids = []
			for label in task["labels"]:
				label_ids.append(self._label(label))
			tsk["label_ids"] = label_ids
		t = self.api.add_task(**tsk)
		print(f"Task: {t.content} ({t.id})")

		if "tasks" in task:
			for subtask in task["tasks"]:
				self._task(project_id=None, section_id=None, parent_id=t.id, task=subtask)
		return t

	def _label(self, name):
		label_id = utils.find_needle_in_haystack([name], self.labels)
		if label_id is None:
			label = self.api.add_label(name=name)
			label_id = label["id"]
			self.labels.append(label)
		return label_id

	def parse(self, template):
		if not template:
			return
		tpl = list(template)
		self._project(tpl[0], template)

def main():
	service_id = "JBROND_ICS2DOIST"
	args = parse_cmd_line()

	try:
		api_token = keyring.get_api_token(service_id)
		while not api_token:
			logging.warning(f"Todoist API token not found for {service_id} application.")
			keyring.setup(service_id)
			api_token = keyring.get_api_token(service_id)

		with args.template as file:
			template = load(file, Loader=Loader)
		tmpl = DoistTemplate(api_token)
		tmpl.parse(template)

		return 0
	except Exception as e:
		logging.error(e, exc_info=True)
		return 1

if __name__ == "__main__":
	sys.exit(main())