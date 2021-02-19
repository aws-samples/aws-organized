# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os

from betterboto import client as betterboto_client

from boto3 import client

import yaml
import click
import logging
import sys
from . import migrations
from extensions.service_control_policies import service_control_policies
from datetime import datetime

logging.disable(sys.maxsize)

STATE_FILE = "state.yaml"
SERVICE_CONTROL_POLICY = "SERVICE_CONTROL_POLICY"
ORGANIZATIONAL_UNIT = "ORGANIZATIONAL_UNIT"
META_FILE_NAME = "_meta.yaml"
SEP = os.path.sep
SSM_PARAMETER_PREFIX = "/_aws-organized/migrations"

EXTENSION = "aws_organized"


def list_policies_for_target(organizations: client, id: str, filter) -> dict:
    return organizations.list_policies_for_target(
        TargetId=id,
        Filter=filter,
    ).get("Policies", [])


def describe_organizational_unit(organizations: client, id: str) -> dict:
    return organizations.describe_organizational_unit(OrganizationalUnitId=id).get(
        "OrganizationalUnit"
    )


def list_children(organizations: client, id: str, child_type: str) -> dict:
    return organizations.list_children_single_page(
        ParentId=id,
        ChildType=child_type,
    ).get("Children", [])


def get_service_control_policies_for_target(organizations: client, id: str) -> dict:
    service_control_policies_for_target = dict()
    for policy in list_policies_for_target(organizations, id, SERVICE_CONTROL_POLICY):
        service_control_policies_for_target[policy.get("Id")] = policy
    return service_control_policies_for_target


def get_children_details_filter_by_organizational_unit(
    organizations: client, id: str, by_name: dict, parent_path: str, by_id: dict
) -> dict:
    result = dict()
    organizational_units = list_children(organizations, id, ORGANIZATIONAL_UNIT)
    for organizational_unit in organizational_units:
        organizational_unit_id = organizational_unit.get("Id")

        details = describe_organizational_unit(organizations, organizational_unit_id)
        path = parent_path + "/" + details.get("Name")
        by_name[path] = details.get("Id")
        by_id[details.get("Id")] = dict(path=path, details=details)

        result[organizational_unit_id] = dict(
            details=details,
            parent_id=id,
            policies=dict(
                service_control_policies=get_service_control_policies_for_target(
                    organizations, organizational_unit_id
                ),
            ),
            organizational_units=get_children_details_filter_by_organizational_unit(
                organizations, organizational_unit_id, by_name, path, by_id
            ),
        )
    return result


def update_state(role_arn) -> None:
    click.echo("Updating state file")
    with betterboto_client.CrossAccountClientContextManager(
        "organizations",
        role_arn,
        f"organizations",
    ) as organizations:
        all_accounts = dict()
        result = dict(accounts=all_accounts)
        list_roots_response = organizations.list_roots_single_page()
        tree = dict()
        by_name = dict()
        by_id = dict()
        organizational_units = dict(tree=tree, by_name=by_name, by_id=by_id)
        click.echo("Getting organizational units")
        result["organizational_units"] = organizational_units
        for root in list_roots_response.get("Roots", []):
            root_id = str(root.get("Id"))
            details = dict(
                Type="Root",
                Id=root_id,
                Name="Root",
            )
            by_name["/"] = root_id
            by_id[root_id] = dict(path="/", details=details)
            tree[root_id] = dict(
                details=details,
                organizational_units=get_children_details_filter_by_organizational_unit(
                    organizations, root_id, by_name, "", by_id
                ),
                policies=dict(
                    service_control_policies=organizations.list_policies_for_target(
                        TargetId=root_id,
                        Filter=SERVICE_CONTROL_POLICY,
                    ).get("Policies", []),
                ),
            )

        with open(STATE_FILE, "w") as f:
            f.write(yaml.safe_dump(result))
        click.echo("Saved organizational units")

        click.echo("Getting accounts")
        accounts = organizations.list_accounts_single_page().get("Accounts", [])
        click.echo(f"Adding accounts: {len(accounts)}")
        counter = 1
        for account in accounts:
            account_id = account.get("Id")
            click.echo(f"Adding {account_id} ({counter} of {len(accounts)})")
            all_accounts[account_id] = dict(
                details=account,
                parents=organizations.list_parents_single_page(ChildId=account_id).get(
                    "Parents"
                ),
                policies=dict(
                    service_control_policies=organizations.list_policies_for_target(
                        TargetId=account_id,
                        Filter=SERVICE_CONTROL_POLICY,
                    ).get("Policies", []),
                ),
            )
            counter += 1
        with open(STATE_FILE, "w") as f:
            f.write(yaml.safe_dump(result))
        click.echo("Saved accounts")

        click.echo("Finished")
        return result


def write_details(details: dict, output_dir: str) -> None:
    details_file = SEP.join([output_dir, META_FILE_NAME])
    with open(details_file, "w") as f:
        f.write(yaml.safe_dump(details))


