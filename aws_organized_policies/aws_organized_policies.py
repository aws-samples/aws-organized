import boto3
import json
import yaml
from aws_organized_policies import helper
import os
from datetime import datetime
import click
import os
from datetime import datetime
from betterboto import client as betterboto_client
from pathlib import Path
import time

STATE_FILE = "state.yaml"
client = boto3.client("sts")
org = boto3.client("organizations")
SERVICE_CONTROL_POLICY = "SERVICE_CONTROL_POLICY"
ORGANIZATIONAL_UNIT = "ORGANIZATIONAL_UNIT"
service_control_policies_path = "environment/Policies/SCPs"
SEP = os.path.sep
ATTACH_POLICY = "ATTACH_POLICY"
DETACH_POLICY = "DETACH_POLICY"

policies_migration_path = "environment/policies_migration"
make_individual_migration_policies_path = (
    "environment/policies_migration/migrations_to_apply"
)


def read_policies() -> None:  # Reads + Returns a list {'SERVICE_CONTROL_POLICIEs': ['c', 'd', 'e']}
    path = "organization/Policies/"
    name = "policy_sample" + ".yml"
    with open(path + name) as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        policies_list = yaml.load(file, Loader=yaml.FullLoader)
        scp_list = policies_list.get("SERVICE_CONTROL_POLICIES")


# get an array of all accounts in the Organisation
def get_accounts() -> dict:
    accounts = dict()
    paginator = org.get_paginator("list_accounts")  # use paginator for efficiency
    page_iterator = paginator.paginate()
    for page in page_iterator:
        for acct in page["Accounts"]:  # get all accounts in org
            accounts[acct.get("Id")] = acct.get("Name")
    return accounts


# map every account + corresponding SCPs in ORG as [target_id]:{policy}
def get_service_control_policies_for_target(policies_target_list, root_id) -> dict:
    policies_for_each_target = dict()
    policies_name_for_each_target = dict()
    policies_target_IDs = list(policies_target_list.keys())
    print("policies_target_list", policies_target_list)

    for target_id in policies_target_IDs:
        list_service_control_policies = org.list_policies_for_target(
            TargetId=target_id, Filter=SERVICE_CONTROL_POLICY
        )
        describe_service_control_policies = (
            [  # for every PolicyId get readable description
                org.describe_policy(PolicyId=target.get("Id"))
                for target in list_service_control_policies.get("Policies")
            ]
        )

        policies_for_each_target[policies_target_list[target_id]] = [
            policy.get("Policy") for policy in describe_service_control_policies
        ]

        policies_name_for_each_target[
            policies_target_list[target_id]
            if policies_target_list[target_id] != "Root"
            else root_id
        ] = [
            helper.get_valid_filename(
                policy.get("Policy").get("PolicySummary").get("Name")
            )
            for policy in describe_service_control_policies
        ]

    print("policies_name_for_each_target", policies_name_for_each_target)
    return policies_for_each_target, policies_name_for_each_target


# get an array of all OUs as a list including route using recursion
# https://stackoverflow.com/questions/57012709/aws-boto3-how-to-list-of-all-the-org-idseven-nested-under-organization
def list_organizational_units(parent_id, ou_list) -> list:
    ou_list.append(parent_id)
    paginator = org.get_paginator("list_children")
    iterator = paginator.paginate(ParentId=parent_id, ChildType=ORGANIZATIONAL_UNIT)
    for page in iterator:
        for ou in page["Children"]:
            list_organizational_units(ou["Id"], ou_list)
    return ou_list


def get_organizational_units(root_id) -> dict:
    ou_list = list_organizational_units(root_id, list())[1:]
    all_ous = {  # map ou_id to ou_name as {"OU_Id":"OU_Name"}
        ou_Id: org.describe_organizational_unit(OrganizationalUnitId=ou_Id)[
            "OrganizationalUnit"
        ]["Name"]
        for ou_Id in ou_list
    }
    all_ous[root_id] = root_id
    return all_ous


def write_all_policies_to_json(path, policies_dict) -> None:
    for policy in policies_dict.values():
        policy_file_name = helper.get_valid_filename(
            policy.get("PolicySummary").get("Name")
        )
        helper.write_to_file(policy, path, policy_file_name + ".json")


