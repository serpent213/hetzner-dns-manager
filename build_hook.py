import os
import shutil
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomBuildHook(BuildHookInterface):
    def initialize(self, _version, build_data):
        # Otherwise the launcher will not be able to import it...
        # When building the wheel, `hdem` will not be included, so we need to catch this case.
        if not os.path.exists("hdem.py"):
            shutil.copy("hdem", "hdem.py")
        return build_data

    def finalize(self, _version, _build_data, artifact_path):
        if os.path.exists("hdem.py"):
            os.remove("hdem.py")
        return artifact_path
