# Install and start **Designate** service in Devstack

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set +o xtrace

# Get backend configuration
# ----------------------------
if is_service_enabled designate && [[ -r $DESIGNATE_PLUGINS/backend-$DESIGNATE_BACKEND_DRIVER ]]; then
    # Load plugin
    source $DESIGNATE_PLUGINS/backend-$DESIGNATE_BACKEND_DRIVER
fi

# Helper Functions
# ----------------
function setup_colorized_logging_designate {
    local conf_file=$1
    local conf_section=$2
    local project_var=${3:-"project_name"}
    local user_var=${4:-"user_name"}

    setup_colorized_logging $conf_file $conf_section $project_var $user_var

    # Override the logging_context_format_string value chosen by
    # setup_colorized_logging.
    iniset $conf_file $conf_section logging_context_format_string "%(asctime)s.%(msecs)03d %(color)s%(levelname)s %(name)s [[01;36m%(request_id)s [00;36m%(user_identity)s%(color)s] [01;35m%(instance)s%(color)s%(message)s[00m"
}

# DevStack Plugin
# ---------------

# cleanup_designate - Remove residual data files, anything left over from previous
# runs that a clean run would need to clean up
function cleanup_designate {
    sudo rm -rf $DESIGNATE_STATE_PATH $DESIGNATE_AUTH_CACHE_DIR
    cleanup_designate_backend
}

# configure_designate - Set config files, create data dirs, etc
function configure_designate {
    [ ! -d $DESIGNATE_CONF_DIR ] && sudo mkdir -m 755 -p $DESIGNATE_CONF_DIR
    sudo chown $STACK_USER $DESIGNATE_CONF_DIR

    [ ! -d $DESIGNATE_LOG_DIR ] &&  sudo mkdir -m 755 -p $DESIGNATE_LOG_DIR
    sudo chown $STACK_USER $DESIGNATE_LOG_DIR

    # (Re)create ``designate.conf``
    rm -f $DESIGNATE_CONF

    # General Configuration
    iniset_rpc_backend designate $DESIGNATE_CONF DEFAULT

    iniset $DESIGNATE_CONF DEFAULT debug $ENABLE_DEBUG_LOG_LEVEL
    iniset $DESIGNATE_CONF DEFAULT verbose True
    iniset $DESIGNATE_CONF DEFAULT state_path $DESIGNATE_STATE_PATH
    iniset $DESIGNATE_CONF DEFAULT root-helper sudo designate-rootwrap $DESIGNATE_ROOTWRAP_CONF
    iniset $DESIGNATE_CONF storage:sqlalchemy connection `database_connection_url designate`

    # Coordination Configuration
    if [[ -n "$DESIGNATE_COORDINATION_URL" ]]; then
        iniset $DESIGNATE_CONF coordination backend_url $DESIGNATE_COORDINATION_URL
    fi

    # Install the policy file for the API server
    cp $DESIGNATE_DIR/etc/designate/policy.json $DESIGNATE_CONF_DIR/policy.json
    iniset $DESIGNATE_CONF DEFAULT policy_file $DESIGNATE_CONF_DIR/policy.json

    # Pool Manager Configuration
    iniset $DESIGNATE_CONF service:pool_manager pool_id $DESIGNATE_POOL_ID
    iniset $DESIGNATE_CONF service:pool_manager cache_driver $DESIGNATE_POOL_MANAGER_CACHE_DRIVER
    iniset $DESIGNATE_CONF service:pool_manager periodic_recovery_interval $DESIGNATE_PERIODIC_RECOVERY_INTERVAL
    iniset $DESIGNATE_CONF service:pool_manager periodic_sync_interval $DESIGNATE_PERIODIC_SYNC_INTERVAL

    # Pool Manager Cache
    if [ "$DESIGNATE_POOL_MANAGER_CACHE_DRIVER" == "sqlalchemy" ]; then
        iniset $DESIGNATE_CONF pool_manager_cache:sqlalchemy connection `database_connection_url designate_pool_manager`
    fi

    # Pool Options
    iniset $DESIGNATE_CONF pool:$DESIGNATE_POOL_ID targets $DESIGNATE_TARGET_ID

    # API Configuration
    sudo cp $DESIGNATE_DIR/etc/designate/api-paste.ini $DESIGNATE_APIPASTE_CONF
    iniset $DESIGNATE_CONF service:api enabled_extensions_v1 $DESIGNATE_ENABLED_EXTENSIONS_V1
    iniset $DESIGNATE_CONF service:api enabled_extensions_v2 $DESIGNATE_ENABLED_EXTENSIONS_V2
    iniset $DESIGNATE_CONF service:api enabled_extensions_admin $DESIGNATE_ENABLED_EXTENSIONS_ADMIN
    iniset $DESIGNATE_CONF service:api api_host $DESIGNATE_SERVICE_HOST
    iniset $DESIGNATE_CONF service:api api_base_uri $DESIGNATE_SERVICE_PROTOCOL://$DESIGNATE_SERVICE_HOST:$DESIGNATE_SERVICE_PORT/
    iniset $DESIGNATE_CONF service:api enable_api_v1 True
    iniset $DESIGNATE_CONF service:api enable_api_v2 True
    iniset $DESIGNATE_CONF service:api enable_api_admin True

    # mDNS Configuration
    iniset $DESIGNATE_CONF service:mdns host $DESIGNATE_SERVICE_HOST
    iniset $DESIGNATE_CONF service:mdns port $DESIGNATE_SERVICE_PORT_MDNS

    # Set up Notifications/Ceilometer Integration
    iniset $DESIGNATE_CONF DEFAULT notification_driver "$DESIGNATE_NOTIFICATION_DRIVER"
    iniset $DESIGNATE_CONF DEFAULT notification_topics "$DESIGNATE_NOTIFICATION_TOPICS"

    # Root Wrap
    sudo cp $DESIGNATE_DIR/etc/designate/rootwrap.conf.sample $DESIGNATE_ROOTWRAP_CONF
    iniset $DESIGNATE_ROOTWRAP_CONF DEFAULT filters_path $DESIGNATE_DIR/etc/designate/rootwrap.d root-helper

    # Oslo Concurrency
    iniset $DESIGNATE_CONF oslo_concurrency lock_path "$DESIGNATE_STATE_PATH"

    # Set up the rootwrap sudoers for designate
    local rootwrap_sudoer_cmd="$DESIGNATE_BIN_DIR/designate-rootwrap $DESIGNATE_ROOTWRAP_CONF *"
    local tempfile=`mktemp`
    echo "$STACK_USER ALL=(root) NOPASSWD: $rootwrap_sudoer_cmd" >$tempfile
    chmod 0440 $tempfile
    sudo chown root:root $tempfile
    sudo mv $tempfile /etc/sudoers.d/designate-rootwrap

    # TLS Proxy Configuration
    if is_service_enabled tls-proxy; then
        # Set the service port for a proxy to take the original
        iniset $DESIGNATE_CONF service:api api_port $DESIGNATE_SERVICE_PORT_INT
    else
        iniset $DESIGNATE_CONF service:api api_port $DESIGNATE_SERVICE_PORT
    fi

    # Setup the Keystone Integration
    if is_service_enabled key; then
        iniset $DESIGNATE_CONF service:api auth_strategy keystone
        configure_auth_token_middleware $DESIGNATE_CONF designate $DESIGNATE_AUTH_CACHE_DIR
    fi

    # Logging Configuration
    if [ "$SYSLOG" != "False" ]; then
        iniset $DESIGNATE_CONF DEFAULT use_syslog True
    fi

    # Format logging
    if [ "$LOG_COLOR" == "True" ] && [ "$SYSLOG" == "False" ]; then
        setup_colorized_logging_designate $DESIGNATE_CONF DEFAULT "tenant" "user"
    fi

    # Backend Plugin Configuation
    configure_designate_backend
}

