# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import click
from aws_organized import aws_organized


@click.group()
def cli():
    """cli"""
    pass


@cli.command()
@click.argument("role_arn")
def import_organization(role_arn):
    aws_organized.import_organization(role_arn)


@cli.command()
@click.argument("role_arn")
def make_migrations(role_arn):
    aws_organized.make_migrations(role_arn)


@cli.command()
@click.argument("role_arn")
def migrate(role_arn):
    aws_organized.migrate(role_arn)


if __name__ == "__main__":
    cli()
