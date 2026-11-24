
CREATE TABLE IF NOT EXISTS locations (
    site_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    employee_count INTEGER NOT NULL,
    is_headquarters INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS departments (
    dept_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    employee_count INTEGER NOT NULL
);


CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dept_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    job_title TEXT,
    hire_date DATE,
    termination_date DATE,
    employment_status TEXT NOT NULL DEFAULT 'Active',
    manager_id TEXT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
    FOREIGN KEY (site_id) REFERENCES locations(site_id),
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
);


CREATE TABLE IF NOT EXISTS site_contacts (
    contact_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    responsibility TEXT,
    is_it_employee INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (site_id) REFERENCES locations(site_id)
);

CREATE TABLE IF NOT EXISTS ad_users (
    ad_user_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    distinguished_name TEXT NOT NULL,
    account_status TEXT NOT NULL DEFAULT 'Enabled',
    is_locked INTEGER NOT NULL DEFAULT 0,
    is_privileged INTEGER NOT NULL DEFAULT 0,
    last_logon DATETIME,
    password_last_set DATETIME,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS ad_groups (
    group_id TEXT PRIMARY KEY,
    group_name TEXT NOT NULL UNIQUE,
    group_type TEXT NOT NULL,
    description TEXT,
    is_privileged INTEGER NOT NULL DEFAULT 0,
    is_critical INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS group_memberships (
    membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_user_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    membership_date DATE,
    FOREIGN KEY (ad_user_id) REFERENCES ad_users(ad_user_id),
    FOREIGN KEY (group_id) REFERENCES ad_groups(group_id),
    UNIQUE (ad_user_id, group_id)
);

CREATE TABLE IF NOT EXISTS group_nesting (
    nesting_id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_group_id TEXT NOT NULL,
    child_group_id TEXT NOT NULL,
    FOREIGN KEY (parent_group_id) REFERENCES ad_groups(group_id),
    FOREIGN KEY (child_group_id) REFERENCES ad_groups(group_id),
    UNIQUE (parent_group_id, child_group_id),
    CHECK (parent_group_id != child_group_id)
);

CREATE TABLE IF NOT EXISTS access_permissions (
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    permission_level TEXT NOT NULL,
    granted_date DATE,
    FOREIGN KEY (group_id) REFERENCES ad_groups(group_id),
    UNIQUE (group_id, resource_type, resource_id, permission_level)
);

CREATE TABLE IF NOT EXISTS m365_accounts (
    m365_account_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    account_status TEXT NOT NULL DEFAULT 'Active',
    license_type TEXT,
    mfa_enabled INTEGER NOT NULL DEFAULT 1,
    created_date DATE,
    last_signin DATETIME,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS computers (
    computer_id TEXT PRIMARY KEY,
    hostname TEXT NOT NULL UNIQUE,
    serial_number TEXT NOT NULL UNIQUE,
    manufacturer TEXT,
    model TEXT,
    device_type TEXT NOT NULL,
    operating_system TEXT,
    site_id TEXT NOT NULL,
    dept_id TEXT NOT NULL,
    ip_address TEXT,
    mac_address TEXT UNIQUE,
    vlan_id INTEGER,
    ou_path TEXT,
    device_status TEXT NOT NULL DEFAULT 'Active',
    purchase_date DATE,
    last_inventory_update DATETIME,
    FOREIGN KEY (site_id) REFERENCES locations(site_id),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);
CREATE TABLE IF NOT EXISTS computer_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    computer_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    assigned_date DATE NOT NULL,
    returned_date DATE,
    assignment_status TEXT NOT NULL DEFAULT 'Active',

    FOREIGN KEY (computer_id) REFERENCES computers(computer_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS ip_assignments (
    ip_assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    computer_id TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    subnet_mask TEXT NOT NULL,
    gateway TEXT NOT NULL,
    vlan_id INTEGER NOT NULL,
    assignment_method TEXT NOT NULL DEFAULT 'DHCP',
    assigned_at DATETIME NOT NULL,
    released_at DATETIME,
    is_current INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (computer_id) REFERENCES computers(computer_id),

    CHECK (is_current IN (0, 1)),
    CHECK (assignment_method IN ('DHCP', 'Static'))
);

CREATE UNIQUE INDEX IF NOT EXISTS
idx_current_ip_address
ON ip_assignments(ip_address)
WHERE is_current = 1;


CREATE TABLE IF NOT EXISTS vlans (
    vlan_id INTEGER NOT NULL,
    site_id TEXT NOT NULL,
    vlan_name TEXT NOT NULL,
    subnet TEXT NOT NULL,
    gateway TEXT NOT NULL,
    dhcp_start TEXT NOT NULL,
    dhcp_end TEXT NOT NULL,

    PRIMARY KEY (vlan_id, site_id),

    FOREIGN KEY (site_id)
        REFERENCES locations(site_id)
);

CREATE TABLE IF NOT EXISTS servers (
    server_id TEXT PRIMARY KEY,
    hostname TEXT NOT NULL UNIQUE,
    server_category TEXT NOT NULL,
    server_role TEXT NOT NULL,
    operating_system TEXT NOT NULL,
    site_id TEXT NOT NULL,
    ip_address TEXT NOT NULL UNIQUE,
    vlan_id INTEGER NOT NULL,
    environment TEXT NOT NULL DEFAULT 'Production',
    server_status TEXT NOT NULL DEFAULT 'Active',
    criticality TEXT NOT NULL DEFAULT 'Medium',
    last_inventory_update DATETIME,

    FOREIGN KEY (site_id) REFERENCES locations(site_id)
);

CREATE TABLE IF NOT EXISTS server_dependencies (
    dependency_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_server_id TEXT NOT NULL,
    target_server_id TEXT NOT NULL,
    dependency_type TEXT NOT NULL,
    description TEXT,

    FOREIGN KEY (source_server_id)
        REFERENCES servers(server_id),

    FOREIGN KEY (target_server_id)
        REFERENCES servers(server_id),

    CHECK (source_server_id != target_server_id),

    UNIQUE (
        source_server_id,
        target_server_id,
        dependency_type
    )
);
CREATE TABLE IF NOT EXISTS application_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_name TEXT NOT NULL,
    server_id TEXT NOT NULL,
    server_role TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(server_id),
    UNIQUE (application_name, server_id)
);

CREATE TABLE IF NOT EXISTS printers (
    printer_id TEXT PRIMARY KEY,
    hostname TEXT NOT NULL UNIQUE,
    manufacturer TEXT NOT NULL,
    model TEXT NOT NULL,
    site_id TEXT NOT NULL,
    department_id TEXT,
    ip_address TEXT NOT NULL UNIQUE,
    mac_address TEXT NOT NULL UNIQUE,
    vlan_id INTEGER NOT NULL DEFAULT 160,
    printer_type TEXT NOT NULL,
    printer_status TEXT NOT NULL DEFAULT 'Active',
    last_inventory_update DATETIME,

    FOREIGN KEY (site_id) REFERENCES locations(site_id),
    FOREIGN KEY (department_id) REFERENCES departments(dept_id)
);

CREATE TABLE IF NOT EXISTS ip_phones (
    phone_id TEXT PRIMARY KEY,
    hostname TEXT NOT NULL UNIQUE,
    manufacturer TEXT NOT NULL,
    model TEXT NOT NULL,
    site_id TEXT NOT NULL,
    department_id TEXT,
    ip_address TEXT NOT NULL UNIQUE,
    mac_address TEXT NOT NULL UNIQUE,
    vlan_id INTEGER NOT NULL DEFAULT 170,
    phone_extension TEXT NOT NULL UNIQUE,
    phone_status TEXT NOT NULL DEFAULT 'Active',
    last_inventory_update DATETIME,

    FOREIGN KEY (site_id) REFERENCES locations(site_id),
    FOREIGN KEY (department_id) REFERENCES departments(dept_id)
);

CREATE TABLE IF NOT EXISTS network_devices (
    device_id TEXT PRIMARY KEY,
    hostname TEXT NOT NULL UNIQUE,
    device_type TEXT NOT NULL,
    manufacturer TEXT NOT NULL,
    model TEXT NOT NULL,
    site_id TEXT NOT NULL,
    management_ip TEXT NOT NULL UNIQUE,
    mac_address TEXT NOT NULL UNIQUE,
    vlan_id INTEGER NOT NULL DEFAULT 150,
    device_status TEXT NOT NULL DEFAULT 'Active',
    last_inventory_update DATETIME,

    FOREIGN KEY (site_id) REFERENCES locations(site_id)
);
CREATE TABLE IF NOT EXISTS dhcp_leases (
    lease_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    mac_address TEXT NOT NULL,
    hostname TEXT,
    site_id TEXT NOT NULL,
    vlan_id INTEGER NOT NULL,
    lease_start DATETIME NOT NULL,
    lease_end DATETIME NOT NULL,
    lease_status TEXT NOT NULL DEFAULT 'Active',

    FOREIGN KEY (site_id) REFERENCES locations(site_id)
);

CREATE TABLE IF NOT EXISTS dns_records (
    dns_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL,
    fqdn TEXT NOT NULL UNIQUE,
    record_type TEXT NOT NULL DEFAULT 'A',
    ip_address TEXT NOT NULL,
    site_id TEXT NOT NULL,
    vlan_id INTEGER,
    source_table TEXT NOT NULL,
    ttl INTEGER NOT NULL DEFAULT 3600,
    record_status TEXT NOT NULL DEFAULT 'Active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (site_id) REFERENCES locations(site_id)
);

CREATE TABLE IF NOT EXISTS ad_login_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_user_id TEXT NOT NULL,
    windows_event_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_time DATETIME NOT NULL,
    source_ip TEXT,
    source_hostname TEXT,
    site_id TEXT,
    logon_type TEXT,
    failure_reason TEXT,

    FOREIGN KEY (ad_user_id)
        REFERENCES ad_users(ad_user_id),

    FOREIGN KEY (site_id)
        REFERENCES locations(site_id),

    CHECK (event_type IN ('Success', 'Failure')),
    CHECK (windows_event_id IN (4624, 4625))
);

CREATE TABLE IF NOT EXISTS ad_account_lockouts (
    lockout_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_user_id TEXT NOT NULL,
    event_time DATETIME NOT NULL,
    source_hostname TEXT,
    source_ip TEXT,
    site_id TEXT,
    windows_event_id INTEGER NOT NULL DEFAULT 4740,

    FOREIGN KEY (ad_user_id) REFERENCES ad_users(ad_user_id),
    FOREIGN KEY (site_id) REFERENCES locations(site_id),

    CHECK (windows_event_id = 4740)
);

CREATE TABLE IF NOT EXISTS ad_password_events (
    password_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_user_id TEXT NOT NULL,
    actor_ad_user_id TEXT,
    windows_event_id INTEGER NOT NULL,
    event_time DATETIME NOT NULL,
    source_hostname TEXT,
    site_id TEXT,
    operation_status TEXT NOT NULL,

    FOREIGN KEY (ad_user_id)
        REFERENCES ad_users(ad_user_id),

    FOREIGN KEY (actor_ad_user_id)
        REFERENCES ad_users(ad_user_id),

    FOREIGN KEY (site_id)
        REFERENCES locations(site_id),

    CHECK (windows_event_id IN (4723, 4724)),
    CHECK (operation_status IN ('Success', 'Failure'))
);

CREATE TABLE IF NOT EXISTS ad_account_events (
    account_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_ad_user_id TEXT NOT NULL,
    actor_ad_user_id TEXT,
    windows_event_id INTEGER NOT NULL,
    event_time DATETIME NOT NULL,
    source_hostname TEXT,
    site_id TEXT,
    operation_status TEXT NOT NULL,

    FOREIGN KEY (target_ad_user_id)
        REFERENCES ad_users(ad_user_id),

    FOREIGN KEY (actor_ad_user_id)
        REFERENCES ad_users(ad_user_id),

    FOREIGN KEY (site_id)
        REFERENCES locations(site_id),

    CHECK (windows_event_id IN (4720, 4722, 4725, 4726)),
    CHECK (operation_status IN ('Success', 'Failure'))
);

CREATE TABLE IF NOT EXISTS ad_group_membership_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_ad_user_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    actor_ad_user_id TEXT,
    windows_event_id INTEGER NOT NULL,
    event_time DATETIME NOT NULL,
    source_hostname TEXT,
    site_id TEXT,
    operation_status TEXT NOT NULL,

    FOREIGN KEY (target_ad_user_id)
        REFERENCES ad_users(ad_user_id),

    FOREIGN KEY (group_id)
        REFERENCES ad_groups(group_id),

    FOREIGN KEY (actor_ad_user_id)
        REFERENCES ad_users(ad_user_id),

    FOREIGN KEY (site_id)
        REFERENCES locations(site_id),

    CHECK (windows_event_id IN (4728, 4729, 4732, 4733)),
    CHECK (operation_status IN ('Success', 'Failure'))
);

CREATE TABLE IF NOT EXISTS m365_signin_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    m365_account_id TEXT NOT NULL,
    event_time DATETIME NOT NULL,
    event_type TEXT NOT NULL,
    signin_status TEXT NOT NULL,
    source_ip TEXT,
    source_hostname TEXT,
    site_id TEXT,
    mfa_result TEXT,
    failure_reason TEXT,
    risk_level TEXT DEFAULT 'None',

    FOREIGN KEY (m365_account_id)
        REFERENCES m365_accounts(m365_account_id),

    FOREIGN KEY (site_id)
        REFERENCES locations(site_id),

    CHECK (event_type IN ('Interactive', 'NonInteractive')),
    CHECK (signin_status IN ('Success', 'Failure')),
    CHECK (mfa_result IN ('Success', 'Failure', 'NotRequired', 'NotApplicable')),
    CHECK (risk_level IN ('None', 'Low', 'Medium', 'High'))
);
CREATE TABLE IF NOT EXISTS firewall_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time DATETIME NOT NULL,
    firewall_hostname TEXT NOT NULL,
    site_id TEXT NOT NULL,
    source_ip TEXT NOT NULL,
    destination_ip TEXT NOT NULL,
    source_port INTEGER,
    destination_port INTEGER,
    protocol TEXT NOT NULL
        CHECK (protocol IN ('TCP', 'UDP', 'ICMP', 'OTHER')),
    direction TEXT NOT NULL
        CHECK (direction IN ('Inbound', 'Outbound', 'InterVLAN', 'VPN')),
    source_zone TEXT,
    destination_zone TEXT,
    action TEXT NOT NULL
        CHECK (action IN ('Allow', 'Deny')),
    rule_name TEXT NOT NULL,
    event_type TEXT NOT NULL
        CHECK (event_type IN ('Connection', 'Threat', 'VPN')),
    severity TEXT NOT NULL
        CHECK (severity IN ('Info', 'Low', 'Medium', 'High', 'Critical')),
    FOREIGN KEY (site_id) REFERENCES locations(site_id),
    CHECK (source_port IS NULL OR source_port BETWEEN 1 AND 65535),
    CHECK (destination_port IS NULL OR destination_port BETWEEN 1 AND 65535)
);
CREATE TABLE IF NOT EXISTS network_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time DATETIME NOT NULL,
    device_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    event_type TEXT NOT NULL
        CHECK (event_type IN (
            'DeviceDown',
            'DeviceUp',
            'PortDown',
            'PortUp',
            'HighLatency',
            'PacketLoss',
            'DeviceRestart',
            'InterfaceError'
        )),
    severity TEXT NOT NULL
        CHECK (severity IN ('Info', 'Low', 'Medium', 'High', 'Critical')),
    interface_name TEXT,
    description TEXT NOT NULL,
    duration_seconds INTEGER,
    FOREIGN KEY (device_id) REFERENCES network_devices(device_id),
    FOREIGN KEY (site_id) REFERENCES locations(site_id)
);
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL,
    assigned_ad_user_id TEXT,
    category TEXT NOT NULL
        CHECK (category IN (
            'Account Access',
            'Network',
            'Hardware',
            'Software',
            'Email',
            'Printer',
            'Server',
            'Other'
        )),
    subcategory TEXT,
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL
        CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    status TEXT NOT NULL
        CHECK (status IN (
            'Open',
            'In Progress',
            'Pending',
            'Resolved',
            'Closed'
        )),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    resolved_at DATETIME,
    site_id TEXT NOT NULL,
    related_computer_id TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (assigned_ad_user_id) REFERENCES ad_users(ad_user_id),
    FOREIGN KEY (site_id) REFERENCES locations(site_id),
    FOREIGN KEY (related_computer_id) REFERENCES computers(computer_id)
);
CREATE TABLE IF NOT EXISTS ticket_comments (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL,
    author_employee_id TEXT,
    comment_text TEXT NOT NULL,
    comment_type TEXT NOT NULL
        CHECK (comment_type IN (
            'UserMessage',
            'ITResponse',
            'InternalNote',
            'Resolution'
        )),
    created_at DATETIME NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id),
    FOREIGN KEY (author_employee_id) REFERENCES employees(employee_id)
);
CREATE TABLE IF NOT EXISTS server_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time DATETIME NOT NULL,
    server_id TEXT NOT NULL,
    event_type TEXT NOT NULL
        CHECK (event_type IN (
            'HighCPU',
            'HighMemory',
            'LowDiskSpace',
            'ServiceDown',
            'ServiceRecovered',
            'BackupFailed',
            'BackupCompleted',
            'ServerDown',
            'ServerRestart',
            'SecurityAlert',
            'UpdateFailed'
        )),
    severity TEXT NOT NULL
        CHECK (severity IN ('Info', 'Low', 'Medium', 'High', 'Critical')),
    metric_name TEXT,
    metric_value REAL,
    description TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(server_id)
);
CREATE TABLE IF NOT EXISTS application_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time DATETIME NOT NULL,
    application_server_id INTEGER NOT NULL,
    event_type TEXT NOT NULL
        CHECK (event_type IN (
            'ApplicationDown',
            'ApplicationRecovered',
            'DatabaseConnectionError',
            'HighResponseTime',
            'AuthenticationFailure',
            'ApplicationError',
            'ServiceUnavailable'
        )),
    severity TEXT NOT NULL
        CHECK (severity IN ('Info', 'Low', 'Medium', 'High', 'Critical')),
    response_time_ms INTEGER,
    error_code TEXT,
    description TEXT NOT NULL,
    FOREIGN KEY (application_server_id)
        REFERENCES application_servers(id),
    CHECK (response_time_ms IS NULL OR response_time_ms >= 0)
);



