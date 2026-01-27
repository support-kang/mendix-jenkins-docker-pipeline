#!/usr/bin/env python3
import json
import logging
import os
import runpy
import sys
import shutil
import tarfile

from buildpack import util
from buildpack.core import java, runtime
from buildpack.util import get_dependency

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='%(levelname)s: %(message)s',
)

def export_vcap_services():
    logging.debug("Executing build_vcap_services...")

    vcap_services = dict()
    vcap_services['PostgreSQL'] = [{'credentials': { 'uri': "postgres://mendix:mendix@172.17.0.2:5432/mendix" } }]

    vcap_services_str = json.dumps(vcap_services , sort_keys=True, indent=4,
        separators=(',', ': '))
    logging.debug("Set environment variable VCAP_SERVICES: \n{0}"
        .format(vcap_services_str))

    os.environ['VCAP_SERVICES'] = vcap_services_str
    os.environ["PATH"] += os.pathsep + "/opt/mendix/buildpack"

def replace_cf_dependencies():
    logging.debug("Ensuring CF Buildpack dependencies are available")

    mx_version = runtime.get_runtime_version("/opt/mendix/build")
    logging.debug("Detected Mendix version {0}".format(mx_version))

    get_jre_dependency("java.11-jre","jre_11")     
    get_jre_dependency("java.17-jre","jre_17")
    get_jre_dependency("java.21-jre","jre_21")        

# JRE 11, 17, 21 support by Docker Buildpack
def get_jre_dependency(jre_version, jre_destination_version):
    jre_dependency = get_dependency(jre_version, "/opt/mendix/buildpack")
    logging.debug("Creating symlink for jre {0}".format(jre_dependency['artifact']))
    jre_cache_artifact = f"/tmp/buildcache/bust/{jre_dependency['artifact']}"
    jre_destination = '/etc/alternatives/'+jre_destination_version
    with tarfile.open(jre_cache_artifact, "w:gz") as tar:
        # Symlinks to use jre from host OS
        for jre_dir in os.listdir(jre_destination):
            symlink = tarfile.TarInfo(f"jre/{jre_dir}")
            symlink.type = tarfile.SYMTYPE
            symlink.linkname = f"{jre_destination}/{jre_dir}"
            tar.addfile(symlink)


def call_buildpack_compilation():
    logging.debug("Executing call_buildpack_compilation...")
    return runpy.run_module("buildpack.stage", run_name="__main__")

def fix_logfilter():
    exclude_logfilter = os.getenv("EXCLUDE_LOGFILTER", "true").lower() == "true"
    if exclude_logfilter:
        logging.info("Removing mendix-logfilter executable")
        shutil.rmtree("/opt/mendix/build/.local/mendix-logfilter")
    else:
        os.chmod("/opt/mendix/build/.local/mendix-logfilter/mendix-logfilter", 0o0755)

if __name__ == '__main__':
    logging.info("Mendix project compilation phase...")

    export_vcap_services()
    replace_cf_dependencies()
    compilation_globals = call_buildpack_compilation()
    fix_logfilter()
