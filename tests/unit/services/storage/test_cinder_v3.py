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
from rally.common import cfg

from rally_openstack.services.storage import cinder_v3
from tests.unit import fakes
from tests.unit import test

BASE_PATH = "rally_openstack.services.storage"
CONF = cfg.CONF


@ddt.ddt
class CinderV3ServiceTestCase(test.ScenarioTestCase):
    def setUp(self):
        super(CinderV3ServiceTestCase, self).setUp()
        self.clients = mock.MagicMock()
        self.cinder = self.clients.cinder.return_value
        self.name_generator = mock.MagicMock()
        self.service = cinder_v3.CinderV3Service(
            self.clients, name_generator=self.name_generator)

    def atomic_actions(self):
        return self.service._atomic_actions

    def test_create_volume(self):
        self.service.generate_random_name = mock.MagicMock(
            return_value="volume")
        self.service._wait_available_volume = mock.MagicMock()
        self.service._wait_available_volume.return_value = fakes.FakeVolume()

        return_volume = self.service.create_volume(1)

        kwargs = {"name": "volume",
                  "description": None,
                  "consistencygroup_id": None,
                  "snapshot_id": None,
                  "source_volid": None,
                  "volume_type": None,
                  "availability_zone": None,
                  "metadata": None,
                  "imageRef": None,
                  "scheduler_hints": None,
                  "backup_id": None}
        self.cinder.volumes.create.assert_called_once_with(1, **kwargs)
        self.service._wait_available_volume.assert_called_once_with(
            self.cinder.volumes.create.return_value)
        self.assertEqual(self.service._wait_available_volume.return_value,
                         return_volume)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.create_volume")

    @mock.patch("%s.cinder_v3.random" % BASE_PATH)
    def test_create_volume_with_size_range(self, mock_random):
        mock_random.randint.return_value = 3
        self.service._wait_available_volume = mock.MagicMock()
        self.service._wait_available_volume.return_value = fakes.FakeVolume()

        return_volume = self.service.create_volume(
            size={"min": 1, "max": 5}, name="volume")

        kwargs = {"name": "volume",
                  "description": None,
                  "consistencygroup_id": None,
                  "snapshot_id": None,
                  "source_volid": None,
                  "volume_type": None,
                  "availability_zone": None,
                  "metadata": None,
                  "imageRef": None,
                  "scheduler_hints": None,
                  "backup_id": None}
        self.cinder.volumes.create.assert_called_once_with(
            3, **kwargs)
        self.service._wait_available_volume.assert_called_once_with(
            self.cinder.volumes.create.return_value)
        self.assertEqual(self.service._wait_available_volume.return_value,
                         return_volume)

    def test_update_volume(self):
        return_value = {"volume": fakes.FakeVolume()}
        self.cinder.volumes.update.return_value = return_value

        self.assertEqual(return_value["volume"],
                         self.service.update_volume(1))
        self.cinder.volumes.update.assert_called_once_with(1)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.update_volume")

    def test_update_volume_with_name_description(self):
        return_value = {"volume": fakes.FakeVolume()}
        self.cinder.volumes.update.return_value = return_value

        return_volume = self.service.update_volume(
            1, name="volume", description="fake")

        self.cinder.volumes.update.assert_called_once_with(
            1, name="volume", description="fake")
        self.assertEqual(return_value["volume"], return_volume)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.update_volume")

    def test_list_volumes(self):
        self.assertEqual(self.cinder.volumes.list.return_value,
                         self.service.list_volumes(
                             detailed=False, search_opts=None, limit=1,
                             marker=None, sort=None
                         ))
        self.cinder.volumes.list.assert_called_once_with(
            detailed=False, search_opts=None, limit=1,
            marker=None, sort=None
        )
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.list_volumes")

    def test_list_types(self):
        self.assertEqual(self.cinder.volume_types.list.return_value,
                         self.service.list_types(search_opts=None,
                                                 is_public=None))

        self.cinder.volume_types.list.assert_called_once_with(
            search_opts=None, is_public=None)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.list_types")

    def test_create_snapshot(self):
        self.service._wait_available_volume = mock.MagicMock()
        self.service._wait_available_volume.return_value = fakes.FakeVolume()
        self.service.generate_random_name = mock.MagicMock(
            return_value="snapshot")

        return_snapshot = self.service.create_snapshot(1)

        self.cinder.volume_snapshots.create.assert_called_once_with(
            1, name="snapshot", description=None, force=False,
            metadata=None)
        self.service._wait_available_volume.assert_called_once_with(
            self.cinder.volume_snapshots.create.return_value)
        self.assertEqual(self.service._wait_available_volume.return_value,
                         return_snapshot)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.create_snapshot")

    def test_create_snapshot_with_name(self):
        self.service._wait_available_volume = mock.MagicMock()
        self.service._wait_available_volume.return_value = fakes.FakeVolume()

        return_snapshot = self.service.create_snapshot(1, name="snapshot")

        self.cinder.volume_snapshots.create.assert_called_once_with(
            1, name="snapshot", description=None, force=False,
            metadata=None)
        self.service._wait_available_volume.assert_called_once_with(
            self.cinder.volume_snapshots.create.return_value)
        self.assertEqual(self.service._wait_available_volume.return_value,
                         return_snapshot)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.create_snapshot")

    def test_create_backup(self):
        self.service._wait_available_volume = mock.MagicMock()
        self.service._wait_available_volume.return_value = fakes.FakeVolume()
        self.service.generate_random_name = mock.MagicMock(
            return_value="backup")

        return_backup = self.service.create_backup(1)

        self.cinder.backups.create.assert_called_once_with(
            1, name="backup", description=None, container=None,
            incremental=False, force=False, snapshot_id=None)
        self.service._wait_available_volume.assert_called_once_with(
            self.cinder.backups.create.return_value)
        self.assertEqual(self.service._wait_available_volume.return_value,
                         return_backup)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.create_backup")

    def test_create_backup_with_name(self):
        self.service._wait_available_volume = mock.MagicMock()
        self.service._wait_available_volume.return_value = fakes.FakeVolume()

        return_backup = self.service.create_backup(1, name="backup")

        self.cinder.backups.create.assert_called_once_with(
            1, name="backup", description=None, container=None,
            incremental=False, force=False, snapshot_id=None)
        self.service._wait_available_volume.assert_called_once_with(
            self.cinder.backups.create.return_value)
        self.assertEqual(self.service._wait_available_volume.return_value,
                         return_backup)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.create_backup")

    def test_create_volume_type(self):
        self.service.generate_random_name = mock.MagicMock(
            return_value="volume_type")
        return_type = self.service.create_volume_type(name=None,
                                                      description=None,
                                                      is_public=True)

        self.cinder.volume_types.create.assert_called_once_with(
            name="volume_type", description=None, is_public=True)
        self.assertEqual(self.cinder.volume_types.create.return_value,
                         return_type)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.create_volume_type")

    def test_create_volume_type_with_name_(self):
        return_type = self.service.create_volume_type(name="type",
                                                      description=None,
                                                      is_public=True)

        self.cinder.volume_types.create.assert_called_once_with(
            name="type", description=None, is_public=True)
        self.assertEqual(self.cinder.volume_types.create.return_value,
                         return_type)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.create_volume_type")

    def test_update_volume_type(self):
        volume_type = mock.Mock()
        name = "random_name"
        self.service.generate_random_name = mock.MagicMock(
            return_value=name)
        description = "test update"

        result = self.service.update_volume_type(volume_type,
                                                 description=description,
                                                 update_name=True,
                                                 is_public=None)
        self.assertEqual(
            self.cinder.volume_types.update.return_value,
            result)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.update_volume_type")

    def test_add_type_access(self):
        volume_type = mock.Mock()
        project = mock.Mock()
        type_access = self.service.add_type_access(volume_type,
                                                   project=project)
        add_project_access = self.cinder.volume_type_access.add_project_access
        add_project_access.assert_called_once_with(
            volume_type=volume_type, project=project)
        self.assertEqual(add_project_access.return_value,
                         type_access)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.add_type_access")

    def test_list_type_access(self):
        volume_type = mock.Mock()
        type_access = self.service.list_type_access(volume_type)
        self.cinder.volume_type_access.list.assert_called_once_with(
            volume_type)
        self.assertEqual(self.cinder.volume_type_access.list.return_value,
                         type_access)
        self._test_atomic_action_timer(self.atomic_actions(),
                                       "cinder_v3.list_type_access")


