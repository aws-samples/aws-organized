# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Callable, Tuple
import yaml
import sys
import botocore
import os

REGISTER_DELEGATED_ADMINISTRATOR = "REGISTER_DELEGATED_ADMINISTRATOR"
DEREGISTER_DELEGATED_ADMINISTRATOR = "DEREGISTER_DELEGATED_ADMINISTRATOR"

OK = "Ok"
MigrationResult = Tuple[bool, str]


def register_delegated_administrator(
    root_id: str,
    client,
    account_id: str,
    service_principal: str,
) -> MigrationResult:
    try:
        client.register_delegated_administrator(
            AccountId=account_id,
            ServicePrincipal=service_principal,
        )
    except botocore.exceptions.ClientError as error:
        message = error.response["Error"]["Message"]
        return False, message
    except:
        message = sys.exc_info()[0]
        return False, "{0}".format(message)
    return True, OK


def deregister_delegated_administrator(
    root_id: str,
    client,
    account_id: str,
    service_principal: str,
) -> MigrationResult:
    try:
        client.deregister_delegated_administrator(
            AccountId=account_id,
            ServicePrincipal=service_principal,
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
        REGISTER_DELEGATED_ADMINISTRATOR: register_delegated_administrator,
        DEREGISTER_DELEGATED_ADMINISTRATOR: deregister_delegated_administrator,
    }.get(migration_name)
