# This mini tutorial shows you how you can call the Genesis Cloud Compute API to create an instance with NVIDIA GPU driver, take a snapshot, and delete it.
# This allows you to write scripts that can programmtically create GPU instances and destroy them when you are done.

# In order to create an instance we first need to look up the IDs of the:
#   - image we want to use
#   - stored public SSH Key(s) we want to use
#   - [OPTIONAL] security groups that we want to use
#
# If we don't specify any security groups the 'standard' security group will be applied which allows incoming Ping, SSH, HTTP, HTTPS.
# If you need an open port to expose a Jupyter notebook or Tensorboard to the internet. You need to create an apply a new security group to your instance,


import requests
import json
import time
import os

# Go to https://account.genesiscloud.com/dashboard/security
# and create and paste your secret API token here
API_TOKEN = os.environ['API_KEY']
# as well as the name of the SSH key you want to use to access your instance
ssh_key_name = os.environ['SSH_KEY_NAME']

startup_script = ""


def main():
    # Instance Configuration
    # Modify the following values to configure the instance that you want to create.
    # Please Note: As of the time of writing only a single SSH key is supported.
    instance = {
        "name": os.environ['INSTANCE_NAME'],
        "type": "vcpu-4_memory-12g_disk-80g_nvidia1080ti-1",
        "image_name": "Ubuntu 18.04",
        "ssh_key_names": [ssh_key_name],
        "security_group_names": ["standard"],
        "startup_script": startup_script,
    }

    # Get the ID for the image we want for our instance.
    instance["image_id"] = get_image_id(instance["image_name"])

    # Get the IDs for the SSH keys we want for our instance.
    # Please Note: As the the time of writing this ONLY ONE KEY is supported.
    instance["ssh_key_ids"] = get_ssh_key_ids(instance["ssh_key_names"])

    # OPTIONAL: Get the IDs of the security groups we want for our instance.
    instance["security_group_ids"] = get_security_group_ids(
        instance["security_group_names"]
    )

    # Create the instance
    instance["id"] = create_instance(instance)

    # The created instance will first be in the status 'enqueued' and then 'creating'
    # before changing to the status 'active' when it has booted and was assigned a public IP address.
    # This typically takes 30 seconds to 2 Minutes.
    while get_instance_status(instance["id"]) != "active":
        time.sleep(1.0)

    # Now you can use your instance: connect via SSH, start a machine learning training, render a movie or find a cure agains Covid-19... ;)
    # For demo purpose we will just wait 10 minutes here.
    # Please Note: if you passed a startup script, i.e. installing the NVIDIA GPU driver, the script is likely still executing by the time the
    # instance changes to acctive.
    print(
        "Instance is ready to be used...Public IP address: "
        + get_instance_public_ip(instance["id"])
    )
    time.sleep(10.0)

    # If you want to save the state of your instance's disk you can take a snapshot before you delete it.
    # Next time you create an instance you can use this snapshot as the instance image.
    # This way all you installed software and stored data are ready to be used.
    # Note: In order to store larger datasets that you want to use with multiple instances it is preferred to use volumes for data storage.
    # snapshot_name = "my-snapshot-2020-04-12"
    # snapshot_id = create_instance_snapshot(instance["id"], snapshot_name)

    # Before we can delete our instance we need to wait for the snapshot to finish.
    # The instance state will change from "copying" during the snapshot back to 'active'.
    # This typically takes 1 to 5 minutes
    # while get_instance_status(instance["id"]) != "active":
    #     time.sleep(1.0)
    # print("Finished taking snapshot " + snapshot_id)

    # Now that we saved our instance data as snapshot we are ready to delete it again.
    delete_instance(instance["id"])

    print("Done.")


def get_image_id(image_name):
    # getting a list of available instance images.

    headers = {"Content-Type": "application/json", "X-Auth-Token": API_TOKEN}
    # You can set the type parameter to get only images of a specific type, e.g. 'base-os' or 'snapshot'.
    params = {
        #'type':'base-os',
        "per_page": 50,
        "page": 1,
    }
    response = requests.get(
        "https://api.genesiscloud.com/compute/v1/images", headers=headers, params=params
    )

    if response.status_code != 200:
        print(response.status_code)
        print(json.dumps(response.json(), indent=4, sort_keys=True))
        exit()

    available_images = {}
    for image in response.json()["images"]:
        available_images[image["name"]] = image["id"]

    return available_images[image_name]


