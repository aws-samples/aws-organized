# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import glob
import collections
from datetime import datetime
import json
import yaml
import click
import os
from betterboto import client as betterboto_client
from . import migrations
from progress import bar

SERVICE_CONTROL_POLICY = "SERVICE_CONTROL_POLICY"
ORGANIZATIONAL_UNIT = "ORGANIZATIONAL_UNIT"
ACCOUNT = "ACCOUNT"
SEP = os.path.sep
EXTENSION = "delegated_administrators"


ServicePrincipal = "ServicePrincipal"


def save_all_policies_from_org(root_id: str, organizations) -> None:
    all_service_control_policies_in_org = organizations.list_policies_single_page(
        Filter=SERVICE_CONTROL_POLICY
    ).get("Policies")
    for policy in all_service_control_policies_in_org:
        described_policy = organizations.describe_policy(PolicyId=policy.get("Id")).get(
            "Policy"
        )
        policy_name = described_policy.get("PolicySummary").get("Name")
        path = f"environment/{root_id}/_policies/service_control_policies/{policy_name}"
        os.makedirs(path, exist_ok=True)
        open(f"{path}/policy.json", "w").write(
            json.dumps(json.loads(described_policy.get("Content")), indent=4)
        )
        del described_policy["Content"]
        open(f"{path}/_meta.yaml", "w").write(
            yaml.safe_dump(described_policy.get("PolicySummary"))
        )


def get_id_for_entity_from_path(entity_path: str) -> str:
    return yaml.safe_load(open(entity_path, "r").read()).get("Id")


def write_policy_for_given_entity_path(
    entity_path: str, application_method: str, policies: dict
) -> None:
    existing = dict()
    existing[application_method] = policies
    open(
        entity_path.replace("_meta.yaml", "_service_control_policies.yaml"), "w"
    ).write(yaml.safe_dump(existing))


def save_policies_for_entity(entity_path: str, organizations) -> None:
    entity_path_parts = entity_path.split(SEP)
    entity_type = entity_path_parts[-3]
    click.echo(f"{entity_type} - {entity_path}")
    policies = organizations.list_policies_for_target_single_page(
        TargetId=get_id_for_entity_from_path(entity_path), Filter=SERVICE_CONTROL_POLICY
    ).get("Policies")
    write_policy_for_given_entity_path(entity_path, "Attached", policies)


def save_policies_for_each_entity(entities: list, organizations) -> None:
    for entity in entities:
        save_policies_for_entity(entity, organizations)


def get_path_for_ou(root_id: str, ou: dict) -> str:
    ou_path = ou.get("path")
    parts = ou_path.split("/")[1:]
    file_path = ["environment", root_id]
    for part in parts:
        file_path.append("_organizational_units")
        file_path.append(part)
    return SEP.join(file_path)


