import troposphere
import yaml
from awacs import (
    organizations as awacs_organizations,
    aws,
    sts as awacs_sts,
)
import pkg_resources

from awacs.iam import ARN as IAM_ARN
from troposphere import iam, s3, codebuild, codecommit, codepipeline, ssm
from betterboto import client as betterboto_client


def generate_role_template(
    command: str,
    actions: list,
    role_name: str,
    path: str,
    assuming_account_id: str,
    assuming_resource: str,
    output_format: str,
) -> str:
    t = troposphere.Template()
    t.description = f"Role used to run the {command} command"

    t.add_resource(
        iam.Role(
            title="role",
            RoleName=role_name,
            Path=path,
            Policies=[
                iam.Policy(
                    PolicyName=f"{command}-permissions",
                    PolicyDocument=aws.PolicyDocument(
                        Version="2012-10-17",
                        Id=f"{command}-permissions",
                        Statement=[
                            aws.Statement(
                                Sid="1",
                                Effect=aws.Allow,
                                Action=actions,
                                Resource=["*"],
                            ),
                        ],
                    ),
                )
            ],
            AssumeRolePolicyDocument=aws.Policy(
                Version="2012-10-17",
                Id="AllowAssume",
                Statement=[
                    aws.Statement(
                        Sid="1",
                        Effect=aws.Allow,
                        Principal=aws.Principal(
                            "AWS", [IAM_ARN(assuming_resource, "", assuming_account_id)]
                        ),
                        Action=[awacs_sts.AssumeRole],
                    ),
                ],
            ),
        )
    )

    if output_format == "json":
        return t.to_json()
    else:
        return t.to_yaml()


def generate_import_organization_role_template(
    role_name: str,
    path: str,
    assuming_account_id: str,
    assuming_resource: str,
    output_format: str,
) -> str:
    return generate_role_template(
        "import-organizations",
        [
            awacs_organizations.ListRoots,
            awacs_organizations.ListPoliciesForTarget,
            awacs_organizations.ListAccounts,
            awacs_organizations.ListChildren,
            awacs_organizations.DescribeOrganizationalUnit,
            awacs_organizations.ListParents,
            awacs_organizations.ListPolicies,
            awacs_organizations.DescribePolicy,
            awacs_organizations.ListTargetsForPolicy,
        ],
        role_name,
        path,
        assuming_account_id,
        assuming_resource,
        output_format,
    )


def provision_stack(stack_name_suffix: str, template: str) -> None:
    with betterboto_client.ClientContextManager(
        "cloudformation",
    ) as cloudformation:
        cloudformation.create_or_update(
            StackName=f"AWSOrganized-{stack_name_suffix}",
            TemplateBody=template,
            Capabilities=["CAPABILITY_NAMED_IAM"],
        )


def provision_import_organization_role_stack(
    role_name: str,
    path: str,
    assuming_account_id: str,
    assuming_resource: str,
    output_format: str,
) -> None:
    template = generate_import_organization_role_template(
        role_name,
        path,
        assuming_account_id,
        assuming_resource,
        output_format,
    )
    provision_stack("import-organization-role", template)


def generate_make_migrations_role_template(
    role_name: str,
    path: str,
    assuming_account_id: str,
    assuming_resource: str,
    output_format: str,
) -> str:
    return generate_role_template(
        "make-migrations",
        [
            awacs_organizations.DescribeOrganizationalUnit,
            awacs_organizations.ListParents,
            awacs_organizations.DescribePolicy,
            awacs_organizations.ListPoliciesForTarget,
        ],
        role_name,
        path,
        assuming_account_id,
        assuming_resource,
        output_format,
    )


def provision_make_migrations_role_stack(
    role_name: str,
    path: str,
    assuming_account_id: str,
    assuming_resource: str,
    output_format: str,
) -> None:
    template = generate_make_migrations_role_template(
        role_name,
        path,
        assuming_account_id,
        assuming_resource,
        output_format,
    )
    provision_stack("make-migrations-role", template)


def generate_migrate_role_template(
    role_name: str,
    path: str,
    assuming_account_id: str,
    assuming_resource: str,
    output_format: str,
) -> str:
    return generate_role_template(
        "migrate",
        [
            awacs_organizations.CreateOrganizationalUnit,
            awacs_organizations.UpdateOrganizationalUnit,
            awacs_organizations.MoveAccount,
            awacs_organizations.CreatePolicy,
            awacs_organizations.UpdatePolicy,
            awacs_organizations.AttachPolicy,
        ],
        role_name,
        path,
        assuming_account_id,
        assuming_resource,
        output_format,
    )


def provision_migrate_role_stack(
    role_name: str,
    path: str,
    assuming_account_id: str,
    assuming_resource: str,
    output_format: str,
) -> None:
    template = generate_migrate_role_template(
        role_name,
        path,
        assuming_account_id,
        assuming_resource,
        output_format,
    )
    provision_stack("migrate-role", template)


