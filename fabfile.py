from fabric.api import env, sudo, run, prefix, cd
import settings as ec2_settings

env.user = 'ubuntu'
env.key_filename = '{}.pem'.format(ec2_settings.KEY_NAME)

if not hasattr(env, 'code_branch'):
    env.code_branch = 'master'


def first_time_setup():
    sudo('apt-get install -y openjdk-6-jre-headless')
    if run('ls commcare-hq', quiet=True).failed:
        run('git clone --depth=50 git://github.com/dimagi/commcare-hq.git')
    if run('ls venv', quiet=True).failed:
        run('virtualenv venv')
    sudo('apt-get install -y moreutils libblas-dev liblapack-dev')
    with prefix('source ~/venv/bin/activate'), cd('commcare-hq'):
        run('pip install coverage unittest2 mock --use-mirrors')

    pg_hba_filepath = '/etc/postgresql/9.1/main/pg_hba.conf'
    pg_hba_lines = [
        'local   all             postgres                                trust'
        'host    all             postgres        127.0.0.1/32            trust'
    ]
    sudo('rm {}'.format(pg_hba_filepath))
    for line in pg_hba_lines:
        sudo('echo "{}" > {}'.format(line, pg_hba_filepath))
    sudo('service postgresql restart')
    with prefix('source ~/venv/bin/activate'), cd('commcare-hq'):
        run('bash -e .travis/misc-setup.sh', warn_only=True)


def install():
    run('curl -X PUT http://localhost:5984/commcarehq_test')
    with prefix('source ~/venv/bin/activate'), cd('commcare-hq'):
        run('git fetch'.format(env.code_branch))
        run('git reset --hard origin/{}'.format(env.code_branch))
        run('git clean -ffd')
        run('bash scripts/uninstall-requirements.sh')
        run('pip install --exists-action w -r requirements/requirements.txt --use-mirrors --timeout 60')
        run('cp .travis/localsettings.py localsettings.py')

        run('rm InsecureTestingKeyStore', quiet=True)
        run("keytool -genkey"
            " -keyalg RSA"
            " -keysize 2048"
            " -validity 10000"
            " -alias javarosakey"
            " -keypass onetwothreefourfive"
            " -keystore InsecureTestingKeyStore"
            " -storepass onetwothreefourfive"
            " -dname 'CN=Foo, OU=Bar, O=Bizzle, L=Bazzle, ST=Bingle, C=US'")


def script():
    if not hasattr(env, 'testargs'):
        env.testargs = ''
    with prefix('source ~/venv/bin/activate'), cd('commcare-hq'):
        run('git submodule update --init --recursive')
        run("time coverage run manage.py test --noinput --traceback {}".format(env.testargs))
