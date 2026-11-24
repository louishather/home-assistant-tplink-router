DEFAULT_NAME = "TP-Link Router"
DOMAIN = "tplink_router"
CONF_CLIENT_CLASS = "client_class"
CONF_SUPPORT_VPN = "support_vpn"
CONF_SUPPORT_TRACKER = "support_tracker"
CONF_TRACKER_AS_DEVICE = "tracker_as_device"
CONF_SUPPORT_DHCP_RESERVATIONS = "support_dhcp_reservations"
CONF_SUPPORT_DHCP_LEASES = "support_dhcp_leases"
CONF_SUPPORT_SERVING_CELLS = "support_serving_cells"
CONF_SCAN_RETRIES = "scan_retries"
CONF_SCAN_BACKOFF = "scan_backoff"
CONF_SCAN_PAUSE = "scan_pause"
CONF_OFFLINE_TIMEOUT = "offline_timeout"
CONF_FAILURE_COOLDOWN = "failure_cooldown"
CONF_SLOW_SCAN_INTERVAL = "slow_scan_interval"
CONF_HOLD_SESSION = "hold_session"
CONF_YIELD_MINUTES = "yield_minutes"
DEFAULT_USER = "admin"
DEFAULT_HOST = "http://192.168.0.1"
DEFAULT_SCAN_RETRIES = 3
DEFAULT_SCAN_BACKOFF = 1.0
DEFAULT_SCAN_PAUSE = 20
DEFAULT_OFFLINE_TIMEOUT = 0
# Fork: seconds to skip polling after a failed update, so a router that locks out logins can recover
DEFAULT_FAILURE_COOLDOWN = 120
# Fork: everything except status/clients (and LTE/SMS) is read at most this often
DEFAULT_SLOW_SCAN_INTERVAL = 300
# Fork: stay logged in between updates; when another login takes the session, leave the router
# alone for this many minutes so its web UI can be used
DEFAULT_HOLD_SESSION = False
DEFAULT_YIELD_MINUTES = 3
MAX_SCAN_RETRIES = 10
MAX_SCAN_BACKOFF = 30.0
MAX_SCAN_PAUSE = 1440
MAX_OFFLINE_TIMEOUT = 86400
MAX_FAILURE_COOLDOWN = 3600
MAX_SLOW_SCAN_INTERVAL = 86400
MAX_YIELD_MINUTES = 120

EVENT_NEW_DEVICE = f"{DOMAIN}_new_device"
EVENT_ONLINE = f"{DOMAIN}_device_online"
EVENT_OFFLINE = f"{DOMAIN}_device_offline"
EVENT_NEW_SMS = f"{DOMAIN}_new_sms"
