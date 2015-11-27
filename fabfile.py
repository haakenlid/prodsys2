"""Deployment of Django website using pyvenv-3.4 and git"""

from __future__ import print_function
import os
from os.path import join, dirname
from fabric.contrib.console import confirm
from fabric.contrib.files import append, exists, put
from fabric.context_managers import shell_env, cd, settings as env_settings
from fabric.api import local, env, run, sudo, settings, task
from fabric.utils import abort
from fabtools.vagrant import vagrant
from deployment_tools.generate_postactivate import make_postactivate_file

# github repo used for deploying the site
REPO_URL = ''

PYVENV = 'pyvenv'         # using python 2.7 for virtual environments
LINUXGROUP = 'www'            # linux user group on the webserver
WEBSERVER_ROOT = '/srv'       # root folder for all websites on the webserver
SITE_NAME = 'prodsys.no'    # the base host name for this project
POSTGRESQL_USER = 'postgres'  # username for the postgresql database root user.

env.site_url = 'vagrant.' + SITE_NAME

# Stops annoying linting error. "vagrant" is a command line task

vagrant = vagrant


@task(name='local')
def localhost():
    """run task on localhost"""
    env.site_url = 'local.' + SITE_NAME
    env.hosts = [env.site_url]


@task(name='prod')
def production_server():
    """run task on development server"""
    env.site_url = SITE_NAME
    env.hosts = [env.site_url]


@task(name='staging')
def staging_server():
    """run task on development server"""
    env.site_url = 'staging.' + SITE_NAME
    env.hosts = [env.site_url]


@task(name='dev')
def development_server():
    """run task on development server"""
    env.site_url = 'dev.' + SITE_NAME
    env.hosts = [env.site_url]


@task(name='notebook')
def start_ipython_notebook():
    """start the ipython notebook"""
    django_admin('shell_plus', '--notebook', '--no-browser')


@task(name='runserver')
def start_runserver_plus():
    """Start a development webserver"""
    folders = _get_folders(env.site_url)
    with cd(folders['venv']):
        run('source bin/activate && django-admin runserver_plus')


@task(name='gulp')
def gulp_watch():
    folders = _get_folders(env.site_url)
    with cd(folders['source']):
        run('../node_modules/.bin/gulp')


@task(name='admin')
def django_admin(*args):
    """run arbitrary django-admin commands"""
    venv_folder = _get_folders(env.site_url)['venv']
    run('source {venv}/bin/activate && django-admin {args}'.format(
        venv=venv_folder,
        args=' '.join(args), ))


def _get_folders(site_url=None):
    """Return a dictionary containing pathnames of named project folders."""
    site_url = site_url or env.site_url
    folders = {
        'site': '{site_folder}',                   # project root folder
        'source': '{site_folder}/source',          # django source code
        'bin': '{site_folder}/bin',                # bash scripts
        # static files served by nginx
        'static': '{site_folder}/static',
        'media': '{site_folder}/static/media',     # user uploaded files
        'venv': '{site_folder}/venv/{venv_name}',  # python virtual environment
        'logs': '{site_folder}/logs',              # contains logfiles
        # global folder with symlinks to all virtual environments
        'venvs': '/home/{user}/.virtualenvs',
    }

    site_folder = '{root}/{url}'.format(
        root=WEBSERVER_ROOT,
        url=site_url,
    )

    for folder in folders:
        folders[folder] = folders[folder].format(
            venv_name=site_url,
            user=env.user,
            site_folder=site_folder,
        )

    return folders


