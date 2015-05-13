from collections import namedtuple
import boto.ec2
from .exceptions import NoMatchingStoppedInstances


EC2InstanceSpec = namedtuple(
    'EC2InstanceSpec', ['image_id', 'instance_type', 'key_name', 'security_groups'])


class Worker(object):

    def __init__(self, id, state, state_code, dns_name):
        self.id = id
        self.state = state
        self.state_code = state_code
        self.dns_name = dns_name

    @classmethod
    def from_boto(cls, instance):
        return Worker(
            id=instance.id,
            state=instance.state,
            state_code=instance.state_code,
            dns_name=instance.dns_name,
        )


class EC2(object):
    def __init__(self, region_name, aws_access_key_id, aws_secret_access_key):
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self._connection = None

    def connect(self):
        self._connection = boto.ec2.connect_to_region(
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        # return self for chaining with init
        return self

    @property
    def connection(self):
        if not self._connection:
            self.connect()
        return self._connection

    def create_instance(self, instance_spec, tags=None):
        """
        instance_spec is an EC2InstanceSpec object
        (or anther implementing that interface)
        """
        result = self.connection.run_instances(**instance_spec._asdict())
        [instance] = result.instances
        if tags:
            self.connection.create_tags(instance.id, tags=tags)
        return Worker.from_boto(instance)

    def get_all_instances(self, tags=None):
        if tags:
            # prefix all of the tag keys with 'tag:'
            filters = {'tag:{}'.format(key): value
                       for key, value in tags.items()}
            result = self.connection.get_all_instances(filters=filters)
        else:
            result = self.connection.get_all_instances()
        return [Worker.from_boto(instance)
                for res in result for instance in res.instances]

    def terminate_instances(self, instances):
        return self.connection.terminate_instances(instances)

    def stop_instances(self, instances):
        if instances:
            return self.connection.stop_instances(instances)
        else:
            return []

    def start_stopped_instance(self, tags=None):
        """
        Find a matching stopped instance and start it

        raises NoMatchingStoppedInstances

        """
        for instance in self.get_all_instances(tags=tags):
            if instance.state == 'stopped':
                [started_instance] = self.connection.start_instances(instance.id)
                return Worker.from_boto(started_instance)
        raise NoMatchingStoppedInstances()
