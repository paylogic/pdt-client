"""pdt-client command line script."""
import argparse

from . import commands


def main():
    """Entry point to migration data commands."""
    parser = argparse.ArgumentParser(prog="pdt-client")
    parser.add_argument(
        "--username",
        dest="username",
        required=True,
        metavar="USERNAME",
        help="Deployment tool username",
    )
    parser.add_argument(
        "--password",
        dest="password",
        required=True,
        metavar="PASSWORD",
        help="Deployment tool password",
    )
    deployment_url = 'http://deployment.paylogic.eu'
    parser.add_argument(
        "--url",
        dest="url",
        metavar="URL",
        help="Deployment tool url. Defaults to {0}".format(deployment_url),
        required=False,
        default=deployment_url
    )
    subparsers = parser.add_subparsers(help="sub-command help", dest='command')
    subparsers.required = True
    add_subparser_migrate(subparsers)
    add_subparser_migration_data(subparsers)
    add_subparser_case_data(subparsers)
    add_subparser_deploy(subparsers)
    add_subparser_graph(subparsers)
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)


def add_subparser_migrate(subparsers):
    """Add migrate subparser to the main subparsers collection."""
    parser_migrate = subparsers.add_parser("migrate", help="apply all previously not applied migrations")
    parser_migrate.add_argument(
        "--instance",
        dest="instance",
        metavar="INSTANCE_NAME",
        help="instance for migration",
        required=True,
    )
    parser_migrate.add_argument(
        "--ci-project",
        dest="ci_project",
        metavar="CI_PROJECT_NAME",
        help="CI project",
        required=True,
    )
    phase_options = sorted(commands.MIGRATION_PHASE_MAPPING.keys())
    parser_migrate.add_argument(
        "--phase",
        dest="phase",
        metavar="[{0}]".format(', '.join(phase_options)),
        help="migration phase",
        choices=phase_options,
        required=True,
    )
    parser_migrate.add_argument(
        "--release",
        dest="release",
        metavar="RELEASE_NUMBER",
        help="release name",
        required=True,
    )
    parser_migrate.add_argument(
        "--show",
        dest="show",
        action="store_true",
        help="Only show what to be done, nothing will actually be done",
    )
    parser_migrate.add_argument(
        "--case",
        dest="case",
        type=int,
        metavar="CASE_ID",
        help="case id",
        required=False,
    )
    parser_migrate.add_argument(
        "--connection-string",
        dest="connection_string",
        metavar="CONNECTION_STRING",
        help="connection string",
        required=True,
    )
    parser_migrate.add_argument(
        "--migrations-dir",
        dest="migrations_dir",
        metavar="DIR",
        help="migrations directory",
        required=True,
    )
    parser_migrate.set_defaults(func=lambda args: commands.migrate(
        url=args.url,
        username=args.username,
        password=args.password,
        instance=args.instance,
        ci_project=args.ci_project,
        phase=args.phase,
        connection_string=args.connection_string,
        migrations_dir=args.migrations_dir,
        release=args.release,
        case=args.case,
        show=args.show)
    )


def add_subparser_migration_data(subparsers):
    """Add migration-data subparser to main subparsers collection."""
    parser_migration_data = subparsers.add_parser("migration-data", help="migration data commands")
    parser_migration_data.add_argument(
        "--case",
        dest="case",
        type=int,
        metavar="CASE_ID",
        help="case id",
        required=False,
    )
    migration_data_subparsers = parser_migration_data.add_subparsers(
        help="sub-command help", dest='migration_data_command')
    parser_push = migration_data_subparsers.add_parser("push", help="push migration data")
    parser_push.add_argument(
        "--alembic-config",
        dest="alembic_config",
        metavar="PATH",
        help="alembic config path",
        required=True,
    )
    parser_push.add_argument(
        "--show",
        dest="show",
        action="store_true",
        help="Only show what to be pushed, nothing will actually be pushed",
    )
    parser_push.set_defaults(func=lambda args: commands.push_data(
        url=args.url,
        username=args.username,
        password=args.password,
        alembic_config=args.alembic_config,
        case=args.case,
        show=args.show)
    )
    parser_get_not_reviewed = migration_data_subparsers.add_parser(
        "get-not-reviewed",
        help="get not reviewed migrations which are in the codebase")
    parser_get_not_reviewed.add_argument(
        "--alembic-config",
        dest="alembic_config",
        metavar="PATH",
        help="alembic config path",
        required=True,
    )
    parser_get_not_reviewed.add_argument(
        "--ci-project",
        dest="ci_project",
        metavar="CI_PROJECT_NAME",
        help="CI project",
        required=True,
    )
    parser_get_not_reviewed.set_defaults(func=lambda args: commands.get_not_reviewed(
        url=args.url,
        username=args.username,
        password=args.password,
        alembic_config=args.alembic_config,
        ci_project=args.ci_project,
        case=args.case)
    )
    parser_get_not_applied = migration_data_subparsers.add_parser(
        "get-not-applied",
        help="get not applied migrations which are in the codebase")
    parser_get_not_applied.add_argument(
        "--instance",
        dest="instance",
        metavar="INSTANCE_NAME",
        help="instance for migration application",
        required=True,
    )
    parser_get_not_applied.add_argument(
        "--ci-project",
        dest="ci_project",
        metavar="CI_PROJECT_NAME",
        help="CI project",
        required=True,
    )
    parser_get_not_applied.add_argument(
        "--release",
        dest="release",
        metavar="RELEASE_NUMBER",
        help="release name",
        required=True,
    )
    parser_get_not_applied.set_defaults(func=lambda args: commands.get_not_applied(
        url=args.url,
        username=args.username,
        password=args.password,
        ci_project=args.ci_project,
        instance=args.instance,
        release=args.release,
        case=args.case)
    )


