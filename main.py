import boto.ec2
import settings
import logging

logging.basicConfig(level=logging.INFO)

conn = boto.ec2.connect_to_region(
    settings.REGION_NAME,
    aws_access_key_id=settings.ACCESS_KEY_ID,
    aws_secret_access_key=settings.SECRET_ACCESS_KEY,
)


def new_instance():
    result = conn.run_instances(
        settings.AMI,
        instance_type=settings.INSTANCE_TYPE,
        key_name=settings.KEY_NAME,
        security_groups=settings.SECURITY_GROUPS,
    )
    [instance] = result.instances
    conn.create_tags(instance.id, tags={'app': 'buildserver'})
    return instance


def stop_all_instances():
    to_stop = []
    other = []

    for instance in get_all_instances():
        if instance.state == 'terminated':
            continue
        elif instance.state == 'stopped':
            other.append(instance.id)
        else:
            to_stop.append(instance.id)

    if to_stop:
        conn.stop_instances(to_stop)
        logging.info('the following instances have been stopped: {}'.format(', '.join(to_stop)))
    else:
        logging.info('all instances are already stopped')

    if other:
        logging.info('the following instances were already stopped: {}'.format(', '.join(other)))


def stop_instance(instance_id):
    return conn.stop_instances(instance_id)


def terminate_all_instances():
    to_kill = []

    for instance in get_all_instances():
        to_kill.append(instance.id)
    if to_kill:
        conn.terminate_instances(to_kill)
        logging.info('the following instances have been terminated: {}'.format(', '.join(to_kill)))
    else:
        logging.info('no instances to terminate')


def terminate_instance(instance_id):
    return conn.terminate_instances(instance_id)


def start_instance():
    for instance in get_all_instances():
        if instance.state == 'stopped':
            [result] = conn.start_instances(instance.id)
            return result
    return new_instance()


def get_all_instances():
    return [instance for res in conn.get_all_instances(filters={'tag:app': 'buildserver'}) for instance in res.instances]


def format_instance(instance):
    return '[{}] {}({}) at {}'.format(instance.id, instance.state, instance.state_code, instance.dns_name or "<no dns>")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'stop-all':
            stop_all_instances()
        elif command == 'stop':
            instance_id = sys.argv[2]
            stop_instance(instance_id)
        elif command == 'terminate-all':
            terminate_all_instances()
        elif command == 'terminate':
            instance_id = sys.argv[2]
            terminate_instance(instance_id)
        elif command == 'status':
            for instance in get_all_instances():
                if '--dns' in sys.argv:
                    print instance.dns_name
                else:
                    print format_instance(instance)
        elif command == 'start':
            instance = start_instance()
            print format_instance(instance)
        elif command == 'new':
            instance = new_instance()
            print format_instance(instance)
        elif command == 'shell':
            import ipdb; ipdb.set_trace()
