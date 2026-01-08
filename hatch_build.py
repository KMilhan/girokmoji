from __future__ import annotations

import os
import subprocess
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface  # type: ignore[import-not-found]


class ZigBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if self.target_name != "wheel":
            return

        zig_cmd = self.config.get("zig", "zig")
        optimize = self.config.get("optimize")
        extra_args = self.config.get("args", [])
        extra_env = self.config.get("env", {})

        if not isinstance(zig_cmd, str) or not zig_cmd:
            raise TypeError("Option `zig` must be a non-empty string")
        if optimize is not None and not isinstance(optimize, str):
            raise TypeError("Option `optimize` must be a string")
        if not isinstance(extra_args, list) or not all(
            isinstance(arg, str) for arg in extra_args
        ):
            raise TypeError("Option `args` must be a list of strings")
        if not isinstance(extra_env, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in extra_env.items()
        ):
            raise TypeError("Option `env` must be a dict of string keys and values")

        cmd = [zig_cmd, "build"]
        if optimize:
            cmd.append(f"-Doptimize={optimize}")
        cmd.extend(extra_args)

        env = os.environ.copy()
        env.update(extra_env)

        subprocess.run(cmd, cwd=self.root, check=True, env=env)