def generate_codepipeline_template(
    codepipeline_role_name: str,
    codepipeline_role_path: str,
    codebuild_role_name: str,
    codebuild_role_path: str,
    ssm_parameter_prefix: str,
    output_format: str,
    migrate_role_arn: str,
) -> str:
    version = pkg_resources.get_distribution("aws-organized").version
    t = troposphere.Template()
    t.set_description(
        "CICD template that runs aws organized migrate for the given branch of the given repo"
    )

    project_name = "AWSOrganized-Migrate"
    repository_name = "AWS-Organized-environment"

    repo = t.add_resource(
        codecommit.Repository("Repository", RepositoryName=repository_name)
    )

    artifact_store = t.add_resource(
        s3.Bucket(
            "ArtifactStore",
            BucketEncryption=s3.BucketEncryption(
                ServerSideEncryptionConfiguration=[
                    s3.ServerSideEncryptionRule(
                        ServerSideEncryptionByDefault=s3.ServerSideEncryptionByDefault(
                            SSEAlgorithm="AES256"
                        )
                    )
                ]
            ),
        )
    )

    codepipeline_role = t.add_resource(
        iam.Role(
            "CodePipelineRole",
            RoleName=codepipeline_role_name,
            Path=codepipeline_role_path,
            ManagedPolicyArns=[
                "arn:aws:iam::aws:policy/AdministratorAccess",
            ],
            AssumeRolePolicyDocument=aws.PolicyDocument(
                Version="2012-10-17",
                Statement=[
                    aws.Statement(
                        Effect=aws.Allow,
                        Action=[awacs_sts.AssumeRole],
                        Principal=aws.Principal(
                            "Service", ["codepipeline.amazonaws.com"]
                        ),
                    ),
                ],
            ),
        )
    )

    codebuild_role = t.add_resource(
        iam.Role(
            "CodeBuildRole",
            RoleName=codebuild_role_name,
            Path=codebuild_role_path,
            ManagedPolicyArns=[
                "arn:aws:iam::aws:policy/AdministratorAccess",
            ],
            AssumeRolePolicyDocument=aws.PolicyDocument(
                Version="2012-10-17",
                Statement=[
                    aws.Statement(
                        Effect=aws.Allow,
                        Action=[awacs_sts.AssumeRole],
                        Principal=aws.Principal("Service", ["codebuild.amazonaws.com"]),
                    ),
                ],
            ),
        )
    )

    version_parameter = ssm.Parameter(
        "versionparameter",
        Name=f"{ssm_parameter_prefix}/version",
        Type="String",
        Value=version,
    )

    t.add_resource(version_parameter)

    project = t.add_resource(
        codebuild.Project(
            "AWSOrganizedMigrate",
            Artifacts=codebuild.Artifacts(Type="CODEPIPELINE"),
            Environment=codebuild.Environment(
                ComputeType="BUILD_GENERAL1_SMALL",
                Image="aws/codebuild/standard:4.0",
                Type="LINUX_CONTAINER",
                EnvironmentVariables=[
                    {
                        "Name": "MIGRATE_ROLE_ARN",
                        "Type": "PLAINTEXT",
                        "Value": migrate_role_arn,
                    },
                    {
                        "Name": "Version",
                        "Type": "PARAMETER_STORE",
                        "Value": troposphere.Ref(version_parameter),
                    },
                ],
            ),
            Name=project_name,
            ServiceRole=troposphere.GetAtt(codebuild_role, "Arn"),
            Source=codebuild.Source(
                Type="CODEPIPELINE",
                BuildSpec=yaml.safe_dump(
                    dict(
                        version="0.2",
                        phases=dict(
                            install={
                                "runtime-versions": dict(python="3.8"),
                                "commands": [
                                    "pip install aws-organized==${Version}",
                                ],
                            },
                            build={
                                "commands": [
                                    "aws-organized migrate $MIGRATE_ROLE_ARN",
                                ],
                            },
                        ),
                        artifacts=dict(
                            files=[
                                "environment",
                            ],
                        ),
                    )
                ),
            ),
        )
    )

    source_actions = codepipeline.Actions(
        Name="SourceAction",
        ActionTypeId=codepipeline.ActionTypeId(
            Category="Source",
            Owner="AWS",
            Version="1",
            Provider="CodeCommit",
        ),
        OutputArtifacts=[codepipeline.OutputArtifacts(Name="SourceOutput")],
        Configuration={
            "RepositoryName": repository_name,
            "BranchName": "main",
            "PollForSourceChanges": "true",
        },
        RunOrder="1",
    )

    t.add_resource(
        codepipeline.Pipeline(
            "Pipeline",
            RoleArn=troposphere.GetAtt(codepipeline_role, "Arn"),
            Stages=[
                codepipeline.Stages(
                    Name="Source",
                    Actions=[source_actions],
                ),
                codepipeline.Stages(
                    Name="Migrate",
                    Actions=[
                        codepipeline.Actions(
                            Name="Migrate",
                            InputArtifacts=[
                                codepipeline.InputArtifacts(Name="SourceOutput")
                            ],
                            ActionTypeId=codepipeline.ActionTypeId(
                                Category="Build",
                                Owner="AWS",
                                Version="1",
                                Provider="CodeBuild",
                            ),
                            Configuration={
                                "ProjectName": troposphere.Ref(project),
                                "PrimarySource": "SourceAction",
                            },
                            RunOrder="1",
                        )
                    ],
                ),
            ],
            ArtifactStore=codepipeline.ArtifactStore(
                Type="S3", Location=troposphere.Ref(artifact_store)
            ),
        )
    )

    if output_format == "json":
        return t.to_json()
    else:
        return t.to_yaml()


def provision_codepipeline_stack(
    codepipeline_role_name: str,
    codepipeline_role_path: str,
    codebuild_role_name: str,
    codebuild_role_path: str,
    ssm_parameter_prefix: str,
    output_format: str,
    migrate_role_arn: str,
) -> None:
    template = generate_codepipeline_template(
        codepipeline_role_name,
        codepipeline_role_path,
        codebuild_role_name,
        codebuild_role_path,
        ssm_parameter_prefix,
        output_format,
        migrate_role_arn,
    )
    provision_stack("codepipeline", template)
