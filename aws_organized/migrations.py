# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Callable, Tuple
from betterboto import client as betterboto_client

OU_CREATE = "OU_CREATE"
OU_CREATE_WITH_NON_EXISTENT_PARENT_OU = "OU_CREATE_WITH_NON_EXISTENT_PARENT_OU"
OU_RENAME = "OU_RENAME"

ACCOUNT_MOVE = "ACCOUNT_MOVE"
ACCOUNT_MOVE_WITH_NON_EXISTENT_PARENT_OU = "ACCOUNT_MOVE_WITH_NON_EXISTENT_PARENT_OU"

MigrationResult = Tuple[bool, str]

OK = "Ok"


def ou_create(role_arn: str, name: str, parent_id: str) -> MigrationResult:
    # with betterboto_client.Client('organizations') as organizations:
    #     organizations.create_organizational_unit(
    #         ParentId=parent_id,
    #         Name=name,
    #     )
    return True, OK


def ou_create_with_non_existent_parent_ou(
    role_arn: str, name: str, parent_ou_path: str
) -> bool:
    return True, OK


def ou_rename(role_arn: str, name: str, organizational_unit_id: str) -> bool:
    return True, OK


def account_move(
    role_arn: str, account_id: str, destination_path: str, source_parent_id: str
) -> bool:
    return True, OK


def account_move_with_non_existent_parent_ou(
    role_arn: str,
    account_id: str,
    source_parent_id: str,
    destination_path: str,
) -> bool:
    return True, OK


def get_function(migration_name) -> Callable[..., bool]:
    return {
        OU_CREATE: ou_create,
        OU_CREATE_WITH_NON_EXISTENT_PARENT_OU: ou_create_with_non_existent_parent_ou,
        OU_RENAME: ou_rename,
        ACCOUNT_MOVE: account_move,
        ACCOUNT_MOVE_WITH_NON_EXISTENT_PARENT_OU: account_move_with_non_existent_parent_ou,
    }.get(migration_name)
