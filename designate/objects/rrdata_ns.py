# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from designate.objects.record import Record
from designate.objects.record import RecordList


class NS(Record):
    """
    NS Resource Record Type
    Defined in: RFC1035
    """
    FIELDS = {
        'nsdname': {
            'schema': {
                'type': 'string',
                'format': 'domainname',
                'maxLength': 255,
            },
            'required': True
        }
    }

    @classmethod
    def get_recordset_schema_changes(cls):
        return {
            'name': {
                'schema': {
                    'format': 'ns-hostname',
                },
            },
        }

    def _to_string(self):
        return self.nsdname

    def _from_string(self, value):
        self.nsdname = value

    # The record type is defined in the RFC. This will be used when the record
    # is sent by mini-dns.
    RECORD_TYPE = 2


class NSList(RecordList):

    LIST_ITEM_TYPE = NS