def write_organizational_units(unit: dict, output_dir: str) -> None:
    details = unit.get("details")
    if details.get("Name") == "Root":
        name = details.get("Id")
    else:
        name = details.get("Name")

    this_output_dir = SEP.join([output_dir, name, "_organizational_units"])
    os.makedirs(this_output_dir, exist_ok=True)

    write_details(details, SEP.join([output_dir, name]))

    for child_unit_id, child_unit in unit.get("organizational_units", {}).items():
        write_organizational_units(
            child_unit,
            this_output_dir,
        )


def import_organization(role_arn: str, root_id: str) -> None:
    update_state(role_arn)
    state = yaml.safe_load(open(STATE_FILE, "r").read())
    output_dir = "environment"
    organizational_units = state.get("organizational_units").get("tree")
    by_id = state.get("organizational_units").get("by_id")

    root = organizational_units.get(root_id)
    write_organizational_units(
        root,
        output_dir,
    )

    # TODO: partition the state file by org id
    for account_id, account in state.get("accounts").items():
        account_details = account.get("details")
        parent_ou_id = account.get("parents")[0].get("Id")
        parent_ou_path = by_id.get(parent_ou_id).get("path")

        output_path_parts = [output_dir, root_id]
        for parent in parent_ou_path.split("/"):
            if parent != "":
                output_path_parts += [
                    "_organizational_units",
                    parent,
                ]
        output_path_parts += [
            "_accounts",
            account_details.get("Name"),
        ]
        output_path = SEP.join(output_path_parts)

        os.makedirs(output_path, exist_ok=True)
        with open(
            f"{output_path}{SEP}{META_FILE_NAME}",
            "w",
        ) as f:
            f.write(yaml.safe_dump(account_details))


def write_migration(
    extension: str, root_id: str, migration_type: str, migration_params: dict
) -> None:
    now = datetime.now()
    timestamp = datetime.timestamp(now)
    migration_file_name = f"{timestamp}_{migration_type}.yaml"
    os.makedirs(
        SEP.join(["environment", root_id, "_migrations"]),
        exist_ok=True,
    )
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


def make_migrations(role_arn: str, root_id: str) -> None:
    os.makedirs(SEP.join(["environment", "migrations"]), exist_ok=True)
    with betterboto_client.CrossAccountClientContextManager(
        "organizations",
        role_arn,
        f"organizations",
    ) as organizations:
        make_migrations_for_organizational_units(root_id, organizations)
        make_migrations_for_accounts(root_id, organizations)


def make_migrations_for_accounts(root_id: str, organizations) -> None:
    """
    Creates migrations for the following account use cases:
      - move an account
      - - when the remote parent ou exists - ACCOUNT_MOVE
      - - when the remote parent ou does not exist - ACCOUNT_MOVE_WITH_NON_EXISTENT_PARENT_OU
    :param organizations:
    :return:
    """
    accounts = get_accounts_folders()
    for account_file_path in accounts:
        account_name = account_file_path.split(SEP)[-1]
        account_details = yaml.safe_load(
            open(f"{account_file_path}{SEP}{META_FILE_NAME}", "r").read()
        )
        list_parents_single_page_response = organizations.list_parents_single_page(
            ChildId=account_details.get("Id")
        ).get("Parents")
        if len(list_parents_single_page_response) != 1:
            raise Exception(
                f"{account_details.get('Id')} has {len(list_parents_single_page_response)} parents."
            )
        remote_parent_organizational_unit_ou_id = list_parents_single_page_response[
            0
        ].get("Id")

        parent_ou_path_details_file_path = SEP.join(
            account_file_path.split(SEP)[0:-2] + [META_FILE_NAME]
        )

        if os.path.exists(parent_ou_path_details_file_path):
            local_parent_ou_details = yaml.safe_load(
                open(parent_ou_path_details_file_path, "r").read()
            )
            local_parent_organizational_unit_ou_id = local_parent_ou_details.get("Id")

            if (
                local_parent_organizational_unit_ou_id
                != remote_parent_organizational_unit_ou_id
            ):
                write_migration(
                    EXTENSION,
                    root_id,
                    migrations.ACCOUNT_MOVE,
                    dict(
                        account_id=account_details.get("Id"),
                        source_parent_id=remote_parent_organizational_unit_ou_id,
                        destination_parent_id=local_parent_organizational_unit_ou_id,
                    ),
                )
        else:
            destination_path = SEP.join(
                [""] + parent_ou_path_details_file_path.split(SEP)[3:-1]
            ).replace(f"{SEP}_organizational_units", "")
            write_migration(
                EXTENSION,
                root_id,
                migrations.ACCOUNT_MOVE_WITH_NON_EXISTENT_PARENT_OU,
                dict(
                    account_id=account_details.get("Id"),
                    source_parent_id=remote_parent_organizational_unit_ou_id,
                    destination_path=destination_path,
                ),
            )


def get_parent_ou_id_for_details_file(details_file_path: str) -> str:
    parent_path = SEP.join(details_file_path.split(SEP)[0:-2])
    if os.path.exists(f"{parent_path}{SEP}{META_FILE_NAME}"):
        parent_details = yaml.safe_load(
            open(f"{parent_path}{SEP}{META_FILE_NAME}", "r").read()
        )
        if parent_details.get("Id"):
            return parent_details.get("Id")
    return None


