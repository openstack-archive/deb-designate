# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from sqlalchemy import MetaData, Table, Enum

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS',
                    'PTR']

    records_table = Table('records', meta, autoload=True)
    records_table.c.type.alter(type=Enum(name='record_types', *RECORD_TYPES))


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'NS', 'PTR']

    records_table = Table('records', meta, autoload=True)

    # Delete all SPF records
    records_table.filter_by(type='SPF').delete()

    # Remove SPF from the ENUM
    records_table.c.type.alter(type=Enum(name='record_types', *RECORD_TYPES))
