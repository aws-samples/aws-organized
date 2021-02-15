import glob
from datetime import datetime

import json
import yaml
import click
import os
from betterboto import client as betterboto_client
from . import migrations

SERVICE_CONTROL_POLICY = "SERVICE_CONTROL_POLICY"
ORGANIZATIONAL_UNIT = "ORGANIZATIONAL_UNIT"
ACCOUNT = "ACCOUNT"
SEP = os.path.sep


def save_all_policies_from_org(root_id: str, organizations) -> None:  # done maybe
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
        open(
            f"{path}/policy.json",
            "w",
        ).write(json.dumps(json.loads(described_policy.get("Content")), indent=4))
        del described_policy["Content"]
        open(
            f"{path}/_meta.yaml",
            "w",
        ).write(yaml.safe_dump(described_policy.get("PolicySummary")))


def get_id_for_entity_from_path(entity_path: str) -> str:  # done
    return yaml.safe_load(open(entity_path, "r").read()).get("Id")


def write_policy_for_given_entity_path(  # done
    entity_path: str, application_method: str, policies: dict
) -> None:
    existing = dict()
    existing[application_method] = policies
    open(
        entity_path.replace("_meta.yaml", "_service_control_policies.yaml"), "w"
    ).write(yaml.safe_dump(existing))


def save_policies_for_entity(entity_path: str, organizations) -> None:  # done
    entity_path_parts = entity_path.split(SEP)
    entity_type = entity_path_parts[-3]
    click.echo(f"{entity_type} - {entity_path}")
    policies = organizations.list_policies_for_target_single_page(
        TargetId=get_id_for_entity_from_path(entity_path),
        Filter=SERVICE_CONTROL_POLICY,
    ).get("Policies")
    write_policy_for_given_entity_path(entity_path, "Attached", policies)


def save_policies_for_each_entity(entities: list, organizations) -> None:  # done
    for entity in entities:
        save_policies_for_entity(entity, organizations)


def save_targets_for_policy(root_id, organizations) -> None:  # done
    policies = glob.glob(
        f"environment/{root_id}/_policies/service_control_policies/*/*.yaml"
    )
    state = yaml.safe_load(open("state.yaml", "r").read())
    for policy_file in policies:
        click.echo("looking at")
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
                    .get("details")
                )
                attached = glob.glob(
                    f"environment/{root_id}/**/{ou.get('Name')}/_meta.yaml",
                    recursive=True,
                )
                inherited += glob.glob(
                    f"environment/{root_id}/**/{ou.get('Name')}/_accounts/*/_meta.yaml",
                    recursive=True,
                )
                inherited += glob.glob(
                    f"environment/{root_id}/**/{ou.get('Name')}/_organizational_units/**/_meta.yaml",
                    recursive=True,
                )
            elif target.get("Type") == "ROOT":
                attached = glob.glob(
                    f"environment/{root_id}/_meta.yaml",
                    recursive=True,
                )
                inherited += glob.glob(
                    f"environment/{root_id}/_meta.yaml",
                    recursive=True,
                )

            else:
                raise Exception(f"Not handled type: {target.get('Type')}")

            if attached:
                assert len(attached) == 1
                attached = attached[0]
                output_path = attached.replace(
                    "_meta.yaml", "_service_control_policies.yaml"
                )
                output = dict(
                    Attached=list(),
                    Inherited=list(),
                )
                if os.path.exists(output_path):
                    output = yaml.safe_load(open(output_path, "r").read())
                output["Attached"].append(policy)
                open(output_path, "w").write(yaml.safe_dump(output))

                for thing in inherited:
                    output_path = thing.replace(
                        "_meta.yaml", "_service_control_policies.yaml"
                    )
                    output = dict(
                        Attached=list(),
                        Inherited=list(),
                    )
                    if os.path.exists(output_path):
                        output = yaml.safe_load(open(output_path, "r").read())
                    i = dict(Source=target.get("Name"))
                    i.update(policy)
                    output["Inherited"].append(i)
                    open(output_path, "w").write(yaml.safe_dump(output))


def remove_any_existing_policy_records(root_id: str) -> None:  # done
    policies = glob.glob(
        f"environment/{root_id}/**/_service_control_policies.yaml", recursive=True
    )
    for policy in policies:
        os.remove(policy)


def import_organization_policies(role_arn, root_id) -> None:  # done
    click.echo("Updating state file")
    with betterboto_client.CrossAccountClientContextManager(
        "organizations",
        role_arn,
        f"organizations",
    ) as organizations:
        remove_any_existing_policy_records(root_id)
        save_all_policies_from_org(root_id, organizations)
        save_targets_for_policy(root_id, organizations)


def check_policies(root_id: str, organizations) -> None:
    scps_path = (
        f"environment/{root_id}/_policies/service_control_policies/*/policy.json"
    )
    for policy_content_path in glob.glob(scps_path):
        policy_file_path = policy_content_path.replace("policy.json", "_meta.yaml")
        if os.path.exists(policy_file_path):
            local_policy = yaml.safe_load(open(policy_file_path, "r").read())
            p = organizations.describe_policy(PolicyId=local_policy.get("Id")).get(
                "Policy"
            )
            remote_policy = p.get("PolicySummary")
            if local_policy.get("Name") != remote_policy.get(
                "Name"
            ) or local_policy.get("Description") != remote_policy.get("Description"):
                write_migration(
                    root_id,
                    migrations.POLICY_DETAILS_UPDATE,
                    dict(
                        id=local_policy.get("Id"),
                        name=local_policy.get("Name"),
                        description=local_policy.get("Description"),
                    ),
                )
            local_policy_content = json.dumps(
                json.loads(open(policy_content_path, "r").read())
            )
            if local_policy_content != p.get("Content"):
                write_migration(
                    root_id,
                    migrations.POLICY_CONTENT_UPDATE,
                    dict(
                        id=local_policy.get("Id"),
                        content=local_policy_content,
                    ),
                )
        else:
            local_policy_content = json.dumps(
                json.loads(open(policy_content_path, "r").read())
            )
            write_migration(
                root_id,
                migrations.POLICY_CREATE,
                dict(
                    name=policy_file_path.split(SEP)[-2],
                    content=local_policy_content,
                ),
            )


def write_migration(root_id: str, migration_type: str, migration_params: dict) -> None:
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
            if local_policy.get("Id") == remote_policy.get("Id"):
                found = True
        if not found:
            write_migration(
                root_id,
                migrations.POLICY_ATTACH,
                dict(
                    policy_id=local_policy.get("Id"),
                    target_id=meta.get("Id"),
                ),
            )


def check_attachments(root_id: str, organizations) -> None:
    policies = glob.glob(
        f"environment/{root_id}/**/_service_control_policies.yaml", recursive=True
    )
    for policy_file_path in policies:
        check_attachment(root_id, policy_file_path, organizations)


def make_migration_policies(role_arn: str, root_id: str) -> None:
    with betterboto_client.CrossAccountClientContextManager(
        "organizations",
        role_arn,
        f"organizations",
    ) as organizations:
        check_policies(root_id, organizations)
        check_attachments(root_id, organizations)
