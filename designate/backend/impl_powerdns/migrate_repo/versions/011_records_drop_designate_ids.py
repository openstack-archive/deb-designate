# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
import sys

from oslo_log import log as logging
from sqlalchemy import MetaData, Table

from designate.i18n import _LW
from designate.i18n import _LE


LOG = logging.getLogger(__name__)
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    LOG.warning(_LW('It will not be possible to downgrade from schema #11'))

    records_table = Table('records', meta, autoload=True)
    records_table.c.designate_id.drop()
    records_table.c.designate_recordset_id.drop()


def downgrade(migrate_engine):
    LOG.error(_LE('It is not possible to downgrade from schema #11'))
    sys.exit(1)
