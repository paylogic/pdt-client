"""Test commands."""
from __future__ import print_function

import mock
import pytest
import sys

from pdt_client.commands import (
    deploy,
    get_not_applied,
    get_not_reviewed,
    migrate,
    push_data,
    graph,
    _label_callback
)


@pytest.mark.parametrize('show', [False, True])
def test_migrate(mocker, show):
    """Test migrate command."""
    mocked_get = mocker.patch('requests.get')
    mocked_post = mocker.patch('requests.post')
    mocked_engine = mocker.patch('sqlalchemy.create_engine')
    mocked_engine.return_value.dialect.name = 'sqlite'
    mocked_engine.return_value.execute.return_value.rowcount = 1
    mocked_check_call = mocker.patch('pdt_client.commands.subprocess.check_call')

    def print_log(*args):
        print('some output log')
        print('some error output log', file=sys.stderr)
    mocked_check_call.side_effect = print_log
    mocked_get.return_value.json.return_value = [
        {
            'uid': '123123',
            'pre_deploy_steps': [
                {
                    'id': 1,
                    'position': 1,
                    'code': 'some script',
                    'type': 'sqlite',
                }
            ],
            'post_deploy_steps': [
                {
                    'id': 2,
                    'position': 2,
                    'code': 'some other script',
                    'type': 'sqlite',
                }
            ],
            'final_steps': [
                {
                    'id': 3,
                    'position': 3,
                    'code': 'some shell script',
                    'path': '/some/path',
                    'type': 'python',
                }
            ],
        }
    ]
    migrate(
        url='http://example.com', username='user', password='password', instance='some', ci_project='some',
        phase='before-deploy', connection_string='sqlite:///', migrations_dir='/tmp', release='1510',
        show=show, case=33322)
    mocked_get.assert_called_with(
        'http://example.com/api/migrations/',
        headers={'content-type': 'application/json'}, params={
            'ci_project': 'some',
            'instance': 'some',
            'exclude_status': 'apl',
            'reviewed': True,
            'release': '1510',
            'case': 33322,
        },
        auth=('user', 'password'))
    if show:
        assert not mocked_engine.return_value.execute.called
    else:
        mocked_engine.return_value.execute.assert_called_with('some script')
        mocked_post.assert_called_with(
            'http://example.com/api/migration-step-reports/',
            headers={'content-type': 'application/json'},
            data='{"log": "Executed SQL with rowcount: 1", "report": {"instance": '
            '{"ci_project": {"name": "some"}, "name": "some"}, "migration": {"uid": "123123"}}, '
            '"status": "apl", "step": {"id": 1}}', auth=('user', 'password'))
    migrate(
        url='http://example.com', username='user', password='password', instance='some', ci_project='some',
        phase='after-deploy', connection_string='sqlite:///', migrations_dir='/tmp', release='1510',
        show=show)
    if show:
        assert not mocked_engine.return_value.execute.called
    else:
        mocked_engine.return_value.execute.assert_called_with('some other script')
        mocked_post.assert_called_with(
            'http://example.com/api/migration-step-reports/',
            headers={'content-type': 'application/json'},
            data='{"log": "Executed SQL with rowcount: 1", "report": {"instance": '
            '{"ci_project": {"name": "some"}, "name": "some"}, "migration": {"uid": "123123"}}, '
            '"status": "apl", "step": {"id": 2}}', auth=('user', 'password'))
    migrate(
        url='http://example.com', username='user', password='password', instance='some', ci_project='some',
        phase='final', connection_string='sqlite:///', migrations_dir='/tmp', release='1510',
        show=show)
    if show:
        assert not mocked_check_call.called
    else:
        mocked_check_call.assert_called_with([sys.executable, '/some/path'])
        mocked_post.assert_called_with(
            'http://example.com/api/migration-step-reports/',
            headers={'content-type': 'application/json'},
            data='{"log": "some output log\\nsome error output log", "report": {"instance": '
            '{"ci_project": {"name": "some"}, "name": "some"}, "migration": {"uid": "123123"}}, '
            '"status": "apl", "step": {"id": 3}}', auth=('user', 'password'))
        mocked_check_call.side_effect = Exception('some error')
        mocked_post.reset_mock()
        mocked_post.return_value.raise_for_status.side_effect = Exception('some post error')
        with pytest.raises(Exception):
            migrate(
                url='http://example.com', username='user', password='password', instance='some', ci_project='some',
                phase='final', connection_string='sqlite:///', migrations_dir='/tmp', release='1510',
                show=show)
        assert '"status": "err"' in mocked_post.call_args[1]['data']
        assert "Traceback (most recent call last)" in mocked_post.call_args[1]['data']


def test_migration_data_push(mocker):
    """Test migration-data push command."""
    mocked_requests = mocker.patch('requests.post')
    mocked_alembic = mocker.patch('pdt_client.commands.get_migrations_data')
    mocked_alembic.return_value = [
        {
            'revision': 2, 'attributes': {'case_id': 33322}, 'down_revision': 1,
            'phases': {
                'before-deploy': {
                    'steps': [{
                        'script': 'some script',
                        'type': 'mysql',
                    }]
                },
                'after-deploy': {
                    'steps': [{
                        'script': 'some script',
                        'type': 'sh',
                    }]
                },
                'final': {
                    'steps': [{
                        'script': 'some script',
                        'type': 'pgsql',
                    }]
                },
            }
        }]
    push_data(
        url='http://example.com', username='user', password='password', alembic_config='some_config')
    mocked_requests.assert_called_with(
        'http://example.com/api/migrations/', headers={
            'content-type': 'application/json'},
        data='{"case": {"id": "33322"}, "final_steps": [{"code": "some script", "position": 0, "type": "pgsql"}], '
        '"parent": 1, "post_deploy_steps": [{"code": "some script", "position": 0, "type": "sh"}], '
        '"pre_deploy_steps": [{"code": "some script", "position": 0, "type": "mysql"}], "uid": 2}',
        auth=('user', 'password'))


