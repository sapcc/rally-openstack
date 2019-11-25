# Copyright 2013: Mirantis Inc.
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

from rally.common import cfg

OPTS = {"openstack": [
    cfg.FloatOpt("neutron_create_loadbalancer_timeout",
                 default=float(500),
                 deprecated_group="benchmark",
                 help="Neutron create loadbalancer timeout"),
    cfg.FloatOpt("neutron_create_loadbalancer_poll_interval",
                 default=float(2),
                 deprecated_group="benchmark",
                 help="Neutron create loadbalancer poll interval"),
    cfg.BoolOpt("pre_newton_neutron",
                default=False,
                help="Whether Neutron API is older then OpenStack Newton or "
                     "not. Based in this option, some external fields for "
                     "identifying resources can be applied."),
    cfg.ListOpt("neutron_bind_l2_agent_types",
                # default to agent types used in gate jobs
                default=[
                    "Open vSwitch agent",
                    "Linux bridge agent",
                ],
                help="Neutron L2 agent types to find hosts to bind"),
]}
