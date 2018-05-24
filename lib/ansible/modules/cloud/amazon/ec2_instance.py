#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ec2_instance
short_description: Create & manage EC2 instances
description:
    - Gather facts about ec2 instances in AWS
version_added: "2.5"
author:
  - Ryan Scott Brown, @ryansb
requirements: [ "boto3", "botocore" ]
options:
  instance_ids:
    description:
      - If you specify one or more instance IDs, only instances that have the specified IDs are returned.
  state:
    description:
      - Goal state for the instances
    choices: [present, terminated, running, started, stopped, restarted, rebooted, absent]
    default: present
  wait:
    description:
      - Whether or not to wait for the desired state (use wait_timeout to customize this)
    default: true
  wait_timeout:
    description:
      - How long to wait (in seconds) for the instance to finish booting/terminating
    default: 600
  instance_type:
    description:
      - Instance type to use for the instance, see U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html)
        Only required when instance is not already present
    default: t2.micro
  user_data:
    description:
      - Opaque blob of data which is made available to the ec2 instance
  tower_callback:
    description:
      - Preconfigured user-data to enable an instance to perform a Tower callback.
      - Requires parameters I(tower_callback.tower_address), I(tower_callback.job_template_id), and I(tower_callback.host_config_key).
      - Mutually exclusive with I(user_data).
      - For Windows instances, to enable remote access via Ansible set I(tower_callback.windows) to true, and optionally set an admin password.
      - If using 'windows' and 'set_password', callback to Tower will not be performed but the instance will be ready to receive winrm connections from Ansible.
  tags:
    description:
      - A hash/dictionary of tags to add to the new instance or to add/remove from an existing one.
  purge_tags:
    description:
      - Delete any tags not specified in the task that are on the instance.
        This means you have to specify all the desired tags on each task affecting an instance.
    default: false
  image:
    description:
      - An image to use for the instance. The ec2_ami_facts module may be used to retrieve images.
        One of I(image) or I(image_id) are required when instance is not already present.
      - Complex object containing I(image.id), I(image.ramdisk), and I(image.kernel).
      - I(image.id) is the AMI ID.
      - I(image.ramdisk) overrides the AMI's default ramdisk ID.
      - I(image.kernel) is a string AKI to override the AMI kernel.
  image_id:
    description:
       - I(ami) ID to use for the instance. One of I(image) or I(image_id) are required when instance is not already present.
       - This is an alias for I(image.id).
  security_groups:
    description:
      - A list of security group IDs or names (strings). Mutually exclusive with I(security_group).
  security_group:
    description:
      - A security group ID or name. Mutually exclusive with I(security_groups).
  name:
    description:
      - The Name tag for the instance.
  vpc_subnet_id:
    description:
      - The subnet ID in which to launch the instance (VPC)
        If none is provided, ec2_instance will chose the default zone of the default VPC
    aliases: ['subnet_id']
  network:
    description:
      - Either a dictionary containing the key 'interfaces' corresponding to a list of network interface IDs or
        containing specifications for a single network interface.
      - If specifications for a single network are given, accepted keys are assign_public_ip (bool),
        private_ip_address (str), ipv6_addresses (list), source_dest_check (bool), description (str),
        delete_on_termination (bool), device_index (int), groups (list of security group IDs),
        private_ip_addresses (list), subnet_id (str).
      - I(network.interfaces) should be a list of ENI IDs (strings) or a list of objects containing the key I(id).
      - Use the ec2_eni to create ENIs with special settings.
  volumes:
    description:
    - A list of block device mappings, by default this will always use the AMI root device so the volumes option is primarily for adding more storage.
    - A mapping contains the (optional) keys device_name, virtual_name, ebs.device_type, ebs.device_size, ebs.kms_key_id,
      ebs.iops, and ebs.delete_on_termination.
    - For more information about each parameter, see U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_BlockDeviceMapping.html)
  launch_template:
    description:
      - The EC2 launch template to base instance configuration on.
      - I(launch_template.id) the ID or the launch template (optional if name is specified)
      - I(launch_template.name) the pretty name of the launch template (optional if id is specified)
      - I(launch_template.version) the specific version of the launch template to use. If unspecified, the template default is chosen.
  key_name:
    description:
    - Name of the SSH access key to assign to the instance - must exist in the region the instance is created.
  availability_zone:
    description:
    - Specify an availability zone to use the default subnet it. Useful if not specifying the I(vpc_subnet_id) parameter.
    - If no subnet, ENI, or availability zone is provided, the default subnet in the default VPC will be used in the first AZ (alphabetically sorted).
  instance_initiated_shutdown_behavior:
    description:
      - Whether to stop or terminate an instance upon shutdown.
    choices: ['stop', 'terminate']
  tenancy:
    description:
      - What type of tenancy to allow an instance to use. Default is shared tenancy. Dedicated tenancy will incur additional charges.
    choices: ['dedicated', 'default']
  termination_protection:
    description:
      - Whether to enable termination protection.
        This module will not terminate an instance with termination protection active, it must be turned off first.
  cpu_credit_specification:
    description:
      - For T2 series instances, choose whether to allow increased charges to buy CPU credits if the default pool is depleted.
      - Choose I(unlimited) to enable buying additional CPU credits.
    choices: [unlimited, standard]
  detailed_monitoring:
    description:
      - Whether to allow detailed cloudwatch metrics to be collected, enabling more detailed alerting.
  ebs_optimized:
    description:
      - Whether instance is should use optimized EBS volumes, see U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSOptimized.html)
  filters:
    description:
      - A dict of filters to apply when deciding whether existing instances match and should be altered. Each dict item
        consists of a filter key and a filter value. See
        U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html)
        for possible filters. Filter names and values are case sensitive.
        By default, instances are filtered for counting by their "Name" tag, base AMI, state (running, by default), and
        subnet ID. Any queryable filter can be used. Good candidates are specific tags, SSH keys, or security groups.
    default: {"tag:Name": "<provided-Name-attribute>", "subnet-id": "<provided-or-default subnet>"}
  instance_role:
    description:
    - The ARN or name of an EC2-enabled instance role to be used. If a name is not provided in arn format
      then the ListInstanceProfiles permission must also be granted.
      U(https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListInstanceProfiles.html) If no full ARN is provided,
      the role with a matching name will be used from the active AWS account.

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Terminate every instance in a region. Use with caution.
- ec2_instance_facts:
    state: absent
    filters:
      instance-state-name: running

