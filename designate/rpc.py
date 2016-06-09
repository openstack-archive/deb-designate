# Copyright 2013 Red Hat, Inc.
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

__all__ = [
    'init',
    'cleanup',
    'set_defaults',
    'add_extra_exmods',
    'clear_extra_exmods',
    'get_allowed_exmods',
    'RequestContextSerializer',
    'get_client',
    'get_server',
    'get_notifier',
    'TRANSPORT_ALIASES',
]

import inspect

from oslo_config import cfg
import oslo_messaging as messaging
from oslo_messaging import server as msg_server
from oslo_messaging.rpc import server as rpc_server
from oslo_messaging.rpc import dispatcher as rpc_dispatcher
from oslo_serialization import jsonutils

import designate.context
import designate.exceptions
from designate import objects


CONF = cfg.CONF
TRANSPORT = None
NOTIFIER = None


# NOTE: Additional entries to designate.exceptions goes here.
CONF.register_opts([
    cfg.ListOpt(
        'allowed_remote_exmods',
        default=[],
        help="Additional modules that contains allowed RPC exceptions.",
        deprecated_name='allowed_rpc_exception_modules')
])
ALLOWED_EXMODS = [
    designate.exceptions.__name__,
    'designate.backend.impl_dynect'
]
EXTRA_EXMODS = []


# NOTE(flaper87): The designate.openstack.common.rpc entries are
# for backwards compat with Havana rpc_backend configuration
# values. The designate.rpc entries are for compat with Folsom values.
TRANSPORT_ALIASES = {
    'designate.openstack.common.rpc.impl_kombu': 'rabbit',
    'designate.openstack.common.rpc.impl_qpid': 'qpid',
    'designate.openstack.common.rpc.impl_zmq': 'zmq',
    'designate.rpc.impl_kombu': 'rabbit',
    'designate.rpc.impl_qpid': 'qpid',
    'designate.rpc.impl_zmq': 'zmq',
}


def init(conf):
    global TRANSPORT, NOTIFIER
    exmods = get_allowed_exmods()
    TRANSPORT = messaging.get_transport(conf,
                                        allowed_remote_exmods=exmods,
                                        aliases=TRANSPORT_ALIASES)

    serializer = RequestContextSerializer(JsonPayloadSerializer())
    NOTIFIER = messaging.Notifier(TRANSPORT, serializer=serializer)


def initialized():
    return None not in [TRANSPORT, NOTIFIER]


def cleanup():
    global TRANSPORT, NOTIFIER
    assert TRANSPORT is not None
    assert NOTIFIER is not None
    TRANSPORT.cleanup()
    TRANSPORT = NOTIFIER = None


def set_defaults(control_exchange):
    messaging.set_transport_defaults(control_exchange)


def add_extra_exmods(*args):
    EXTRA_EXMODS.extend(args)


def clear_extra_exmods():
    del EXTRA_EXMODS[:]


def get_allowed_exmods():
    return ALLOWED_EXMODS + EXTRA_EXMODS + CONF.allowed_remote_exmods


class JsonPayloadSerializer(messaging.NoOpSerializer):
    @staticmethod
    def serialize_entity(context, entity):
        return jsonutils.to_primitive(entity, convert_instances=True)


class DesignateObjectSerializer(messaging.NoOpSerializer):
    def _process_iterable(self, context, action_fn, values):
        """Process an iterable, taking an action on each value.
        :param:context: Request context
        :param:action_fn: Action to take on each item in values
        :param:values: Iterable container of things to take action on
        :returns: A new container of the same type (except set) with
        items from values having had action applied.
        """
        iterable = values.__class__
        if iterable == set:
            # NOTE: A set can't have an unhashable value inside, such as
            # a dict. Convert sets to tuples, which is fine, since we can't
            # send them over RPC anyway.
            iterable = tuple
        return iterable([action_fn(context, value) for value in values])

    def serialize_entity(self, context, entity):
        if isinstance(entity, (tuple, list, set)):
            entity = self._process_iterable(context, self.serialize_entity,
                                            entity)
        elif hasattr(entity, 'to_primitive') and callable(entity.to_primitive):
            entity = entity.to_primitive()

        return jsonutils.to_primitive(entity, convert_instances=True)

    def deserialize_entity(self, context, entity):
        if isinstance(entity, dict) and 'designate_object.name' in entity:
            entity = objects.DesignateObject.from_primitive(entity)
        elif isinstance(entity, (tuple, list, set)):
            entity = self._process_iterable(context, self.deserialize_entity,
                                            entity)
        return entity


class RequestContextSerializer(messaging.Serializer):

    def __init__(self, base):
        self._base = base

    def serialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.serialize_entity(context, entity)

    def deserialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.deserialize_entity(context, entity)

    def serialize_context(self, context):
        return context.to_dict()

    def deserialize_context(self, context):
        return designate.context.DesignateContext.from_dict(context)


class RPCDispatcher(rpc_dispatcher.RPCDispatcher):
    def _dispatch(self, *args, **kwds):
        # TODO(kiall): Remove when oslo.messaging 5 is the min in requirements
        try:
            return super(RPCDispatcher, self)._dispatch(*args, **kwds)
        except Exception as e:
            if getattr(e, 'expected', False):
                raise rpc_dispatcher.ExpectedException()
            else:
                raise

    def dispatch(self, *args, **kwds):
        try:
            return super(RPCDispatcher, self).dispatch(*args, **kwds)
        except Exception as e:
            if getattr(e, 'expected', False):
                raise rpc_dispatcher.ExpectedException()
            else:
                raise


def get_transport_url(url_str=None):
    return messaging.TransportURL.parse(CONF, url_str, TRANSPORT_ALIASES)


def get_client(target, version_cap=None, serializer=None):
    assert TRANSPORT is not None
    if serializer is None:
        serializer = DesignateObjectSerializer()
    serializer = RequestContextSerializer(serializer)
    return messaging.RPCClient(TRANSPORT,
                               target,
                               version_cap=version_cap,
                               serializer=serializer)


def get_server(target, endpoints, serializer=None):
    assert TRANSPORT is not None
    if serializer is None:
        serializer = DesignateObjectSerializer()
    serializer = RequestContextSerializer(serializer)

    # TODO(kiall): Remove when oslo.messaging 5 is the min in requirements
    argspec = inspect.getargspec(rpc_dispatcher.RPCDispatcher.__init__)
    if 'target' in argspec.args:
        # We're on oslo.messaging < 5
        dispatcher = RPCDispatcher(target, endpoints, serializer)

        return msg_server.MessageHandlingServer(
            TRANSPORT, dispatcher, 'eventlet')

    else:
        # We're on oslo.messaging >= 5
        dispatcher = RPCDispatcher(endpoints, serializer)

        return rpc_server.RPCServer(
            TRANSPORT, target, dispatcher, 'eventlet')


def get_listener(targets, endpoints, serializer=None):
    assert TRANSPORT is not None
    if serializer is None:
        serializer = JsonPayloadSerializer()
    return messaging.get_notification_listener(TRANSPORT,
                                               targets,
                                               endpoints,
                                               executor='eventlet',
                                               serializer=serializer)


def get_notifier(service=None, host=None, publisher_id=None):
    assert NOTIFIER is not None
    if not publisher_id:
        publisher_id = "%s.%s" % (service, host or CONF.host)
    return NOTIFIER.prepare(publisher_id=publisher_id)
