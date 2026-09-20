name: OCI ARM Catcher
on:
  schedule:
    - cron: '*/15 * * * *'
  workflow_dispatch:

jobs:
  catch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install OCI SDK
        run: pip install oci
      - name: Run catcher
        env:
          OCI_USER_OCID: ${{ secrets.OCI_USER_OCID }}
          OCI_TENANCY_OCID: ${{ secrets.OCI_TENANCY_OCID }}
          OCI_FINGERPRINT: ${{ secrets.OCI_FINGERPRINT }}
          OCI_REGION: ${{ secrets.OCI_REGION }}
          OCI_PRIVATE_KEY: ${{ secrets.OCI_PRIVATE_KEY }}
          OCI_COMPARTMENT_OCID: ${{ secrets.OCI_COMPARTMENT_OCID }}
          OCI_AVAILABILITY_DOMAIN: ${{ secrets.OCI_AVAILABILITY_DOMAIN }}
          OCI_SUBNET_OCID: ${{ secrets.OCI_SUBNET_OCID }}
          OCI_SSH_PUBLIC_KEY: ${{ secrets.OCI_SSH_PUBLIC_KEY }}
        run: python catcher.py
