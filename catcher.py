```python
import os
import oci
import sys
import time

def main():
    config = {
        "user": os.environ["OCI_USER_OCID"],
        "tenancy": os.environ["OCI_TENANCY_OCID"],
        "fingerprint": os.environ["OCI_FINGERPRINT"],
        "region": os.environ["OCI_REGION"],
        "key_content": os.environ["OCI_PRIVATE_KEY"].replace("\\n", "\n"),
    }

    compute = oci.core.ComputeClient(config)
    network = oci.core.VirtualNetworkClient(config)
    identity = oci.identity.IdentityClient(config)

    compartment_id = os.environ["OCI_COMPARTMENT_OCID"]
    subnet_id = os.environ["OCI_SUBNET_OCID"]
    ssh_key = os.environ["OCI_SSH_PUBLIC_KEY"]

    display_name = "omee-arm"

    print("Tenancy: " + config["tenancy"])
    print("Compartment: " + compartment_id)
    print("Subnet: " + subnet_id)

    # Keep trying until the server is created
    while True:
        print("\nChecking Oracle ARM capacity...")

        try:
            existing = compute.list_instances(
                compartment_id=compartment_id,
                display_name=display_name
            ).data

            active = [
                i for i in existing
                if i.lifecycle_state not in ["TERMINATED", "TERMINATING"]
            ]

            if active:
                print("Already created. Nothing to do.")
                sys.exit(0)

            ads = identity.list_availability_domains(
                compartment_id=config["tenancy"]
            ).data

            if not ads:
                print("No availability domains found.")
                sys.exit(1)

            ad_name = ads[0].name
            print("Using Availability Domain: " + ad_name)

            subnet = network.get_subnet(subnet_id).data
            print("Subnet OK: " + subnet.display_name)

            images = compute.list_images(
                compartment_id=compartment_id,
                operating_system="Canonical Ubuntu",
                operating_system_version="24.04",
                shape="VM.Standard.A1.Flex",
                sort_by="TIMECREATED",
                sort_order="DESC"
            ).data

            if not images:
                print("Ubuntu 24.04 ARM image not found.")
                sys.exit(1)

            image_id = images[0].id
            print("Using image: " + images[0].display_name)

            instance_details = oci.core.models.LaunchInstanceDetails(
                compartment_id=compartment_id,
                availability_domain=ad_name,
                shape="VM.Standard.A1.Flex",
                shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                    ocpus=2,
                    memory_in_gbs=12
                ),
                source_details=oci.core.models.InstanceSourceViaImageDetails(
                    image_id=image_id
                ),
                create_vnic_details=oci.core.models.CreateVnicDetails(
                    subnet_id=subnet_id,
                    assign_public_ip=True
                ),
                metadata={
                    "ssh_authorized_keys": ssh_key
                },
                display_name=display_name
            )

            try:
                response = compute.launch_instance(instance_details)

                print("SUCCESS! Server created.")
                print(response.data)
                sys.exit(0)

            except oci.exceptions.ServiceError as e:
                message = str(e.message)

                if "Out of capacity" in message or "Out of host capacity" in message:
                    print("No capacity yet.")
                    print("Waiting 15 minutes before next attempt...")
                    time.sleep(900)
                    continue

                elif e.status == 429:
                    print("Rate limited (429).")
                    print("Waiting 60 minutes before next attempt...")
                    time.sleep(3600)
                    continue

                else:
                    print("Error code: " + str(e.status))
                    print("Error message: " + message)
                    sys.exit(1)

        except Exception as e:
            print("Unexpected error: " + str(e))
            print("Waiting 15 minutes before retry...")
            time.sleep(900)


if __name__ == "__main__":
    main()
```
