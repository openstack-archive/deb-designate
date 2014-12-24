#!/bin/bash

set -ex

pushd $BASE/new/devstack

DEVSTACK_GATE_DESIGNATE_DRIVER=${DEVSTACK_GATE_DESIGNATE_DRIVER:-powerdns}

export KEEP_LOCALRC=1
export ENABLED_SERVICES=designate,designate-api,designate-central,designate-sink,designate-mdns,designate-pool-manager

echo "DESIGNATE_SERVICE_PORT_DNS=5322" >> $BASE/new/devstack/localrc
echo "DESIGNATE_BACKEND_DRIVER=$DEVSTACK_GATE_DESIGNATE_DRIVER" >> $BASE/new/devstack/localrc

popd

# Run DevStack Gate
$BASE/new/devstack-gate/devstack-vm-gate.sh
