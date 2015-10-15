"""pdt-client commands."""
import json
from functools import partial
import os
import pprint
import sys
import traceback

from alembic.config import Config
from alembic_offline import get_migrations_data, generate_migration_graph
from capturer import CaptureOutput
import requests
import six
import sqlalchemy

try:
    import subprocess32 as subprocess
except ImportError:  # pragma: no cover
    import subprocess


MIGRATION_PHASE_MAPPING = {
    'before-deploy': 'pre_deploy_steps',
    'after-deploy': 'post_deploy_steps',
    'final': 'final_steps',
}


def apply_migration_step(
        url, username, password, migration, step, instance, ci_project, phase, engine, migrations_dir, show):
    """Apply migration step."""
    print("-- Applying migration step: id={step[id]}, position={step[position]}".format(step=step))
    report = ''
    exc = None
    try:
        if step['type'] == engine.dialect.name:
            if show:
                print(step['code'])
            else:
                report = 'Executed SQL with rowcount: {0}'.format(engine.execute(step['code']).rowcount)
        else:
            path = os.path.join(migrations_dir, step['path'])
            args = [path]
            if step['type'] == 'python':
                args.insert(0, sys.executable)
            if show:
                print('-- Script to be executed: {0}'.format(' '.join(args)))
            else:
                with CaptureOutput() as capturer:
                    subprocess.check_call(args)
                    report = capturer.get_text()
        status = 'apl'
    except Exception as exc:
        report = traceback.format_exc()
        status = 'err'
    try:
        if not show:
            print('Applied migration step with status: {0}'.format(status))
            print('Reporting status to deployment tool')
            data = {
                "report": {
                    "migration": {
                        "uid": migration['uid']
                    },
                    "instance": {
                        "name": instance,
                        "ci_project": {
                            "name": ci_project
                        }
                    }
                },
                "step": {
                    "id": step['id']
                },
                "status": status,
                "log": report
            }
            response = requests.post(
                '{url}/api/migration-step-reports/'.format(url=url),
                auth=(username, password),
                data=json.dumps(data, sort_keys=True),
                headers={'content-type': 'application/json'}
            )
            try:
                response.raise_for_status()
            except Exception:
                pprint.pprint(response.json())
                raise
    finally:
        if exc:
            six.reraise(exc, None, sys.exc_traceback)


def apply_migration(url, username, password, migration, instance, ci_project, phase, engine, migrations_dir, show):
    """Apply migration."""
    print("-- Applying migration: {migration[uid]}".format(migration=migration))
    for step in migration[MIGRATION_PHASE_MAPPING[phase]]:
        apply_migration_step(
            url=url, username=username, password=password,
            migration=migration, step=step, instance=instance, ci_project=ci_project, phase=phase, engine=engine,
            migrations_dir=migrations_dir, show=show)


def migrate(
        url, username, password, instance, ci_project, phase, connection_string, migrations_dir, release, case=None,
        show=False):
    """Apply previously not applied migrations."""
    engine = sqlalchemy.create_engine(connection_string)
    params = dict(
        reviewed=True, exclude_status='apl', instance=instance, ci_project=ci_project, release=release)
    if case:
        params['case'] = case
    response = requests.get(
        '{url}/api/migrations/'.format(url=url),
        auth=(username, password),
        params=params,
        headers={'content-type': 'application/json'}
    )
    try:
        response.raise_for_status()
    except Exception:
        pprint.pprint(response.json())
        raise
    migrations = response.json()
    print('-- Got migration data with count: {0}'.format(len(migrations)))
    for migration in migrations:
        apply_migration(
            url=url, username=username, password=password,
            migration=migration, instance=instance, ci_project=ci_project, phase=phase, engine=engine,
            migrations_dir=migrations_dir, show=show)


def get_phase_steps(migration, phase):
    """Get migration phase steps.

    :param migration: migration data dict
    :type migration: dict
    :param phase: migration phase name
    :type phase: str

    :return: generator of migration step data in form: {'position': 1, code: 'code', 'type': 'type'[, 'path': 'path']}
    """
    for index, step in enumerate(migration['phases'].get(phase, dict(steps=[]))['steps']):
        kwargs = {}
        if 'path' in step:
            kwargs['path'] = step['path']
        yield dict(position=index, code=step['script'], type=step['type'], **kwargs)


def push_data(url, username, password, alembic_config, case=None, show=False):
    """Push migration data.

    :args: command line arguments namespace object

    :raises: Exception if PDT replied with an error
    """
    config = Config(alembic_config)
    for migration in get_migrations_data(config):
        if case == migration['attributes']['case_id'] or not case:
            print(
                'Got migration data for migration: {migration[revision]}, case: {migration[attributes][case_id]}'
                .format(migration=migration))
            call_url = '{0}/api/migrations/'.format(url)
            data = {
                "uid": migration['revision'],
                "parent": migration['down_revision'],
                "case": {
                    "id": str(migration['attributes']['case_id'])
                },
                "pre_deploy_steps": list(get_phase_steps(migration, 'before-deploy')),
                "post_deploy_steps": list(get_phase_steps(migration, 'after-deploy')),
                "final_steps": list(get_phase_steps(migration, 'final')),
            }
            if show:
                print('URL: {call_url}, data: \n{data}'.format(call_url=call_url, data=pprint.pformat(data)))
            else:
                response = requests.post(
                    call_url,
                    auth=(username, password),
                    data=json.dumps(data, sort_keys=True), headers={'content-type': 'application/json'})
                try:
                    response.raise_for_status()
                    print(
                        'Pushed migration data for migration: {migration[revision]}, '
                        'case: {migration[attributes][case_id]}'
                        .format(
                            migration=migration))
                except Exception:
                    pprint.pprint(response.json())
                    raise
            if case:
                break


