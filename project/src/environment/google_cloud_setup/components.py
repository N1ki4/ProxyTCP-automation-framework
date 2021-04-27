from collections import namedtuple


Project = namedtuple("Project", ["id", "network", "credentials"])
InstTemplate = namedtuple("InstTemplate", ["name", "machine_type", "disk_size", "os"])
Instance = namedtuple("Instance", ["name", "zone", "external_ip", "tags", "from_"])
FirewallRule = namedtuple(
    "FirewallRule",
    ["name", "source_ip_ranges", "priority", "tags", "protocol", "ports"],
)
