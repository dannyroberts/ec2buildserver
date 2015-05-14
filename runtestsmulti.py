import functools
from itertools import izip_longest
import os
import subprocess
import uuid
from const import TEST_APPS
from ec2poolmanager import Pool, Group
from main import instance_spec, ec2


def call_fab_suprocess(dns, testargs, log_home):
    print testargs
    command = ['fab', '-H', dns, 'script', '--set',
               'testargs={}'.format(testargs)]
    stdout = open(os.path.join(log_home, '{}.out'.format(testargs)), 'w')
    stderr = open(os.path.join(log_home, '{}.err'.format(testargs)), 'w')
    p = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                         close_fds=True)
    exit_code = p.wait()
    with open(os.path.join(log_home, '{}.exit'.format(testargs)), 'w') as exit_code_f:
        exit_code_f.write(str(exit_code))
        exit_code_f.write('\n')
    return exit_code

pool = Pool(ec2=ec2, worker_spec=instance_spec, max_workers=10,
            tags={'app': 'buildserver'})


def chunked(things, n):
    return izip_longest(*[iter(things)] * n)


def run_tests():
    job_id = uuid.uuid4().hex
    print job_id
    path = os.path.join('log', job_id)
    os.mkdir(path)
    group = Group(pool)
    for app_labels in chunked(TEST_APPS, 3):
        app_labels = filter(None, app_labels)
        callback = functools.partial(call_fab_suprocess,
                                     testargs=' '.join(app_labels),
                                     log_home=path)
        group.add(callback)

    group.join()


if __name__ == '__main__':
    run_tests()