# Configure the needed tempest options
function configure_designate_tempest() {
    if is_service_enabled tempest; then
        nameservers=$DESIGNATE_SERVICE_HOST:$DESIGNATE_SERVICE_PORT_DNS
        case $DESIGNATE_BACKEND_DRIVER in
            bind9|powerdns)
                nameservers="$DESIGNATE_SERVICE_HOST:$DESIGNATE_SERVICE_PORT_DNS"
                ;;
            akamai)
                nameservers="$DESIGNATE_AKAMAI_NAMESERVERS"
                ;;
            dynect)
                nameservers="$DESIGNATE_DYNECT_NAMESERVERS"
                ;;
        esac

        if [ ! -z "$DESIGNATE_NAMESERVERS" ]; then
            nameservers=$DESIGNATE_NAMESERVERS
        fi

        iniset $TEMPEST_CONFIG designate nameservers $nameservers
    fi
}

# create_designate_accounts - Set up common required designate accounts

# Tenant               User       Roles
# ------------------------------------------------------------------
# service              designate  admin        # if enabled
function create_designate_accounts {
    if is_service_enabled designate-api; then
        create_service_user "designate"

        if [[ "$KEYSTONE_CATALOG_BACKEND" = 'sql' ]]; then
            get_or_create_service "designate" "dns" "Designate DNS Service"
            get_or_create_endpoint "dns" \
                "$REGION_NAME" \
                "$DESIGNATE_SERVICE_PROTOCOL://$DESIGNATE_SERVICE_HOST:$DESIGNATE_SERVICE_PORT/" \
                "$DESIGNATE_SERVICE_PROTOCOL://$DESIGNATE_SERVICE_HOST:$DESIGNATE_SERVICE_PORT/" \
                "$DESIGNATE_SERVICE_PROTOCOL://$DESIGNATE_SERVICE_HOST:$DESIGNATE_SERVICE_PORT/"
        fi
    fi
}

# create_designate_ns_records - Create Pool NS Records
function create_designate_ns_records {
    # Allow Backends to install their own NS Records rather than the default
    if function_exists create_designate_ns_records_backend; then
        create_designate_ns_records_backend
    else
        designate server-create --name $DESIGNATE_DEFAULT_NS_RECORD
    fi
}

