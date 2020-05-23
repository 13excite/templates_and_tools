from troveclient.v1 import client
from keystoneauth1.identity.generic import password
from keystoneauth1.identity.generic import token
from keystoneauth1 import loading
from oslo_utils import importutils
import argparse

from troveclient.apiclient import exceptions as exc
import troveclient.auth_plugin
from troveclient import client
import troveclient.extension
from troveclient.i18n import _  # noqa
from troveclient import utils
from troveclient.v1 import shell as shell_v1
import sys
import json

AUTH_URL = "https://infra.mail.ru:35357/v3/"

PROJECT_ID = "11b1b1bb1b1"
PROJECT_NAME = "Dev project for myemail@exmpl.com"
USER_DOMAIN_NAME = "Default"
PROJECT_DOMAIN_ID = "default"

USERNAME = "myemail@exmpl.com"
PASSWORD = "testTest"

REGION_NAME = "RegionOne"

INTERFACE = "public"
IDENTITY_API_VERSION = 3
osprofiler_profiler = importutils.try_import("osprofiler.profiler")
DEFAULT_OS_DATABASE_API_VERSION = "1.0"
DEFAULT_TROVE_ENDPOINT_TYPE = 'publicURL'
DEFAULT_TROVE_SERVICE_TYPE = 'database'
PROJ_DOM_NAME = None