def make_migrations_for_organizational_units(organizations, root_id: str) -> None:
    """
    Creates migrations for the following OU use cases:
      - add an ou
      - - where the remote parent exists - OU_CREATE
      - - where the remote parent does not exist yet - OU_CREATE_WITH_NON_EXISTENT_PARENT_OU
      - rename an ou
      - - where the remote ou existed already - OU_RENAME

    Does not support the following OU use cases:
      - delete an ou
      - - where the remote ou exists already
      - - where the remote ou does not exist already
      - move an ou
      - - where there is already a remote target ou
      - - where there is not already a remote target ou
      - - where there is already a remote parent ou
      - - where there is not already a remote parent ou

    :param organizations:
    :return:
    """
    organizational_units_folders = get_organizational_units_folders()
    for organizational_unit_folder in organizational_units_folders:
        if os.path.exists(SEP.join([organizational_unit_folder, META_FILE_NAME])):
            details = yaml.safe_load(
                open(
                    SEP.join([organizational_unit_folder, META_FILE_NAME]),
                    "r",
                ).read()
            )
            remote_name = (
                organizations.describe_organizational_unit(
                    OrganizationalUnitId=details.get("Id")
                )
                .get("OrganizationalUnit")
                .get("Name")
            )

            local_name = organizational_unit_folder.split(SEP)[-1]
            if remote_name != local_name:
                write_migration(
                    EXTENSION,
                    root_id,
                    migrations.OU_RENAME,
                    dict(
                        name=local_name,
                        organizational_unit_id=details.get("Id"),
                    ),
                )

        else:
            parent_organizational_unit_folder = SEP.join(
                organizational_unit_folder.split(SEP)[0:-2]
            )
            new_ou_name = organizational_unit_folder.split(SEP)[-1]
            if os.path.exists(
                SEP.join([parent_organizational_unit_folder, META_FILE_NAME])
            ):
                parent_id = yaml.safe_load(
                    open(
                        SEP.join([parent_organizational_unit_folder, META_FILE_NAME]),
                        "r",
                    ).read()
                ).get("Id")
                write_migration(
                    EXTENSION,
                    root_id,
                    migrations.OU_CREATE,
                    dict(name=new_ou_name, parent_id=parent_id),
                )
            else:
                parent_ou_path = "/".join(
                    [""]
                    + parent_organizational_unit_folder.replace(
                        "_organizational_units", ""
                    )
                    .replace(f"{SEP}{SEP}", SEP)
                    .split(SEP)[2:]
                )
                write_migration(
                    EXTENSION,
                    root_id,
                    migrations.OU_CREATE_WITH_NON_EXISTENT_PARENT_OU,
                    dict(name=new_ou_name, parent_ou_path=parent_ou_path),
                )


def get_organizational_units_folders() -> list:
    return [
        x[0]
        for x in os.walk("environment/")
        if x[0].split(SEP)[-2] == "_organizational_units"
    ]


def get_accounts_folders() -> list:
    return [x[0] for x in os.walk("environment/") if x[0].split(SEP)[-2] == "_accounts"]


def migrate(role_arn: str) -> None:
    with betterboto_client.CrossAccountClientContextManager(
        "ssm",
        role_arn,
        f"ssm",
    ) as ssm:
        for migration_file in sorted(os.listdir("environment/migrations")):
            migration_id = migration_file.split(SEP)[-1].replace(".yaml", "")

            try:
                ssm.get_parameter(Name=f"{SSM_PARAMETER_PREFIX}/{migration_id}")
                click.echo(f"Migration: {migration_id} already run")
            except ssm.exceptions.ParameterNotFound:
                click.echo(
                    f"Record of migration: {migration_id} being run not found, running now"
                )
                migration = yaml.safe_load(
                    open(f"environment/migrations/{migration_file}", "r").read()
                )
                migration_extension = migration.get("extension")
                migration_type = migration.get("migration_type")
                migration_params = migration.get("migration_params")

                if migration_extension == EXTENSION:
                    migration_function = migrations.get_function(migration_type)
                elif migration_extension == service_control_policies.EXTENSION:
                    migration_function = (
                        service_control_policies.migrations.get_function(migration_type)
                    )

                try:

                    with betterboto_client.CrossAccountClientContextManager(
                        "organizations",
                        role_arn=role_arn,
                        role_session_name="ou_create",
                    ) as client:
                        result = migration_function(client, **migration_params)
                        status = "Ok" if result else "Failed"
                except Exception as ex:
                    status = "Errored"

                print(f"{migration_id}: { status }")
                ssm.put_parameter(
                    Name=f"{SSM_PARAMETER_PREFIX}/{migration_id}",
                    Description=f"Migration run: {datetime.utcnow()}",
                    Value=status,
                    Type="String",
                    Tags=[
                        {"Key": "AWS-Organized:Actor", "Value": "Framework"},
                    ],
                )
