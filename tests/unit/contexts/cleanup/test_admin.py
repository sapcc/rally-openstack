# Copyright 2014: Mirantis Inc.
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

import ddt
import mock
from rally.common import utils
from rally.task import context

from rally_openstack.contexts.cleanup import admin
from rally_openstack import scenario
from tests.unit import test


ADMIN = "rally_openstack.contexts.cleanup.admin"
BASE = "rally_openstack.contexts.cleanup.base"


@ddt.ddt
class AdminCleanupTestCase(test.TestCase):

    @mock.patch("%s.manager" % BASE)
    @ddt.data((["a", "b"], True),
              (["a", "e"], False),
              (3, False))
    @ddt.unpack
    def test_validate(self, config, valid, mock_manager):
        mock_manager.list_resource_names.return_value = {"a", "b", "c"}
        results = context.Context.validate(
            "admin_cleanup", None, None, config, allow_hidden=True)
        if valid:
            self.assertEqual([], results)
        else:
            self.assertGreater(len(results), 0)

    @mock.patch("rally.common.plugin.discover.itersubclasses")
    @mock.patch("%s.manager.find_resource_managers" % ADMIN,
                return_value=[mock.MagicMock(), mock.MagicMock()])
    @mock.patch("%s.manager.SeekAndDestroy" % ADMIN)
    def test_cleanup(self, mock_seek_and_destroy, mock_find_resource_managers,
                     mock_itersubclasses):
        class ResourceClass(utils.RandomNameGeneratorMixin):
            pass

        mock_itersubclasses.return_value = [ResourceClass]

        ctx = {
            "config": {"admin_cleanup": ["a", "b"]},
            "admin": mock.MagicMock(),
            "users": mock.MagicMock(),
            "task": {"uuid": "task_id"}
        }

        admin_cleanup = admin.AdminCleanup(ctx)
        admin_cleanup.setup()
        admin_cleanup.cleanup()

        mock_itersubclasses.assert_called_once_with(scenario.OpenStackScenario)
        mock_find_resource_managers.assert_called_once_with(("a", "b"), True)
        mock_seek_and_destroy.assert_has_calls([
            mock.call(mock_find_resource_managers.return_value[0],
                      ctx["admin"],
                      ctx["users"],
                      api_versions=None,
                      resource_classes=[ResourceClass],
                      task_id="task_id"),
            mock.call().exterminate(),
            mock.call(mock_find_resource_managers.return_value[1],
                      ctx["admin"],
                      ctx["users"],
                      api_versions=None,
                      resource_classes=[ResourceClass],
                      task_id="task_id"),
            mock.call().exterminate()
        ])