class OpenStackTroveShell(object):

    def __init__(self):
        # Discover available auth plugins
        troveclient.auth_plugin.discover_auth_systems()

        args = argparse.Namespace(bypass_url='',
                                  collect_timing=False,
                                  database_service_name='',
                                  debug=False, endpoint_type='publicURL',
                                  help=False,
                                  include_clustered=False,
                                  insecure=False, json=False,
                                  limit=None, marker=None,
                                  os_auth_system='',
                                  os_auth_token='',
                                  os_auth_type='password',
                                  os_auth_url=AUTH_URL,
                                  os_cacert=None,
                                  os_cert=None,
                                  os_database_api_version='1.0',
                                  os_default_domain_id=None,
                                  os_default_domain_name=None,
                                  os_domain_id=None,
                                  os_domain_name=None,
                                  os_key=None,
                                  os_password=PASSWORD,
                                  os_project_domain_id='default',
                                  os_project_domain_name=None,
                                  os_project_id=PROJECT_ID,
                                  os_project_name=PROJECT_NAME,
                                  os_region_name=REGION_NAME,
                                  os_system_scope=None,
                                  os_tenant_id=None,
                                  os_tenant_name=None,
                                  os_trust_id=None,
                                  os_user_domain_id=None,
                                  os_user_domain_name='Default',
                                  os_user_id=None,
                                  os_username=USERNAME,
                                  retries=0,
                                  service_name='',
                                  service_type='',
                                  timeout=600,
                                  func=None)
        os_username = args.os_username
        os_password = args.os_password
        os_user_domain_id = args.os_user_domain_id
        os_project_domain_id = args.os_project_domain_id
        os_project_name = getattr(args, 'os_project_name',
                                  getattr(args, 'os_tenant_name', None))
        os_auth_url = args.os_auth_url
        os_region_name = args.os_region_name
        os_project_id = getattr(
            args, 'os_project_id',
            getattr(args, 'os_tenant_id', None))
        os_auth_system = args.os_auth_system

        if "v2.0" not in os_auth_url:
            if (not args.os_project_domain_id and
                    not args.os_project_domain_name):
                setattr(args, "os_project_domain_id", "default")
            if not args.os_user_domain_id and not args.os_user_domain_name:
                setattr(args, "os_user_domain_id", "default")


        endpoint_type = args.endpoint_type
        insecure = args.insecure
        service_type = args.service_type
        service_name = args.service_name
        database_service_name = args.database_service_name
        cacert = args.os_cacert
        bypass_url = args.bypass_url
        os_database_api_version = args.os_database_api_version
        retries = args.retries

        if os_auth_system and os_auth_system != "keystone":
            auth_plugin = troveclient.auth_plugin.load_plugin(os_auth_system)
        else:
            auth_plugin = None

        if not endpoint_type:
            endpoint_type = DEFAULT_TROVE_ENDPOINT_TYPE

        if not service_type:
            service_type = DEFAULT_TROVE_SERVICE_TYPE
            service_type = utils.get_service_type(args.func) or service_type

        # FIXME(usrleon): Here should be restrict for project id same as
        # for os_username or os_password but for compatibility it is not.

        if not utils.isunauthenticated(args.func):

            if auth_plugin:
                auth_plugin.parse_opts(args)

            if not auth_plugin or not auth_plugin.opts:
                if not os_username:
                    raise exc.CommandError(_(
                        "You must provide a username "
                        "via either --os-username or env[OS_USERNAME]"))

            if not os_auth_url:
                if os_auth_system and os_auth_system != 'keystone':
                    os_auth_url = auth_plugin.get_auth_url()

        # V3 stuff
        project_info_provided = (os_project_name or
                                 os_project_id)

        if (not project_info_provided):
            raise exc.CommandError(
                _("You must provide a "
                  "project_id or project_name (with "
                  "project_domain_name or project_domain_id) via "
                  "  --os-project-id (env[OS_PROJECT_ID])"
                  "  --os-project-name (env[OS_PROJECT_NAME]),"
                  "  --os-project-domain-id "
                  "(env[OS_PROJECT_DOMAIN_ID])"
                  "  --os-project-domain-name "
                  "(env[OS_PROJECT_DOMAIN_NAME])"))

        if not os_auth_url:
            raise exc.CommandError(_("You must provide an auth url "
                                     "via either --os-auth-url or "
                                     "env[OS_AUTH_URL] or specify an "
                                     "auth_system which defines a default "
                                     "url with --os-auth-system or "
                                     "env[OS_AUTH_SYSTEM]"))

        use_session = True
        if auth_plugin or bypass_url:
            use_session = False

        ks_session = None
        keystone_auth = None
        if use_session:
            project_id = args.os_project_id or args.os_tenant_id
            project_name = args.os_project_name or args.os_tenant_name

            ks_session = loading.load_session_from_argparse_arguments(args)

            keystone_auth = self._get_keystone_auth(
                ks_session,
                os_auth_url,
                username=os_username,
                user_id=None,
                user_domain_id=os_user_domain_id,
                user_domain_name=USER_DOMAIN_NAME,
                password=os_password,
                project_id=project_id,
                project_name=project_name,
                project_domain_id=os_project_domain_id)

        self.cs = client.Client(os_database_api_version, os_username,
                                os_password, os_project_name, os_auth_url,
                                insecure, region_name=os_region_name,
                                tenant_id=os_project_id,
                                endpoint_type=endpoint_type,
                                #extensions=self.extensions,
                                service_type=service_type,
                                service_name=service_name,
                                database_service_name=database_service_name,
                                retries=retries,
                                http_log_debug=args.debug,
                                cacert=cacert,
                                bypass_url=bypass_url,
                                auth_system=os_auth_system,
                                auth_plugin=auth_plugin,
                                session=ks_session,
                                auth=keystone_auth)

        try:
            if not utils.isunauthenticated(args.func):
                # If Keystone is used, authentication is handled as
                # part of session.
                if not use_session:
                    self.cs.authenticate()
        except exc.Unauthorized:
            raise exc.CommandError(_("Invalid OpenStack Trove credentials."))
        except exc.AuthorizationFailure:
            raise exc.CommandError(_("Unable to authorize user"))

        endpoint_api_version = self.cs.get_database_api_version_from_endpoint()

        if endpoint_api_version != os_database_api_version:
            msg = (_("Database API version is set to %(db_ver)s "
                     "but you are accessing a %(ep_ver)s endpoint. "
                     "Change its value via either --os-database-api-version "
                     "or env[OS_DATABASE_API_VERSION]") %
                   {'db_ver': os_database_api_version,
                    'ep_ver': endpoint_api_version})
            # raise exc.InvalidAPIVersion(msg)
            raise exc.UnsupportedVersion(msg)

    def _get_keystone_auth(self, session, auth_url, **kwargs):
        auth_token = kwargs.pop('auth_token', None)
        if auth_token:
            return token.Token(auth_url, auth_token, **kwargs)
        else:
            return password.Password(
                auth_url,
                username=kwargs.pop('username'),
                user_id=kwargs.pop('user_id'),
                password=kwargs.pop('password'),
                user_domain_id=kwargs.pop('user_domain_id'),
                user_domain_name=kwargs.pop('user_domain_name'),
                **kwargs)
    def create_backup(self, instance, name):
        self.cs.backups.create(name, instance)

    def list_backups(self):
        return self.cs.backups.list()

    def delete_backup(self, backup_id):
        self.cs.backups.delete(backup_id)


def main():
    try:
        OS_DB = OpenStackTroveShell()
        #print(OS_DB.cs.backups('71afb40d-61e5-46a1-949e-428399af5f63'))
        print(json.dumps(OS_DB.cs.instances.get('e3d462ec-6a17-4f52-9cb5-bb8782521bce').to_dict(), indent=4,))
    except KeyboardInterrupt:
        print(_("... terminating trove client"), file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print("Something error: ", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
