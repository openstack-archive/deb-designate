"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from functionaltests.api.v2.models.zone_export_model import ZoneExportModel
from functionaltests.api.v2.models.zone_export_model import ZoneExportListModel
from functionaltests.common import utils
from functionaltests.common.client import ClientMixin
from functionaltests.common.models import ZoneFile


class ZoneExportClient(ClientMixin):

    def zone_exports_uri(self, filters=None):
        return self.create_uri("/zones/tasks/exports", filters=filters)

    def create_zone_export_uri(self, zone_id, filters=None):
        return self.create_uri(
            "/zones/{0}/tasks/export".format(zone_id),
            filters=filters,
        )

    def zone_export_uri(self, id):
        return "{0}/{1}".format(self.zone_exports_uri(), id)

    def list_zone_exports(self, filters=None, **kwargs):
        resp, body = self.client.get(
            self.zone_exports_uri(filters), **kwargs)
        return self.deserialize(resp, body, ZoneExportListModel)

    def get_zone_export(self, id, **kwargs):
        resp, body = self.client.get(self.zone_export_uri(id))
        return self.deserialize(resp, body, ZoneExportModel)

    def get_exported_zone(self, id, **kwargs):
        uri = "{0}/export".format(self.zone_export_uri(id))
        headers = {'Accept': 'text/dns'}
        resp, body = self.client.get(uri, headers=headers)
        if resp.status < 400:
            return resp, ZoneFile.from_text(body)
        return resp, body

    def post_zone_export(self, zone_id, **kwargs):
        uri = self.create_zone_export_uri(zone_id)
        resp, body = self.client.post(uri, body='', **kwargs)
        return self.deserialize(resp, body, ZoneExportModel)

    def delete_zone_export(self, id, **kwargs):
        resp, body = self.client.delete(self.zone_export_uri(id), **kwargs)
        return resp, body

    def wait_for_zone_export(self, zone_export_id):
        utils.wait_for_condition(
            lambda: self.is_zone_export_active(zone_export_id))

    def is_zone_export_active(self, zone_export_id):
        resp, model = self.get_zone_export(zone_export_id)
        # don't have assertEqual but still want to fail fast
        assert resp.status == 200
        if model.status == 'COMPLETE':
            return True
        elif model.status == 'ERROR':
            raise Exception("Saw ERROR status")
        return False
