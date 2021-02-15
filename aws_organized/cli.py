# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import click

from aws_organized import helpers
from aws_organized import aws_organized
from aws_organized_policies import aws_organized_policies


@click.group()
def cli():
    """cli"""
    pass


@cli.command()
@click.argument("role_arn")
def import_organization_policies(role_arn) -> None:
    aws_organized_policies.import_organization_policies(role_arn)


@cli.command()
@click.argument("role_arn")
def make_migration_policies(role_arn) -> None:
    aws_organized_policies.make_migration_policies(role_arn)


@cli.command()
@click.argument("role_arn")
def apply_migration_policies(role_arn) -> None:
    aws_organized_policies.apply_migration_policies(role_arn)


@cli.command()
@click.argument("role_arn")
def import_organization(role_arn):
    aws_organized.import_organization(role_arn)


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
    click.echo(
        helpers.generate_import_organization_role_template(
            role_name,
            path,
            assuming_account_id,
            assuming_resource,
            output_format.lower(),
        )
    )


@cli.command()
@click.option("--role-name", default="ImportOrganizationRole")
@click.option("--path", default="/AWSOrganized/")
@click.option("--assuming-resource", default="root")
@click.option("--output-format", default="yaml")
@click.argument("assuming-account-id")
def provision_import_organization_role_stack(
    role_name: str,
    path: str,
    assuming_resource: str,
    output_format: str,
    assuming_account_id: str,
):
    helpers.provision_import_organization_role_stack(
        role_name,
        path,
        assuming_account_id,
        assuming_resource,
        output_format.lower(),
    )


@cli.command()
@click.argument("role_arn")
def make_migrations(role_arn):
    aws_organized.make_migrations(role_arn)


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
    click.echo(
        helpers.generate_make_migrations_role_template(
            role_name,
            path,
            assuming_account_id,
            assuming_resource,
            output_format.lower(),
        )
    )


@cli.command()
@click.option("--role-name", default="MakeMigrationsRole")
@click.option("--path", default="/AWSOrganized/")
@click.option("--assuming-resource", default="root")
@click.option("--output-format", default="yaml")
@click.argument("assuming-account-id")
def provision_make_migrations_role_stack(
    role_name: str,
    path: str,
    assuming_resource: str,
    output_format: str,
    assuming_account_id: str,
):
    helpers.provision_make_migrations_role_stack(
        role_name,
        path,
        assuming_account_id,
        assuming_resource,
        output_format.lower(),
    )


@cli.command()
@click.argument("role_arn")
def migrate(role_arn):
    aws_organized.migrate(role_arn)


@cli.command()
@click.option("--role-name", default="MigrateRole")
@click.option("--path", default="/AWSOrganized/")
@click.option("--assuming-resource", default="root")
@click.option("--output-format", default="yaml")
@click.argument("assuming-account-id")
def generate_migrate_role_template(
    role_name: str,
    path: str,
    assuming_resource: str,
    output_format: str,
    assuming_account_id: str,
):
    click.echo(
        helpers.generate_migrate_role_template(
            role_name,
            path,
            assuming_account_id,
            assuming_resource,
            output_format.lower(),
        )
    )


@cli.command()
@click.option("--role-name", default="MigrateRole")
@click.option("--path", default="/AWSOrganized/")
@click.option("--assuming-resource", default="root")
@click.option("--output-format", default="yaml")
@click.argument("assuming-account-id")
def provision_migrate_role_stack(
    role_name: str,
    path: str,
    assuming_resource: str,
    output_format: str,
    assuming_account_id: str,
):
    helpers.provision_migrate_role_stack(
        role_name,
        path,
        assuming_account_id,
        assuming_resource,
        output_format.lower(),
    )


@cli.command()
@click.option("--output-format", default="yaml")
@click.option("--codepipeline-role-name", default="CodePipelineRole2")
@click.option("--codepipeline-role-path", default="/AWSOrganized/")
@click.option("--codebuild-role-name", default="CodeBuildRole2")
@click.option("--codebuild-role-path", default="/AWSOrganized/")
@click.option("--output_format", default="yaml")
@click.argument("migrate-role-arn")
def generate_codepipeline_template(
    codepipeline_role_name: str,
    codepipeline_role_path: str,
    codebuild_role_name: str,
    codebuild_role_path: str,
    output_format: str,
    migrate_role_arn: str,
):
    click.echo(
        helpers.generate_codepipeline_template(
            codepipeline_role_name,
            codepipeline_role_path,
            codebuild_role_name,
            codebuild_role_path,
            output_format.lower(),
            migrate_role_arn,
        )
    )


@cli.command()
@click.option("--output-format", default="yaml")
@click.option("--codepipeline-role-name", default="CodePipelineRole2")
@click.option("--codepipeline-role-path", default="/AWSOrganized/")
@click.option("--codebuild-role-name", default="CodeBuildRole2")
@click.option("--codebuild-role-path", default="/AWSOrganized/")
@click.option("--output-format", default="yaml")
@click.argument("migrate-role-arn")
def provision_codepipeline_stack(
    codepipeline_role_name: str,
    codepipeline_role_path: str,
    codebuild_role_name: str,
    codebuild_role_path: str,
    output_format: str,
    migrate_role_arn: str,
):
    helpers.provision_codepipeline_stack(
        codepipeline_role_name,
        codepipeline_role_path,
        codebuild_role_name,
        codebuild_role_path,
        output_format.lower(),
        migrate_role_arn,
    )


if __name__ == "__main__":
    cli()