# Gather facts about all instances in AZ ap-southeast-2a
- ec2_instance_facts:
    filters:
      availability-zone: ap-southeast-2a

# Gather facts about a particular instance using ID
- ec2_instance_facts:
    instance_ids:
      - i-12345678

# Gather facts about any instance with a tag key Name and value Example
- ec2_instance_facts:
    filters:
      "tag:Name": Example
'''

RETURN = '''
instances:
    description: a list of ec2 instances
    returned: always
    type: complex
    contains:
        ami_launch_index:
            description: The AMI launch index, which can be used to find this instance in the launch group.
            returned: always
            type: int
            sample: 0
        architecture:
            description: The architecture of the image
            returned: always
            type: string
            sample: x86_64
        block_device_mappings:
            description: Any block device mapping entries for the instance.
            returned: always
            type: complex
            contains:
                device_name:
                    description: The device name exposed to the instance (for example, /dev/sdh or xvdh).
                    returned: always
                    type: string
                    sample: /dev/sdh
                ebs:
                    description: Parameters used to automatically set up EBS volumes when the instance is launched.
                    returned: always
                    type: complex
                    contains:
                        attach_time:
                            description: The time stamp when the attachment initiated.
                            returned: always
                            type: string
                            sample: "2017-03-23T22:51:24+00:00"
                        delete_on_termination:
                            description: Indicates whether the volume is deleted on instance termination.
                            returned: always
                            type: bool
                            sample: true
                        status:
                            description: The attachment state.
                            returned: always
                            type: string
                            sample: attached
                        volume_id:
                            description: The ID of the EBS volume
                            returned: always
                            type: string
                            sample: vol-12345678
        client_token:
            description: The idempotency token you provided when you launched the instance, if applicable.
            returned: always
            type: string
            sample: mytoken
        ebs_optimized:
            description: Indicates whether the instance is optimized for EBS I/O.
            returned: always
            type: bool
            sample: false
        hypervisor:
            description: The hypervisor type of the instance.
            returned: always
            type: string
            sample: xen
        iam_instance_profile:
            description: The IAM instance profile associated with the instance, if applicable.
            returned: always
            type: complex
            contains:
                arn:
                    description: The Amazon Resource Name (ARN) of the instance profile.
                    returned: always
                    type: string
                    sample: "arn:aws:iam::000012345678:instance-profile/myprofile"
                id:
                    description: The ID of the instance profile
                    returned: always
                    type: string
                    sample: JFJ397FDG400FG9FD1N
        image_id:
            description: The ID of the AMI used to launch the instance.
            returned: always
            type: string
            sample: ami-0011223344
        instance_id:
            description: The ID of the instance.
            returned: always
            type: string
            sample: i-012345678
        instance_type:
            description: The instance type size of the running instance.
            returned: always
            type: string
            sample: t2.micro
        key_name:
            description: The name of the key pair, if this instance was launched with an associated key pair.
            returned: always
            type: string
            sample: my-key
        launch_time:
            description: The time the instance was launched.
            returned: always
            type: string
            sample: "2017-03-23T22:51:24+00:00"
        monitoring:
            description: The monitoring for the instance.
            returned: always
            type: complex
            contains:
                state:
                    description: Indicates whether detailed monitoring is enabled. Otherwise, basic monitoring is enabled.
                    returned: always
                    type: string
                    sample: disabled
        network_interfaces:
            description: One or more network interfaces for the instance.
            returned: always
            type: complex
            contains:
                association:
                    description: The association information for an Elastic IPv4 associated with the network interface.
                    returned: always
                    type: complex
                    contains:
                        ip_owner_id:
                            description: The ID of the owner of the Elastic IP address.
                            returned: always
                            type: string
                            sample: amazon
                        public_dns_name:
                            description: The public DNS name.
                            returned: always
                            type: string
                            sample: ""
                        public_ip:
                            description: The public IP address or Elastic IP address bound to the network interface.
                            returned: always
                            type: string
                            sample: 1.2.3.4
                attachment:
                    description: The network interface attachment.
                    returned: always
                    type: complex
                    contains:
                        attach_time:
                            description: The time stamp when the attachment initiated.
                            returned: always
                            type: string
                            sample: "2017-03-23T22:51:24+00:00"
                        attachment_id:
                            description: The ID of the network interface attachment.
                            returned: always
                            type: string
                            sample: eni-attach-3aff3f
                        delete_on_termination:
                            description: Indicates whether the network interface is deleted when the instance is terminated.
                            returned: always
                            type: bool
                            sample: true
                        device_index:
                            description: The index of the device on the instance for the network interface attachment.
                            returned: always
                            type: int
                            sample: 0
                        status:
                            description: The attachment state.
                            returned: always
                            type: string
                            sample: attached
                description:
                    description: The description.
                    returned: always
                    type: string
                    sample: My interface
                groups:
                    description: One or more security groups.
                    returned: always
                    type: complex
                    contains:
                        - group_id:
                              description: The ID of the security group.
                              returned: always
                              type: string
                              sample: sg-abcdef12
                          group_name:
                              description: The name of the security group.
                              returned: always
                              type: string
                              sample: mygroup
                ipv6_addresses:
                    description: One or more IPv6 addresses associated with the network interface.
                    returned: always
                    type: complex
                    contains:
                        - ipv6_address:
                              description: The IPv6 address.
                              returned: always
                              type: string
                              sample: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
                mac_address:
                    description: The MAC address.
                    returned: always
                    type: string
                    sample: "00:11:22:33:44:55"
                network_interface_id:
                    description: The ID of the network interface.
                    returned: always
                    type: string
                    sample: eni-01234567
                owner_id:
                    description: The AWS account ID of the owner of the network interface.
                    returned: always
                    type: string
                    sample: 01234567890
                private_ip_address:
                    description: The IPv4 address of the network interface within the subnet.
                    returned: always
                    type: string
                    sample: 10.0.0.1
                private_ip_addresses:
                    description: The private IPv4 addresses associated with the network interface.
                    returned: always
                    type: complex
                    contains:
                        - association:
                              description: The association information for an Elastic IP address (IPv4) associated with the network interface.
                              returned: always
                              type: complex
                              contains:
                                  ip_owner_id:
                                      description: The ID of the owner of the Elastic IP address.
                                      returned: always
                                      type: string
                                      sample: amazon
                                  public_dns_name:
                                      description: The public DNS name.
                                      returned: always
                                      type: string
                                      sample: ""
                                  public_ip:
                                      description: The public IP address or Elastic IP address bound to the network interface.
                                      returned: always
                                      type: string
                                      sample: 1.2.3.4
                          primary:
                              description: Indicates whether this IPv4 address is the primary private IP address of the network interface.
                              returned: always
                              type: bool
                              sample: true
                          private_ip_address:
                              description: The private IPv4 address of the network interface.
                              returned: always
                              type: string
                              sample: 10.0.0.1
                source_dest_check:
                    description: Indicates whether source/destination checking is enabled.
                    returned: always
                    type: bool
                    sample: true
                status:
                    description: The status of the network interface.
                    returned: always
                    type: string
                    sample: in-use
                subnet_id:
                    description: The ID of the subnet for the network interface.
                    returned: always
                    type: string
                    sample: subnet-0123456
                vpc_id:
                    description: The ID of the VPC for the network interface.
                    returned: always
                    type: string
                    sample: vpc-0123456
        placement:
            description: The location where the instance launched, if applicable.
            returned: always
            type: complex
            contains:
                availability_zone:
                    description: The Availability Zone of the instance.
                    returned: always
                    type: string
                    sample: ap-southeast-2a
                group_name:
                    description: The name of the placement group the instance is in (for cluster compute instances).
                    returned: always
                    type: string
                    sample: ""
                tenancy:
                    description: The tenancy of the instance (if the instance is running in a VPC).
                    returned: always
                    type: string
                    sample: default
        private_dns_name:
            description: The private DNS name.
            returned: always
            type: string
            sample: ip-10-0-0-1.ap-southeast-2.compute.internal
        private_ip_address:
            description: The IPv4 address of the network interface within the subnet.
            returned: always
            type: string
            sample: 10.0.0.1
        product_codes:
            description: One or more product codes.
            returned: always
            type: complex
            contains:
                - product_code_id:
                      description: The product code.
                      returned: always
                      type: string
                      sample: aw0evgkw8ef3n2498gndfgasdfsd5cce
                  product_code_type:
                      description: The type of product code.
                      returned: always
                      type: string
                      sample: marketplace
        public_dns_name:
            description: The public DNS name assigned to the instance.
            returned: always
            type: string
            sample:
        public_ip_address:
            description: The public IPv4 address assigned to the instance
            returned: always
            type: string
            sample: 52.0.0.1
        root_device_name:
            description: The device name of the root device
            returned: always
            type: string
            sample: /dev/sda1
        root_device_type:
            description: The type of root device used by the AMI.
            returned: always
            type: string
            sample: ebs
        security_groups:
            description: One or more security groups for the instance.
            returned: always
            type: complex
            contains:
                - group_id:
                      description: The ID of the security group.
                      returned: always
                      type: string
                      sample: sg-0123456
                - group_name:
                      description: The name of the security group.
                      returned: always
                      type: string
                      sample: my-security-group
        network.source_dest_check:
            description: Indicates whether source/destination checking is enabled.
            returned: always
            type: bool
            sample: true
        state:
            description: The current state of the instance.
            returned: always
            type: complex
            contains:
                code:
                    description: The low byte represents the state.
                    returned: always
                    type: int
                    sample: 16
                name:
                    description: The name of the state.
                    returned: always
                    type: string
                    sample: running
        state_transition_reason:
            description: The reason for the most recent state transition.
            returned: always
            type: string
            sample:
        subnet_id:
            description: The ID of the subnet in which the instance is running.
            returned: always
            type: string
            sample: subnet-00abcdef
        tags:
            description: Any tags assigned to the instance.
            returned: always
            type: dict
            sample:
        virtualization_type:
            description: The type of virtualization of the AMI.
            returned: always
            type: string
            sample: hvm
        vpc_id:
            description: The ID of the VPC the instance is in.
            returned: always
            type: dict
            sample: vpc-0011223344