def add_subparser_case_data(subparsers):
    """Add case-data subparser to main subparsers collection."""
    parser_case_data = subparsers.add_parser("case-data", help="case data commands")
    parser_case_data.add_argument(
        "--case",
        dest="case",
        type=int,
        metavar="CASE_ID",
        help="case id",
        required=False,
    )
    migration_data_subparsers = parser_case_data.add_subparsers(
        help="sub-command help", dest='case_data_command')
    parser_get_revisions = migration_data_subparsers.add_parser(
        "get-revisions",
        help="get case revisions")
    parser_get_revisions.add_argument(
        "--ci-project",
        dest="ci_project",
        metavar="CI_PROJECT_NAME",
        help="CI project",
        required=True,
    )
    parser_get_revisions.add_argument(
        "--release",
        dest="release",
        metavar="RELEASE_NUMBER",
        help="release name",
        required=True,
    )
    parser_get_revisions.add_argument(
        "--instance",
        dest="instance",
        metavar="INSTANCE_NAME",
        help="instance for deployment",
        required=True,
    )
    parser_get_revisions.set_defaults(func=lambda args: commands.get_not_deployed_cases(
        url=args.url,
        username=args.username,
        password=args.password,
        ci_project=args.ci_project,
        release=args.release,
        instance=args.instance,
        case=args.case)
    )


def add_subparser_deploy(subparsers):
    """Add deploy subparser to main subparsers collection."""
    parser_deploy = subparsers.add_parser("deploy", help="report the deployment results")
    parser_deploy.add_argument(
        "--instance",
        dest="instance",
        metavar="INSTANCE_NAME",
        help="instance for deployment",
        required=True,
    )
    parser_deploy.add_argument(
        "--ci-project",
        dest="ci_project",
        metavar="CI_PROJECT_NAME",
        help="CI project",
        required=True,
    )
    parser_deploy.add_argument(
        "--release",
        dest="release",
        metavar="RELEASE_NUMBER",
        help="release name",
        required=True,
    )
    parser_deploy.add_argument(
        "--revision",
        dest="revision",
        metavar="REVISION",
        help="revision",
        required=False,
    )
    parser_deploy.add_argument(
        "--status",
        dest="status",
        metavar="[dpl,err]",
        choices=('dpl', 'err'),
        help="deployment status, pass 'dpl' for 'Deployed OK', 'err' for 'Deployment Error'",
        required=True,
    )
    parser_deploy.add_argument(
        "--case",
        dest="cases",
        action="append",
        metavar="CASE_ID",
        type=int,
        default=[],
        help="id of the deployed case",
        required=False,
    )
    parser_deploy.add_argument(
        'log',
        type=argparse.FileType('r'),
        default='-',
    )
    parser_deploy.set_defaults(func=lambda args: commands.deploy(
        url=args.url,
        username=args.username,
        password=args.password,
        instance=args.instance,
        ci_project=args.ci_project,
        release=args.release,
        status=args.status,
        cases=args.cases,
        revision=args.revision,
        log=args.log)
    )


def add_subparser_graph(subparsers):
    """Add a graph subparser to main subparser collection."""
    parser_graph = subparsers.add_parser("graph", help="Graph the migrations")
    parser_graph.add_argument(
        '--filename',
        dest="filename",
        metavar="FILENAME",
        help="The filename to store the dotfile too.",
        required=True,
    )
    parser_graph.add_argument(
        "--alembic-config",
        dest="alembic_config",
        metavar="PATH",
        help="alembic config path",
        required=True,
    )
    parser_graph.add_argument(
        '--quiet',
        dest='verbose',
        action='store_false',
        help="Should it print output?",
        required=False
    )

    parser_graph.set_defaults(func=lambda args: commands.graph(
        url=args.url,
        username=args.username,
        password=args.password,
        alembic_config=args.alembic_config,
        filename=args.filename,
        verbose=args.verbose)
    )
