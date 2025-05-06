"""
aGENtrader v2 Version Information

This module provides version information for the aGENtrader v2 system.
All components should import VERSION from this module for consistency.
"""

# Current version of aGENtrader
VERSION = "0.2.2"

# ASCII art logo for display in console applications
ASCII_LOGO = """
   _____  _____ ______ _   _ _                    _           
  / ____|/ ____|  ____| \ | | |                  | |          
 | |  __| |  __| |__  |  \| | |_ _ __ __ _  __| | ___ _ __ 
 | | |_ | | |_ |  __| | . ` | __| '__/ _` |/ _` |/ _ \ '__|
 | |__| | |__| | |____| |\  | |_| | | (_| | (_| |  __/ |   
  \_____|\_____\______|_| \_|\__|_|  \__,_|\__,_|\___|_|   
                                                          v""" + VERSION

def get_version() -> str:
    """
    Get the current version of aGENtrader.
    
    Returns:
        Version string
    """
    return VERSION
    
def get_version_banner(include_logo: bool = True, mini: bool = False) -> str:
    """
    Get a formatted version banner with ASCII art.
    
    Args:
        include_logo: Whether to include the ASCII logo
        mini: Whether to use a compact version
        
    Returns:
        Formatted version banner string
    """
    if not include_logo:
        if mini:
            return f"aGENtrader v{VERSION}"
        else:
            return f"aGENtrader version {VERSION}"
    
    if mini:
        # Return a smaller version of the logo
        return f"aGENtrader v{VERSION}"
        
    return ASCII_LOGO