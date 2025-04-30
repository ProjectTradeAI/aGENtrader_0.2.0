"""
aGENtrader v2 - Version Information

This module defines version constants and provides version information
for the aGENtrader system.
"""

# Version string should follow semantic versioning (major.minor.patch)
VERSION = "0.2.0"

# ASCII Art Logo
ASCII_LOGO = r"""
    ___   ______ _____  _   _  __               __           
   /   | / ____// ___/ / | / |/ /  __  ______  / /___  ____  
  / /| |/ / __  \__ \ /  |/   /  / / / / __ \/ __/ _ \/ __ \ 
 / ___ / /_/ / ___/ // /|  /   / /_/ / / / / /_/  __/ / / / 
/_/  |_\____/ /____//_/ |_/    \__,_/_/ /_/\__/\___/_/ /_/  
 
 Multi-Agent AI Trading System | Version {version}
 ----------------------------------------------------
"""

def get_version_string() -> str:
    """
    Get the full version string.
    
    Returns:
        String with version information
    """
    return f"aGENtrader v{VERSION}"

def print_banner() -> None:
    """
    Print the aGENtrader ASCII logo banner with version.
    """
    print(ASCII_LOGO.format(version=VERSION))
    
def get_version_banner(include_logo: bool = True, mini: bool = False) -> str:
    """
    Get the formatted version banner as a string.
    
    Args:
        include_logo: Whether to include the ASCII logo
        mini: Whether to use a compact version of the banner
        
    Returns:
        String containing the version banner
    """
    if not include_logo:
        if mini:
            return f"aGENtrader v{VERSION}"
        else:
            return f"aGENtrader v{VERSION} - Multi-Agent AI Trading System"
            
    if mini:
        # Just return the first and last lines
        lines = ASCII_LOGO.split('\n')
        filtered_lines = [line for line in lines if line.strip()]
        return f"{filtered_lines[0]}\n{filtered_lines[-1].format(version=VERSION)}"
        
    return ASCII_LOGO.format(version=VERSION)

def get_version_dict() -> dict:
    """
    Get version information as a dictionary.
    
    Returns:
        Dictionary with version components
    """
    parts = VERSION.split('.')
    
    version_dict = {
        'version': VERSION,
        'major': int(parts[0]) if len(parts) > 0 else 0,
        'minor': int(parts[1]) if len(parts) > 1 else 0,
        'patch': int(parts[2]) if len(parts) > 2 else 0,
    }
    
    return version_dict