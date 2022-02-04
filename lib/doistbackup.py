import gzip
import json
import uuid
import logging
import todoist
from datetime import datetime

def state_default(obj):
	return obj.data

class DoistBackup:

	def __init__(self, filename, api_token):
		self.filename = filename
		self.api = todoist.TodoistAPI(api_token)

	def backup(self):
		bkgfile = f"{self.filename}-{datetime.now().strftime('%Y%m%d%H%M%S')}.bak.gz"
		self.write_file(bkgfile, self.sync())

	def restore(self):
		bkgfile = self.filename
		self.sync(self.read_file(bkgfile))

	def read_file(self, bkgfile):
		logging.info(f"read from {bkgfile}")
		with gzip.open(bkgfile , 'rb') as f:
			content = f.read()
		logging.debug(f"read {len(content)} bytes")
		return content

	def write_file(self, bkgfile, content):
		logging.info(f"write to {bkgfile}")
		with gzip.open(bkgfile, 'wb') as f:
			f.write(content)
		logging.debug(f"wrote {len(content)} bytes")

	def sync(self, content=None):
		self.api.reset_state()
		if content is None:
			resp = self.api.sync()
			return bytes(json.dumps(resp), 'utf8')
		else:
			self.api._update_state(json.loads(content.decode('utf8')))
			self.api._write_cache()
			resp = self.api.sync()
			# print(bytes(json.dumps(resp), 'utf8'))
			logging.debug(resp)
			commands = []
			for i in resp.labels:
				commands.append(self.command("label_add", i.id, self.command_args_label(i)))
			for i in resp.projects:
				commands.append(self.command("project_add", i.id, self.command_args_project(i)))
			for i in resp.sections:
				commands.append(self.command("section_add", i.id, self.command_args_section(i)))
			for i in resp.items:
				if i.is_deleted:
					commands.append(self.command("item_add", i.id, self.command_args_item(i)))

			raise NotImplementedError("Not implemented yet because sync doesn't update server")
			# https://todoist.com/help/articles/how-to-format-your-csv-file-so-you-can-import-it-into-todoist

	def command(self, type, id, args):
		return {
			"type": type,
			"uuid":  self.generate_uuid(),
			"temp_id": id,
			"args": args
		}

	def command_args_label(self, item):
		return {

		}

	def command_args_project(self, item):
		return {

		}

	def command_args_section(self, item):
		return {

		}

	def command_args_item(self, item):
		return {
			"content": item.content,
			"description": item.description,
			"due": item.due,
			"labels": item.labels,
			"parent_id": item.parent_id,
			"priority": item.priority,
			"project_id": item.project_id,
			"section_id": item.section_id,
		}

	def generate_uuid(self):
		return str(uuid.uuid4())
# ~@:-]