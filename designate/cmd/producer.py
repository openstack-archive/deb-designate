# Copyright 2016 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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

from oslo_config import cfg
from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr

from designate.i18n import _LE
from designate import hookpoints
from designate import service
from designate import utils
from designate import version
from designate.producer import service as producer_service


LOG = logging.getLogger(__name__)
CONF = cfg.CONF
CONF.import_opt('workers', 'designate.producer', group='service:producer')
CONF.import_opt('threads', 'designate.producer', group='service:producer')


def main():
    utils.read_config('designate', sys.argv)
    logging.setup(CONF, 'designate')
    gmr.TextGuruMeditation.setup_autorun(version)

    # NOTE(timsim): This is to ensure people don't start the wrong
    #               services when the worker model is enabled.
    if not cfg.CONF['service:worker'].enabled:
        LOG.error(_LE('You do not have designate-worker enabled, starting '
                      'designate-producer is not allowed. '
                      'You need to start designate-zone-manager instead.'))
        sys.exit(1)

    hookpoints.log_hook_setup()

    server = producer_service.Service(threads=CONF['service:producer'].threads)
    service.serve(server, workers=CONF['service:producer'].workers)
    service.wait()
