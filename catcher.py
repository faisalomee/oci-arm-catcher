import os
import oci
import sys

def main():
    config = {
        "user": os.environ["OCI_USER_OCID"],
        "tenancy": os.environ["OCI_TENANCY_OCID"],
        "fingerprint": os.environ["OCI_FINGERPRINT"],
        "region": os.environ["OCI_REGION"],
        "key_content": os.environ["OCI_PRIVATE_KEY"].replace("\\n", "\n"),
    }

    compute = oci.core.ComputeClient(config)
    compartment_id = os.environ["OCI_COMPARTMENT_OCID"]
    availability_domain = os.environ["OCI_AVAILABILITY_DOMAIN"]
    subnet_id = os.environ["OCI_SUBNET_OCID"]
    ssh_key = os.environ["OCI_SSH_PUBLIC_KEY"]
    display_name = "omee-arm"

    # Check if instance already exists
    existing = compute.list_instances(
        compartment_id=compartment_id,
        display_name=display_name
    ).data
    active = [i for i in existing if i.lifecycle_state not in ["TERMINATED", "TERMINATING"]]
    if active:
        print("Already created. Nothing to do.")
        sys.exit(0)

    # Find Ubuntu 24.04 ARM image
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

    # Try to launch instance
    instance_details = oci.core.models.LaunchInstanceDetails(
        compartment_id=compartment_id,
        availability_domain=availability_domain,
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
        metadata={"ssh_authorized_keys": ssh_key},
        display_name=display_name
    )

    try:
        response = compute.launch_instance(instance_details)
        print("SUCCESS! Server created.")
        print(response.data)
    except oci.exceptions.ServiceError as e:
        if "Out of capacity" in str(e.message) or "Out of host capacity" in str(e.message):
            print("No capacity yet. Will try again next run.")
            sys.exit(0)
        else:
            print("Error: " + str(e))
            sys.exit(1)

if __name__ == "__main__":
    main()
