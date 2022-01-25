import gzip
import json
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
		if content is None:
			return bytes(json.dumps(self.api.state, default=state_default), 'utf8')
		else:
			self.api.reset_state()
			self.api._update_state(json.loads(content.decode('utf8')))
			self.api._write_cache()
			raise NotImplementedError("Not implemented yet because sync doesn't update server")
			# resp = self.api.sync()
			# print(bytes(json.dumps(resp), 'utf8'))
			# logging.debug(resp)

# ~@:-]