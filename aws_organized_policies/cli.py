import click
from aws_organized_policies import aws_organized_policies


@click.group()
def cli():
    """cli for pipeline tools"""
    pass




@cli.command()
def make_migrations() -> None:
    print(aws_organized_policies.make_migrations())


@cli.command()
def apply_migrations() -> None:
    print(aws_organized_policies.apply_migrations())


@cli.command()
def clean_up() -> None:
    print(aws_organized_policies.clean_up())


""" 

@cli.command()
def write_policies() -> None:
    print(scp_org.write_policies())


@cli.command()
def read_policies() -> None:
    print(scp_org.read_policies())


create migration
execute organisation

@cli.command()
def foo() -> None:
    print("bar")


@cli.command()
def who_am_i() -> None:
    print(scp_demo.who_am_i())


@cli.command()
def how_many_buckets() -> None:
    print(scp_demo.how_many_buckets())


@cli.command()
def how_many_accounts() -> None:
    print(scp_org.get_client())


@cli.command()
def get_all_policies() -> None:
    print(scp_org.get_policies())

"""
