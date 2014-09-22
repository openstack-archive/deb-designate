#!/usr/bin/env python
# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
import socket
import binascii

# Bind to UDP 5355
sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_udp.bind(('', 5355))

# Receive a Packet
payload, addr = sock_udp.recvfrom(8192)

# Print the hex representation of the packet
print(binascii.b2a_hex(payload))

# The request just happens to be a kinda-ish valid response
sock_udp.sendto(payload, addr)
