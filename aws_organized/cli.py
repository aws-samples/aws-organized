# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os
import click
from aws_organized import helpers
from aws_organized import aws_organized
from aws_organized.extensions.service_control_policies import service_control_policies
from aws_organized.extensions.delegated_administrators import delegated_administrators
from betterboto import client as betterboto_client


@click.group()
def cli():
    """cli"""
    pass


@cli.command()
@click.argument("role_arn")
def make_migration_policies(role_arn) -> None:
    service_control_policies.make_migration_policies(role_arn)


@cli.command()
@click.argument("role_arn")
def apply_migration_policies(role_arn) -> None:
    service_control_policies.apply_migration_policies(role_arn)


@cli.command()
@click.argument("role_arn")
def import_organization(role_arn):
    with betterboto_client.CrossAccountClientContextManager(
        "organizations", role_arn, f"organizations"
    ) as organizations:
        for root in organizations.list_roots_single_page().get("Roots", []):
            os.makedirs(f"environment/{root.get('Id')}", exist_ok=True)
    roots = os.listdir("environment")
    for root_id in roots:
        if root_id in ["migrations", "Policies", "policies_migration"]:
            continue
        click.echo(f"Processing root_id: {root_id}")
        aws_organized.import_organization(role_arn, root_id)
        service_control_policies.import_organization_policies(role_arn, root_id)
        delegated_administrators.import_organization(role_arn, root_id)


@cli.command()
@click.option("--role-name", default="ImportOrganizationRole")
@click.option("--path", default="/AWSOrganized/")
@click.option("--assuming-resource", default="root")
@click.option("--output-format", default="yaml")
@click.argument("assuming-account-id")
def generate_import_organization_role_template(
    role_name: str,
    path: str,
    assuming_resource: str,
    output_format: str,
    assuming_account_id: str,
):
    t = helpers.generate_import_organization_role_template(
        role_name, path, assuming_account_id, assuming_resource
    )
    if output_format.lower() == "json":
        click.echo(t.to_json())
    else:
        click.echo(t.to_yaml())


@cli.command()
@click.option("--role-name", default="ImportOrganizationRole")
@click.option("--path", default="/AWSOrganized/")
@click.option("--assuming-resource", default="root")
@click.argument("assuming-account-id")
def provision_import_organization_role_stack(
    role_name: str, path: str, assuming_resource: str, assuming_account_id: str
):
    helpers.provision_import_organization_role_stack(
        role_name, path, assuming_account_id, assuming_resource
    )


@cli.command()
@click.argument("role_arn")
def make_migrations(role_arn):
    for root_id in os.listdir("environment"):
        if root_id in ["migrations", "Policies", "policies_migration"]:
            continue
        click.echo(f"Processing root_id: {root_id}")
        aws_organized.make_migrations(role_arn, root_id)
        service_control_policies.make_migrations(role_arn, root_id)
        delegated_administrators.make_migrations(role_arn, root_id)


@cli.command()
@click.option("--role-name", default="MakeMigrationsRole")
@click.option("--path", default="/AWSOrganized/")
@click.option("--assuming-resource", default="root")
@click.option("--output-format", default="yaml")
@click.argument("assuming-account-id")
def generate_make_migrations_role_template(
    role_name: str,
    path: str,
    assuming_resource: str,
    output_format: str,
    assuming_account_id: str,
):
    t = helpers.generate_make_migrations_role_template(
        role_name, path, assuming_account_id, assuming_resource
    )
    if output_format.lower() == "json":
        click.echo(t.to_json())
    else:
        click.echo(t.to_yaml())


@cli.command()
@click.option("--role-name", default="MakeMigrationsRole")
@click.option("--path", default="/AWSOrganized/")
@click.option("--assuming-resource", default="root")
@click.argument("assuming-account-id")
def provision_make_migrations_role_stack(
    role_name: str, path: str, assuming_resource: str, assuming_account_id: str
):
    helpers.provision_make_migrations_role_stack(
        role_name, path, assuming_account_id, assuming_resource
    )


@cli.command()
@click.option("--ssm-parameter-prefix", default="/-AWS-Organized")
@click.argument("role_arn")
def migrate(ssm_parameter_prefix: str, role_arn: str):
    for root_id in os.listdir("environment"):
        aws_organized.migrate(root_id, role_arn, ssm_parameter_prefix)


@cli.command()
@click.option("--role-name", default="MigrateRole")
@click.option("--path", default="/AWSOrganized/")
@click.option("--assuming-resource", default="root")
@click.option("--ssm-parameter-prefix", default="/-AWS-Organized")
@click.option("--output-format", default="yaml")
@click.argument("assuming-account-id")
def generate_migrate_role_template(
    role_name: str,
    path: str,
    assuming_resource: str,
    ssm_parameter_prefix: str,
    output_format: str,
    assuming_account_id: str,
):
    t = helpers.generate_migrate_role_template(
        role_name, path, assuming_account_id, assuming_resource, ssm_parameter_prefix
    )
    if output_format.lower() == "json":
        click.echo(t.to_json())
    else:
        click.echo(t.to_yaml(clean_up=True))