'''

import re
import uuid
import string
import textwrap
from collections import namedtuple

try:
    import boto3
    import botocore.exceptions
except ImportError:
    pass

from ansible.module_utils.six import text_type
from ansible.module_utils._text import to_bytes, to_native
import ansible.module_utils.ec2 as ec2_utils
from ansible.module_utils.ec2 import (boto3_conn,
                                      ec2_argument_spec,
                                      get_aws_connection_info,
                                      AWSRetry,
                                      ansible_dict_to_boto3_filter_list,
                                      compare_aws_tags,
                                      boto3_tag_list_to_ansible_dict,
                                      ansible_dict_to_boto3_tag_list,
                                      camel_dict_to_snake_dict)

from ansible.module_utils.aws.core import AnsibleAWSModule

module = None


def tower_callback_script(tower_conf, windows=False, passwd=None):
    script_url = 'https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/ConfigureRemotingForAnsible.ps1'
    if windows and passwd is not None:
        script_tpl = """<powershell>
        $admin = [adsi]("WinNT://./administrator, user")
        $admin.PSBase.Invoke("SetPassword", "{PASS}")
        Invoke-Expression ((New-Object System.Net.Webclient).DownloadString('{SCRIPT}'))
        </powershell>
        """
        return to_native(textwrap.dedent(script_tpl).format(PASS=passwd, SCRIPT=script_url))
    elif windows and passwd is None:
        script_tpl = """<powershell>
        $admin = [adsi]("WinNT://./administrator, user")
        Invoke-Expression ((New-Object System.Net.Webclient).DownloadString('{SCRIPT}'))
        </powershell>
        """
        return to_native(textwrap.dedent(script_tpl).format(PASS=passwd, SCRIPT=script_url))
    elif not windows:
        for p in ['tower_address', 'job_template_id', 'host_config_key']:
            if p not in tower_conf:
                module.fail_json(msg="Incomplete tower_callback configuration. tower_callback.{0} not set.".format(p))

        tpl = string.Template(textwrap.dedent("""#!/bin/bash
        set -x

        retry_attempts=10
        attempt=0
        while [[ $attempt -lt $retry_attempts ]]
        do
          status_code=`curl --max-time 10 -v -k -s -i \
                  --data "host_config_key=${host_config_key}" \
                  https://${tower_address}/api/v1/job_templates/${template_id}/callback/ \
                  | head -n 1 \
                  | awk '{print $2}'`
          if [[ $status_code == 201 ]]
            then
            exit 0
          fi
          attempt=$(( attempt + 1 ))
          echo "$${status_code} received... retrying in 1 minute. (Attempt $${attempt})"
          sleep 60
        done
        exit 1
        """))
        return tpl.safe_substitute(tower_address=tower_conf['tower_address'],
                                   template_id=tower_conf['job_template_id'],
                                   host_config_key=tower_conf['host_config_key'])
    raise NotImplementedError("Only windows with remote-prep or non-windows with tower job callback supported so far.")


@AWSRetry.jittered_backoff()
def manage_tags(match, new_tags, purge_tags, ec2):
    changed = False
    old_tags = boto3_tag_list_to_ansible_dict(match['Tags'])
    tags_to_set, tags_to_delete = compare_aws_tags(
        old_tags, new_tags,
        purge_tags=purge_tags,
    )
    if tags_to_set:
        ec2.create_tags(
            Resources=[match['InstanceId']],
            Tags=ansible_dict_to_boto3_tag_list(tags_to_set))
        changed |= True
    if tags_to_delete:
        delete_with_current_values = dict((k, old_tags.get(k)) for k in tags_to_delete)
        ec2.delete_tags(
            Resources=[match['InstanceId']],
            Tags=ansible_dict_to_boto3_tag_list(delete_with_current_values))
        changed |= True
    return changed


def build_volume_spec(params):
    volumes = params.get('volumes') or []
    return [ec2_utils.snake_dict_to_camel_dict(v, capitalize_first=True) for v in volumes]


def build_network_spec(params, ec2=None):
    """
    Returns list of interfaces [complex]
    Interface type: {
        'AssociatePublicIpAddress': True|False,
        'DeleteOnTermination': True|False,
        'Description': 'string',
        'DeviceIndex': 123,
        'Groups': [
            'string',
        ],
        'Ipv6AddressCount': 123,
        'Ipv6Addresses': [
            {
                'Ipv6Address': 'string'
            },
        ],
        'NetworkInterfaceId': 'string',
        'PrivateIpAddress': 'string',
        'PrivateIpAddresses': [
            {
                'Primary': True|False,
                'PrivateIpAddress': 'string'
            },
        ],
        'SecondaryPrivateIpAddressCount': 123,
        'SubnetId': 'string'
    },
    """
    if ec2 is None:
        ec2 = module.client('ec2')

    interfaces = []
    network = params.get('network') or {}
    if not network.get('interfaces'):
        # they only specified one interface
        spec = {
            'DeviceIndex': 0,
        }
        if network.get('assign_public_ip') is not None:
            spec['AssociatePublicIpAddress'] = network['assign_public_ip']

        if params.get('vpc_subnet_id'):
            spec['SubnetId'] = params['vpc_subnet_id']
        else:
            default_vpc = get_default_vpc(ec2)
            if default_vpc is None:
                raise module.fail_json(
                    msg="No default subnet could be found - you must include a VPC subnet ID (vpc_subnet_id parameter) to create an instance")
            else:
                sub = get_default_subnet(ec2, default_vpc)
                spec['SubnetId'] = sub['SubnetId']

        if network.get('private_ip_address'):
            spec['PrivateIpAddress'] = network['private_ip_address']

        if params.get('security_group') or params.get('security_groups'):
            groups = discover_security_groups(
                group=params.get('security_group'),
                groups=params.get('security_groups'),
                subnet_id=spec['SubnetId'],
                ec2=ec2
            )
            spec['Groups'] = [g['GroupId'] for g in groups]
        # TODO more special snowflake network things

        return [spec]

    # handle list of `network.interfaces` options
    for idx, interface_params in enumerate(network.get('interfaces', [])):
        spec = {
            'DeviceIndex': idx,
        }

        if isinstance(interface_params, text_type):
            # naive case where user gave
            # network_interfaces: [eni-1234, eni-4567, ....]
            # put into normal data structure so we don't dupe code
            interface_params = {'id': interface_params}

        if interface_params.get('id') is not None:
            # if an ID is provided, we don't want to set any other parameters.
            spec['NetworkInterfaceId'] = interface_params['id']
            interfaces.append(spec)
            continue

        spec['DeleteOnTermination'] = interface_params.get('delete_on_termination', True)

        if interface_params.get('ipv6_addresses'):
            spec['Ipv6Addresses'] = [{'Ipv6Address': a} for a in interface_params.get('ipv6_addresses', [])]

        if interface_params.get('private_ip_address'):
            spec['PrivateIpAddress'] = interface_params.get('private_ip_address')

        if interface_params.get('description'):
            spec['Description'] = interface_params.get('description')

        if interface_params.get('subnet_id', params.get('vpc_subnet_id')):
            spec['SubnetId'] = interface_params.get('subnet_id', params.get('vpc_subnet_id'))
        elif not spec.get('SubnetId') and not interface_params['id']:
            # TODO grab a subnet from default VPC
            raise ValueError('Failed to assign subnet to interface {0}'.format(interface_params))

        interfaces.append(spec)
    return interfaces


def warn_if_public_ip_assignment_changed(instance):
    # This is a non-modifiable attribute.
    assign_public_ip = (module.params.get('network') or {}).get('assign_public_ip')
    if assign_public_ip is None:
        return

    # Check that public ip assignment is the same and warn if not
    public_dns_name = instance.get('PublicDnsName')
    if (public_dns_name and not assign_public_ip) or (assign_public_ip and not public_dns_name):
        module.warn(
            "Unable to modify public ip assignment to {0} for instance {1}. "
            "Whether or not to assign a public IP is determined during instance creation.".format(
                assign_public_ip, instance['InstanceId']))


def discover_security_groups(group, groups, parent_vpc_id=None, subnet_id=None, ec2=None):
    if ec2 is None:
        ec2 = module.client('ec2')

    if subnet_id is not None:
        try:
            sub = ec2.describe_subnets(SubnetIds=[subnet_id])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidGroup.NotFound':
                module.fail_json(
                    "Could not find subnet {0} to associate security groups. Please check the vpc_subnet_id and security_groups parameters.".format(
                        subnet_id
                    )
                )
            module.fail_json_aws(e, msg="Error while searching for subnet {0} parent VPC.".format(subnet_id))
        except botocore.exceptions.BotoCoreError as e:
            module.fail_json_aws(e, msg="Error while searching for subnet {0} parent VPC.".format(subnet_id))
        parent_vpc_id = sub['Subnets'][0]['VpcId']

    vpc = {
        'Name': 'vpc-id',
        'Values': [parent_vpc_id]
    }

    # because filter lists are AND in the security groups API,
    # make two separate requests for groups by ID and by name
    id_filters = [vpc]
    name_filters = [vpc]

    if group:
        name_filters.append(
            dict(
                Name='group-name',
                Values=[group]
            )
        )
        if group.startswith('sg-'):
            id_filters.append(
                dict(
                    Name='group-id',
                    Values=[group]
                )
            )
    if groups:
        name_filters.append(
            dict(
                Name='group-name',
                Values=groups
            )
        )
        if [g for g in groups if g.startswith('sg-')]:
            id_filters.append(
                dict(
                    Name='group-id',
                    Values=[g for g in groups if g.startswith('sg-')]
                )
            )

    found_groups = []
    for f_set in (id_filters, name_filters):
        if len(f_set) > 1:
            found_groups.extend(ec2.get_paginator(
                'describe_security_groups'
            ).paginate(
                Filters=f_set
            ).search('SecurityGroups[]'))
    return list(dict((g['GroupId'], g) for g in found_groups).values())


def build_top_level_options(params):
    spec = {}
    if params.get('image_id'):
        spec['ImageId'] = params['image_id']
    elif isinstance(params.get('image'), dict):
        image = params.get('image', {})
        spec['ImageId'] = image.get('id')
        if 'ramdisk' in image:
            spec['RamdiskId'] = image['ramdisk']
        if 'kernel' in image:
            spec['KernelId'] = image['kernel']
    if not spec.get('ImageId') and not params.get('launch_template'):
        module.fail_json(msg="You must include an image_id or image.id parameter to create an instance, or use a launch_template.")

    if params.get('key_name') is not None:
        spec['KeyName'] = params.get('key_name')
    if params.get('user_data') is not None:
        spec['UserData'] = to_native(params.get('user_data'))
    elif params.get('tower_callback') is not None:
        spec['UserData'] = tower_callback_script(
            tower_conf=params.get('tower_callback'),
            windows=params.get('tower_callback').get('windows', False),
            passwd=params.get('tower_callback').get('set_password'),
        )

    if params.get('launch_template') is not None:
        spec['LaunchTemplate'] = {}
        if not params.get('launch_template').get('id') or params.get('launch_template').get('name'):
            module.fail_json(msg="Could not create instance with launch template. Either launch_template.name or launch_template.id parameters are required")

        if params.get('launch_template').get('id') is not None:
            spec['LaunchTemplate']['LaunchTemplateId'] = params.get('launch_template').get('id')
        if params.get('launch_template').get('name') is not None:
            spec['LaunchTemplate']['LaunchTemplateName'] = params.get('launch_template').get('name')
        if params.get('launch_template').get('version') is not None:
            spec['LaunchTemplate']['Version'] = to_native(params.get('launch_template').get('version'))

    if params.get('detailed_monitoring', False):
        spec['Monitoring'] = {'Enabled': True}
    if params.get('cpu_credit_specification') is not None:
        spec['CreditSpecification'] = {'CpuCredits': params.get('cpu_credit_specification')}
    if params.get('tenancy') is not None:
        spec['Placement'] = {'Tenancy': params.get('tenancy')}
    if (params.get('network') or {}).get('ebs_optimized') is not None:
        spec['EbsOptimized'] = params['network'].get('ebs_optimized')
    if params.get('instance_initiated_shutdown_behavior'):
        spec['InstanceInitiatedShutdownBehavior'] = params.get('instance_initiated_shutdown_behavior')
    if params.get('termination_protection') is not None:
        spec['DisableApiTermination'] = params.get('termination_protection')
    return spec


def build_instance_tags(params, propagate_tags_to_volumes=True):
    tags = params.get('tags', {})
    if params.get('name') is not None:
        if tags is None:
            tags = {}
        tags['Name'] = params.get('name')
    return [
        {
            'ResourceType': 'volume',
            'Tags': ansible_dict_to_boto3_tag_list(tags),
        },
        {
            'ResourceType': 'instance',
            'Tags': ansible_dict_to_boto3_tag_list(tags),
        },
    ]


def build_run_instance_spec(params, ec2=None):
    if ec2 is None:
        ec2 = module.client('ec2')

    spec = dict(
        ClientToken=uuid.uuid4().hex,
        MaxCount=1,
        MinCount=1,
    )
    # network parameters
    spec['NetworkInterfaces'] = build_network_spec(params, ec2)
    spec['BlockDeviceMappings'] = build_volume_spec(params)
    spec.update(**build_top_level_options(params))
    spec['TagSpecifications'] = build_instance_tags(params)

    # IAM profile
    if params.get('instance_role'):
        spec['IamInstanceProfile'] = dict(Arn=determine_iam_role(params.get('iam_profile')))

    spec['InstanceType'] = params['instance_type']
    return spec


def await_instances(ids, state='OK'):
    if not module.params.get('wait', True):
        # the user asked not to wait for anything
        return
    state_opts = {
        'OK': 'instance_status_ok',
        'STOPPED': 'instance_stopped',
        'TERMINATED': 'instance_terminated',
        'EXISTS': 'instance_exists',
        'RUNNING': 'instance_running',
    }
    if state not in state_opts:
        module.fail_json(msg="Cannot wait for state {0}, invalid state".format(state))
    waiter = module.client('ec2').get_waiter(state_opts[state])
    try:
        waiter.wait(
            InstanceIds=ids,
            WaiterConfig={
                'Delay': 15,
                'MaxAttempts': module.params.get('wait_timeout', 600) // 15,
            }
        )
    except botocore.exceptions.WaiterConfigError as e:
        module.fail_json(msg="{0}. Error waiting for instances {1} to reach state {2}".format(
            to_native(e), ', '.join(ids), state))
    except botocore.exceptions.WaiterError as e:
        module.warn("Instances {0} took too long to reach state {1}. {2}".format(
            ', '.join(ids), state, to_native(e)))


def diff_instance_and_params(instance, params, ec2=None, skip=None):
    """boto3 instance obj, module params"""
    if ec2 is None:
        ec2 = module.client('ec2')

    if skip is None:
        skip = []

    changes_to_apply = []
    id_ = instance['InstanceId']

    ParamMapper = namedtuple('ParamMapper', ['param_key', 'instance_key', 'attribute_name', 'add_value'])

    def value_wrapper(v):
        return {'Value': v}

    param_mappings = [
        ParamMapper('ebs_optimized', 'EbsOptimized', 'ebsOptimized', value_wrapper),
        ParamMapper('termination_protection', 'DisableApiTermination', 'disableApiTermination', value_wrapper),
        # user data is an immutable property
        # ParamMapper('user_data', 'UserData', 'userData', value_wrapper),
    ]

    for mapping in param_mappings:
        if params.get(mapping.param_key) is not None and mapping.instance_key not in skip:
            value = ec2.describe_instance_attribute(Attribute=mapping.attribute_name, InstanceId=id_)
            if params.get(mapping.param_key) is not None and value[mapping.instance_key]['Value'] != params.get(mapping.param_key):
                arguments = dict(
                    InstanceId=instance['InstanceId'],
                    # Attribute=mapping.attribute_name,
                )
                arguments[mapping.instance_key] = mapping.add_value(params.get(mapping.param_key))
                changes_to_apply.append(arguments)

    if (params.get('network') or {}).get('source_dest_check') is not None:
        # network.source_dest_check is nested, so needs to be treated separately
        check = bool(params.get('network').get('source_dest_check'))
        if instance['SourceDestCheck'] != check:
            changes_to_apply.append(dict(
                InstanceId=instance['InstanceId'],
                SourceDestCheck={'Value': check},
            ))

    return changes_to_apply


def change_network_attachments(instance, params, ec2):
    if (params.get('network') or {}).get('interfaces') is not None:
        new_ids = []
        for inty in params.get('network').get('interfaces'):
            if isinstance(inty, dict) and 'id' in inty:
                new_ids.append(inty['id'])
            elif isinstance(inty, text_type):
                new_ids.append(inty)
        # network.interfaces can create the need to attach new interfaces
        old_ids = [inty['NetworkInterfaceId'] for inty in instance['NetworkInterfaces']]
        to_attach = set(new_ids) - set(old_ids)
        for eni_id in to_attach:
            ec2.attach_network_interface(
                DeviceIndex=new_ids.index(eni_id),
                InstanceId=instance['InstanceId'],
                NetworkInterfaceId=eni_id,
            )
        return bool(len(to_attach))
    return False


def find_instances(ec2, ids=None, filters=None):
    paginator = ec2.get_paginator('describe_instances')
    if ids:
        return list(paginator.paginate(
            InstanceIds=ids,
        ).search('Reservations[].Instances[]'))
    elif filters is None:
        module.fail_json(msg="No filters provided when they were required")
    elif filters is not None:
        for key in filters.keys():
            if not key.startswith("tag:"):
                filters[key.replace("_", "-")] = filters.pop(key)
        return list(paginator.paginate(
            Filters=ansible_dict_to_boto3_filter_list(filters)
        ).search('Reservations[].Instances[]'))
    return []


@AWSRetry.jittered_backoff()
def get_default_vpc(ec2):
    vpcs = ec2.describe_vpcs(Filters=ansible_dict_to_boto3_filter_list({'isDefault': 'true'}))
    if len(vpcs.get('Vpcs', [])):
        return vpcs.get('Vpcs')[0]
    return None


@AWSRetry.jittered_backoff()
def get_default_subnet(ec2, vpc, availability_zone=None):
    subnets = ec2.describe_subnets(
        Filters=ansible_dict_to_boto3_filter_list({
            'vpc-id': vpc['VpcId'],
            'state': 'available',
            'default-for-az': 'true',
        })
    )
    if len(subnets.get('Subnets', [])):
        if availability_zone is not None:
            subs_by_az = dict((subnet['AvailabilityZone'], subnet) for subnet in subnets.get('Subnets'))
            if availability_zone in subs_by_az:
                return subs_by_az[availability_zone]

        # to have a deterministic sorting order, we sort by AZ so we'll always pick the `a` subnet first
        # there can only be one default-for-az subnet per AZ, so the AZ key is always unique in this list
        by_az = sorted(subnets.get('Subnets'), key=lambda s: s['AvailabilityZone'])
        return by_az[0]
    return None


def ensure_instance_state(state, ec2=None):
    if ec2 is None:
        module.client('ec2')
    if state in ('running', 'started'):
        changed, failed, instances = change_instance_state(filters=module.params.get('filters'), desired_state='RUNNING')

        if failed:
            module.fail_json(
                msg="Unable to start instances",
                reboot_success=list(changed),
                reboot_failed=failed)

        module.exit_json(
            msg='Instances started',
            reboot_success=list(changed),
            changed=bool(len(changed)),
            reboot_failed=[],
            instances=[pretty_instance(i) for i in instances],
        )
    elif state in ('restarted', 'rebooted'):
        changed, failed, instances = change_instance_state(
            filters=module.params.get('filters'),
            desired_state='STOPPED')
        changed, failed, instances = change_instance_state(
            filters=module.params.get('filters'),
            desired_state='RUNNING')

        if failed:
            module.fail_json(
                msg="Unable to restart instances",
                reboot_success=list(changed),
                reboot_failed=failed)

        module.exit_json(
            msg='Instances restarted',
            reboot_success=list(changed),
            changed=bool(len(changed)),
            reboot_failed=[],
            instances=[pretty_instance(i) for i in instances],
        )
    elif state in ('stopped',):
        changed, failed, instances = change_instance_state(
            filters=module.params.get('filters'),
            desired_state='STOPPED')

        if failed:
            module.fail_json(
                msg="Unable to stop instances",
                stop_success=list(changed),
                stop_failed=failed)

        module.exit_json(
            msg='Instances stopped',
            stop_success=list(changed),
            changed=bool(len(changed)),
            stop_failed=[],
            instances=[pretty_instance(i) for i in instances],
        )
    elif state in ('absent', 'terminated'):
        terminated, terminate_failed, instances = change_instance_state(
            filters=module.params.get('filters'),
            desired_state='TERMINATED')

        if terminate_failed:
            module.fail_json(
                msg="Unable to terminate instances",
                terminate_success=list(terminated),
                terminate_failed=terminate_failed)
        module.exit_json(
            msg='Instances terminated',
            terminate_success=list(terminated),
            changed=bool(len(terminated)),
            terminate_failed=[],
            instances=[pretty_instance(i) for i in instances],
        )


@AWSRetry.jittered_backoff()
def change_instance_state(filters, desired_state, ec2=None):
    """Takes STOPPED/RUNNING/TERMINATED"""
    if ec2 is None:
        ec2 = module.client('ec2')

    changed = set()
    instances = find_instances(ec2, filters=filters)
    to_change = set(i['InstanceId'] for i in instances)
    unchanged = set()

    for inst in instances:
        try:
            if desired_state == 'TERMINATED':
                # TODO use a client-token to prevent double-sends of these start/stop/terminate commands
                # https://docs.aws.amazon.com/AWSEC2/latest/APIReference/Run_Instance_Idempotency.html
                resp = ec2.terminate_instances(InstanceIds=[inst['InstanceId']])
                [changed.add(i['InstanceId']) for i in resp['TerminatingInstances']]
            if desired_state == 'STOPPED':
                if inst['State']['Name'] == 'stopping':
                    unchanged.add(inst['InstanceId'])
                    continue
                resp = ec2.stop_instances(InstanceIds=[inst['InstanceId']])
                [changed.add(i['InstanceId']) for i in resp['StoppingInstances']]
            if desired_state == 'RUNNING':
                resp = ec2.start_instances(InstanceIds=[inst['InstanceId']])
                [changed.add(i['InstanceId']) for i in resp['StartingInstances']]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
            # we don't care about exceptions here, as we'll fail out if any instances failed to terminate
            pass

    if changed:
        await_instances(ids=list(changed) + list(unchanged), state=desired_state)

    change_failed = list(to_change - changed)
    instances = find_instances(ec2, ids=list(to_change))
    return changed, change_failed, instances


def pretty_instance(i):
    instance = camel_dict_to_snake_dict(i, ignore_list=['Tags'])
    instance['tags'] = boto3_tag_list_to_ansible_dict(i['Tags'])
    return instance


def determine_iam_role(name_or_arn, iam):
    if re.match(r'^arn:aws:iam::\d+:instance-profile/[\w+=/,.@-]+$', name_or_arn):
        return name_or_arn
    if iam is None:
        iam = module.client('iam')
    try:
        role = iam.get_instance_profile(InstanceProfileName=name_or_arn)
        return role['InstanceProfile']['Arn']
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            module.fail_json_aws(e, msg="Could not find instance_role {0}".format(name_or_arn))
        module.fail_json_aws(e, msg="An error occurred while searching for instance_role {0}. Please try supplying the full ARN.".format(name_or_arn))


def handle_existing(existing_matches, changed, ec2, state):
    if state in ('running', 'started') and [i for i in existing_matches if i['State']['Name'] != 'running']:
        ins_changed, failed, instances = change_instance_state(filters=module.params.get('filters'), desired_state='RUNNING')
        module.exit_json(
            changed=bool(len(ins_changed)) or changed,
            instances=[pretty_instance(i) for i in instances],
            instance_ids=[i['InstanceId'] for i in instances],
        )
    changes = diff_instance_and_params(existing_matches[0], module.params)
    for c in changes:
        ec2.modify_instance_attribute(**c)
    changed |= change_network_attachments(existing_matches[0], module.params, ec2)
    altered = find_instances(ec2, ids=[i['InstanceId'] for i in existing_matches])
    module.exit_json(
        changed=bool(len(changes)) or changed,
        instances=[pretty_instance(i) for i in altered],
        instance_ids=[i['InstanceId'] for i in altered],
        changes=changes,
    )


def ensure_present(existing_matches, changed, ec2, state):
    if len(existing_matches):
        try:
            handle_existing(existing_matches, changed, ec2, state)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(
                e, msg="Failed to handle existing instances {0}".format(', '.join([i['InstanceId'] for i in existing_matches])),
                # instances=[pretty_instance(i) for i in existing_matches],
                # instance_ids=[i['InstanceId'] for i in existing_matches],
            )
    try:
        instance_spec = build_run_instance_spec(module.params)
        instance_response = AWSRetry.jittered_backoff()(ec2.run_instances)(**instance_spec)
        instances = instance_response['Instances']
        instance_ids = [i['InstanceId'] for i in instances]

        for ins in instances:
            changes = diff_instance_and_params(ins, module.params, skip=['UserData', 'EbsOptimized'])
            for c in changes:
                try:
                    AWSRetry.jittered_backoff()(ec2.modify_instance_attribute)(**c)
                except botocore.exceptions.ClientError as e:
                    module.fail_json_aws(e, msg="Could not apply change {0} to new instance.".format(str(c)))

        await_instances(instance_ids)
        instances = ec2.get_paginator('describe_instances').paginate(
            InstanceIds=instance_ids
        ).search('Reservations[].Instances[]')

        module.exit_json(
            changed=True,
            instances=[pretty_instance(i) for i in instances],
            instance_ids=instance_ids,
            spec=instance_spec,
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to create new EC2 instance")


def main():
    global module
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=['present', 'started', 'running', 'stopped', 'restarted', 'rebooted', 'terminated', 'absent']),
        wait=dict(default=True, type='bool'),
        wait_timeout=dict(default=600, type='int'),
        # count=dict(default=1, type='int'),
        image=dict(type='dict'),
        image_id=dict(type='str'),
        instance_type=dict(default='t2.micro', type='str'),
        user_data=dict(type='str'),
        tower_callback=dict(type='dict'),
        ebs_optimized=dict(type='bool'),
        vpc_subnet_id=dict(type='str', aliases=['subnet_id']),
        availability_zone=dict(type='str'),
        security_groups=dict(default=[], type='list'),
        security_group=dict(type='str'),
        instance_role=dict(type='str'),
        name=dict(type='str'),
        tags=dict(type='dict'),
        purge_tags=dict(type='bool', default=False),
        filters=dict(type='dict', default=None),
        launch_template=dict(type='dict'),
        key_name=dict(type='str'),
        cpu_credit_specification=dict(type='str', choices=['standard', 'unlimited']),
        tenancy=dict(type='str', choices=['dedicated', 'default']),
        instance_initiated_shutdown_behavior=dict(type='str', choices=['stop', 'terminate']),
        termination_protection=dict(type='bool'),
        detailed_monitoring=dict(type='bool'),
        instance_ids=dict(default=[], type='list'),
        network=dict(default=None, type='dict'),
        volumes=dict(default=None, type='list'),
    ))
    # running/present are synonyms
    # as are terminated/absent
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['security_groups', 'security_group'],
            ['availability_zone', 'vpc_subnet_id'],
            ['tower_callback', 'user_data'],
            ['image_id', 'image'],
        ],
        supports_check_mode=True
    )

    if module.params.get('network'):
        if module.params.get('network').get('interfaces'):
            if module.params.get('security_group'):
                module.fail_json(msg="Parameter network.interfaces can't be used with security_group")
            if module.params.get('security_groups'):
                module.fail_json(msg="Parameter network.interfaces can't be used with security_groups")

    state = module.params.get('state')
    ec2 = module.client('ec2')
    if module.params.get('filters') is None:
        filters = {
            # all states except shutting-down and terminated
            'instance-state-name': ['pending', 'running', 'stopping', 'stopped']
        }
        if state == 'stopped':
            # only need to change instances that aren't already stopped
            filters['instance-state-name'] = ['stopping', 'pending', 'running']

        if isinstance(module.params.get('instance_ids'), text_type):
            filters['instance-id'] = [module.params.get('instance_ids')]
        elif isinstance(module.params.get('instance_ids'), list) and len(module.params.get('instance_ids')):
            filters['instance-id'] = module.params.get('instance_ids')
        else:
            if not module.params.get('vpc_subnet_id'):
                if module.params.get('network'):
                    # grab AZ from one of the ENIs
                    ints = module.params.get('network').get('interfaces')
                    if ints:
                        filters['network-interface.network-interface-id'] = []
                        for i in ints:
                            if isinstance(i, dict):
                                i = i['id']
                            filters['network-interface.network-interface-id'].append(i)
                else:
                    sub = get_default_subnet(ec2, get_default_vpc(ec2), availability_zone=module.params.get('availability_zone'))
                    filters['subnet-id'] = sub['SubnetId']
            else:
                filters['subnet-id'] = [module.params.get('vpc_subnet_id')]

            if module.params.get('name'):
                filters['tag:Name'] = [module.params.get('name')]

            if module.params.get('image_id'):
                filters['image-id'] = [module.params.get('image_id')]
            elif (module.params.get('image') or {}).get('id'):
                filters['image-id'] = [module.params.get('image', {}).get('id')]

        module.params['filters'] = filters

    existing_matches = find_instances(ec2, filters=module.params.get('filters'))
    changed = False

    if state not in ('terminated', 'absent') and existing_matches:
        for match in existing_matches:
            warn_if_public_ip_assignment_changed(match)
            changed |= manage_tags(match, (module.params.get('tags') or {}), module.params.get('purge_tags', False), ec2)

    if state in ('present', 'running', 'started'):
        ensure_present(existing_matches=existing_matches, changed=changed, ec2=ec2, state=state)
    elif state in ('restarted', 'rebooted', 'stopped', 'absent', 'terminated'):
        if existing_matches:
            ensure_instance_state(state, ec2)
        else:
            module.exit_json(
                msg='No matching instances found',
                changed=False,
                instances=[],
            )
    else:
        module.fail_json(msg="We don't handle the state {0}".format(state))


if __name__ == '__main__':
    main()
