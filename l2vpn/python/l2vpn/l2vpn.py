# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service


# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class ServiceCallbacks(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')

        # "vars" will be used to store all variables need for the l2vpn-template XML file
        vars = ncs.template.Variables()
        template = ncs.template.Template(service)
        # qos_service_id contains the ID of the referenced QoS service instance
        # any dash in elements defined in the yang module are replaced by underscode in maapi
        qos_service_id = service.link.qos_service_id
        # MAAGIC is used to walk through the NSO databse.
        # starting from root
        # then we enter the referenced qos services instance data by .qos[qos_service_id]
        # in the end the variable qos_policy_name contains the policy-name defined in the qos service instance
        qos_policy_name = root.qos[qos_service_id].policy_name
        # MAAGIC is an easy to use SDK to walk through NSO's data
        # for more convenience, we shorten the paths
        # e.g.: the variabel "ad" is equal to root.l2vpn[{current-instance-id}].access_device
        # thus, "ad" contains the path of the access-device container
        ad = service.access_device
        dd = service.delivery_device
        link = service.link
        # FILL CONFIGURATION TEMPLATE FOR ACCESS DEVICE
        # iface description is generated using multiple input parameters define the yang instance
        iface_description = "-"
        iface_d_params = ("service", service.service_id, "svc", "to", dd.device_id, dd.interface_id,
                          str(dd.vlan_id))
        iface_description = iface_description.join(iface_d_params)
        vars.add('DEVICE_NAME', ad.device_id)
        vars.add('VC_CLASS', link.vc_class)
        vars.add('INTERFACE_ID', ad.interface_id)
        vars.add('SERVICE_ETHERNET_INSTANCE_ID', ad.instance_id)
        vars.add('QOS_POLICY_NAME', qos_policy_name)
        vars.add('VLAN_ID', ad.vlan_id)
        vars.add('REMOTE_IP', dd.ip_add)
        vars.add('VC_ID',link.vc_id)
        vars.add('VC_CLASS',link.vc_class)
        vars.add('IFACE_DESCRIPTION', iface_description)
        # after collecting all required parameters,
        # they are applied in the l2vpn-template to the candidate configuration of NSO
        template.apply('l2vpn-template', vars)
        # FILL CONFIGURATION TEMPLATE FOR DELIVERY DEVICE
        iface_description = "-"
        iface_d_params = ("service", service.service_id, "svc", "to", ad.device_id, ad.interface_id,
                          str(ad.vlan_id))
        iface_description = iface_description.join(iface_d_params)
        vars.add('DEVICE_NAME', dd.device_id)
        vars.add('VC_CLASS', link.vc_class)
        vars.add('INTERFACE_ID', dd.interface_id)
        vars.add('SERVICE_ETHERNET_INSTANCE_ID', dd.instance_id)
        vars.add('QOS_POLICY_NAME', qos_policy_name)
        vars.add('VLAN_ID', dd.vlan_id)
        vars.add('REMOTE_IP', ad.ip_add)
        vars.add('VC_ID',link.vc_id)
        vars.add('VC_CLASS',link.vc_class)
        vars.add('IFACE_DESCRIPTION', iface_description)
        # The new recollected variables are applied in the template to the candidate configuration
        # As you see, we can call the same template multiple times with different parameters for different devices
        template.apply('l2vpn-template', vars)


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Main RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service('l2vpn-servicepoint', ServiceCallbacks)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