def test_migration_data_get_not_reviewed(mocker):
    """Test migration-data get-not-reviewed command."""
    mocked_requests = mocker.patch('requests.get')
    mocked_alembic = mocker.patch('pdt_client.commands.get_migrations_data')
    mocked_alembic.return_value = [
        {
            'revision': 2, 'attributes': {'case_id': 33322}, 'down_revision': 1,
            'phases': {
                'before-deploy': {
                    'steps': [{
                        'script': 'some script',
                        'type': 'mysql',
                    }]
                },
                'after-deploy': {
                    'steps': [{
                        'script': 'some script',
                        'type': 'sh',
                    }]
                },
                'final': {
                    'steps': [{
                        'script': 'some script',
                        'type': 'pgsql',
                    }]
                },
            }
        }]
    with pytest.raises(SystemExit):
        get_not_reviewed(
            url='http://example.com', username='user', password='password', alembic_config='some_config',
            ci_project='some_project')
    mocked_requests.assert_called_with(
        'http://example.com/api/migrations/',
        headers={
            'content-type': 'application/json'},
        params={'ci_project': 'some_project', 'reviewed': True}, auth=('user', 'password'))


def test_migration_data_get_not_applied(mocker):
    """Test migration-data get-not-applied command."""
    mocked_requests = mocker.patch('requests.get')
    mocked_requests.return_value.json.return_value = [
        {
            'uid': '123123',
            'case': {'id': 33322},
            'pre_deploy_steps': [
                {
                    'id': 1,
                    'position': 1,
                    'code': 'some script',
                    'type': 'sqlite',
                }
            ],
            'post_deploy_steps': [
                {
                    'id': 2,
                    'position': 2,
                    'code': 'some other script',
                    'type': 'sqlite',
                }
            ],
            'final_steps': [
                {
                    'id': 3,
                    'position': 3,
                    'code': 'some shell script',
                    'path': '/some/path',
                    'type': 'python',
                }
            ],
        }
    ]
    with pytest.raises(SystemExit):
        get_not_applied(
            url='http://example.com', username='user', password='password',
            ci_project='some_project', instance='some_instance', release='1520')
    mocked_requests.assert_called_with(
        'http://example.com/api/migrations/',
        headers={'content-type': 'application/json'},
        params={'ci_project': 'some_project', 'instance': 'some_instance', 'exclude_status': 'apl', 'release': '1520'},
        auth=('user', 'password'))


def test_deploy(mocker):
    """Test deploy command."""
    mocked_requests = mocker.patch('requests.post')
    log = mock.Mock()
    log.read.return_value = 'some log'
    deploy(
        url='http://example.com', username='user', password='password', status='dpl',
        instance='some_instnace', ci_project='paylogic', log=log, release=1520)
    mocked_requests.assert_called_with(
        'http://example.com/api/deployment-reports/',
        headers={'content-type': 'application/json'},
        data='{"instance": {"ci_project": {"name": "paylogic"}, "name": "some_instnace"}, '
        '"log": "some log", "release": {"number": 1520}, "status": "dpl"}',
        auth=('user', 'password'))


def test_graph(mocker, tmpdir, capsys):
    """Test graph command."""
    mocked_requests = mocker.patch('requests.get')
    mocked_alembic = mocker.patch('pdt_client.commands.generate_migration_graph')
    mocked_alembic.return_value = "Hello"
    fp = tmpdir.join('test.dot')
    graph(
        url='http://example.com',
        username='user',
        password='password',
        filename=str(fp),
        alembic_config='some_config',
        verbose=True
    )
    mocked_requests.assert_called_with(
        'http://example.com/api/migrations/',
        headers={'content-type': 'application/json'},
        auth=('user', 'password'))

    assert fp.read() == "Hello"
    out, err = capsys.readouterr()
    assert out == "Done\nTo generate an image use: dot -Tpng -O {0}\n".format(fp)
    assert err == ""


def test_graph_key_error(mocker, tmpdir):
    """Test unhappy path for graph command."""
    mocked_requests = mocker.patch('requests.get')
    mocked_requests.return_value = mock.Mock()
    mocked_requests.return_value.json = mock.Mock(return_value=[{}])
    mocked_alembic = mocker.patch('pdt_client.commands.generate_migration_graph')
    mocked_alembic.return_value = "Hello"
    fp = tmpdir.join('test.dot')
    graph(
        url='http://example.com',
        username='user',
        password='password',
        filename=str(fp),
        alembic_config='some_config',
        verbose=False
    )
    mocked_requests.assert_called_with(
        'http://example.com/api/migrations/',
        headers={'content-type': 'application/json'},
        auth=('user', 'password'))

    assert fp.read() == "Hello"


def test_label_callback():
    """Test the label callback function."""
    release_numbers = dict(a='123')
    data = dict(revision='a', attributes=dict(b='c'))
    data2 = dict(revision='b', attributes=dict(d='e'))

    assert _label_callback(data, release_numbers) == u'a\n- Release: 123\n- b: c'
    assert _label_callback(data2) == u'b\n- Release: Unknown\n- d: e'