@cli.command()
@click.option("--role-name", default="MigrateRole")
@click.option("--path", default="/AWSOrganized/")
@click.option("--assuming-resource", default="root")
@click.option("--ssm-parameter-prefix", default="/-AWS-Organized")
@click.argument("assuming-account-id")
def provision_migrate_role_stack(
    role_name: str,
    path: str,
    assuming_resource: str,
    assuming_account_id: str,
    ssm_parameter_prefix: str,
):
    helpers.provision_migrate_role_stack(
        role_name, path, assuming_account_id, assuming_resource, ssm_parameter_prefix
    )


@cli.command()
@click.option("--codepipeline-role-name", default="CodePipelineRole")
@click.option("--codepipeline-role-path", default="/AWSOrganized/")
@click.option("--codebuild-role-name", default="CodeBuildRole")
@click.option("--codebuild-role-path", default="/AWSOrganized/")
@click.option("--ssm-parameter-prefix", default="/-AWS-Organized")
@click.option("--scm-provider", default="CodeCommit")
@click.option("--scm-connection-arn")
@click.option("--scm-full-repository-id", default="AWS-Organized-environment")
@click.option("--scm-branch-name", default="main")
@click.option("--scm-bucket-name")
@click.option("--scm-object-key", default="environment.zip")
@click.option("--scm-skip-creation-of-repo", default=False)
@click.option("--output_format", default="yaml")
@click.argument("migrate-role-arn")
def generate_codepipeline_template(
    codepipeline_role_name: str,
    codepipeline_role_path: str,
    codebuild_role_name: str,
    codebuild_role_path: str,
    ssm_parameter_prefix: str,
    scm_provider: str,
    scm_connection_arn: str,
    scm_full_repository_id: str,
    scm_branch_name: str,
    scm_bucket_name: str,
    scm_object_key: str,
    scm_skip_creation_of_repo: str,
    output_format: str,
    migrate_role_arn: str,
):
    t = helpers.generate_codepipeline_template(
        codepipeline_role_name,
        codepipeline_role_path,
        codebuild_role_name,
        codebuild_role_path,
        ssm_parameter_prefix,
        scm_provider,
        scm_connection_arn,
        scm_full_repository_id,
        scm_branch_name,
        scm_bucket_name,
        scm_object_key,
        scm_skip_creation_of_repo,
        migrate_role_arn,
    )
    if output_format.lower() == "json":
        click.echo(t.to_json())
    else:
        click.echo(t.to_yaml())


@cli.command()
@click.option("--codepipeline-role-name", default="AWSOrganizedCodePipelineRole")
@click.option("--codepipeline-role-path", default="/AWSOrganized/")
@click.option("--codebuild-role-name", default="AWSOrganizedCodeBuildRole")
@click.option("--codebuild-role-path", default="/AWSOrganized/")
@click.option("--ssm-parameter-prefix", default="/-AWS-Organized")
@click.option("--scm-provider", default="CodeCommit")
@click.option("--scm-connection-arn")
@click.option("--scm-full-repository-id", default="AWS-Organized-environment")
@click.option("--scm-branch-name", default="main")
@click.option("--scm-bucket-name")
@click.option("--scm-object-key")
@click.option("--scm-skip-creation-of-repo", default=False)
@click.argument("migrate-role-arn")
def provision_codepipeline_stack(
    codepipeline_role_name: str,
    codepipeline_role_path: str,
    codebuild_role_name: str,
    codebuild_role_path: str,
    ssm_parameter_prefix: str,
    scm_provider: str,
    scm_connection_arn: str,
    scm_full_repository_id: str,
    scm_branch_name: str,
    scm_bucket_name: str,
    scm_object_key: str,
    scm_skip_creation_of_repo: str,
    migrate_role_arn: str,
):
    helpers.provision_codepipeline_stack(
        codepipeline_role_name,
        codepipeline_role_path,
        codebuild_role_name,
        codebuild_role_path,
        ssm_parameter_prefix,
        scm_provider,
        scm_connection_arn,
        scm_full_repository_id,
        scm_branch_name,
        scm_bucket_name,
        scm_object_key,
        scm_skip_creation_of_repo,
        migrate_role_arn,
    )

@cli.command()
def prune_metadata():
    for root_id in os.listdir("environment"):
        if root_id in ["migrations", "Policies", "policies_migration"]:
            continue
        click.echo(f"Processing root_id: {root_id}")
        aws_organized.prune_metadata()
        service_control_policies.prune_metadata(root_id)
        delegated_administrators.prune_metadata(root_id)

if __name__ == "__main__":
    cli()
