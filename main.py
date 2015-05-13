from ec2poolmanager import EC2, NoMatchingStoppedInstances, EC2InstanceSpec
import settings
import logging

logging.basicConfig(level=logging.INFO)

ec2 = EC2(
    settings.REGION_NAME,
    aws_access_key_id=settings.ACCESS_KEY_ID,
    aws_secret_access_key=settings.SECRET_ACCESS_KEY,
).connect()

instance_spec = EC2InstanceSpec(
    image_id=settings.AMI,
    instance_type=settings.INSTANCE_TYPE,
    key_name=settings.KEY_NAME,
    security_groups=settings.SECURITY_GROUPS,
)


def new_instance():
    return ec2.create_instance(instance_spec, tags={'app': 'buildserver'})


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
        ec2.stop_instances(to_stop)
        logging.info('the following instances have been stopped: {}'.format(', '.join(to_stop)))
    else:
        logging.info('all instances are already stopped')

    if other:
        logging.info('the following instances were already stopped: {}'.format(', '.join(other)))


def stop_instance(instance_id):
    return ec2.stop_instances(instance_id)


def terminate_all_instances():
    to_kill = []

    for instance in get_all_instances():
        to_kill.append(instance.id)
    if to_kill:
        ec2.terminate_instances(to_kill)
        logging.info('the following instances have been terminated: {}'.format(', '.join(to_kill)))
    else:
        logging.info('no instances to terminate')


def terminate_instance(instance_id):
    return ec2.terminate_instances(instance_id)


def start_instance():
    try:
        return ec2.start_stopped_instance(tags={'app': 'buildserver'})
    except NoMatchingStoppedInstances:
        return new_instance()


def get_all_instances():
    return ec2.get_all_instances(tags={'app': 'buildserver'})


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
