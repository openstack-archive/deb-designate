# Copyright 2016 Rackspace Inc.
#
# Author: Eric Larson <eric.larson@rackspace.com>
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
import time

from concurrent import futures
from oslo_log import log as logging
from oslo_config import cfg

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def default_executor():
    thread_count = 5
    try:
        thread_count = CONF['service:worker'].threads
    except Exception:
        pass

    return futures.ThreadPoolExecutor(thread_count)


class Executor(object):
    """
    Object to facilitate the running of a task, or a set of tasks on an
    executor that can map multiple tasks across a configurable number of
    threads
    """
    def __init__(self, executor=None):
        self._executor = executor or default_executor()

    @staticmethod
    def do(task):
        return task()

    def task_name(self, task):
        if hasattr(task, 'task_name'):
            return str(task.task_name)
        if hasattr(task, 'func_name'):
            return str(task.func_name)
        return 'UnnamedTask'

    def run(self, tasks):
        """
        Run task or set of tasks
        :param tasks: the task or tasks you want to execute in the
                      executor's pool

        :return: The results of the tasks (list)

        If a single task is pass
        """
        self.start_time = time.time()

        if callable(tasks):
            tasks = [tasks]
        results = [r for r in self._executor.map(self.do, tasks)]

        self.end_time = time.time()
        self.task_time = self.end_time - self.start_time

        task_names = [self.task_name(t) for t in tasks]
        LOG.debug("Finished Tasks %(tasks)s in %(time)fs",
                {'tasks': task_names, 'time': self.task_time})

        return results
