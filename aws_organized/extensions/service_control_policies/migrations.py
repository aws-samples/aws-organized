from typing import Callable, Tuple
import json
import sys
import botocore

POLICY_ATTACH = "POLICY_ATTACH"
POLICY_DETAILS_UPDATE = "POLICY_DETAILS_UPDATE"
POLICY_CONTENT_UPDATE = "POLICY_CONTENT_UPDATE"
POLICY_CREATE = "POLICY_CREATE"

OK = "Ok"
MigrationResult = Tuple[bool, str]


def policy_details_update(
    client,
    id: str,
    name: str,
    description: str,
) -> MigrationResult:
    try:
        client.update_policy(
            PolicyId=id,
            Name=name,
            Description=description,
        )
    except botocore.exceptions.ClientError as error:
        message = error.response["Error"]["Message"]
        return False, message
    except:
        message = sys.exc_info()[0]
        return False, "{0}".format(message)
    return True, OK


def policy_content_update(client, id: str, content: str) -> MigrationResult:
    try:
        client.update_policy(
            PolicyId=id,
            Content=content,
        )
    except botocore.exceptions.ClientError as error:
        message = error.response["Error"]["Message"]
        return False, message
    except:
        message = sys.exc_info()[0]
        return False, "{0}".format(message)
    return True, OK


def policy_create(
    client,
    name: str,
    content: str,
) -> MigrationResult:
    try:
        client.create_policy(
            Content=content,
            Description="-",
            Name=name,
            Type="SERVICE_CONTROL_POLICY",
        )

    except botocore.exceptions.ClientError as error:
        message = error.response["Error"]["Message"]
        return False, message
    except:
        message = sys.exc_info()[0]
        return False, "{0}".format(message)
    return True, OK


def policy_attach(
    client,
    policy_id: str,
    target_id: str,
) -> MigrationResult:
    try:
        client.attach_policy(
            PolicyId=policy_id,
            TargetId=target_id,
        )

    except botocore.exceptions.ClientError as error:
        message = error.response["Error"]["Message"]
        return False, message
    except:
        message = sys.exc_info()[0]
        return False, "{0}".format(message)
    return True, OK


def get_function(migration_name) -> Callable[..., MigrationResult]:
    return {
        POLICY_DETAILS_UPDATE: policy_details_update,
        POLICY_CONTENT_UPDATE: policy_content_update,
        POLICY_CREATE: policy_create,
        POLICY_ATTACH: policy_attach,
    }.get(migration_name)