def save_targets_for_policy(root_id, organizations) -> None:
    policies = glob.glob(
        f"environment/{root_id}/_policies/service_control_policies/*/*.yaml"
    )
    state = yaml.safe_load(open("state.yaml", "r").read())
    progress = bar.IncrementalBar("Importing policies", max=len(policies))
    for policy_file in policies:
        progress.next()
        policy = yaml.safe_load(open(policy_file, "r").read())
        policy_id = policy.get("Id")
        targets = organizations.list_targets_for_policy_single_page(
            PolicyId=policy_id
        ).get("Targets", [])
        for target in targets:
            inherited = list()
            if target.get("Type") == ACCOUNT:
                account = (
                    state.get("accounts").get(target.get("TargetId")).get("details")
                )
                attached = glob.glob(
                    f"environment/{root_id}/**/{account.get('Name')}/_meta.yaml",
                    recursive=True,
                )
            elif target.get("Type") == ORGANIZATIONAL_UNIT:
                ou = (
                    state.get("organizational_units")
                    .get("by_id")
                    .get(target.get("TargetId"))
                )
                path_to_ou = get_path_for_ou(root_id, ou)
                attached = glob.glob(f"{path_to_ou}/_meta.yaml")
                inherited += glob.glob(
                    f"{path_to_ou}/_accounts/**/_meta.yaml", recursive=True
                )
                inherited += glob.glob(
                    f"{path_to_ou}/_organizational_units/**/_meta.yaml", recursive=True
                )
            elif target.get("Type") == "ROOT":
                attached = glob.glob(
                    f"environment/{root_id}/_meta.yaml", recursive=True
                )
                inherited += glob.glob(
                    f"environment/{root_id}/_meta.yaml", recursive=True
                )
            else:
                raise Exception(f"Not handled type: {target.get('Type')}")
            if attached:
                assert (
                    len(attached) == 1
                ), f"mapping to attached entity found {len(attached)} entities for {target}"
                attached = attached[0]
                output_path = attached.replace(
                    "_meta.yaml", "_service_control_policies.yaml"
                )
                output = dict(Attached=list(), Inherited=list())
                if os.path.exists(output_path):
                    output = yaml.safe_load(open(output_path, "r").read())
                output["Attached"].append(policy)
                open(output_path, "w").write(yaml.safe_dump(output))
                for thing in inherited:
                    output_path = thing.replace(
                        "_meta.yaml", "_service_control_policies.yaml"
                    )
                    output = dict(Attached=list(), Inherited=list())
                    if os.path.exists(output_path):
                        output = yaml.safe_load(open(output_path, "r").read())
                    i = dict(Source=target.get("Name"))
                    i.update(policy)
                    output["Inherited"].append(i)
                    open(output_path, "w").write(yaml.safe_dump(output))
    progress.finish()


def remove_any_existing_records(root_id: str) -> None:
    policies = glob.glob(
        f"environment/{root_id}/**/_delegated_administrators.yaml", recursive=True
    )
    for policy in policies:
        os.remove(policy)


def import_organization(role_arn, root_id) -> None:
    remove_any_existing_records(root_id)
    with betterboto_client.CrossAccountClientContextManager(
        "organizations", role_arn, f"organizations"
    ) as organizations:
        delegated_administrators = (
            organizations.list_delegated_administrators_single_page().get(
                "DelegatedAdministrators", []
            )
        )
        progress = bar.IncrementalBar(
            "Importing Delegated Administrators", max=len(delegated_administrators)
        )
        for delegated_administrator in delegated_administrators:
            progress.next()
            account_id = delegated_administrator.get("Id")
            account_name = delegated_administrator.get("Name")
            delegated_services = (
                organizations.list_delegated_services_for_account_single_page(
                    AccountId=account_id
                ).get("DelegatedServices")
            )

            account_file = glob.glob(
                f"environment/{root_id}/**/{account_name}/_meta.yaml",
                recursive=True,
            )
            assert (
                len(account_file) == 1
            ), "found more or less than 1 account_meta file when searching by name"
            delegated_administrators_file = account_file[0].replace(
                "_meta", "_delegated_administrators"
            )
            open(delegated_administrators_file, "w").write(
                yaml.safe_dump(delegated_services)
            )


def write_migration(
    extension: str, root_id: str, migration_type: str, migration_params: dict
) -> None:
    now = datetime.now()
    timestamp = datetime.timestamp(now)
    migration_file_name = f"{timestamp}_{migration_type}.yaml"
    os.makedirs(SEP.join(["environment", root_id, "_migrations"]), exist_ok=True)
    with open(
        SEP.join(["environment", root_id, "_migrations", migration_file_name]), "w"
    ) as f:
        f.write(
            yaml.safe_dump(
                dict(
                    extension=extension,
                    migration_type=migration_type,
                    migration_params=migration_params,
                )
            )
        )


