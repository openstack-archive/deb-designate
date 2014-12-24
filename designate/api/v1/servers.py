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
import flask

from designate.openstack.common import log as logging
from designate import schema
from designate.central import rpcapi as central_rpcapi
from designate.objects import Server


LOG = logging.getLogger(__name__)
blueprint = flask.Blueprint('servers', __name__)
server_schema = schema.Schema('v1', 'server')
servers_schema = schema.Schema('v1', 'servers')


@blueprint.route('/schemas/server', methods=['GET'])
def get_server_schema():
    return flask.jsonify(server_schema.raw)


@blueprint.route('/schemas/servers', methods=['GET'])
def get_servers_schema():
    return flask.jsonify(servers_schema.raw)


@blueprint.route('/servers', methods=['POST'])
def create_server():
    context = flask.request.environ.get('context')
    values = flask.request.json

    server_schema.validate(values)
    central_api = central_rpcapi.CentralAPI.get_instance()
    server = central_api.create_server(context, server=Server(**values))

    response = flask.jsonify(server_schema.filter(server))
    response.status_int = 201
    response.location = flask.url_for('.get_server', server_id=server['id'])

    return response


@blueprint.route('/servers', methods=['GET'])
def get_servers():
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()
    servers = central_api.find_servers(context)

    return flask.jsonify(servers_schema.filter({'servers': servers}))


@blueprint.route('/servers/<uuid:server_id>', methods=['GET'])
def get_server(server_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()
    server = central_api.get_server(context, server_id)

    return flask.jsonify(server_schema.filter(server))


@blueprint.route('/servers/<uuid:server_id>', methods=['PUT'])
def update_server(server_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    central_api = central_rpcapi.CentralAPI.get_instance()

    # Fetch the existing resource
    server = central_api.get_server(context, server_id)

    # Prepare a dict of fields for validation
    server_data = server_schema.filter(server)
    server_data.update(values)

    # Validate the new set of data
    server_schema.validate(server_data)

    # Update and persist the resource
    server.update(values)
    server = central_api.update_server(context, server)

    return flask.jsonify(server_schema.filter(server))


@blueprint.route('/servers/<uuid:server_id>', methods=['DELETE'])
def delete_server(server_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()
    central_api.delete_server(context, server_id)

    return flask.Response(status=200)
