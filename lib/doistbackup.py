import gzip
import logging
import requests
from datetime import datetime

TODOIST_SYNC_URL = 'https://api.todoist.com/sync/v8/sync'

class DoistBackup:

	def __init__(self, filename, api_token):
		self.token = api_token
		self.bkgfile = f"{filename}-{datetime.now().strftime('%Y%m%d%H%M%S')}.bak.gz"

	def backup(self):
		self.write_file(self.sync())

	def write_file(self, content):
		logging.info(f"write to {self.bkgfile}")
		with gzip.open(self.bkgfile, 'wb') as f:
			f.write(content)
		logging.debug(f"writed {len(content)} bytes")

	def sync(self):
		headers = {"Authorization": f"Bearer {self.token}"}
		params = {
			"sync_token": "*",
			"resource_types": '["all"]'
		}
		resp = requests.get(TODOIST_SYNC_URL, headers=headers, params=params)
		if resp.status_code == 200:
			return resp.content
		return ""

# ~@:-]