# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

from sqlalchemy.schema import MetaData


meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    if migrate_engine.name != "mysql":
        return

    sql = """SET foreign_key_checks = 0;
    ALTER TABLE service_statuses CONVERT TO CHARACTER SET utf8;
    SET foreign_key_checks = 1;
    ALTER DATABASE %s DEFAULT CHARACTER SET utf8;
    """ % migrate_engine.url.database
    migrate_engine.execute(sql)