class UnifiedCinderV3ServiceTestCase(test.TestCase):
    def setUp(self):
        super(UnifiedCinderV3ServiceTestCase, self).setUp()
        self.clients = mock.MagicMock()
        self.service = cinder_v3.UnifiedCinderV3Service(self.clients)
        self.service._impl = mock.MagicMock()

    def test__unify_volume(self):
        class SomeVolume(object):
            id = 1
            name = "volume"
            size = 1
            status = "st"
        volume = self.service._unify_volume(SomeVolume())
        self.assertEqual(1, volume.id)
        self.assertEqual("volume", volume.name)
        self.assertEqual(1, volume.size)
        self.assertEqual("st", volume.status)

    def test__unify_volume_with_dict(self):
        some_volume = {"name": "volume", "id": 1, "size": 1, "status": "st"}
        volume = self.service._unify_volume(some_volume)
        self.assertEqual(1, volume.id)
        self.assertEqual("volume", volume.name)
        self.assertEqual(1, volume.size)
        self.assertEqual("st", volume.status)

    def test__unify_snapshot(self):
        class SomeSnapshot(object):
            id = 1
            name = "snapshot"
            volume_id = "volume"
            status = "st"
        snapshot = self.service._unify_snapshot(SomeSnapshot())
        self.assertEqual(1, snapshot.id)
        self.assertEqual("snapshot", snapshot.name)
        self.assertEqual("volume", snapshot.volume_id)
        self.assertEqual("st", snapshot.status)

    def test_create_volume(self):
        self.service._unify_volume = mock.MagicMock()
        self.assertEqual(self.service._unify_volume.return_value,
                         self.service.create_volume(1))
        self.service._impl.create_volume.assert_called_once_with(
            1, availability_zone=None, consistencygroup_id=None,
            description=None, imageRef=None,
            metadata=None, name=None,
            scheduler_hints=None, snapshot_id=None,
            source_volid=None, volume_type=None, backup_id=None)
        self.service._unify_volume.assert_called_once_with(
            self.service._impl.create_volume.return_value)

    def test_list_volumes(self):
        self.service._unify_volume = mock.MagicMock()
        self.service._impl.list_volumes.return_value = ["vol"]
        self.assertEqual([self.service._unify_volume.return_value],
                         self.service.list_volumes(detailed=True))
        self.service._impl.list_volumes.assert_called_once_with(
            detailed=True, limit=None, marker=None, search_opts=None,
            sort=None)
        self.service._unify_volume.assert_called_once_with("vol")

    def test_get_volume(self):
        self.service._unify_volume = mock.MagicMock()
        self.assertEqual(self.service._unify_volume.return_value,
                         self.service.get_volume(1))
        self.service._impl.get_volume.assert_called_once_with(1)
        self.service._unify_volume.assert_called_once_with(
            self.service._impl.get_volume.return_value)

    def test_extend_volume(self):
        self.service._unify_volume = mock.MagicMock()
        self.assertEqual(self.service._unify_volume.return_value,
                         self.service.extend_volume("volume", new_size=1))
        self.service._impl.extend_volume.assert_called_once_with("volume",
                                                                 new_size=1)
        self.service._unify_volume.assert_called_once_with(
            self.service._impl.extend_volume.return_value)

    def test_update_volume(self):
        self.service._unify_volume = mock.MagicMock()
        self.assertEqual(
            self.service._unify_volume.return_value,
            self.service.update_volume(1, name="volume",
                                       description="fake"))
        self.service._impl.update_volume.assert_called_once_with(
            1, description="fake", name="volume")
        self.service._unify_volume.assert_called_once_with(
            self.service._impl.update_volume.return_value)

    def test_list_types(self):
        self.assertEqual(
            self.service._impl.list_types.return_value,
            self.service.list_types(search_opts=None, is_public=True))
        self.service._impl.list_types.assert_called_once_with(
            search_opts=None, is_public=True)

    def test_create_snapshot(self):
        self.service._unify_snapshot = mock.MagicMock()
        self.assertEqual(
            self.service._unify_snapshot.return_value,
            self.service.create_snapshot(1, force=False,
                                         name=None,
                                         description=None,
                                         metadata=None))
        self.service._impl.create_snapshot.assert_called_once_with(
            1, force=False, name=None, description=None, metadata=None)
        self.service._unify_snapshot.assert_called_once_with(
            self.service._impl.create_snapshot.return_value)

    def test_list_snapshots(self):
        self.service._unify_snapshot = mock.MagicMock()
        self.service._impl.list_snapshots.return_value = ["snapshot"]
        self.assertEqual([self.service._unify_snapshot.return_value],
                         self.service.list_snapshots(detailed=True))
        self.service._impl.list_snapshots.assert_called_once_with(
            detailed=True)
        self.service._unify_snapshot.assert_called_once_with(
            "snapshot")

    def test_create_backup(self):
        self.service._unify_backup = mock.MagicMock()
        self.assertEqual(
            self.service._unify_backup.return_value,
            self.service.create_backup(1, container=None,
                                       name=None,
                                       description=None,
                                       incremental=False,
                                       force=False,
                                       snapshot_id=None))
        self.service._impl.create_backup.assert_called_once_with(
            1, container=None, name=None, description=None,
            incremental=False, force=False, snapshot_id=None)
        self.service._unify_backup(
            self.service._impl.create_backup.return_value)

    def test_create_volume_type(self):
        self.assertEqual(
            self.service._impl.create_volume_type.return_value,
            self.service.create_volume_type(name="type",
                                            description="desp",
                                            is_public=True))
        self.service._impl.create_volume_type.assert_called_once_with(
            name="type", description="desp", is_public=True)

    def test_restore_backup(self):
        self.service._unify_volume = mock.MagicMock()
        self.assertEqual(self.service._unify_volume.return_value,
                         self.service.restore_backup(1, volume_id=1))
        self.service._impl.restore_backup.assert_called_once_with(
            1, volume_id=1)
        self.service._unify_volume.assert_called_once_with(
            self.service._impl.restore_backup.return_value)
