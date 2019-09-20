# ansible-nfvis

An Ansible Role for automating Cisco NFVIS

This is a hybrid role that contains the following modules:

- nfvis_system
- nfvis_bridge
- nfvis_network
- nfvis_vlan
- nfvis_deployment
- nfvis_package

To use this role, clone it into your `roles` directory:

```
git clone https://github.com/ciscops/ansible-nfvis.git
```

To load the modules for use in your playbook:

```yaml
- hosts: nfvis
  connection: local
  gather_facts: no
  roles:
    - ansible-nfvis
  tasks:
    - name: Build Bridges
      nfvis_bridge:
        host: 1.2.3.4
        user: admin
        password: cisco
        name: service
        state: present
```

## Tasks
In addition to the modules, the role can be called to help create packages:

### Build Packages

The `build-package` task can be called to build the packages that can be uploaded to the NFVIS host with the `nfvis_package` module.

```yaml
- name: Build packages
  include_role:
    name: ansible-nfvis
    tasks_from: build-package
  vars:
    package_name: asav
    package_version: 9.10.1
    package_image: asav9101.qcow2
    package_template: centos.image_properties.xml.j2
```

* `package_name`: The name of the package as referecned in deployments
* `package_version`: The version of the package
* `package_image`: The image with which to build the package
* `package_template`: The template from which the image_properties is derived.  This uses the default Ansible search
behavior for templates.  Sock templates are located in `ansible-nfvis/tempaltes`.

The `build-package` task looks for the image files used to build the packages in the directory specified by `nfvis_package_dir` (Default: `"{{ playbook_dir }}/packages"`).
It builds the packages in the directory specified by `nfvis_temp_dir` (Default: /tmp/nfvis_packages) and stores the packages
in the directory specified in `nfvis_package_dir` (Default: `"{{ playbook_dir }}/packages"`).

The default values for `nfvis_package_dir`, `nfvis_temp_dir`, and `nfvis_package_dir` are found in `ansible-nfvis/defaults/main.yml`.

>Note: Since nfvis_deployment inject the config into the deployments, this task does not include any configuration.

## Modules

All modules require authentication information for the NFVIS host:
* `host`: The address of the NFVIS device in which the API can be reached
* `user`: The username with which to authenticate to the NFVIS API
* `password`: The password with which to authenticate to the NFVIS API

###
### Get System Facts:
```yaml
- name: Configure system
  nfvis_facts:
    host: 1.2.3.4
    user: admin
    password: cisco
```

Returns:
* System settings
* CPU usage
* VLANs
* Bridges
* Networks
* Deployments

### Configure System Settings:
```yaml
- name: Configure system
  nfvis_system:
    host: 1.2.3.4
    user: admin
    password: cisco
    mgmt: 2.3.4.5/24
    gateway_ip: 2.3.4.1
    hostname: "{{ inventory_hostname }}"
    trusted_source:
      - 0.0.0.0/0
```

* `hostname`: The hostname of the NFVIS host (required)
* `mgmt`: The management IP of the NFVIS host in CIDR notation or `dhcp` for DHCP (required)
* `gateway_ip`: The IP address of the gateway of the NFVIS host
* `trusted_source`: A list of trusted sources in CIDR notation

### Configure VLANs:

The `nfvis_vlan` module maintains vlans on the switch:
```yaml
- nfvis_vlan:
    host: 1.2.3.4
    user: admin
    password: cisco
    state: present
    vlan_id: 100
```

* `vlan_id`: The VLAN ID to add to the NFVIS host
* `state`: The state of the VLAN.  Can be `present` to add the VLAN or `absent` to delete the VLAN. (default: `present`)

>Note: This requires that the NFVIS device contain an embedded switch (e.g. ENCS)

### Configure Bridges:
```yaml
- nfvis_bridge:
    host: 1.2.3.4
    user: admin
    password: cisco
    name: service-br
    state: present
```

* `name`: Name of the bridge (required)
* `state`: The state of the bridge ('present' or 'absent')
* `ports`: List of ports to which the bridge is attached
* `ip`: IP address and netmask of the bridge
* `vlan`: VLAN tag
* `dhcp`: Flag to specify DHCP configuration

### Configure Networks:
```yaml
- nfvis_network:
    host: 1.2.3.4
    user: admin
    password: cisco
    name: new-network
    bridge: net-bridge
    trunk: no
    vlan: 100
    state: present
```

* `name`: Name of the network (required)
* `state`: The state if the network ('present' or 'absent')
* `bridge`: The bridge to which the network is associated
* `trunk`: Set network to trunk mode
* `sriov`: SR-IOV supported on the network
* `native_tagged`: Specifies if the netowrk is tagged or not
* `native_vlan`: Specifies a native VLAN. It sets the native characteristics when the interface is in trunk mode. If you do not configure a native VLAN, the default VLAN 1 is used as the native VLAN

* `vlan`: Specifies the VLAN ID when the network is in access mode (i.e NOT a trunk)

### Deploy VNF:
```yaml
- nfvis_deployment:
    host: 1.2.3.4
    user: admin
    password: cisco
    name: isrv1
    state: present
    image: isrv
    flavor: isrv-small
    interfaces:
      - network: int-mgmt-net
      - network: wan-net
      - network: lan-net
    bootup_time: 600
    port_forwarding:
      - proxy_port: 20001
        source_bridge: 'wan-br'
    config_data:
      - dst: iosxe_config.txt
        data: "{{ lookup('template', 'iosxe_config.txt.j2') }}"
```

* `name`: Name of the deployment (required)
* `state`: The state of the VLAN.  Can be `present` to add the VLAN or `absent` to delete the deployment. (default: `present`)
* `image`: The name of the image to use for the deployment (required)
* `flavor`: The name of the flavor to use for the deployment (required)
* `interfaces`: A list of dictionaries specifying the interfaces to create for the VNF
    * `network`: The name of the network to attach the interface (required)
    * `nicid`: The nic id of the interface.  (Default: the index of that element in the list)
    * `model`: The model of the deriver to use (default `vitio`)
* `bootup_time`: The time to allow the VNF to boot before starting monitoring
* `port_forwarding`: A list of dictionaries specifying which ports to proxy to the VNF (_Note: monitoring must be enabled_)
    * `proxy_port`: The port on the NFVIS device to be proxied to the VNF (required)
    * `vnf_port`: The destination port on the VNF (Default: 22)
    * `source_bridge`: The bridge on the NFVIS device to attach the proxy (Default: MGMT)
    * `protocol`: The protocol of the port to be proxied (default `tcp`)
    * `type`: The type of proxy (default `ssh`)
* `config_data`: A list of dictionaries defining the configuration data to feed to the deployment via cloud-init:
    * `dst`: The name of the file to place in the config drive
    * `data`

### Upload Packages
```yaml
- name: Package
  nfvis_package:
    host: 1.2.3.4
    user: admin
    password: cisco
    file: asav.tar.gz
    name: asav
    state: present
```

* `name`: The name of the package
* `file`: The file name of the package
* `state`: The state of the VLAN.  Can be `present` to add package or `absent` to delete the package. (default: `present`)

License
-------

CISCO SAMPLE CODE LICENSE
