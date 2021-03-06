import os
import json
import yaml
import logging
import lib.utils as utils
from typing import Any, IO
from todoist_api_python.api import TodoistAPI

class Loader(yaml.SafeLoader):
	"""YAML Loader with `!include` constructor."""

	def __init__(self, stream: IO) -> None:
		"""Initialise Loader."""

		try:
			self._root = os.path.split(stream.name)[0]
		except AttributeError:
			self._root = os.path.curdir
		super().__init__(stream)

def construct_include(loader: Loader, node: yaml.Node) -> Any:
	"""Include file referenced at node."""

	filename = os.path.abspath(os.path.join(loader._root, loader.construct_scalar(node)))
	extension = os.path.splitext(filename)[1].lstrip('.')
	logging.debug(f"include {filename}")
	with open(filename, 'r', encoding="utf8") as f:
		if extension in ('yaml', 'yml'):
			return yaml.load(f, Loader)
		elif extension in ('json', ):
			return json.load(f)
		else:
			return ''.join(f.readlines())

yaml.add_constructor('!include', construct_include, Loader)

class DoistTemplate:
	"""
	Import YAML template file into Todoist application
	"""

	def __init__(self, api_token):
		self.api = TodoistAPI(api_token)
		self.projects = self.api.get_projects()
		self.sections = self.api.get_sections()
		self.labels = self.api.get_labels()

	def parse(self, file, placelholders):
		"""
		Parse the template YAML file using placeholdes dictionary
		"""

		if file is None:
			return
		template = yaml.load(file, Loader=Loader)
		for t in template:
			if isinstance(t, str):
				self._project(t, template[t], placelholders)
			else:
				p = list(t)[0]
				self._project(p, t[p], placelholders)

	def _parse_items(self, obj, list_keys, placeholders=None):
		item = {}
		for k in list_keys:
			if k in obj:
				item[k] = self._replace(obj[k], placeholders)
		return item

	def _replace(self, value, placeholders):
		if value is not None and isinstance(value, str) and placeholders is not None:
			return value.format(**placeholders)
		return value

	def _project(self, name, inner, placeholders):
		project_id = utils.find_needle_in_haystack([name], self.projects)
		if project_id is None:
			prj = self._parse_items(inner, ["color", "favorite"])
			prj["name"] = self._replace(name, placeholders)
			logging.debug(f"create project {prj}")
			project = self.api.add_project(**prj)
			self.projects.append(project)
			project_id = project.id

		logging.info(f"Project: {name} ({project_id})")

		sections = list(inner)
		for section in sections:
			if section == "tasks":
				for task in inner[section]:
					self._task(project_id=project_id, section_id=None, parent_id=None, task=task, placeholders=placeholders)
			else:
				logging.debug(f"{section}: {inner[section]}")
				self._section(project_id, section, inner[section], placeholders)

	def _section(self, project_id, name, content, placeholders):
		section_id = utils.find_needle_in_haystack([name, project_id], self.sections, ["name", "project_id"])
		if section_id is None:
			sec = {
				"name": self._replace(name, placeholders),
				"project_id": project_id
			}
			logging.debug(f"create section {sec}")
			section_object = self.api.add_section(**sec)
			self.sections.append(section_object)
			section_id = section_object.id

		logging.info(f"Section: {name} ({section_id})")

		if "tasks" in content:
			for task in content["tasks"]:
				self._task(project_id=None, section_id=section_id, parent_id=None, task=task, placeholders=placeholders)

	def _task(self, project_id, section_id, parent_id, task, placeholders):
		tsk = self._parse_items(task, ["content", "description", "completed", "priority", "due_string"], placeholders)

		if section_id is not None:
			tsk["section_id"] = section_id
		elif project_id is not None:
			tsk["project_id"] = project_id
		elif parent_id is not None:
			tsk["parent_id"] = parent_id

		if "labels" in task:
			label_ids = []
			for label in task["labels"]:
				label_ids.append(self._label(label, placeholders))
			tsk["label_ids"] = label_ids
		logging.debug(f"create task {tsk}")
		t = self.api.add_task(**tsk)
		logging.info(f"Task: {t.content} ({t.id})")

		if "tasks" in task:
			for subtask in task["tasks"]:
				self._task(project_id=None, section_id=None, parent_id=t.id, task=subtask, placeholders=placeholders)
		return t

	def _label(self, name, placeholders):
		n = self._replace(name, placeholders)
		label_id = utils.find_needle_in_haystack([n], self.labels)
		if label_id is None:
			logging.debug(f"create label {n}")
			label = self.api.add_label(name=n)
			label_id = label.id
			self.labels.append(label)
		return label_id

# ~@:-]