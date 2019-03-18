#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nfvis_upload

short_description: This is my sample module

version_added: "2.4"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils._text import to_native
from ansible.module_utils.nfvis import nfvisModule, nfvis_argument_spec

def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    argument_spec = nfvis_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present'], default='present'),
                         name=dict(type='str', aliases=['deployment']),
                         image=dict(type='str', required=True),
                         flavor=dict(type='str', required=True),
                         bootup_time=dict(type='int', default=-1),
                         recovery_wait_time=dict(type='int', default=0),
                         kpi_data=dict(type='bool', default=False),
                         scaling=dict(type='bool', default=False),
                         scaling_min_active=dict(type='int', default=1),
                         scaling_max_active=dict(type='int', default=1),
                         placement_type=dict(type='str', default='zone_host'),
                         placement_enforcement=dict(type='str', default='strict'),
                         placement_host=dict(type='str', default='datastore1'),
                         recovery_type=dict(type='str', default='AUTO'),
                         action_on_recovery=dict(type='str', default='REBOOT_ONLY'),
                         interfaces=dict(type='list'),
                         port_forwarding=dict(type='list'),
                         config_data=dict(type='list'),
                         )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )
    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )
    nfvis = nfvisModule(module, function='deployment')

    payload = None
    port = None
    response = {}

    # Get the list of existing deployments
    url = 'https://{0}/api/config/vm_lifecycle/tenants/tenant/admin/deployments?deep'.format(nfvis.params['host'])
    response = nfvis.request(url, method='GET')
    nfvis.result['data'] = response
    
    # Turn the list of dictionaries returned in the call into a dictionary of dictionaries hashed by the deployment name
    deployment_dict = {}
    try:
        for item in response['vmlc:deployments']['deployment']:
            name = item['name']
            deployment_dict[name] = item
    except TypeError:
        pass
    except KeyError:
        pass

    if nfvis.params['state'] == 'present':
        if nfvis.params['name'] in deployment_dict:
            # The deployment exists on the device, so check to see if it is the same configuration
            nfvis.result['changed'] = False
        else:
            # The deployment does not exist on the device, so add it
            # Construct the payload
            payload = {'deployment': {}}
            payload['deployment']['name'] = nfvis.params['name']
            payload['deployment']['vm_group'] = {}
            payload['deployment']['vm_group']['name'] = nfvis.params['name']
            payload['deployment']['vm_group']['image'] = nfvis.params['image']
            payload['deployment']['vm_group']['flavor'] = nfvis.params['flavor']
            payload['deployment']['vm_group']['bootup_time'] = nfvis.params['bootup_time']
            payload['deployment']['vm_group']['recovery_wait_time'] = nfvis.params['recovery_wait_time']
            payload['deployment']['vm_group']['kpi_data'] = {}
            payload['deployment']['vm_group']['kpi_data']['enabled'] = nfvis.params['kpi_data']
            payload['deployment']['vm_group']['scaling'] = {}
            payload['deployment']['vm_group']['scaling']['min_active'] = nfvis.params['scaling_min_active']
            payload['deployment']['vm_group']['scaling']['max_active'] = nfvis.params['scaling_max_active']
            payload['deployment']['vm_group']['scaling']['elastic'] = nfvis.params['scaling']
            payload['deployment']['vm_group']['placement'] = {}
            payload['deployment']['vm_group']['placement']['type'] = nfvis.params['placement_type']
            payload['deployment']['vm_group']['placement']['enforcement'] = nfvis.params['placement_enforcement']
            payload['deployment']['vm_group']['placement']['host'] = nfvis.params['placement_host']
            payload['deployment']['vm_group']['recovery_policy'] = {}
            payload['deployment']['vm_group']['recovery_policy']['recovery_type'] = nfvis.params['recovery_type']
            payload['deployment']['vm_group']['recovery_policy']['action_on_recovery'] = nfvis.params['action_on_recovery']

            port_forwarding = {}
            if nfvis.params['port_forwarding']:
               for item in nfvis.params['port_forwarding']:
                   port_forwarding['port'] = {}
                   port_forwarding['port']['type'] = item.get('type', 'ssh')
                   port_forwarding['port']['vnf_port'] = item.get('vnf_port', 22)
                   port_forwarding['port']['external_port_range'] = {}
                   if 'proxy_port' in item:
                       port_forwarding['port']['external_port_range']['start'] = item['proxy_port']
                       port_forwarding['port']['external_port_range']['end'] = item['proxy_port']
                   else:
                       module.fail_json(msg="proxy_port must be specified for port_forwarding")
                   port_forwarding['port']['protocol'] = item.get('protocol', 'tcp')
                   port_forwarding['port']['source_bridge'] = item.get('source_bridge', 'MGMT')

            if nfvis.params['interfaces']:
                payload['deployment']['vm_group']['interfaces'] = []
                for index, item in enumerate(nfvis.params['interfaces']):
                    entry = {}
                    entry['interface'] = {}
                    entry['interface']['nicid'] = item.get('nicid', index)
                    if 'network' in item:
                       entry['interface']['network'] = item['network']
                    else:
                        module.fail_json(msg="network must be specified for interface")
                    entry['interface']['model'] = item.get('model', 'virtio')
                    if index == 0 and 'port' in port_forwarding:
                       entry['interface']['port_forwarding'] = port_forwarding
                    payload['deployment']['vm_group']['interfaces'].append(entry)

            if nfvis.params['config_data']:
                payload['deployment']['vm_group']['config_data'] = []
                for item in nfvis.params['config_data']:
                    entry = {'configuration': {}}
                    if 'dst' in item:
                       entry['configuration']['dst'] = item['dst']
                    else:
                       module.fail_json(msg="dst must be specified for config_data")
                    if 'data' in item:
                        if isinstance(item['data'], str):
                            entry['configuration']['data'] = item['data']
                        else:
                            entry['configuration']['data'] = json.dumps(item['data'])
                    else:
                       module.fail_json(msg="data must be specified for config_data")
                    payload['deployment']['vm_group']['config_data'].append(entry)

            if nfvis.params['kpi_data'] == True or nfvis.params['bootup_time'] > 0:
                payload['deployment']['vm_group']['kpi_data']['kpi'] = {}
                payload['deployment']['vm_group']['kpi_data']['kpi']['event_name'] = 'VM_ALIVE'
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_value'] = 1
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_cond'] = 'GT'
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_type'] = 'UINT32'
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector'] = {}
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector']['type'] = 'ICMPPing'
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector']['nicid'] = 0
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector']['poll_frequency'] = 3
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector']['polling_unit'] = 'seconds'
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector']['continuous_alarm'] = False
                payload['deployment']['vm_group']['rules'] = {}
                payload['deployment']['vm_group']['rules']['admin_rules'] = {}
                payload['deployment']['vm_group']['rules']['admin_rules']['rule'] = {}
                payload['deployment']['vm_group']['rules']['admin_rules']['rule']['event_name'] = 'VM_ALIVE'
                payload['deployment']['vm_group']['rules']['admin_rules']['rule']['action'] = [ "ALWAYS log", "FALSE recover autohealing", "TRUE servicebooted.sh" ]



            nfvis.result['payload'] = payload
            url = 'https://{0}/api/config/vm_lifecycle/tenants/tenant/admin/deployments'.format(nfvis.params['host'])
            response = nfvis.request(url, method='POST', payload=json.dumps(payload))
            nfvis.result['changed'] = True
    else:
        if nfvis.params['name'] in deployment_dict:
            url = 'https://{0}/api/config/vm_lifecycle/tenants/tenant/admin/deployments/deployment/{1}'.format(nfvis.params['host'], nfvis.params['name'])
            response = nfvis.request(url, 'DELETE')
            nfvis.result['changed'] = True


    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    # FIXME: Work with nfvis so they can implement a check mode
    if module.check_mode:
        module.exit_json(**nfvis.result)

    # execute checks for argument completeness

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**nfvis.result)


if __name__ == '__main__':
    main()