..
    Copyright 2014 Hewlett-Packard Development Company, L.P.

    Author: Endre Karlson <endre.karlson@hp.com>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.


Secondary Zones
===============

The Designate v2 API introduced functionality that allows Designate to act as a
DNS slave, rather than a master for a zone. This is accomplished by completing
a zone transfer (AXFR) from a DNS server managed outside of Designate.

RecordSets / Records
--------------------

Changes to secondary zones are managed outside of Designate. Users must make
the changes they wish, and prompt a fresh zone transfer (AXFR) into Designate
to make those changes live on any DNS servers Designate manages.

Setup
-----

To add a secondary zone to Designate, there must be a DNS master for the zone,
to which Designate can act as a slave. For this guide, we assume that you have
already set this up.

The remaining Designate set up will be similar to a non-secondary zone setup.
You'll need a primary DNS server for Designate to manage and transfer secondary
zones to.

In our examples we'll use the following values:

*Name* - example.com.

*Masters* - 192.168.27.100


Setup - example NSD4
^^^^^^^^^^^^^^^^^^^^

Skip this section if you have a master already to use.


.. note::

    For this it is assumed that you are running on Ubuntu.

Install
^^^^^^^

For some reason there's a bug with the nsd package so it doesn't create the user that it needs for the installation. So we'll create that before installing the package.

.. code-block:: bash

    $ sudo apt-get install nsd


Configure
^^^^^^^^^

.. code-block:: bash

    $ sudo zcat /usr/share/doc/nsd/examples/nsd.conf.sample.gz >/tmp/nsd.conf
    $ sudo mv /tmp/nsd.conf /etc/nsd/nsd.conf

Add the following to /etc/nsd/nsd.conf

.. note::

    If you're wondering why we set notify to `192.168.27.100`:`5354` it's because MDNS runs on 5354 by default.

.. code-block:: bash

    $ sudo vi /etc/nsd/nsd.conf

Add the contents:

.. code-block:: yaml

    pattern:
        name: "mdns"
        zonefile: "%s.zone"
        notify: 192.168.27.100@5354 NOKEY
        provide-xfr: 192.168.27.100 NOKEY
        allow-axfr-fallback: yes

Add a zone file
^^^^^^^^^^^^^^^

Create a new *Zone* in NSD called *example.com.*

**/etc/nsd/example.com.zone**

.. code-block:: bash

    $ sudo vi /etc/nsd/example.com.zone

And add the contents:

::

    $TTL 1800 ;minimum ttl
    example.com.         IN      SOA     ns1.example.com. admin.example.net. (
                            2014111301      ;serial
                            3600            ;refresh
                            600             ;retry
                            180000          ;expire
                            600             ;negative ttl
                            )

                    TXT             "v=spf1 +a +mx ~all"
                    SPF             "v=spf1 +a +mx ~all"

                    NS              ns1.example.com.
                    NS              ns2.example.com.
                    NS              ns3.example.com.

                    MX      0       mail1.example.com.
                    MX      5       mail2.example.com.
                    MX      10      mail3.example.com.

                    A               10.0.0.1
                    A               10.0.0.2
                    A               10.0.0.3


    ns1             A               172.16.28.100
    ns2             A               172.16.28.101
    ns3             A               172.16.28.103

    mail1             A               10.0.10.1
    mail2             A               10.0.10.2
    mail3             A               10.0.10.3

    google          CNAME           google.com.


Restart NSD
^^^^^^^^^^^

.. code-block:: bash

    $ sudo service nsd restart

Check that it's working

.. code-block:: bash

    $ sudo nsd-control status

Activate the zone in NSD

.. code-block:: bash

    $ sudo nsd-control addzone example.com mdns

Creating the Zone
-----------------

When you create a domain in Designate there are two possible initial actions:

-   Domain is created but transfer fails if it's not available yet in master,
    then typically the initial transfer will be done once the master sends first
    NOTIFY.

-   Domain is created and transfers straight away.

In both cases the interaction between your master and Designate is handled by
the MDNS instance at the Designate side.


Definition of values:

-   *email* set to the value of the *managed_resource_email* option in the
    *central* section of the Designate configuration.

-   *transferred_at* is **null** and *version* is **1** since the zone has not
    transferred yet.

