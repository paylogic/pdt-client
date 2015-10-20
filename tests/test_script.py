"""Test script."""
import pytest

from pdt_client.script import main


class equals_any(object):

    """Helper object comparison to which is always 'equal'."""

    def __init__(self, type=None):
        """Store provided type."""
        self.type = type

    def __eq__(self, other):
        """Return True if same type."""
        return isinstance(other, self.type) if self.type else True

    def __cmp__(self, other):
        """Return same if same type."""
        return 0 if (isinstance(other, self.type) if self.type else False) else -1


def test_migrate(monkeypatch, mocker):
    """Test script entry point: migrate."""
    mocked_command = mocker.patch('pdt_client.commands.migrate')
    monkeypatch.setattr('sys.argv', [
        '', '--username=username', '--password=password', 'migrate', '--instance=test',
        '--phase=before-deploy', '--connection-string=sqlite:///', '--migrations-dir=/tmp', '--release=1510'])
    main()
    mocked_command.assert_called_with(
        case=None, username='username', instance='test', connection_string='sqlite:///', phase='before-deploy',
        migrations_dir='/tmp', url='http://deployment.paylogic.eu', password='password',
        release='1510', show=False)


@pytest.mark.parametrize('case', [33322, None])
def test_migration_data_push(monkeypatch, mocker, case):
    """Test script entry point: migration-data push."""
    mocked_command = mocker.patch('pdt_client.commands.push_data')
    case_args = ['--case={0}'.format(case)] if case else []
    monkeypatch.setattr('sys.argv', [
        '', '--username=username', '--password=password', 'migration-data',
    ] + case_args + ['push', '--alembic-config=some_alembic_config'])
    main()
    mocked_command.assert_called_with(
        case=case, alembic_config='some_alembic_config', show=False,
        url='http://deployment.paylogic.eu', username='username', password='password')


@pytest.mark.parametrize('case', [33322, None])
def test_migration_data_get_not_reviewed(monkeypatch, mocker, case):
    """Test script entry point: migration-data get-not-reviewed."""
    mocked_command = mocker.patch('pdt_client.commands.get_not_reviewed')
    case_args = ['--case={0}'.format(case)] if case else []
    monkeypatch.setattr('sys.argv', [
        '', '--username=username', '--password=password', 'migration-data',
    ] + case_args + ['get-not-reviewed', '--ci-project=some_project', '--alembic-config=some_alembic_config'])
    main()
    mocked_command.assert_called_with(
        case=case, alembic_config='some_alembic_config', username='username',
        ci_project='some_project',
        password='password', url='http://deployment.paylogic.eu')


@pytest.mark.parametrize('case', [33322, None])
def test_migration_data_get_not_applied(monkeypatch, mocker, case):
    """Test script entry point: migration-data get-not-applied."""
    mocked_command = mocker.patch('pdt_client.commands.get_not_applied')
    case_args = ['--case={0}'.format(case)] if case else []
    monkeypatch.setattr('sys.argv', [
        '', '--username=username', '--password=password', 'migration-data',
    ] + case_args + ['get-not-applied', '--instance=some_instance', '--release=1520'])
    main()
    mocked_command.assert_called_with(
        case=case, username='username',
        password='password', url='http://deployment.paylogic.eu',
        instance='some_instance', release='1520')


@pytest.mark.parametrize('case', [33322, None])
def test_case_data_get_not_deployed(monkeypatch, mocker, case):
    """Test script entry point: case-data get-not-deployed."""
    mocked_command = mocker.patch('pdt_client.commands.get_not_deployed_cases')
    case_args = ['--case={0}'.format(case)] if case else []
    monkeypatch.setattr('sys.argv', [
        '', '--username=username', '--password=password', 'case-data',
    ] + case_args + ['get-not-deployed', '--release=1520', '--ci-project=some_project', '--instance=some_instance'])
    main()
    mocked_command.assert_called_with(
        case=case, username='username',
        ci_project='some_project',
        release='1520',
        instance='some_instance',
        password='password', url='http://deployment.paylogic.eu')


@pytest.mark.parametrize('revision', ['123123', None])
@pytest.mark.parametrize('cases', [[33322], []])
def test_deploy(monkeypatch, mocker, revision, cases):
    """Test script entry point: deploy."""
    mocked_command = mocker.patch('pdt_client.commands.deploy')
    monkeypatch.setattr('sys.argv', [
        '', '--username=username', '--password=password', 'deploy', '--instance=some-instance', '--status=dpl'] +
        ['--case={0}'.format(case) for case in cases] +
        [
        '/dev/null'])
    main()
    mocked_command.assert_called_with(
        status='dpl', username='username',
        log=equals_any(), url='http://deployment.paylogic.eu',
        instance='some-instance', password='password', cases=cases)
