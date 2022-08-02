"""DoistBackup class"""

import logging
import gzip
import json
import uuid
from datetime import datetime
import requests


class DoistBackup:
    """Bakcup and restore of todoist"""

    def __init__(self, filename, api_token):
        self.filename = filename
        self.api_token = api_token
        self.temp_ids = {}

    def backup(self):
        """Backups all from todoist"""
        bkgfile = f"{self.filename}-{datetime.now().strftime('%Y%m%d%H%M%S')}.bak.gz"
        self._write_file(bkgfile, self._sync())

    def restore(self):
        """Restores only projects, sections, labels and tasks"""
        content = self._read_file(self.filename)
        data = json.loads(content)
        commands = []
        for item in data.get("labels"):
            commands.append(self._command_label(item))
        for item in data.get("projects"):
            commands.append(self._command_project(item))
        for item in data.get("sections"):
            commands.append(self._command_section(item))
        for item in data.get("items"):
            commands.append(self._command_item(item))
        self._sync(json.dumps(commands))

    def _command_label(self, obj):
        tmp_uuid = self._uuid()
        self.temp_ids[obj.get("id")] = tmp_uuid
        cmd = {
            "type": "label_add",
            "temp_id": tmp_uuid,
            "uuid": self._uuid(),
            "args": {
                "name": obj.get("name"),
                "color": obj.get("color"),
                "item_order": obj.get("item_order"),
                "is_favorite": obj.get("is_favorite")
            }
        }
        return cmd

    def _command_project(self, obj):
        tmp_uuid = self._uuid()
        self.temp_ids[obj.get("id")] = tmp_uuid
        cmd = {
            "type": "project_add",
            "temp_id": tmp_uuid,
            "uuid": self._uuid(),
            "args": {
                "name": obj.get("name"),
                "color": obj.get("color"),
                "parent_id": self.temp_ids.get(obj.get("parent_id")),
                "child_order": obj.get("child_order"),
                "is_favorite": obj.get("is_favorite")
            }
        }
        return cmd

    def _command_section(self, obj):
        tmp_uuid = self._uuid()
        self.temp_ids[obj.get("id")] = tmp_uuid
        cmd = {
            "type": "section_add",
            "temp_id": tmp_uuid,
            "uuid": self._uuid(),
            "args": {
                "name": obj.get("name"),
                "project_id": self.temp_ids.get(obj.get("project_id")),
                "section_order": obj.get("section_order")
            }
        }
        return cmd

    def _command_item(self, obj):
        tmp_uuid = self._uuid()
        self.temp_ids[obj.get("id")] = tmp_uuid
        cmd = {
            "type": "item_add",
            "temp_id": tmp_uuid,
            "uuid": self._uuid(),
            "args": {
                "content": obj.get("content"),
                "description": obj.get("description"),
                "project_id": self.temp_ids.get(obj.get("project_id")),
                "due": obj.get("due"),
                "priority": obj.get("priority"),
                "parent_id": self.temp_ids.get(obj.get("parent_id")),
                "child_order": obj.get("child_order"),
                "section_id": self.temp_ids.get(obj.get("section_id")),
                "day_order": obj.get("day_order"),
                "collapsed": obj.get("collapsed"),
                "labels": []
            }
        }
        for label in obj.get("labels"):
            cmd["args"]["labels"].append(self.temp_ids.get(label))

        return cmd

    def _read_file(self, bkgfile):
        logging.info("read from %s", bkgfile)
        with gzip.open(bkgfile , 'rb') as f:
            content = f.read()
        logging.debug("read %d bytes", len(content))
        return  str(content, "UTF-8")

    def _write_file(self, bkgfile, content):
        logging.info("write to %s", bkgfile)
        with gzip.open(bkgfile, 'wb') as f:
            f.write(content)
        logging.debug("wrote %d bytes", len(content))

    def _sync(self, commands=None):
        if not commands:
            params = {
                "sync_token": "*",
                "resource_types": '["all"]'
            }
        else:
            params = {"commands": commands}

        response = requests.get("https://api.todoist.com/sync/v8/sync",
            params=params,
            headers={"Authorization": f"Bearer {self.api_token}"}
        )
        if response.status_code == 200:
            print(response.content)
            return response.content
        return ""

    def _uuid(self):
        return str(uuid.uuid4())

# ~@:-]
