## AWS Organized

This library helps you manage your AWS Organization by allowing you to describe your organization in code and by
allowing you to create migrations for changes to be made in your organization so they can be approved before being
applied.

### How to use

To use the library you will need to create your AWS Organization within an environment folder.  You can do this using
the `import-organization` command:

```shell script
aws-organized import-organization <role_arn>
```

Please replace <role_arn> with the arn of the role you want to assume that has read access to your organization.

This will create a folder similar to this:

```shell script
environment
├── migrations
└── r-japk
    ├── _accounts
    │   └── account1
    │       └── _meta.yaml
    ├── _meta.yaml
    └── _organizational_units
        ├── ou-1
        │   ├── _meta.yaml
        │   └── _accounts
        │       └── account2
        │           └── _meta.yaml
        │   └── _organizational_units
        │       └── nested-ou-1
        │           └── _meta.yaml
```

Once you have imported your organization you can make changes to the environment folder and create a migration:

```shell script
aws-organized make-migrations <role_arn>
```

Please replace <role_arn> with the arn of the role you want to assume that has read access to your organization.

```shell script
aws-organized migrate <role_arn>
```

Please replace <role_arn> with the arn of the role you want to assume that has write access to your organization so that
changes can be made.

### Making changes

You can create directories that will result in the creation of organizational units.  You can rename directories that 
are organizational units which will result in the renaming of your organizational unit.  You can move accounts into 
different organizational units by moving the directory.

Do not manually create _meta.yaml files - these are created by the framework.  If you move an account then you should
ensure the _meta.yaml file is also moved.

## PLEASE NOTE

Currently migrations have no affect and there are no sample IAM roles or CICD pipeline for the automated running of 
migrations.

This will be added shortly.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

#
