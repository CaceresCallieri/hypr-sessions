"""
Hyprctl client for retrieving window and workspace data
"""

import json
import subprocess


class HyprctlClient:
    def get_hyprctl_data(self, command):
        """Execute hyprctl command and return JSON data"""
        try:
            result = subprocess.run(
                ["hyprctl", command, "-j"], capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Error executing hyprctl {command}: {e}")
            return None