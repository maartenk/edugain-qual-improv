#!/usr/bin/env python3

# This script will download the current edugain metadata aggregate XML
# and parse it to derive a list in CSV format of entities who do have a security contact
# but do not carry a SIRTFI EC.

# This list will be printed to stdout.

# Based on the code of https://gitlab.geant.org/edugain/edugain-contacts

import csv
import sys
from xml.etree import ElementTree as ET

import requests

# production
xml_req = requests.get('https://mds.edugain.org/edugain-v2.xml')
root = ET.fromstring(xml_req.content)

# local
# root = ET.parse('./edugain-v1.xml')

entities_list = []

ns = {
    'md': 'urn:oasis:names:tc:SAML:2.0:metadata',
    'mdui': 'urn:oasis:names:tc:SAML:metadata:ui',
    'shibmd': 'urn:mace:shibboleth:metadata:1.0',
    'remd': 'http://refeds.org/metadata',
    'icmd': 'http://id.incommon.org/metadata',
    'mdrpi': 'urn:oasis:names:tc:SAML:metadata:rpi',
    'mdattr': 'urn:oasis:names:tc:SAML:metadata:attribute',
    'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
}

entities = root.findall('./md:EntityDescriptor', ns)

for entity in entities:
    sirtfi = False

    sec_contact_els = entity.findall(
        './md:ContactPerson[@remd:contactType="http://refeds.org/metadata/contactType/security"]', ns) + \
                      entity.findall(
                          './md:ContactPerson[@icmd:contactType="http://id.incommon.org/metadata/contactType/security"]',
                          ns)

    for ec in entity.findall(
            './md:Extensions/mdattr:EntityAttributes/saml:Attribute[@Name="urn:oasis:names:tc:SAML:attribute:assurance-certification"]/saml:AttributeValue',
            ns):
        if ec.text == "https://refeds.org/sirtfi":
            sirtfi = True

    if sec_contact_els and not sirtfi:

        ent_id = (entity.find('.').attrib['entityID'])

        registration_authority = ''
        registration_info = entity.find(
            './md:Extensions/mdrpi:RegistrationInfo', ns)
        if registration_info is None:
            continue
        else:
            registration_authority = registration_info.attrib['registrationAuthority'].strip(
            )
        orgname = entity.find(
            './md:Organization/md:OrganizationDisplayName', ns).text.strip()

        if entity.find('./md:SPSSODescriptor', ns):
            ent = "SP"
        elif entity.find('./md:IDPSSODescriptor', ns):
            ent = "IdP"
        else:
            ent = None

        entities_list.append([registration_authority, ent, orgname, ent_id])

writer = csv.writer(sys.stdout)
writer.writerows(entities_list)