# TODO extend to other policies by adding policy_type parameter
def write_policies_to_individual_target_yaml(
    all_policies_for_target, path, file_name
) -> None:
    data = {"Policies_Attached": all_policies_for_target}
    Path(path).mkdir(parents=True, exist_ok=True)
    with open(path + file_name, "w") as outfile:
        yaml.dump(data, outfile, default_flow_style=False)


def write_policies_to_target_yaml(target_SCPs, target_name_path) -> dict:
    policies_per_target = dict()

    for target_id, policies_attached_to_target in target_SCPs.items():
        policies_name = [
            helper.get_valid_filename(policy["PolicySummary"]["Name"])
            for policy in policies_attached_to_target
        ]

        target_path = target_name_path[target_id] + "/"
        policies_per_target[target_id] = policies_name  # saved initial state policies
        policy_file_name = "_service_control_policies.yaml"

        write_policies_to_individual_target_yaml(
            policies_name, target_path, policy_file_name
        )
    return policies_per_target


def get_unique_policies(policies_dic) -> dict:
    common_policies = {}
    for policies_list in policies_dic.values():
        for policy in policies_list:
            common_policies[policy.get("PolicySummary").get("Id")] = policy
    return common_policies


def get_org_structure(org_path) -> dict:
    file_list = helper.getListOfFiles(org_path)
    accounts_path = helper.get_account_paths(file_list)
    ous_path = {
        path[0].split("/")[-1]: path[0] + "/"
        for path in os.walk(org_path)
        if path[0][-9:] != "_accounts"
    }
    return accounts_path, ous_path


def get_id_from_name(target_name, id_name_map) -> str:
    for id, name in id_name_map.items():
        if target_name == name:
            return id


def get_all_policies_in_account():
    org_policies = org.list_policies(Filter="SERVICE_CONTROL_POLICY").get("Policies")
    all_SCPs = dict()
    for policy in org_policies:
        policy_id = policy.get("Id")
        # policy_name = helper.get_valid_filename(policy.get('Name'))
        policy_full = org.describe_policy(PolicyId=policy_id)
        if (
            policy_full.get("Policy").get("PolicySummary").get("Type")
            == "SERVICE_CONTROL_POLICY"
        ):
            all_SCPs[policy_id] = policy_full.get("Policy")
    return all_SCPs


def import_organization_policies(role_arn) -> None:
    click.echo("Updating state file")
    with betterboto_client.CrossAccountClientContextManager(
        "organizations",
        role_arn,
        f"organizations",
    ) as organizations:
        list_accounts_details = organizations.list_accounts_single_page()
        list_roots_response = organizations.list_roots_single_page()
        root_id = list_roots_response.get("Roots")[0].get("Id")
        org_path = SEP.join(["environment", root_id])
        all_files_in_environment_list = helper.getListOfFiles(org_path)

    # Step 0 get all policies in org
    all_service_control_policies_in_org = org.list_policies(
        Filter=SERVICE_CONTROL_POLICY
    ).get("Policies")

    all_service_control_policies_in_org_with_policy_summary = [
        org.describe_policy(PolicyId=policy.get("Id")).get("Policy")
        for policy in all_service_control_policies_in_org
    ]

    [
        helper.write_to_file(
            {
                "PolicySummary": policy.get("PolicySummary"),
                "Content": json.loads(policy.get("Content")),
            },
            service_control_policies_path,
            helper.get_valid_filename(policy.get("PolicySummary").get("Name"))
            + ".json",
        )
        for policy in all_service_control_policies_in_org_with_policy_summary
    ]

    # Step 1 Save Attached policies
    accounts = {
        account.get("Id"): account.get("Name")
        for account in list_accounts_details.get("Accounts")
    }
    ous = get_organizational_units(root_id)  # list all OUs in org
    service_control_policies_path_for_target = helper.map_scp_path_for_target_name(
        all_files_in_environment_list, root_id
    )

    (
        service_control_policies_for_target,
        scp_name_for_each_target,
    ) = get_service_control_policies_for_target(ous | accounts, root_id)
    write_policies_to_target_yaml(
        service_control_policies_for_target, service_control_policies_path_for_target
    )

    # Step 2 Save Inherited policies
    for file_path in all_files_in_environment_list:
        if "_service_control_policies.yaml" in file_path:
            current_scp_path_list = file_path.split("/")
            root_org_scp_path = org_path + "/_service_control_policies.yaml"
            local_policy = [
                policy
                for policy in helper.read_yaml(root_org_scp_path)["Policies_Attached"]
            ]
            for i in range(len(current_scp_path_list)):
                # go through every OU in org structure
                if "_organizational_units" in current_scp_path_list[i]:
                    current_organizational_unit_index = current_scp_path_list.index(
                        current_scp_path_list[i + 1]
                    )
                    current_policy_path = (
                        SEP.join(
                            current_scp_path_list[:-current_organizational_unit_index]
                        )
                        + "/_service_control_policies.yaml"
                    )

                    # TODO change this to save as policy_name ===> source: Org_source
                    local_policy.extend(
                        [
                            attached_policy
                            for attached_policy in helper.read_yaml(
                                current_policy_path
                            )["Policies_Attached"]
                            if attached_policy not in local_policy
                        ]
                    )

                if (
                    file_path != root_org_scp_path
                    and "_service_control_policies.yaml" in current_scp_path_list[i]
                ):
                    helper.write_inherited_yaml(local_policy, file_path)
    # save initial set up
    helper.write_to_file(
        scp_name_for_each_target, policies_migration_path, "initial_state.yaml"
    )


