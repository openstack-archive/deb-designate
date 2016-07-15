.. _rest:

========================
 REST API Documentation
========================

Intro
=====

In the REST API examples, HTTP requests are defined as raw HTTP. For
example:

.. code-block:: http

   POST /v2/pools HTTP/1.1          # The HTTP Method, Path and HTTP Version
   Accept: application/json         # Headers
   Content-Type: application/json

   {                                # The rest is the body of request
        "name": "Example Pool",
        "ns_records": [
            {
              "hostname": "ns1.example.org.",
              "priority": 1
            }
        ]
   }

With this info we can make this request using the cURL_ tool. We'll
assume we are running Designate on `localhost`.

.. code-block:: bash

   curl -X POST -i \
        -H 'Accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{"name": "ns1.example.org."}' \
        http://localhost:9001/v1/servers

The `-i` flag is used to dump the response headers as well as the
response body.

The cURL tool is extremely robust. Please take a look at the `cURL
tutorial`_ for more info.

.. _cURL: http://curl.haxx.se/
.. _cURL tutorial: http://curl.haxx.se/docs/manual.html

HTTP Headers
============

These headers work for all APIs

* X-Designate-Edit-Managed-Records
    - Allows admins (or users with the right role) to modify managed records (records created by designate-sink / reverse floating ip API)
* X-Auth-All-Projects
    - Allows admins (or users with the right role) to view and edit zones / recordsets for all tenants
* X-Auth-Sudo-Tenant-ID / X-Auth-Sudo-Project-ID
    - Allows admins (or users with the right role) to impersonate another tenant specified by this header

API Versions
============

The API has 2 versions - V1 and V2.

.. note:: V1 has been deprecated since the Kilo release.

V1 API
------
    .. toctree::
       :maxdepth: 2
       :glob:

       rest/v1/servers
       rest/v1/domains
       rest/v1/records
       rest/v1/diagnostics
       rest/v1/quotas
       rest/v1/reports
       rest/v1/sync

V2 API
------

    The V2 API is documented on the OpenStack Developer `api site`_


Admin API
---------
    .. toctree::
       :maxdepth: 2
       :glob:

       rest/admin/quotas

.. _api site: http://developer.openstack.org/api-ref/dns/
