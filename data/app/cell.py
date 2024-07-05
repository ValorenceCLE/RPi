import logging
from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd

# Router model and OID mappings
ROUTER_MODEL = "Pepwave MAX BR1 Pro 5G"
OID_MAPPINGS = {
    "Pepwave MAX BR1 Pro 5G": {
        'rsrp_oid': '.1.3.6.1.2.1.1.1.0',
        'rsrq_oid': '.1.3.6.1.2.1.1.5.0',
        'sinr_oid': '.1.3.6.1.2.1.1.3.0'
    }
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_snmp_data(host, community, oid_dict):
    """Fetch SNMP data synchronously."""
    engine = SnmpEngine()
    results = {}
    for oid_name, oid in oid_dict.items():
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(
                engine,
                CommunityData(community, mpModel=1),
                UdpTransportTarget((host, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )
        )

        if errorIndication:
            print(f"SNMP error: {errorIndication}")
            continue
        elif errorStatus:
            print(f"SNMP error at {errorIndex}: {errorStatus.prettyPrint()}")
            continue
        else:
            results[oid_name] = varBinds[0][1].prettyPrint()

    return results

def cell():
    host = '192.168.1.1'  # SNMP server address
    community = 'public'  # SNMP community
    oid_dict = OID_MAPPINGS.get(ROUTER_MODEL)

    if not oid_dict:
        print(f"No OID mapping found for {ROUTER_MODEL}")
        return

    # Fetch and print SNMP data
    data = fetch_snmp_data(host, community, oid_dict)
    for key, value in data.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    cell()