def map_policy_name_to_id(org_ids_map, attached_Policies, policy_ids_map) -> dict:
    policies_to_apply = dict()
    for id, name in org_ids_map.items():
        if name in attached_Policies.keys():
            policies_to_apply[id] = [policy_ids_map[x] for x in attached_Policies[name]]
    return policies_to_apply


def write_migrations(attach_policies, detach_policies):
    policies_migration_path + "/migrations_to_apply"
    # target: policies

    for target, policy_list in attach_policies.items():
        # data, path, file_name
        for policy in policy_list:
            file_name = f"{ATTACH_POLICY}_{target}_{policy}"
            helper.write_to_file(
                "a", policies_migration_path + "/migrations_to_apply", file_name
            )


def make_migration_policies(role_arn) -> None:
    # 0 get initial state
    # 0.1 read for org state
    # 0.2 read for account state
    # 1. read current state by looking through _policies folders in organization
    # 1.1 read for org state
    # 1.2 read for account state

    with betterboto_client.CrossAccountClientContextManager(
        "organizations",
        role_arn,
        f"organizations",
    ) as organizations:
        list_accounts_response = organizations.list_accounts_single_page()
        list_roots_response = organizations.list_roots_single_page()
        root_id = list_roots_response.get("Roots")[0].get("Id")
        org_path = SEP.join(["environment", root_id])
        all_files_in_environment_list = helper.getListOfFiles(org_path)

    # read initial setup
    initial_scp_per_target_state = helper.read_yaml(
        policies_migration_path + "/initial_state.yaml"
    )
    current_policies_state = dict()
    attach_policies = dict()
    detach_policies = dict()

    print("all_files_in_environment_list", all_files_in_environment_list)
    for file_path in all_files_in_environment_list:
        if "_service_control_policies.yaml" in file_path:
            target_name = file_path.split("/")[-2]
            print(target_name)
            policies_list = helper.read_yaml(file_path)["Policies_Attached"]
            current_policies_state[target_name] = policies_list

    # 2 Compare migration state to current  state
    for key, value in current_policies_state.items():
        print("key", key)
        print("value", value)
        print("initial_scp_per_target_state", initial_scp_per_target_state)
        # find diff policy
        if value != initial_scp_per_target_state[key]:
            detached_policy_list = [
                item
                for item in initial_scp_per_target_state[key]
                if item not in current_policies_state[key]
            ]
            attach_policies_list = [
                item
                for item in current_policies_state[key]
                if item not in initial_scp_per_target_state[key]
            ]
            # make sure non empty values are not saved
            if detached_policy_list:
                detach_policies[key] = detached_policy_list
            if attach_policies_list:
                attach_policies[key] = attach_policies_list

    # 3 Create migration document summary
    helper.write_to_file(
        {
            "Attached_Policies": attach_policies,
            "Detached_Policies": detach_policies,
        },
        policies_migration_path,
        "migration_state_summary.yaml",
    )

    # 3 Create migration folder
    # map policy name to policy content
    policies_map = dict()
    for policy in os.listdir(service_control_policies_path):
        policies_map[policy.replace(".json", "")] = helper.read_json(
            SEP.join([service_control_policies_path, policy])
        )

    for target, policy_list in attach_policies.items():
        print(attach_policies.items())
        print("\n")
        print("target", target)
        print("\n")
        # data, path, file_name
        for policy in policy_list:
            file_name = f"{ATTACH_POLICY}_SCP_{policy}_TARGET_{target}.json"
            policies_map[policy]["Migration"] = {
                "Migration_Type": ATTACH_POLICY,
                "Target": target,
                "Policy_Name": policy,
                "Policy_Id": policies_map[policy].get("PolicySummary").get("Id"),
            }
            helper.write_to_file(
                policies_map[policy],
                policies_migration_path + "/migrations_to_apply",
                file_name,
            )

    for target, policy_list in detach_policies.items():
        # data, path, file_name
        for policy in policy_list:
            file_name = f"{DETACH_POLICY}_SCP_{policy}_TARGET_{target}.json"
            policies_map[policy]["Migration"] = {
                "Migration_Type": DETACH_POLICY,
                "Target": target,
                "Policy_Name": policy,
                "Policy_Id": policies_map[policy].get("PolicySummary").get("Id"),
            }
            helper.write_to_file(
                policies_map[policy],
                policies_migration_path + "/migrations_to_apply",
                file_name,
            )
    return


