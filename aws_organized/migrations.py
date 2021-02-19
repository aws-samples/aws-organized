# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import sys
from typing import Callable, Tuple
from betterboto import client as betterboto_client
import botocore

OU_CREATE = "OU_CREATE"
OU_CREATE_WITH_NON_EXISTENT_PARENT_OU = "OU_CREATE_WITH_NON_EXISTENT_PARENT_OU"
OU_RENAME = "OU_RENAME"

ACCOUNT_MOVE = "ACCOUNT_MOVE"
ACCOUNT_MOVE_WITH_NON_EXISTENT_PARENT_OU = "ACCOUNT_MOVE_WITH_NON_EXISTENT_PARENT_OU"

MigrationResult = Tuple[bool, str]

OK = "Ok"


def ou_create(client, name: str, parent_id: str) -> MigrationResult:
    try:
        client.create_organizational_unit(
            ParentId=parent_id,
            Name=name,
        )
    except botocore.exceptions.ClientError as error:
        message = error.response["Error"]["Message"]
        return False, message
    except:
        message = sys.exc_info()[0]
        return False, "{0}".format(message)
    return True, OK


def ou_create_with_non_existent_parent_ou(
    client, name: str, parent_ou_path: str
) -> MigrationResult:
    try:
        parent_id = client.convert_path_to_ou(parent_ou_path)
        return ou_create(client=client, name=name, parent_id=parent_id)
    except botocore.exceptions.ClientError as error:
        message = error.response["Error"]["Message"]
        return False, message
    except:
        message = sys.exc_info()[0]
        return False, "{0}".format(message)


def ou_rename(client, name: str, organizational_unit_id: str) -> MigrationResult:
    try:
        client.update_organizational_unit(
            OrganizationalUnitId=organizational_unit_id,
            Name=name,
        )
        return True, OK
    except botocore.exceptions.ClientError as error:
        message = error.response["Error"]["Message"]
        return False, message
    except:
        message = sys.exc_info()[0]
        return False, "{0}".format(message)


def account_move(
    client, account_id: str, destination_parent_id: str, source_parent_id: str
) -> MigrationResult:
    try:
        client.move_account(
            AccountId=account_id,
            SourceParentId=source_parent_id,
            DestinationParentId=destination_parent_id,
        )
        return True, OK
    except botocore.exceptions.ClientError as error:
        message = error.response["Error"]["Message"]
        return False, message
    except:
        message = sys.exc_info()[0]
        return False, "{0}".format(message)


def account_move_with_non_existent_parent_ou(
    client,
    account_id: str,
    source_parent_id: str,
    destination_path: str,
) -> MigrationResult:
    try:
        destination_parent_id = client.convert_path_to_ou(destination_path)
        return account_move(
            client=client,
            account_id=account_id,
            destination_parent_id=destination_parent_id,
            source_parent_id=source_parent_id,
        )
    except botocore.exceptions.ClientError as error:
        message = error.response["Error"]["Message"]
        return False, message
    except:
        message = sys.exc_info()[0]
        return False, "{0}".format(message)


def get_function(migration_name) -> Callable[..., MigrationResult]:
    return {
        OU_CREATE: ou_create,
        OU_CREATE_WITH_NON_EXISTENT_PARENT_OU: ou_create_with_non_existent_parent_ou,
        OU_RENAME: ou_rename,
        ACCOUNT_MOVE: account_move,
        ACCOUNT_MOVE_WITH_NON_EXISTENT_PARENT_OU: account_move_with_non_existent_parent_ou,
    }.get(migration_name)
