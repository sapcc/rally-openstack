# Copyright 2016 IBM Corp.
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

from rally import exceptions
from rally.task import types
from rally.task import validation

from rally_openstack import consts
from rally_openstack import scenario
from rally_openstack.scenarios.nova import utils


"""Scenarios for Nova aggregates."""


@validation.add("required_services", services=[consts.Service.NOVA])
@validation.add("required_platform", platform="openstack", admin=True)
@scenario.configure(name="NovaAggregates.list_aggregates",
                    platform="openstack")
class ListAggregates(utils.NovaScenario):

    def run(self):
        """List all nova aggregates.

        Measure the "nova aggregate-list" command performance.
        """
        self._list_aggregates()


@validation.add("required_services", services=[consts.Service.NOVA])
@validation.add("required_platform", platform="openstack", admin=True)
@scenario.configure(context={"admin_cleanup@openstack": ["nova"]},
                    name="NovaAggregates.create_and_list_aggregates",
                    platform="openstack")
class CreateAndListAggregates(utils.NovaScenario):
    """scenario for create and list aggregate."""

    def run(self, availability_zone):
        """Create a aggregate and then list all aggregates.

        This scenario creates a aggregate and then lists all aggregates.
        :param availability_zone: The availability zone of the aggregate
        """
        aggregate = self._create_aggregate(availability_zone)
        msg = "Aggregate isn't created"
        self.assertTrue(aggregate, err_msg=msg)
        all_aggregates = self._list_aggregates()
        msg = ("Created aggregate is not in the"
               " list of all available aggregates")
        self.assertIn(aggregate, all_aggregates, err_msg=msg)


@validation.add("required_services", services=[consts.Service.NOVA])
@validation.add("required_platform", platform="openstack", admin=True)
@scenario.configure(context={"admin_cleanup@openstack": ["nova"]},
                    name="NovaAggregates.create_and_delete_aggregate",
                    platform="openstack")
class CreateAndDeleteAggregate(utils.NovaScenario):
    """Scenario for create and delete aggregate."""

    def run(self, availability_zone):
        """Create an aggregate and then delete it.

        This scenario first creates an aggregate and then delete it.
        :param availability_zone: The availability zone of the aggregate
        """
        aggregate = self._create_aggregate(availability_zone)
        self._delete_aggregate(aggregate)


@validation.add("required_services", services=[consts.Service.NOVA])
@validation.add("required_platform", platform="openstack", admin=True)
@scenario.configure(context={"admin_cleanup@openstack": ["nova"]},
                    name="NovaAggregates.create_and_update_aggregate",
                    platform="openstack")
class CreateAndUpdateAggregate(utils.NovaScenario):
    """Scenario for create and update aggregate."""

    def run(self, availability_zone):
        """Create an aggregate and then update its name and availability_zone

        This scenario first creates an aggregate and then update its name and
        availability_zone
        :param availability_zone: The availability zone of the aggregate
        """
        aggregate = self._create_aggregate(availability_zone)
        self._update_aggregate(aggregate)


@validation.add("required_services", services=[consts.Service.NOVA])
@validation.add("required_platform", platform="openstack", admin=True)
@scenario.configure(context={"admin_cleanup@openstack": ["nova"]},
                    name="NovaAggregates.create_aggregate_add_and_remove_host",
                    platform="openstack")
class CreateAggregateAddAndRemoveHost(utils.NovaScenario):
    """Scenario for add a host to and remove the host from an aggregate."""

    def run(self, availability_zone):
        """Create an aggregate, add a host to and remove the host from it

        Measure "nova aggregate-add-host" and "nova aggregate-remove-host"
        command performance.
        :param availability_zone: The availability zone of the aggregate
        """
        aggregate = self._create_aggregate(availability_zone)
        hosts = self._list_hypervisors()
        host_name = hosts[0].service["host"]
        self._aggregate_add_host(aggregate, host_name)
        self._aggregate_remove_host(aggregate, host_name)


@validation.add("required_services", services=[consts.Service.NOVA])
@validation.add("required_platform", platform="openstack", admin=True)
@scenario.configure(context={"admin_cleanup@openstack": ["nova"]},
                    name="NovaAggregates.create_and_get_aggregate_details",
                    platform="openstack")
class CreateAndGetAggregateDetails(utils.NovaScenario):
    """Scenario for create and get aggregate details."""

    def run(self, availability_zone):
        """Create an aggregate and then get its details.

        This scenario first creates an aggregate and then get details of it.
        :param availability_zone: The availability zone of the aggregate
        """
        aggregate = self._create_aggregate(availability_zone)
        self._get_aggregate_details(aggregate)


@types.convert(image={"type": "glance_image"})
@validation.add("required_services", services=[consts.Service.NOVA])
@validation.add("required_platform", platform="openstack",
                admin=True, users=True)
@scenario.configure(
    context={"admin_cleanup@openstack": ["nova"],
             "cleanup@openstack": ["nova"]},
    name="NovaAggregates.create_aggregate_add_host_and_boot_server",
    platform="openstack")
class CreateAggregateAddHostAndBootServer(utils.NovaScenario):
    """Scenario to verify an aggregate."""

    def run(self, image, metadata, availability_zone=None, ram=512, vcpus=1,
            disk=1, boot_server_kwargs=None):
        """Scenario to create and verify an aggregate

        This scenario creates an aggregate, adds a compute host and metadata
        to the aggregate, adds the same metadata to the flavor and creates an
        instance. Verifies that instance host is one of the hosts in the
        aggregate.

        :param image: The image ID to boot from
        :param metadata: The metadata to be set as flavor extra specs
        :param availability_zone: The availability zone of the aggregate
        :param ram: Memory in MB for the flavor
        :param vcpus: Number of VCPUs for the flavor
        :param disk: Size of local disk in GB
        :param boot_server_kwargs: Optional additional arguments to verify host
        aggregates
        :raises RallyException: if instance and aggregate hosts do not match
        """

        boot_server_kwargs = boot_server_kwargs or {}

        aggregate = self._create_aggregate(availability_zone)
        hosts = self._list_hypervisors()

        host_name = None
        for i in range(len(hosts)):
            if hosts[i].state == "up" and hosts[i].status == "enabled":
                host_name = hosts[i].service["host"]
                break
        if not host_name:
            raise exceptions.RallyException("Could not find an available host")

        self._aggregate_set_metadata(aggregate, metadata)
        self._aggregate_add_host(aggregate, host_name)
        flavor = self._create_flavor(ram, vcpus, disk)
        flavor.set_keys(metadata)

        server = self._boot_server(image, flavor.id, **boot_server_kwargs)
        # NOTE: we need to get server object by admin user to obtain
        # "hypervisor_hostname" attribute
        server = self.admin_clients("nova").servers.get(server.id)
        instance_hostname = getattr(server,
                                    "OS-EXT-SRV-ATTR:hypervisor_hostname")
        if instance_hostname != host_name:
            raise exceptions.RallyException("Instance host and aggregate "
                                            "host are different")