def _get_configs(
        site_url=None, user_name=None, bin_folder=None, config_folder=None):
    """
    Return a dictionary containing configuration for webserver services.
    """
    # user name for database and linux
    site_url = site_url or env.site_url
    user_name = user_name or site_url.replace('.', '_')
    # folder to put shell scripts
    project_folder = '{root}/{url}/'.format(
        root=WEBSERVER_ROOT,
        url=site_url)
    bin_folder = bin_folder or project_folder + 'bin'
    # parent folder of config file templates.
    config_folder = config_folder or dirname(__file__) + '/deployment_tools'

    configs = {
        # 'service': # name of program or service that need configuration files.
        # 'template': # template for configuration file
        # 'filename': # what to call the config file made from template
        # 'target folder': # where to put the config file
        # 'install': # bash command to prepare and activate the config file.
        # 'start': # bash command to start the service
        # 'stop': # bash command to stop the service
        # },
        'site': {  # python wsgi runner for django
            'template': '{config}/site/template'.format(config=config_folder,),
            'filename': '{user}.sh'.format(user=user_name,),
            'target folder': bin_folder,
            # make bash file executable by the supervisor user.
            'install': 'sudo chmod 774 $FILENAME && sudo chown {user} $FILENAME'.format(user=user_name,),
            'start': ':',
            'stop': ':',
        },
        'supervisor': {  # keeps gunicorn running
            'template': '{config}/supervisor/template'.format(config=config_folder,),
            'filename': '{user}.conf'.format(user=user_name,),
            'target folder': '/etc/supervisor/conf.d',
            # read all config files in conf.d folder
            'install': 'sudo supervisorctl reread && sudo supervisorctl update',
            'start': 'sudo supervisorctl start {url}:*'.format(url=site_url,),
            'stop': 'sudo supervisorctl stop {url}:*'.format(url=site_url,),
        },
        'nginx': {  # webserver
            'template': '{config}/nginx/template'.format(config=config_folder,),
            'filename': '{url}'.format(url=site_url,),
            'target folder': '/etc/nginx/sites-available',
            'install': ':',
            'start': (
                # create symbolic link from config file to sites-enabled
                'sudo ln -sf /etc/nginx/sites-available/{url} /etc/nginx/sites-enabled/{url} '
                # reload nginx service
                '&& sudo nginx -s reload').format(url=site_url),
            # remove symbolic link
            'stop': 'sudo rm -f /etc/nginx/sites-enabled/{url} && sudo nginx -s reload'.format(url=site_url,),
        },
    }
    return configs


@task
def fix_permissions():
    folders = _get_folders()
    _folders_and_permissions(folders)


@task
def deploy():
    """
    CWeate database, make folders, install django,
    create linux user, make virtualenv.
    """
    # Folders are named something like www.example.com
    # or www.staging.example.com for production or staging
    folders = _get_folders()

    postactivate_file, project_settings = make_postactivate_file(env.site_url, )

    _create_postgres_db(project_settings)
    _create_linux_user(project_settings['user'], LINUXGROUP)

    _folders_and_permissions(folders)
    _create_virtualenv(folders)
    _upload_postactivate(postactivate_file, folders['venv'], folders['bin'])
    _deploy_configs()
    update()


@task
def npmtest():
    """npm and bower install"""
    folders = _get_folders()
    _update_npm_and_bower(folders)


@task
def update():
    """
    Update repo from github, install pip reqirements,
    collect staticfiles and run database migrations.
    """
    folders = _get_folders()
    _get_latest_source(folders['source'])
    _update_virtualenv(folders['source'], folders['venv'],)
    _update_npm_and_bower(folders)
    _gulp_build(folders['source'])
    _collectstatic(folders['venv'])
    _update_database(folders['venv'])
    stop()
    start()


@task
def start():
    """Start webserver for site"""
    _enable_site()


@task
def stop():
    """Stop webserver from serving site"""
    with settings(warn_only=True):
        _enable_site(start=False)


@task
def dropdb():
    """Delete the site database"""
    db_name = env.site_url.replace('.', '_')
    _drop_postgres_db(db_name)


@task
def resetdb():
    """Reset and repopulate database with dummy data."""
    stop()
    run('source {venv}/bin/activate && reset-database.sh'.format(
        venv=_get_folders(env.site_url)['venv']))
    start()


@task
def reboot():
    """Restart all services connected to website"""
    _enable_site(start=False)
    sudo('service nginx restart; service supervisor restart')
    _enable_site()


@task
def make_configs():
    """Create configuration files, but do not upload"""
    _deploy_configs(upload=False)


@task
def update_config():
    """Update the configuration files for services and restart site."""
    stop()
    _deploy_configs()
    start()