def apply_migration_policies(role_arn):
    click.echo("Updating state file")
    with betterboto_client.CrossAccountClientContextManager(
        "organizations",
        role_arn,
        f"organizations",
    ) as organizations:
        list_accounts_response = organizations.list_accounts_single_page()
        list_roots_response = organizations.list_roots_single_page()
        root_id = list_roots_response.get("Roots")[0].get("Id")
        org_path = SEP.join(["environment", root_id])
        all_files_in_environment_list = helper.getListOfFiles(org_path)

    # Step 1 Save Attached policies
    accounts = {
        account.get("Id"): account.get("Name")
        for account in list_accounts_response.get("Accounts")
    }
    ous = get_organizational_units(root_id)  # list all OUs in org

    org_ids_map = accounts | ous
    policy_ids_map = dict()

    # map SCP name to Ids
    for file_path in os.listdir(service_control_policies_path):
        policy = helper.read_json(SEP.join([service_control_policies_path, file_path]))[
            "PolicySummary"
        ]
        policy_ids_map[helper.get_valid_filename(policy["Name"])] = policy["Id"]

    # TODO make this in accordance with Eamonn's AWS Organized general way of doing things
    # so the user will be able to type in the file name and the migration wil be applied
    reverse_org_ids_map = dict((v, k) for k, v in org_ids_map.items())
    for migration_policy in os.listdir(make_individual_migration_policies_path):
        policy = helper.read_json(
            SEP.join([make_individual_migration_policies_path, migration_policy])
        ).get("Migration")

        policy_id = policy.get("Policy_Id")
        policy_name = policy.get("Policy_Name")
        target_name = policy.get("Target")
        target_id = reverse_org_ids_map[target_name]
        policy_type = policy.get("Migration_Type")

        try:
            org.attach_policy(
                PolicyId=policy_id, TargetId=target_id
            ) if policy_type == ATTACH_POLICY else org.detach_policy(
                PolicyId=policy_id, TargetId=target_id
            )
        except:
            print(
                f"Error when attempting to {policy_type} {policy_name} on target {target_name}."
            )
        else:
            print(
                f"Successfully performed {policy_type} {policy_name} on target {target_name}."
            )

    # Write history file
    # with open(policies_migration_path + "migration_history.yaml", "w") as outfile:
    #     yaml.dump(
    #         {
    #             f"Attached_Policies {datetime.now()}": attached_Policies,
    #             f"Detached_Policies {datetime.now()}": detached_Policies,
    #         },
    #         outfile,
    #         default_flow_style=False,
    #     )


def clean_up():
    for file_path in helper.getListOfFiles(policies_migration_path):
        if "policies.yaml" in file_path:
            print(f"Deleted {file_path} policy descriptions files")
            os.remove(file_path)


# TO DO List
# TODO add source on inherited policies
# extra features:
#   SCPs add new
#   TODO Extend to other policy types
# Important for functionality:
#   TODO Add Unattached Policies
#   TODO Add Inherited policies?
