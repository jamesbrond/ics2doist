import gzip
import logging

class DoistRestore:
	def __init__(self, filename, api_token):
		self.token = api_token
		self.restore_file = filename

	def restore(self):
		self.sync_back(self.read_file())

	def read_file(self):
		logging.info(f"read file {self.restore_file}")
		with gzip.open(self.restore_file , 'rb') as f:
			content = f.read()
		logging.debug(f"readed {len(content)} bytes")
		return content

	def sync_back(self, content):
		raise NotImplementedError("Not implemented yet")
# ~@:-]