# init_designate - Initialize etc.
function init_designate {
    # Create cache dir
    sudo mkdir -p $DESIGNATE_AUTH_CACHE_DIR
    sudo chown $STACK_USER $DESIGNATE_AUTH_CACHE_DIR
    rm -f $DESIGNATE_AUTH_CACHE_DIR/*

    # Some Designate Backends require mdns be bound to port 53, make that
    # doable.
    sudo setcap 'cap_net_bind_service=+ep' $(readlink -f /usr/bin/python)

    # (Re)create designate database
    recreate_database designate utf8

    # Init and migrate designate database
    designate-manage database sync

    if [ "$DESIGNATE_POOL_MANAGER_CACHE_DRIVER" == "sqlalchemy" ]; then
        # (Re)create designate_pool_manager cache
        recreate_database designate_pool_manager utf8

        # Init and migrate designate pool-manager-cache
        designate-manage pool-manager-cache sync
    fi

    init_designate_backend
}

# install_designate - Collect source and prepare
function install_designate {
    if is_fedora; then
        # This package provides `dig`
        install_package bind-utils
    fi

    git_clone $DESIGNATE_REPO $DESIGNATE_DIR $DESIGNATE_BRANCH
    setup_develop $DESIGNATE_DIR

    install_designate_backend
}

# install_designateclient - Collect source and prepare
function install_designateclient {
    if use_library_from_git "python-designateclient"; then
        git_clone_by_name "python-designateclient"
        setup_dev_lib "python-designateclient"
    else
        pip_install_gr "python-designateclient"
    fi
}

# install_designatedashboard - Collect source and prepare
function install_designatedashboard {
    git_clone $DESIGNATEDASHBOARD_REPO $DESIGNATEDASHBOARD_DIR $DESIGNATEDASHBOARD_BRANCH
    setup_develop $DESIGNATEDASHBOARD_DIR
    ln -fs $DESIGNATEDASHBOARD_DIR/designatedashboard/enabled/_1710_project_dns_panel_group.py $HORIZON_DIR/openstack_dashboard/local/enabled/_1710_project_dns_panel_group.py
    ln -fs $DESIGNATEDASHBOARD_DIR/designatedashboard/enabled/_1720_project_dns_panel.py $HORIZON_DIR/openstack_dashboard/local/enabled/_1720_project_dns_panel.py
}

# start_designate - Start running processes, including screen
function start_designate {
    start_designate_backend

    run_process designate-central "$DESIGNATE_BIN_DIR/designate-central --config-file $DESIGNATE_CONF"
    run_process designate-api "$DESIGNATE_BIN_DIR/designate-api --config-file $DESIGNATE_CONF"
    run_process designate-pool-manager "$DESIGNATE_BIN_DIR/designate-pool-manager --config-file $DESIGNATE_CONF"
    run_process designate-zone-manager "$DESIGNATE_BIN_DIR/designate-zone-manager --config-file $DESIGNATE_CONF"
    run_process designate-mdns "$DESIGNATE_BIN_DIR/designate-mdns --config-file $DESIGNATE_CONF"
    run_process designate-agent "$DESIGNATE_BIN_DIR/designate-agent --config-file $DESIGNATE_CONF"
    run_process designate-sink "$DESIGNATE_BIN_DIR/designate-sink --config-file $DESIGNATE_CONF"

    # Start proxies if enabled
    if is_service_enabled designate-api && is_service_enabled tls-proxy; then
        start_tls_proxy '*' $DESIGNATE_SERVICE_PORT $DESIGNATE_SERVICE_HOST $DESIGNATE_SERVICE_PORT_INT &
    fi

    if ! timeout $SERVICE_TIMEOUT sh -c "while ! wget --no-proxy -q -O- $DESIGNATE_SERVICE_PROTOCOL://$DESIGNATE_SERVICE_HOST:$DESIGNATE_SERVICE_PORT; do sleep 1; done"; then
        die $LINENO "Designate did not start"
    fi
}

# stop_designate - Stop running processes
function stop_designate {
    # Kill the designate screen windows
    stop_process designate-central
    stop_process designate-api
    stop_process designate-pool-manager
    stop_process designate-zone-manager
    stop_process designate-mdns
    stop_process designate-agent
    stop_process designate-sink

    stop_designate_backend
}

# This is the main for plugin.sh
if is_service_enabled designate; then

    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing Designate client"
        install_designateclient

        echo_summary "Installing Designate"
        install_designate

        if is_service_enabled horizon; then
            echo_summary "Installing Designate dashboard"
            install_designatedashboard
        fi

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring Designate"
        configure_designate

        if is_service_enabled key; then
            echo_summary "Creating Designate Keystone accounts"
            create_designate_accounts
        fi

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Designate"
        init_designate

        echo "Configuring Tempest options for Designate"
        configure_designate_tempest

        echo_summary "Starting Designate"
        start_designate

        echo_summary "Creating pool NS records"
        create_designate_ns_records
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_designate
    fi

    if [[ "$1" == "clean" ]]; then
        echo_summary "Cleaning Designate"
        cleanup_designate
    fi
fi

# Restore xtrace
$XTRACE
