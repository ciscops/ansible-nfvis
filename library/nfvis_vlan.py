#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nfvis_vlan

short_description: This is my sample module

version_added: "2.4"

description:
    - "Create a VLAN on an NFVIS host"

options:
    vlan_id:
        description:
            - The VLAN ID of the VLAN.
        required: true
    state:
        description:
            - The state of the VLAN (i.e. `present` or `absent`)
        required: false

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Create VLAN 10
- nfvis_vlan:
    host: 1.2.3.4
    user: admin
    password: cisco
    state: present
    vlan_id: 100

# Delete VLAN 10
- nfvis_vlan:
    host: 1.2.3.4
    user: admin
    password: cisco
    state: absent
    vlan_id: 100
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
                         vlan_id=dict(type='int', required=True))

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
                           supports_check_mode=True)
    nfvis = nfvisModule(module)

    payload = None
    nfvis.result['changed'] = False

    # Get the list of existing vlans
    url_path = '/running/switch/vlan?deep'
    response = nfvis.request(url_path, method='GET', operation='get_vlan')
    nfvis.result['current'] = response
    
    # Turn the list of dictionaries returned in the call into a dictionary of dictionaries hashed by the bridge name
    vlan_dict = {}
    try:
        for item in response['collection']['switch:vlan']:
            name = item['vlan-id']
            vlan_dict[name] = item
    except TypeError:
        pass
    except KeyError:
        pass

    if nfvis.params['state'] == 'present':
        # Construct the payload
        payload = {'vlan':{}}
        payload['vlan']['vlan-id'] = nfvis.params['vlan_id']

        if nfvis.params['vlan_id'] not in vlan_dict:
            # The vlan does not exist on the device, so add it
            url_path = '/running/switch'
            if not module.check_mode:
                response = nfvis.request(url_path, method='POST', payload=json.dumps(payload))
            nfvis.result['changed'] = True
    else:
        if nfvis.params['vlan_id'] in vlan_dict:
            url = '/running/switch/vlan/{0}'.format(nfvis.params['vlan_id'])
            if not module.check_mode:
                response = nfvis.request(url, 'DELETE')
            nfvis.result['changed'] = True


    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    # FIXME: Work with nfvis so they can implement a check mode
    # if module.check_mode:
    #     nfvis.exit_json(**nfvis.result)

    # execute checks for argument completeness

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    nfvis.exit_json(**nfvis.result)


if __name__ == '__main__':
    main()
