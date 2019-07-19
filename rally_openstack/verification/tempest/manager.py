# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import re
import shutil
import subprocess

from rally.common import yamlutils as yaml
from rally import exceptions
from rally.plugins.common.verification import testr
from rally.verification import manager
from rally.verification import utils

from rally_openstack.verification.tempest import config
from rally_openstack.verification.tempest import consts


AVAILABLE_SETS = (list(consts.TempestTestSets) +
                  list(consts.TempestApiTestSets) +
                  list(consts.TempestScenarioTestSets))


@manager.configure(name="tempest", platform="openstack",
                   default_repo="https://opendev.org/openstack/tempest",
                   context={"tempest": {}, "testr": {}})
class TempestManager(testr.TestrLauncher):
    """Tempest verifier.

    **Description**:

    Quote from official documentation:

      This is a set of integration tests to be run against a live OpenStack
      cluster. Tempest has batteries of tests for OpenStack API validation,
      Scenarios, and other specific tests useful in validating an OpenStack
      deployment.

    Rally supports features listed below:

    * *cloning Tempest*: repository and version can be specified
    * *installation*: system-wide with checking existence of required
      packages or in virtual environment
    * *configuration*: options are discovered via OpenStack API, but you can
      override them if you need
    * *running*: pre-creating all required resources(i.e images, tenants,
      etc), prepare arguments, launching Tempest, live-progress output
    * *results*: all verifications are stored in db, you can built reports,
      compare verification at whatever you want time.

    Appeared in Rally 0.8.0 *(actually, it appeared long time ago with first
    revision of Verification Component, but 0.8.0 is mentioned since it is
    first release after Verification Component redesign)*
    """

    RUN_ARGS = {"set": "Name of predefined set of tests. Known names: %s"
                       % ", ".join(AVAILABLE_SETS)}

    @property
    def run_environ(self):
        env = super(TempestManager, self).run_environ
        env["TEMPEST_CONFIG_DIR"] = os.path.dirname(self.configfile)
        env["TEMPEST_CONFIG"] = os.path.basename(self.configfile)
        # TODO(andreykurilin): move it to Testr base class
        env["OS_TEST_PATH"] = os.path.join(self.repo_dir,
                                           "tempest/test_discover")
        return env

    @property
    def configfile(self):
        return os.path.join(self.home_dir, "tempest.conf")

    def validate_args(self, args):
        """Validate given arguments."""
        super(TempestManager, self).validate_args(args)

        if args.get("pattern"):
            pattern = args["pattern"].split("=", 1)
            if len(pattern) == 1:
                pass  # it is just a regex
            elif pattern[0] == "set":
                if pattern[1] not in AVAILABLE_SETS:
                    raise exceptions.ValidationError(
                        "Test set '%s' not found in available "
                        "Tempest test sets. Available sets are '%s'."
                        % (pattern[1], "', '".join(AVAILABLE_SETS)))
            else:
                raise exceptions.ValidationError(
                    "'pattern' argument should be a regexp or set name "
                    "(format: 'tempest.api.identity.v3', 'set=smoke').")

    def configure(self, extra_options=None):
        """Configure Tempest."""
        utils.create_dir(self.home_dir)
        tcm = config.TempestConfigfileManager(self.verifier.deployment)
        return tcm.create(self.configfile, extra_options)

    def is_configured(self):
        """Check whether Tempest is configured or not."""
        return os.path.exists(self.configfile)

    def get_configuration(self):
        """Get Tempest configuration."""
        with open(self.configfile) as f:
            return f.read()

    def extend_configuration(self, extra_options):
        """Extend Tempest configuration with extra options."""
        return utils.extend_configfile(extra_options, self.configfile)

    def override_configuration(self, new_configuration):
        """Override Tempest configuration by new configuration."""
        with open(self.configfile, "w") as f:
            f.write(new_configuration)

    def install_extension(self, source, version=None, extra_settings=None):
        """Install a Tempest plugin."""
        if extra_settings:
            raise NotImplementedError(
                "'%s' verifiers don't support extra installation settings "
                "for extensions." % self.get_name())
        version = version or "master"
        egg = re.sub("\.git$", "", os.path.basename(source.strip("/")))
        full_source = "git+{0}@{1}#egg={2}".format(source, version, egg)
        # NOTE(ylobankov): Use 'develop mode' installation to provide an
        #                  ability to advanced users to change tests or
        #                  develop new ones in verifier repo on the fly.
        cmd = ["pip", "install",
               "--src", os.path.join(self.base_dir, "extensions"),
               "-e", full_source]
        if self.verifier.system_wide:
            cmd.insert(2, "--no-deps")
        utils.check_output(cmd, cwd=self.base_dir, env=self.environ)

        # Very often Tempest plugins are inside projects and requirements
        # for plugins are listed in the test-requirements.txt file.
        test_reqs_path = os.path.join(self.base_dir, "extensions",
                                      egg, "test-requirements.txt")
        if os.path.exists(test_reqs_path):
            if not self.verifier.system_wide:
                utils.check_output(["pip", "install", "-r", test_reqs_path],
                                   cwd=self.base_dir, env=self.environ)
            else:
                self.check_system_wide(reqs_file_path=test_reqs_path)

    def list_extensions(self):
        """List all installed Tempest plugins."""
        # TODO(andreykurilin): find a better way to list tempest plugins
        cmd = ("from tempest.test_discover import plugins; "
               "plugins_manager = plugins.TempestTestPluginManager(); "
               "plugins_map = plugins_manager.get_plugin_load_tests_tuple(); "
               "plugins_list = ["
               "    {'name': p.name, "
               "     'entry_point': p.entry_point_target, "
               "     'location': plugins_map[p.name][1]} "
               "    for p in plugins_manager.ext_plugins.extensions]; "
               "print(plugins_list)")
        try:
            output = utils.check_output(["python", "-c", cmd],
                                        cwd=self.base_dir, env=self.environ,
                                        debug_output=False).strip()
        except subprocess.CalledProcessError:
            raise exceptions.RallyException(
                "Cannot list installed Tempest plugins for verifier %s." %
                self.verifier)

        return yaml.safe_load(output)

    def uninstall_extension(self, name):
        """Uninstall a Tempest plugin."""
        for ext in self.list_extensions():
            if ext["name"] == name and os.path.exists(ext["location"]):
                shutil.rmtree(ext["location"])
                break
        else:
            raise exceptions.RallyException(
                "There is no Tempest plugin with name '%s'. "
                "Are you sure that it was installed?" % name)

    def list_tests(self, pattern=""):
        """List all Tempest tests."""
        if pattern:
            pattern = self._transform_pattern(pattern)
        return super(TempestManager, self).list_tests(pattern)

    def prepare_run_args(self, run_args):
        """Prepare 'run_args' for testr context."""
        if run_args.get("pattern"):
            run_args["pattern"] = self._transform_pattern(run_args["pattern"])
        return run_args

    @staticmethod
    def _transform_pattern(pattern):
        """Transform pattern into Tempest-specific pattern."""
        parsed_pattern = pattern.split("=", 1)
        if len(parsed_pattern) == 2:
            if parsed_pattern[0] == "set":
                if parsed_pattern[1] in consts.TempestTestSets:
                    return "smoke" if parsed_pattern[1] == "smoke" else ""
                elif parsed_pattern[1] in consts.TempestApiTestSets:
                    return "tempest.api.%s" % parsed_pattern[1]
                else:
                    return "tempest.%s" % parsed_pattern[1]

        return pattern  # it is just a regex