def _deploy_configs(user_name=None, user_group=None, upload=True):
    """
    Creates new configs for webserver and services and uploads them to webserver.
    If a custom version of config exists locally that is newer than the template config,
    a new config file will not be created from template.
    """
    site_url = env.site_url
    user_name = user_name or site_url.replace('.', '_')
    user_group = user_group or LINUXGROUP
    configs = _get_configs(site_url)
    for service in configs:  # services are webserver, wsgi service and so on.
        config = configs[service]
        template = config['template']  # template config file
        target = join(
            dirname(template),
            config['filename'])  # name for parsed config file
        # server filepath to place config file. Outside git repo.
        destination = join(config['target folder'], config['filename'])
        if not os.path.exists(target) or os.path.getctime(
                target) < os.path.getctime(template):
            # Generate config file from template if a newer custom file does not exist.
            # use sed to change variable names that will differ between
            # deployments and sites.
            local((
                'cat "{template}" | '
                'sed "s/SITEURL/{url}/g" | '
                'sed "s/USERNAME/{user}/g" | '
                'sed "s/USERGROUP/{group}/g" > '
                '"{filename}"'
            ).format(
                template=template,
                url=site_url,
                user=user_name,
                group=user_group,
                filename=target,
            ))
        if upload:
            # upload config file
            put(target, destination, use_sudo=True)
            with shell_env(FILENAME=destination):
                # run command to make service register new config and restart if
                # needed.
                run(config['install'])


def _enable_site(start=True):
    """Start webserver and enable configuration and services to serve the site.

    if start=False, stops the wsgi-server and disable nginx  for the site.
    """
    command = 'start' if start else 'stop'
    configs = _get_configs()
    for service in configs.values():
        run(service[command])


def _upload_postactivate(postactivate_file, venv_folder, bin_folder):
    """Uploads postactivate shell script file to server."""
    # full filepath for the uploaded file.
    postactivate_path = '{bin}/postactivate'.format(bin=bin_folder,)
    # full filepath for python virtual environment activation shellscript on
    # the server.
    activate_path = '{venv}/bin/activate'.format(venv=venv_folder,)
    # add bash command to activate shellscript to source (run) postactivate
    # script when the virtualenvironment is activated.
    append(
        activate_path,
        'source {postactivate}'.format(
            postactivate=postactivate_path,
        ))
    # upload file.
    put(postactivate_file, postactivate_path)


def _folders_and_permissions(folders):
    """Ensure basic file structure in project."""
    site_folder = folders['site']

    run('mkdir -p {folder_paths}'.format(
        folder_paths=' '.join(folders.values())))

    sudo('chown -R :{group} {site_folder}'.format(
        group=LINUXGROUP,
        site_folder=site_folder))


def _create_linux_user(username, group):
    """Create a linux user to run programs and own files on the webserver."""
    # Bash command id user returns error code 1 if user does not exist and code
    # 0 if user exists. To avoid Fabric raising an exception on an expected
    # shell error, return code ($?) is echoded to stdout and passed to python as
    # a string.
    user_exists = run(
        'id {linux_user}; echo $?'.format(
            linux_user=username,
        ))
    user_exists = user_exists.split()[-1] == '0'
    if not user_exists:
        # Create new group if it doesn't exist
        sudo((
            'groupadd --force {linux_group}'
        ).format(
            linux_group=group,
        ))
        # Create user and add to the default group.
        sudo((
            'useradd --shell /bin/bash '
            '-g {linux_group} -M -c '
            '"runs gunicorn for {site_url}" {linux_user}'
        ).format(
            linux_group=group,
            site_url=env.site_url,
            linux_user=username
        ))


def _postgres(command, settings=None, sudo_user=POSTGRESQL_USER):
    """Run command as postgres."""
    if settings is None:
        settings = {}
    parsed_command = command.format(**settings)
    with env_settings(
        shell=env.shell.replace(' -l', ''),
        sudo_user=sudo_user,
    ):
        result = sudo(parsed_command)
    return result


def _drop_postgres_db(db_name, backup=True):
    """Delete database and user. Dumps the database to file before deleting"""
    settings = {
        'db_name': db_name,
        'db_user': db_name,
        'site_folder': _get_folders()['site'],
    }
    if backup:
        _postgres(
            'pg_dump -Fc {db_name} > {site_folder}'
            '/{db_name}_$(date +"%Y-%m-%d").sql',
            settings,
            user=db_name,
        )
    _postgres('psql -c "DROP DATABASE {db_name}"', settings)
    _postgres('psql -c "DROP USER {db_user}"', settings)