def get_not_reviewed(url, username, password, alembic_config, ci_project, case=None):
    """Get not reviewed migrations.

    :args: command line arguments namespace object

    :raises:
        * Exception - PDT replied with an error
        * SystemExit(<number>) - found <number> of not reviewed migrations
    """
    config = Config(alembic_config)
    migrations = frozenset(migration['attributes']['case_id'] for migration in get_migrations_data(config))
    params = dict(reviewed=True, ci_project=ci_project)
    if case:
        params['case'] = case
    response = requests.get(
        '{0}/api/migrations/'.format(url),
        params=params,
        auth=(username, password),
        headers={'content-type': 'application/json'}
    )
    try:
        response.raise_for_status()
        print('Got migration data')
    except Exception:
        pprint.pprint(response.json())
        raise
    response_migrations = frozenset(migration['case']['id'] for migration in response.json())
    diff = migrations - response_migrations
    if diff:
        print('Found not reviewed migrations for these cases: {0}'.format(sorted(diff)))
        sys.exit(len(diff))
    else:
        print('No not reviewed migrations found so far')


def get_not_applied(url, username, password, ci_project, instance, release, case=None):
    """Get not applied migrations.

    :args: command line arguments namespace object

    :raises:
        * Exception - PDT replied with an error
        * SystemExit(<number>) - found <number> of not applied migrations
    """
    params = dict(
        exclude_status='apl', ci_project=ci_project, instance=instance, release=release)
    if case:
        params['case'] = case
    response = requests.get(
        '{0}/api/migrations/'.format(url),
        params=params,
        auth=(username, password),
        headers={'content-type': 'application/json'}
    )
    try:
        response.raise_for_status()
        print('Got migration data')
    except Exception:
        pprint.pprint(response.json())
        raise
    response_migrations = sorted(migration['case']['id'] for migration in response.json())
    if response_migrations:
        print('Found not applied migrations for these cases: {0}'.format(response_migrations))
        sys.exit(len(response_migrations))
    else:
        print('No not applied migrations found so far')


def get_case_revisions(url, username, password, ci_project, release, case=None):
    """Get case revisions.

    :args: command line arguments namespace object

    :raises:
        * Exception - PDT replied with an error
        * SystemExit(<number>) - found <number> of not applied migrations
    """
    params = dict(ci_project=ci_project, release=release)
    if case:
        params['id'] = case
    response = requests.get(
        '{0}/api/cases/'.format(url),
        params=params,
        auth=(username, password),
        headers={'content-type': 'application/json'}
    )
    try:
        response.raise_for_status()
        for case in response.json():
            print('{0}\t{1}'.format(case['id'], case['revision']))
    except Exception:
        pprint.pprint(response.json())
        raise


def deploy(url, username, password, instance, ci_project, release, status, log, cases):
    """Report the deployment."""
    data = dict(
        status=status,
        instance=dict(name=instance, ci_project=dict(name=ci_project)),
        release=dict(number=release),
        cases=[dict(id=case) for case in cases],
        log=log.read()
    )
    response = requests.post(
        '{url}/api/deployment-reports/'.format(url=url),
        auth=(username, password),
        data=json.dumps(data, sort_keys=True),
        headers={'content-type': 'application/json'}
    )
    try:
        response.raise_for_status()
        print(
            'Reported the deployment for ci project: {instance[ci_project][name]}, instance: {instance[name]}, '
            'release: {release[number]}'
            .format(**data))
    except Exception:
        pprint.pprint(response.json())
        raise


def _label_callback(data, release_numbers=None):
    """Generate a label for the revision.

    :param data: Dict with migration data.
    :type data: dict.

    :param release_numbers: dict containing the migration data from pdt.
    :type release_numbers: dict.

    :return: String with the label.
    :rtype: str
    """
    if not release_numbers:
        release_numbers = {}
    attributes = []
    release = release_numbers.get(data['revision'], "Unknown")
    attributes.append(u'- Release: {0}'.format(release))
    for key, value in data['attributes'].items():
        attributes.append(u'- {0}: {1}'.format(key, value))
    return u'{0}\n{1}'.format(data['revision'], '\n'.join(attributes))


def graph(url, username, password, alembic_config, filename, verbose=True):
    """Generate a dotfile with an overview of all the migrations."""
    config = Config(alembic_config)

    response = requests.get(
        '{0}/api/migrations/'.format(url),
        auth=(username, password),
        headers={'content-type': 'application/json'}
    )
    release_numbers = {}
    try:
        release_numbers = dict(
            (migration['uid'], (migration.get('release') or {}).get('number'))
            for migration in response.json()
        )
    except KeyError:
        pass

    label_callback = partial(_label_callback, release_numbers=release_numbers)

    with open(filename, 'w') as fp:
        fp.write(generate_migration_graph(config, label_callback))

    if verbose:
        print("Done")
        print("To generate an image use: dot -Tpng -O {0}".format(filename))
