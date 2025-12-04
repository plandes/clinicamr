#!/usr/bin/env python

from zensols.cli import ConfigurationImporterCliHarness


if (__name__ == '__main__'):
    harness = ConfigurationImporterCliHarness(
        src_dir_name='src',
        package_resource='zensols.clinicamr',
        config_path='etc/clinicamr.conf',
        proto_args={0: 'proto',
                    1: 'proto --override amr_default.parse_model=gsii'
                    }[0],
        proto_factory_kwargs={'reload_pattern': r'^zensols.clinicamr'},
    )
    harness.run()