def check_attachment(root_id: str, policy_file_path: str, organizations) -> None:
    local_policies = yaml.safe_load(open(policy_file_path, "r").read())
    meta = yaml.safe_load(
        open(
            policy_file_path.replace("_service_control_policies.yaml", "_meta.yaml"),
            "r",
        ).read()
    )
    remote_policies = organizations.list_policies_for_target_single_page(
        TargetId=meta.get("Id"), Filter=SERVICE_CONTROL_POLICY
    ).get("Policies")
    for local_policy in local_policies.get("Attached", []):
        found = False
        for remote_policy in remote_policies:
            if local_policy.get("Name") == remote_policy.get("Name"):
                found = True
        if not found:
            write_migration(
                EXTENSION,
                root_id,
                migrations.POLICY_ATTACH,
                dict(policy_name=local_policy.get("Name"), target_id=meta.get("Id")),
            )


def check_existing(root_id: str, organizations) -> None:
    administrators = glob.glob(
        f"environment/{root_id}/**/_delegated_administrators.yaml", recursive=True
    )
    for administrator in administrators:
        local_delegated = yaml.safe_load(open(administrator, "r").read())
        account_details = yaml.safe_load(
            open(
                administrator.replace("_delegated_administrators", "_meta"), "r"
            ).read()
        )
        try:
            response = organizations.list_delegated_services_for_account_single_page(
                AccountId=account_details.get("Id")
            )
            remote_delegated_as_dict = dict()
            for delegated_service in response.get("DelegatedServices", []):
                remote_delegated_as_dict[
                    delegated_service.get(ServicePrincipal)
                ] = delegated_service

            local_delegated_as_dict = dict()
            for administrator_detail in local_delegated:
                local_delegated_as_dict[
                    administrator_detail.get(ServicePrincipal)
                ] = administrator_detail
                if (
                    remote_delegated_as_dict.get(
                        administrator_detail.get(ServicePrincipal)
                    )
                    is None
                ):
                    write_migration(
                        EXTENSION,
                        root_id,
                        migrations.REGISTER_DELEGATED_ADMINISTRATOR,
                        dict(
                            account_id=account_details.get("Id"),
                            service_principal=administrator_detail.get(
                                ServicePrincipal
                            ),
                        ),
                    )
            for delegated_service in response.get("DelegatedServices", []):
                if (
                    local_delegated_as_dict.get(delegated_service.get(ServicePrincipal))
                    is None
                ):
                    write_migration(
                        EXTENSION,
                        root_id,
                        migrations.DEREGISTER_DELEGATED_ADMINISTRATOR,
                        dict(
                            account_id=account_details.get("Id"),
                            service_principal=delegated_service.get(ServicePrincipal),
                        ),
                    )

        except organizations.exceptions.AccountNotRegisteredException:
            for administrator_detail in local_delegated:
                write_migration(
                    EXTENSION,
                    root_id,
                    migrations.REGISTER_DELEGATED_ADMINISTRATOR,
                    dict(
                        account_id=account_details.get("Id"),
                        service_principal=administrator_detail.get(ServicePrincipal),
                    ),
                )


def make_migrations(role_arn: str, root_id: str) -> None:
    with betterboto_client.CrossAccountClientContextManager(
        "organizations", role_arn, f"organizations"
    ) as organizations:
        check_existing(root_id, organizations)



def prune_metadata(root_id: str) -> None:
    policies = glob.glob(
        f"environment/{root_id}/**/_delegated_administrators.yaml", recursive=True
    )
    progress = bar.IncrementalBar(
        "Pruning Delegated Administrator metadata", max=len(policies)
    )
    for policy in policies:
        progress.next()
        p = yaml.safe_load(open(policy, 'r').read())
        new_delegated_administrators = list()
        for a in p:
            new_delegated_administrators.append(dict(ServicePrincipal=a.get("ServicePrincipal")))
        open(policy, 'w').write(yaml.safe_dump(new_delegated_administrators))
    progress.finish()
