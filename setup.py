#!/usr/bin/env python
import logging
from pkg_resources import Requirement
from setuptools import setup, find_packages

log = logging.getLogger(__name__)

with open('requirements.txt') as f:
    REQUIREMENTS = []
    for req in f.readlines():
        req = req.strip()
        try:
            Requirement.parse(req)
        except:
            log.warning('failed to parse `{0}` from requirements.txt, skipping\n'.format(req))
            continue
        if len(req) is 0:
            continue
        REQUIREMENTS.append(req)


setup(
    name='Sublime Text Ansible Vault',
    version='1.0.0',
    description='',
    author='Adam Bullmer',
    author_email='psycodrumfreak@gmail.com',
    url='https://github.com/rewardStyle/sublime_ansible_vault',
    packages=find_packages(),
    include_package_data=True,
    install_requires=REQUIREMENTS,
    zip_safe=False,
)