def _create_postgres_db(settings):
    """
    Create postgres database and user for the django deployment.
    Will also change that user's postgres password.
    """
    create_db = _postgres(
        'psql "{db_name}" -c "" || echo "does not exist"',
        settings)

    if create_db:
        # create user and database if they do not exist
        _postgres('psql -c "DROP ROLE IF EXISTS {db_user};"', settings)
        _postgres(
            'psql -c "CREATE ROLE {db_user}'
            ' NOSUPERUSER CREATEDB NOCREATEROLE LOGIN;"',
            settings)
        _postgres(
            'psql -c "CREATE DATABASE {db_name}'
            ' WITH OWNER={db_user}  ENCODING=\'utf-8\';"',
            settings)

    # change the password to match with postactivate file
    _postgres(
        'psql -c "ALTER ROLE {db_user} WITH PASSWORD \'{db_password}\';"',
        settings)


def _get_latest_source(source_folder):
    """Updates files on staging server with current git commit on dev branch."""
    current_commit = local('git log -n 1 --format=%H', capture=True)

    if not exists(source_folder + '/.git'):
        run('git clone {} {}'.format(REPO_URL, source_folder))

    git_status = local('git status', capture=True)
    if not (
        'vagrant' in env.site_url or
        'local' in env.site_url
    ) and (
        'nothing to commit' not in git_status or
        'branch is ahead' in git_status
    ):
        if not confirm(
            'There are changes in the local repo that have been pushed.\n'
            'Do you want to continue deploying to the server?',
            default=False,):
            abort('please commit and push changes.')

    with cd(source_folder):
        run('git fetch && git reset --hard {}'.format(current_commit))


def _create_virtualenv(folders):
    """Create python virtual environment."""
    # This file will exist if the virtual env is already created.
    venv_python_bin = os.path.join(folders['venv'], 'bin', 'python')

    if not exists(venv_python_bin):
        commands = [
            '{virtualenv_binary} {venv}',  # create venv
            'ln -fs {venv} {venvs}',  # symlink to $WORKON_HOME folder
            'echo {source} > {venv}/.project',  # create .project file
        ]
        kwargs = folders.copy()
        kwargs['virtualenv_binary'] = PYVENV

        for command in commands:
            run(command.format(**kwargs))


def _update_virtualenv(source_folder, venv_folder):
    """Install required python packages from pip requirements file."""
    run('{venv}/bin/pip install -vr {source}/requirements.txt'.format(
        venv=venv_folder, source=source_folder, ))


def _update_npm_and_bower(folders):
    """Install npm and bower dependencies"""
    with cd(folders['site']):
        # NPM only wants to install bower_modules into the same folder that
        # package.json is in. To avoid putting all the node packages into the
        # source folder, the json files are symlinked to the parent folder
        # before installing bower and npm dependencies.
        run('ln -sf source/package.json .')
        run('ln -sf source/bower.json .')
        # Install node and bower dependencies
        run('npm install')
        run('node_modules/.bin/bower install')
        # Clean up symlinks.
        # run('rm package.json')
        # run('rm bower.json')


def _gulp_build(source_folder):
    """Build with gulp"""
    with cd(source_folder):
        run('source {venv}/bin/activate && gulp production'.format(
            venv=_get_folders(env.site_url)['venv']))


def _collectstatic(venv_folder):
    """Run django collectstatic on server."""
    django_admin('collectstatic', '--noinput')


def _update_database(venv_folder):
    """Run database migrations if required by changed apps."""
    django_admin('migrate', '--noinput')


def _fix_permissions(folder):
    """Fix folder permissions"""
    sudo('')


def run_bg(cmd, before=None, sockname="dtach", use_sudo=False):
    """Run a command in the background using dtach

    :param cmd: The command to run
    :param output_file: The file to send all of the output to.
    :param before: The command to run before the dtach. E.g. exporting
                   environment variable
    :param sockname: The socket name to use for the temp file
    :param use_sudo: Whether or not to use sudo
    """
    if not exists("/usr/bin/dtach"):
        sudo("apt-get install dtach")
    if before:
        cmd = "{}; dtach -n `mktemp -u /tmp/{}.XXXX` {}".format(
            before, sockname, cmd)
    else:
        cmd = "dtach -n `mktemp -u /tmp/{}.XXXX` {}".format(sockname, cmd)
    if use_sudo:
        return sudo(cmd)
    else:
        return run(cmd)
