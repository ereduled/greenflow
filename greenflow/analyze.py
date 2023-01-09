#!/usr/bin/env python3
import json
from os import chmod, walk
from shlex import split

import ansible_runner
import gin
import pendulum
from sh import ansible_playbook, rm

from .g import g
from .g5k import G5KPlatform
from .platform import MockPlatform, Platform


def pre_deploy(platform: Platform):
    # g.storage.create_new_exp()
    g.storage.create_new_exp()
    g.storage.write_gin_config()
    platform.pre_setup()


def post_deploy(platform: Platform):
    # g.storage.create_new_exp()
    platform.post_setup()


@gin.configurable
def deploy(*, platform: type[Platform] = gin.REQUIRED):
    p: Platform = platform()
    g.deployment_start = pendulum.now()
    match p:
        case MockPlatform():
            p.pre_deploy()
        case G5KPlatform():
            pre_deploy(p)
            inv = p.setup()
            post_deploy(p)

            # sh.rm(split("-rfv ./ansible/main.json"), _ok_code=[0, 1])
            rm(
                split("-rfv ./ansible/project/main.json"),
                _ok_code=[0, 1],
            )
            # for r, d, f in walk("./ansible"):
            #     chmod(r, 0o777)
            # chmod("./inventory/inventory/hosts.json", 0o600)
            with open("./ansible/inventory/hosts.json", "w") as f:
                json.dump(inv, f, ensure_ascii=False, indent=4)
            ansible_runner.run(
                # host_pattern="control,worker",
                # role="k3s-common",
                playbook="k3s-setup.yaml",
                # inventory=inv,
                private_data_dir="./ansible",
                extravars={"kubeconfig_path": "../../kubeconfig"},
                # verbosity=3,
            )
            # ansible_runner.run(
            #     playbook="k3s-setup.yaml",
            #     inventory=p.ansible_inventory_file_path,
            #     private_data_dir="./ansible",
            # )
            # ansible_runner.run(
            #     playbook="helm-setup.yaml",
            #     inventory=p.ansible_inventory_file_path,
            #     private_data_dir="./ansible",
            #     tags=["redeploy"]
            #     # cmdline=["-t", "redeploy"],
            # )
            # ansible_playbook(
            #     split(
            #         f"helm-setup.yaml -i {p.ansible_inventory_file_path} -t redeploy"
            #     ),
            #     _fg=True,
            # )
            # run = ansible_runner.run(
            #     playbook="helm-setup.yaml",
            #     inventory=p.ansible_inventory_file_path,
            #     private_data_dir="./ansible",
            #     extravars={"deployment_ts": g.deployment_start.to_iso8601_string()},
            #     rotate_artifacts=5,
            # )
            run = ansible_runner.run(
                # role="helm",
                # inventory=p.ansible_inventory_file_path,
                playbook="helm.yaml",
                private_data_dir="./ansible",
                extravars={"deployment_ts": g.deployment_start.to_iso8601_string()},
                # rotate_artifacts=5,
            )

            # run.get_fact_cache("nova-1.lyon.grid5000.fr")
            # ansible_playbook(
            #     split(f"helm-setup.yaml -i {p.ansible_inventory_file_path}"), _fg=True
            # )


if __name__ == "__main__":
    deploy()