-   *serial* gets set automatically by the system initially and to the value of the master's serial post initial AXFR.


.. http:post:: /zones

    Creates a new zone.

    **Example request:**

    .. sourcecode:: http

        POST /v2/zones HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
            "name": "example.com.",
            "type": "SECONDARY",
            "masters": ["192.168.27.100"],
            "description": "This is a slave for example.com."
        }

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "id": "a86dba58-0043-4cc6-a1bb-69d5e86f3ca3",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "example.com.",
            "email": "email@example.io",
            "ttl": 3600,
            "serial": 1404757531,
            "status": "ACTIVE",
            "description": "This is a slave for example.com."
            "masters": ["192.168.27.100"],
            "type": "SECONDARY",
            "transferred_at": null,
            "version": 1,
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": null,
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3"
            }
        }


Get Zone
--------

.. http:get:: /zones/(uuid:id)

    Retrieves a secondary zone with the specified zone ID.

    **Example request:**

    .. sourcecode:: http

        GET /v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
            "id": "a86dba58-0043-4cc6-a1bb-69d5e86f3ca3",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "example.com.",
            "email": "email@example.io",
            "ttl": 3600,
            "serial": 1404757531,
            "status": "ACTIVE",
            "description": "This is a slave for example.com."
            "masters": ["192.168.27.100"],
            "type": "SECONDARY",
            "transferred_at": null,
            "version": 1,
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": null,
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3"
            }
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied


List Secondary Zones
--------------------

.. http:get:: /zones

    Lists all zones.

    **Example Request:**

    .. sourcecode:: http

        GET /v2/zones?type=SECONDARY HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
          "zones": [{
            "id": "a86dba58-0043-4cc6-a1bb-69d5e86f3ca3",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "example.com.",
            "email": "email@example.io",
            "ttl": 3600,
            "serial": 1404757531,
            "status": "ACTIVE",
            "description": "This is a slave for example.com.",
            "masters": ["192.168.27.100"],
            "type": "SECONDARY",
            "transferred_at": null,
            "version": 1,
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": null,
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3"
            }
          }, {
            "id": "a86dba58-0043-4cc6-a1bb-69d5e86f3ca4",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "bar.io.",
            "email": "email@example.io",
            "ttl": 3600,
            "serial": 10,
            "status": "ACTIVE",
            "description": "This is a slave for bar.io.",
            "masters": ["192.168.27.100"],
            "type": "SECONDARY",
            "transferred_at": "2014-07-07T18:25:35.275934",
            "version": 2,
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": null,
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3"
            }
          }],
          "links": {
            "self": "https://127.0.0.1:9001/v2/zones"
          }
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied

Update Zone
-----------

.. http:patch:: /zones/(uuid:id)

    Changes the specified attribute(s) for an existing zone.

    In the example below, we update the TTL to 3600.

    **Request:**

    .. sourcecode:: http

        PATCH /v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
            "masters": ["192.168.27.101"]
        }

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": "a86dba58-0043-4cc6-a1bb-69d5e86f3ca3",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "example.com.",
            "email": "email@example.io",
            "ttl": 3600,
            "serial": 1404757531,
            "status": "ACTIVE",
            "description": "This is a slave for example.com.",
            "masters": ["192.168.27.101"],
            "type": "SECONDARY",
            "transferred_at": null,
            "version": 2,
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": "2014-07-07T18:25:34.275934",
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3"
            }
        }

    :form description: UTF-8 text field.
    :form name: Valid zone name (Immutable).
    :form type: Enum PRIMARY/SECONDARY, default PRIMARY (Immutable).
    :form email: email address, required for type PRIMARY, NULL for SECONDARY.
    :form ttl: time-to-live numeric value in seconds, NULL for SECONDARY
    :form masters: Array of master nameservers. (NULL for type PRIMARY, required for SECONDARY otherwise zone will not be transferred before set.)

    :statuscode 200: Success
    :statuscode 202: Accepted
    :statuscode 401: Access Denied

Delete Zone
-----------

.. http:delete:: zones/(uuid:id)

    Deletes a zone with the specified zone ID.

    **Example Request:**

    .. sourcecode:: http

        DELETE /v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

    **Example Response:**

    .. sourcecode:: http

        HTTP/1.1 204 No Content

    :statuscode 204: No content
