# AWS Organized

## What does this do?

This library does two things for you:

1. It allows you to visualise and make changes to your AWS Organization using folders and files
1. Instead of making changes directly you build up a migration which can then be reviewed before being applied.

### How does it do this

Using a read only role with access to your AWS Organization you run an import-organization command.  This generates a
directory that represents your AWS Organization.  It contains directories for OUs and accounts.  It contains files
describing the OUs, accounts and SCP policies.

You then make changes to the files and folders - for example, you move account folders to other OU folders to move the 
account.

Once you are happy with your changes you run a make-migrations command.  This generates some migrations files that
describe what changes you are making.  These changes should be reviewed and then added to git.  You can then use your 
fave branching strategy to approve the change in your team.  Once the changes are in your mainline they trigger a
pipeline that will run your migrations using a read/write role.

## How can I use this?

### Installing

This tool has been built in Python 3.7.  We recommend using [pipx](https://github.com/pipxproject/pipx) to install this 
tool:

```shell script
pipx install aws-organized
```

#### Setting up the IAM Roles

This tool ships with definitions for each IAM role with minimal permissions.  

You can see and execute the commands as follows:

##### Import Organization
The import organization command requires an IAM role in the Organizations management account.  Before you provision the
role you need to decide where this tool will be installed.  We recommend installing the tool into a dedicated prod 
shared services foundation account.  Once you have that account which we will call the organized account you are ready
to view or provision the template or stack.  

*You will need to provision this stack into your AWS Organizations management account*

To preview the template you can run:

```shell script
aws-organized generate-import-organization-role-stack <organized_account_id>
```

To provision the stack you can run:

```shell script
aws-organized provision-import-organization-role-stack <organized_account_id>
```

##### Make Migrations
The make-migrations command requires an IAM role in the Organizations management account.

*You will need to provision this stack into your AWS Organizations management account*

To preview the template you can run:

```shell script
aws-organized generate-make-migrations-role-template <organized_account_id>
```

To provision the stack you can run:

```shell script
aws-organized provision-make-migrations-role-template <organized_account_id>
```


##### Migrate
The migrate command requires an IAM role in the Organizations management account.

*You will need to provision this stack into your AWS Organizations management account*

To preview the template you can run:

```shell script
aws-organized generate-migrate-role-template <organized_account_id>
```

To provision the stack you can run:

```shell script
aws-organized provision-migrate-role-template <organized_account_id>
```


#### Setting up the pipelines

We recommend running the migrate command in a pipeline so that it is run in a controlled environment where history is 
recorded and so audit is possible.

You can run this in AWS CodePipeline using our template.

run:

```shell script
aws-organized generate-codepipeline-template <organized_account_id>
```

To provision the stack you can run:

```shell script
aws-organized provision-codepipeline-template <organized_account_id>
```


### Making changes to your Org
Once you run the import-organization command you have a directory created containing the accounts, OUs and SCPs defined:

```shell script
environment
└── r-japk
    ├── _accounts
    │   └── eamonnf+SCT-demo-hub
    │       ├── _meta.yaml
    │       └── _service_control_policies.yaml
    ├── _meta.yaml
    ├── _migrations
    │   ├── 1613407148.432513_POLICY_CONTENT_UPDATE.yaml
    │   └── 1613407148.435472_POLICY_CREATE.yaml
    ├── _organizational_units
    │   ├── foo
    │   │   ├── _meta.yaml
    │   │   ├── _organizational_units
    │   │   │   └── bar
    │   │   │       ├── _meta.yaml
    │   │   │       ├── _organizational_units
    │   │   │       └── _service_control_policies.yaml
    │   │   └── _service_control_policies.yaml
    │   └── sharedservices
    │       ├── _accounts
    │       │   ├── eamonnf+SCT-demo-spoke-1
    │       │   │   ├── _meta.yaml
    │       │   │   └── _service_control_policies.yaml
    │       │   ├── eamonnf+SCT-demo-spoke-2
    │       │   │   ├── _meta.yaml
    │       │   │   └── _service_control_policies.yaml
    │       │   ├── eamonnf+SCT-demo-spoke-4
    │       │   │   ├── _meta.yaml
    │       │   │   └── _service_control_policies.yaml
    │       │   └── eamonnf+SCT-demo-spoke-5
    │       │       ├── _meta.yaml
    │       │       └── _service_control_policies.yaml
    │       ├── _meta.yaml
    │       ├── _organizational_units
    │       │   └── infra
    │       │       ├── _accounts
    │       │       │   └── eamonnf+SCT-demo-spoke-3
    │       │       │       ├── _meta.yaml
    │       │       │       └── _service_control_policies.yaml
    │       │       ├── _meta.yaml
    │       │       ├── _organizational_units
    │       │       └── _service_control_policies.yaml
    │       └── _service_control_policies.yaml
    ├── _policies
    │   └── service_control_policies
    │       ├── FullAWSAccess
    │       │   ├── _meta.yaml
    │       │   └── policy.json
    │       ├── OnlyEc2
    │       │   └── policy.json
    │       └── OnlyS3
    │           ├── _meta.yaml
    │           └── policy.json
    └── _service_control_policies.yaml



```

You can currently perform the following operations:

#### Core features
The following capabilities are provided:

##### Create an OU
To create an OU you need to create a directory within a new or existing _organizational_units directory.  When creating
a directory you should not add the _meta.yaml file yourself.  You should name the directory with the name of the OU
you want to use.

##### Rename an OU
To rename an OU you need to rename the directory for the OU.  You should not edit the attributes in the _meta.yaml file.

##### Move an account
To move an account from one OU to another you have to move the directory for the account.  You should move the contents
of the directory with it - including the _meta.yaml and _service_control_policies.yaml files.

#### Service Control Policy features
The following capabilities are provided:

##### Create a policy
To create a policy you need to add a directory in the _policies/service_control_policies directory.  The name of the 
directory becomes the initial name for the policy.  Within the directory you need to add a file policy.json which 
contains the actual SCP policy you want to attach.  When you create a policy do not add a _meta.yaml file for it, the 
tool will add it for you.  When you create a policy you cannot set the description, that needs to be another change.

##### Update a policy
To update a policy you either modify the _meta.yaml file or the policy.json file.  If you want to change the 
description change the attribute in your _meta.yaml file.  If you want to change the policy content you will need to 
edit the policy.json.  At the moment you cannot change the policy name.

##### Attach a policy
To attach a policy to an OU or an account you should add it to the Attached section of the
_service_control_policies.yaml file.  Once you have added it, it should look like this:

```yaml
Attached:
- Arn: arn:aws:organizations::aws:policy/service_control_policy/p-FullAWSAccess
  AwsManaged: true
  Description: Allows access to every operation
  Id: p-FullAWSAccess
  Name: FullAWSAccess
  Type: SERVICE_CONTROL_POLICY
- Arn: arn:aws:organizations::156551640785:policy/o-78bxnm2a5p/service_control_policy/p-uc5s2thj
  AwsManaged: false
  Description: allow all of s3
  Id: p-uc5s2thj
  Name: OnlyS3
  Source: infra
  Type: SERVICE_CONTROL_POLICY
Inherited:
- Arn: arn:aws:organizations::aws:policy/service_control_policy/p-FullAWSAccess
  AwsManaged: true
  Description: Allows access to every operation
  Id: p-FullAWSAccess
  Name: FullAWSAccess
  Source: sharedservices
  Type: SERVICE_CONTROL_POLICY
```
In the above example we appended:

```yaml
Arn: arn:aws:organizations::156551640785:policy/o-78bxnm2a5p/service_control_policy/p-uc5s2thj
AwsManaged: false
Description: allow all of s3
Id: p-uc5s2thj
Name: OnlyS3
Type: SERVICE_CONTROL_POLICY
```


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

#
