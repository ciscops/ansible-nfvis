import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native, to_bytes, to_text


def nfvis_argument_spec():
    return dict(host=dict(type='str', required=True, fallback=(env_fallback, ['nfvis_HOST'])),
            user=dict(type='str', required=True, fallback=(env_fallback, ['nfvis_USER'])),
            password=dict(type='str', required=True, fallback=(env_fallback, ['nfvis_PASSWORD'])),
            validate_certs=dict(type='bool', required=False, default=False),
            timeout=dict(type='int', default=30)
    )


class nfvisModule(object):

    def __init__(self, module, function=None):
        self.module = module
        self.params = module.params
        self.result = dict(changed=False)
        self.headers = dict()
        self.function = function
        self.orgs = None
        self.nets = None
        self.org_id = None
        self.net_id = None

        # normal output
        self.existing = None

        # info output
        self.config = dict()
        self.original = None
        self.proposed = dict()
        self.merged = None

        # debug output
        self.filter_string = ''
        self.method = None
        self.path = None
        self.response = None
        self.status = None
        self.url = None
        self.params['force_basic_auth'] = True
        self.params['url_username'] = url_username = self.params['user']
        self.params['url_password'] = self.params['password']

        self.modifiable_methods = ['POST', 'PUT', 'DELETE']

        if function == 'vlan':
            self.headers = {'Content-Type': 'application/vnd.yang.data+json',
                            'Accept': 'application/vnd.yang.collection+json'}
        else:
            self.headers = {'Content-Type': 'application/vnd.yang.data+json',
                            'Accept': 'application/vnd.yang.data+json'}

    def request(self, url, method=None, payload=None):
        """Generic HTTP method for nfvis requests."""

        if method is not None:
            self.method = method
        # self.url = 'https://{host}/api/v0/{path}'.format(path=self.path.lstrip('/'), **self.params)
        self.url = url
        self.method = method
        self.payload = payload

        resp, info = fetch_url(self.module, self.url,
                               headers=self.headers,
                               data=payload,
                               method=self.method,
                               timeout=self.params['timeout'],
                               )
        self.response = info['msg']
        self.status = info['status']

        if self.status >= 300:
            try:
                self.fail_json(msg='Request failed for {url}: {status} - {msg}'.format(**info),
                                  body=json.loads(to_native(info['body'])))
            except Exception:
                pass

            self.fail_json(msg='Request failed for {url}: {status} - {msg}'.format(**info))

        try:
            return json.loads(to_native(resp.read()))
        except Exception:
            pass
        
    def exit_json(self, **kwargs):
        """Custom written method to exit from module."""
        self.result['response'] = self.response
        self.result['status'] = self.status
        self.result['url'] = self.url
        self.result['payload'] = self.payload
        self.result['method'] = self.method

        self.result.update(**kwargs)
        self.module.exit_json(**self.result)

    def fail_json(self, msg, **kwargs):
        """Custom written method to return info on failure."""
        self.result['response'] = self.response
        self.result['status'] = self.status
        self.result['url'] = self.url
        self.result['payload'] = self.payload
        self.result['method'] = self.method

        self.result.update(**kwargs)
        self.module.fail_json(msg=msg, **self.result)