def get_ssh_key_ids(ssh_key_names):
    # getting a list of available SSH Keys and looking up the ID

    # Setting the secret auth token and content type in the headers of all API calls
    headers = {"Content-Type": "application/json", "X-Auth-Token": API_TOKEN}
    params = {"per_page": 50, "page": 1}
    response = requests.get(
        "https://api.genesiscloud.com/compute/v1/ssh-keys",
        headers=headers,
        params=params,
    )

    if response.status_code != 200:
        print(response.status_code)
        print(json.dumps(response.json(), indent=4, sort_keys=True))
        exit()

    available_ssh_keys = {}
    for ssh_key in response.json()["ssh_keys"]:
        available_ssh_keys[ssh_key["name"]] = ssh_key["id"]

    ssh_key_ids = []
    for ssh_key_name in ssh_key_names:
        ssh_key_ids.append(available_ssh_keys[ssh_key_name])

    return ssh_key_ids


def get_security_group_ids(security_group_names):
    # getting a list of security groups and the id of a specifc security group

    headers = {"Content-Type": "application/json", "X-Auth-Token": API_TOKEN}
    params = {"per_page": 50, "page": 1}
    response = requests.get(
        "https://api.genesiscloud.com/compute/v1/security-groups",
        headers=headers,
        params=params,
    )

    if response.status_code != 200:
        print(response.status_code)
        print(json.dumps(response.json(), indent=4, sort_keys=True))
        exit()

    available_security_groups = {}
    for security_group in response.json()["security_groups"]:
        available_security_groups[security_group["name"]] = security_group["id"]

    security_group_ids = []
    for security_group_name in security_group_names:
        security_group_ids.append(available_security_groups[security_group_name])

    return security_group_ids


def create_instance(instance):
    # Creating an instance

    headers = {"Content-Type": "application/json", "X-Auth-Token": API_TOKEN}
    jsonbody = {
        "name": instance["name"],
        "hostname": instance["name"],
        "type": instance["type"],
        "image": instance["image_id"],
        "ssh_keys": instance["ssh_key_ids"],
        "security_groups": instance["security_group_ids"],
        "metadata": {"startup_script": instance["startup_script"]},
    }
    response = requests.post(
        "https://api.genesiscloud.com/compute/v1/instances",
        headers=headers,
        json=jsonbody,
    )

    if response.status_code != 201:
        print(response.status_code)
        print(json.dumps(response.json(), indent=4, sort_keys=True))
        exit()

    instance_id = response.json()["instance"]["id"]
    print("Creating instance " + instance_id)
    return instance_id


def get_instance_status(instance_id):

    headers = {"Content-Type": "application/json", "X-Auth-Token": API_TOKEN}
    response = requests.get(
        "https://api.genesiscloud.com/compute/v1/instances/" + instance_id,
        headers=headers,
    )
    if response.status_code == 200:
        return response.json()["instance"]["status"]
    else:
        print(response.status_code)
        print(json.dumps(response.json(), indent=4, sort_keys=True))
        exit()


def get_instance_public_ip(instance_id):

    headers = {"Content-Type": "application/json", "X-Auth-Token": API_TOKEN}
    response = requests.get(
        "https://api.genesiscloud.com/compute/v1/instances/" + instance_id,
        headers=headers,
    )
    if response.status_code == 200:
        return response.json()["instance"]["public_ip"]
    else:
        print(response.status_code)
        print(json.dumps(response.json(), indent=4, sort_keys=True))
        exit()


def create_instance_snapshot(instance_id, snapshot_name):

    headers = {"Content-Type": "application/json", "X-Auth-Token": API_TOKEN}
    jsonbody = {
        "name": snapshot_name,
    }
    response = requests.post(
        "https://api.genesiscloud.com/compute/v1/instances/"
        + instance_id
        + "/snapshots",
        headers=headers,
        json=jsonbody,
    )

    if response.status_code != 201:
        print(response.status_code)
        print(json.dumps(response.json(), indent=4, sort_keys=True))
        exit()

    snapshot_id = response.json()["snapshot"]["id"]
    print("Creating snapshot " + snapshot_id + " of instance " + instance_id)
    return snapshot_id


def delete_instance(instance_id):

    headers = {"Content-Type": "application/json", "X-Auth-Token": API_TOKEN}
    response = requests.delete(
        "https://api.genesiscloud.com/compute/v1/instances/" + instance_id,
        headers=headers,
    )

    if response.status_code != 204:
        print(response.status_code)
        print(json.dumps(response.json(), indent=4, sort_keys=True))
        exit()
    print("Deleting instance " + instance_id)


# run the main function
if __name__ == "__main__":
    main()
