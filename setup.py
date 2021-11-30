# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': '.'}

packages = \
['aws_organized',
 'aws_organized.extensions',
 'aws_organized.extensions.delegated_administrators',
 'aws_organized.extensions.service_control_policies']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML==5.4',
 'awacs==2.0.2',
 'better-boto==0.38.0',
 'boto3>=1.16.4,<2.0.0',
 'click>=7.1.2,<8.0.0',
 'progress>=1.5,<2.0',
 'troposphere==3.1.0']

entry_points = \
{'console_scripts': ['aws-organized = aws_organized.cli:cli']}

setup_kwargs = {
    'name': 'aws-organized',
    'version': '0.4.1',
    'description': 'Manage your AWS Organizations infrastructure using a simple file system based approach.  You create files and folders that correspond to AWS Organizations organizational units and accounts and this tooling manages changes for you.',
    'long_description': '# AWS Organized\n\n## What does this do?\n\nThis library does two things for you:\n\n1. It allows you to visualise and make changes to your AWS Organization using folders and files\n1. Instead of making changes directly you build up a migration which can then be reviewed before being applied.\n\n### How does it do this\n\nUsing a read only role with access to your AWS Organization you run an import-organization command.  This generates a\ndirectory that represents your AWS Organization.  It contains directories for OUs and accounts.  It contains files\ndescribing the OUs, accounts and SCP policies.\n\nYou then make changes to the files and folders - for example, you move account folders to other OU folders to move the \naccount.\n\nOnce you are happy with your changes you run a make-migrations command.  This generates some migrations files that\ndescribe what changes you are making.  These changes should be reviewed and then added to git.  You can then use your \nfave branching strategy to approve the change in your team.  Once the changes are in your mainline they trigger a\npipeline that will run your migrations using a read/write role.\n\n## How can I use this?\n\n### Installing\n\nThis tool has been built in Python 3.7.  We recommend using [pipx](https://github.com/pipxproject/pipx) to install this \ntool:\n\n```shell script\npipx install aws-organized\n```\n\n#### Setting up the IAM Roles\n\nThis tool ships with definitions for each IAM role with minimal permissions.  \n\nYou can see and execute the commands as follows:\n\n##### Import Organization\nThe import organization command requires an IAM role in the Organizations management account.  Before you provision the\nrole you need to decide where this tool will be installed.  We recommend installing the tool into a dedicated prod \nshared services foundation account.  Once you have that account which we will call the organized account you are ready\nto view or provision the template or stack.  \n\n*You will need to provision this stack into your AWS Organizations management account*\n\nTo preview the template you can run:\n\n```shell script\naws-organized generate-import-organization-role-template <organized_account_id>\n```\n\nTo provision the stack you can run:\n\n```shell script\naws-organized provision-import-organization-role-stack <organized_account_id>\n```\n\n##### Make Migrations\nThe make-migrations command requires an IAM role in the Organizations management account.\n\n*You will need to provision this stack into your AWS Organizations management account*\n\nTo preview the template you can run:\n\n```shell script\naws-organized generate-make-migrations-role-template <organized_account_id>\n```\n\nTo provision the stack you can run:\n\n```shell script\naws-organized provision-make-migrations-role-stack <organized_account_id>\n```\n\n\n##### Migrate\nThe migrate command requires an IAM role in the Organizations management account.\n\n*You will need to provision this stack into your AWS Organizations management account*\n\nTo preview the template you can run:\n\n```shell script\naws-organized generate-migrate-role-template <organized_account_id>\n```\n\nTo provision the stack you can run:\n\n```shell script\naws-organized provision-migrate-role-stack <organized_account_id>\n```\n\n\n#### Setting up the pipelines\n\nWe recommend running the migrate command in a pipeline so that it is run in a controlled environment where history is \nrecorded and so audit is possible.\n\nYou can run this in AWS CodePipeline using our template.\n\nWhen running you have the option of which SCM you would like to use\n\n##### AWS CodeCommit\n\npreview the template:\n\n```shell script\naws-organized generate-codepipeline-template <MIGRATE_ROLE_ARN>\n```\n\nprovision the template:\n\n```shell script\naws-organized provision-codepipeline-stack <MIGRATE_ROLE_ARN>\n```\nPlease note, you can specify --scm-full-repository-id to provide the name of the repo and you can use scm-branch-name to provide a branch.  If you omit either a default value will be used.\n\nFinally, you can specify --scm-skip-creation-of-repo and the template will not include the AWS CodeCommit repo - you can bring your own.\n\n##### AWS S3\n\npreview the template:\n\n```shell script\naws-organized generate-codepipeline-template --scm-provider s3 --scm-bucket-name foo --scm-object-key environment.zip <MIGRATE_ROLE_ARN>\n```\n\nprovision the template:\n\n```shell script\naws-organized provision-codepipeline-stack --scm-provider s3 --scm-bucket-name foo --scm-object-key environment.zip <MIGRATE_ROLE_ARN>\n```\n\nPlease note if you omit --scm-bucket-name we will auto generate a bucket name for you.  If you omit --scm-object-key we will generate a value for you.\n\nFinally, you can specify --scm-skip-creation-of-repo and the template will not include the AWS S3 bucket - you can bring your own.\n\n##### Github / Github Enterprise / Bitbucket cloud (via CodeStarSourceConnections)\n\npreview the template:\n\n```shell script\naws-organized generate-codepipeline-template --scm-provider CodeStarSourceConnection --scm-connection-arn <CODE_STAR_CONNECTION_ARN> --scm-full-repository-id <GIT_REPO_NAME> --scm-branch-name <GIT_BRANCH_NAME> <MIGRATE_ROLE_ARN>\n```\n\nprovision the template:\n\n```shell script\naws-organized provision-codepipeline-stack --scm-provider CodeStarSourceConnection --scm-connection-arn <CODE_STAR_CONNECTION_ARN> --scm-full-repository-id <GIT_REPO_NAME> --scm-branch-name <GIT_BRANCH_NAME> <MIGRATE_ROLE_ARN>\n```\nIf you do not provide values for --scm-full-repository-id or --scm-branch-name default values will be provided for you.\n\n### Making changes to your Org\nBefore you can make changes you need to run:\n\n```shell script\naws-organized import-organization <import-organization-role>\n```\n\nwhere `import-organization-role` is the role created by the `provision-import-organization-role-stack` command\n\nOnce you run the import-organization command you have a directory created containing the accounts, OUs and SCPs defined:\n\n```shell script\nenvironment\n└── r-japk\n    ├── _accounts\n    │\xa0\xa0 └── eamonnf+SCT-demo-hub\n    │\xa0\xa0     ├── _meta.yaml\n    │\xa0\xa0     └── _service_control_policies.yaml\n    ├── _meta.yaml\n    ├── _migrations\n    │\xa0\xa0 ├── 1613407148.432513_POLICY_CONTENT_UPDATE.yaml\n    │\xa0\xa0 └── 1613407148.435472_POLICY_CREATE.yaml\n    ├── _organizational_units\n    │\xa0\xa0 ├── foo\n    │\xa0\xa0 │\xa0\xa0 ├── _meta.yaml\n    │\xa0\xa0 │\xa0\xa0 ├── _organizational_units\n    │\xa0\xa0 │\xa0\xa0 │\xa0\xa0 └── bar\n    │\xa0\xa0 │\xa0\xa0 │\xa0\xa0     ├── _meta.yaml\n    │\xa0\xa0 │\xa0\xa0 │\xa0\xa0     ├── _organizational_units\n    │\xa0\xa0 │\xa0\xa0 │\xa0\xa0     └── _service_control_policies.yaml\n    │\xa0\xa0 │\xa0\xa0 └── _service_control_policies.yaml\n    │\xa0\xa0 └── sharedservices\n    │\xa0\xa0     ├── _accounts\n    │\xa0\xa0     │\xa0\xa0 ├── eamonnf+SCT-demo-spoke-1\n    │\xa0\xa0     │\xa0\xa0 │\xa0\xa0 ├── _meta.yaml\n    │\xa0\xa0     │\xa0\xa0 │\xa0\xa0 └── _service_control_policies.yaml\n    │\xa0\xa0     │\xa0\xa0 ├── eamonnf+SCT-demo-spoke-2\n    │\xa0\xa0     │\xa0\xa0 │\xa0\xa0 ├── _meta.yaml\n    │\xa0\xa0     │\xa0\xa0 │\xa0\xa0 └── _service_control_policies.yaml\n    │\xa0\xa0     │\xa0\xa0 ├── eamonnf+SCT-demo-spoke-4\n    │\xa0\xa0     │\xa0\xa0 │\xa0\xa0 ├── _meta.yaml\n    │\xa0\xa0     │\xa0\xa0 │\xa0\xa0 └── _service_control_policies.yaml\n    │\xa0\xa0     │\xa0\xa0 └── eamonnf+SCT-demo-spoke-5\n    │\xa0\xa0     │\xa0\xa0     ├── _meta.yaml\n    │\xa0\xa0     │\xa0\xa0     └── _service_control_policies.yaml\n    │\xa0\xa0     ├── _meta.yaml\n    │\xa0\xa0     ├── _organizational_units\n    │\xa0\xa0     │\xa0\xa0 └── infra\n    │\xa0\xa0     │\xa0\xa0     ├── _accounts\n    │\xa0\xa0     │\xa0\xa0     │\xa0\xa0 └── eamonnf+SCT-demo-spoke-3\n    │\xa0\xa0     │\xa0\xa0     │\xa0\xa0     ├── _meta.yaml\n    │\xa0\xa0     │\xa0\xa0     │\xa0\xa0     └── _service_control_policies.yaml\n    │\xa0\xa0     │\xa0\xa0     ├── _meta.yaml\n    │\xa0\xa0     │\xa0\xa0     ├── _organizational_units\n    │\xa0\xa0     │\xa0\xa0     └── _service_control_policies.yaml\n    │\xa0\xa0     └── _service_control_policies.yaml\n    ├── _policies\n    │\xa0\xa0 └── service_control_policies\n    │\xa0\xa0     ├── FullAWSAccess\n    │\xa0\xa0     │\xa0\xa0 ├── _meta.yaml\n    │\xa0\xa0     │\xa0\xa0 └── policy.json\n    │\xa0\xa0     ├── OnlyEc2\n    │\xa0\xa0     │\xa0\xa0 └── policy.json\n    │\xa0\xa0     └── OnlyS3\n    │\xa0\xa0         ├── _meta.yaml\n    │\xa0\xa0         └── policy.json\n    └── _service_control_policies.yaml\n\n\n\n```\n\nYou can currently perform the following operations:\n\n#### Core features\nThe following capabilities are provided:\n\n##### Create an OU\nTo create an OU you need to create a directory within a new or existing _organizational_units directory.  When creating\na directory you should not add the _meta.yaml file yourself.  You should name the directory with the name of the OU\nyou want to use.\n\n##### Rename an OU\nTo rename an OU you need to rename the directory for the OU.  You should not edit the attributes in the _meta.yaml file.\n\n##### Move an account\nTo move an account from one OU to another you have to move the directory for the account.  You should move the contents\nof the directory with it - including the _meta.yaml and _service_control_policies.yaml files.\n\n#### Service Control Policy features\nThe following capabilities are provided:\n\n##### Create a policy\nTo create a policy you need to add a directory in the _policies/service_control_policies directory.  The name of the \ndirectory becomes the initial name for the policy.  Within the directory you need to add a file policy.json which \ncontains the actual SCP policy you want to attach.  When you create a policy do not add a _meta.yaml file for it, the \ntool will add it for you.  When you create a policy you cannot set the description, that needs to be another change.\n\n##### Update a policy\nTo update a policy you either modify the _meta.yaml file or the policy.json file.  If you want to change the \ndescription change the attribute in your _meta.yaml file.  If you want to change the policy content you will need to \nedit the policy.json.  At the moment you cannot change the policy name.\n\n##### Attach a policy\nTo attach a policy to an OU or an account you should add it to the Attached section of the\n_service_control_policies.yaml file.  Once you have added it, it should look like this:\n\n```yaml\nAttached:\n- Arn: arn:aws:organizations::aws:policy/service_control_policy/p-FullAWSAccess\n  AwsManaged: true\n  Description: Allows access to every operation\n  Id: p-FullAWSAccess\n  Name: FullAWSAccess\n  Type: SERVICE_CONTROL_POLICY\n- Name: OnlyS3\nInherited:\n- Arn: arn:aws:organizations::aws:policy/service_control_policy/p-FullAWSAccess\n  AwsManaged: true\n  Description: Allows access to every operation\n  Id: p-FullAWSAccess\n  Name: FullAWSAccess\n  Source: sharedservices\n  Type: SERVICE_CONTROL_POLICY\n```\nIn the above example we appended the name only:\n\n```yaml\nName: OnlyS3\n```\n\nAWS-Organized will look up the rest of the details for you.\n\n### Generating migrations\nOnce you have made your changes you can then run `aws-organized make-migrations <make-migrations-role-arn>` where\nmake-migrations-role-arn is the Arn of the role created in the steps above.\n\nThis creates a _migrations directory in your environment/organization direction.  Within the _migrations directory\nthere should be a file describing the change you want to make.\n\n### Applying migrations\nOnce you have made your migrations you will want to review them - they are human (ish) readable YAML documents that\ndescribe the change you are applying.  Once you are happy with them you will want to run them.\n\n#### Running migrations in a pipeline (recommended)\nOnce you have your migrations you add them to the git repository created in the create pipeline step above.  The default\nname for the git repo is `AWS-Organized-environment`\n\n#### Running migrations locally (not recommended)\nOnce you have your migrations you can then run `aws-organized migrate <migrate-role-arn>` where\nmigrate-role-arn is the Arn of the role created in the steps above.\n\n\n## Security\n\nSee [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.\n\n## License\n\nThis project is licensed under the Apache-2.0 License.\n\n#\n',
    'author': 'Eamonn Faherty',
    'author_email': 'eamonnf@amazon.co.uk',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/aws-samples/aws-organized',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4',
}


setup(**setup_kwargs)
