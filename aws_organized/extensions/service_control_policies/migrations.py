from typing import Callable, Tuple


POLICY_ATTACH = "POLICY_ATTACH"
POLICY_DETAILS_UPDATE = "POLICY_DETAILS_UPDATE"
POLICY_CONTENT_UPDATE = "POLICY_CONTENT_UPDATE"
POLICY_CREATE = "POLICY_CREATE"

OK = "Ok"
MigrationResult = Tuple[bool, str]


def policy_details_update(
    client,
) -> MigrationResult:
    return True, OK


def policy_content_update(
    client,
) -> MigrationResult:
    return True, OK


def policy_create(
    client,
) -> MigrationResult:
    return True, OK


def policy_attach(
    client,
) -> MigrationResult:
    return True, OK


def get_function(migration_name) -> Callable[..., MigrationResult]:
    return {
        POLICY_DETAILS_UPDATE: policy_details_update,
        POLICY_CONTENT_UPDATE: policy_content_update,
        POLICY_CREATE: policy_create,
        POLICY_ATTACH: policy_attach,
    }.get(migration_name)
