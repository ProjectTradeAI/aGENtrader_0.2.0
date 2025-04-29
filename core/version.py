"""
aGENtrader Version Information

This module provides centralized version information for the aGENtrader system.
All components should import version information from here to ensure consistency.
"""

# Current version of the aGENtrader system
VERSION = "v2.2.0"

# ASCII logo for branding (with ANSI color codes for terminal output)
ASCII_LOGO = """
\033[38;5;208m   █████╗  ██████╗ ███████╗███╗   ██╗████████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
\033[38;5;214m  ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
\033[38;5;220m  ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝███████║██║  ██║█████╗  ██████╔╝
\033[38;5;226m  ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗██╔══██║██║  ██║██╔══╝  ██╔══██╗
\033[38;5;227m  ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ██║  ██║██║  ██║██████╔╝███████╗██║  ██║
\033[38;5;228m  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
\033[0m                                                                                        
"""

# Plain ASCII logo (no color codes) for non-terminal environments
PLAIN_ASCII_LOGO = """
   █████╗  ██████╗ ███████╗███╗   ██╗████████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
  ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
  ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝███████║██║  ██║█████╗  ██████╔╝
  ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗██╔══██║██║  ██║██╔══╝  ██╔══██╗
  ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ██║  ██║██║  ██║██████╔╝███████╗██║  ██║
  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                                        
"""

# Bitcoin-themed mini logo for compact displays
MINI_LOGO = """
\033[38;5;208m  ₿₿₿   ₿₿₿₿₿  ₿₿₿₿₿  ₿   ₿  ₿₿₿₿₿₿  ₿₿₿₿   ₿₿₿₿   ₿₿₿₿₿  ₿₿₿₿₿  ₿₿₿₿  
\033[38;5;214m ₿   ₿  ₿      ₿      ₿₿  ₿    ₿    ₿    ₿  ₿   ₿  ₿      ₿      ₿   ₿ 
\033[38;5;220m ₿₿₿₿₿  ₿  ₿₿  ₿₿₿₿   ₿ ₿ ₿    ₿    ₿₿₿₿₿   ₿₿₿₿   ₿₿₿₿   ₿₿₿₿   ₿₿₿₿  
\033[38;5;226m ₿   ₿  ₿   ₿  ₿      ₿  ₿₿    ₿    ₿    ₿  ₿   ₿  ₿      ₿      ₿ ₿   
\033[38;5;227m ₿   ₿  ₿₿₿₿₿  ₿₿₿₿₿  ₿   ₿    ₿    ₿    ₿  ₿   ₿  ₿₿₿₿₿  ₿₿₿₿₿  ₿  ₿  
\033[0m                                                                                
"""

# Version banner for logs
VERSION_BANNER = f"aGENtrader {VERSION} - Multi-Agent AI Trading System"

def get_version_banner(include_logo=False, mini=False):
    """
    Get a formatted version banner, optionally with a logo.
    
    Args:
        include_logo: Whether to include the ASCII logo
        mini: Whether to use the mini logo (if including a logo)
        
    Returns:
        A formatted string with version information
    """
    if include_logo:
        if mini:
            return f"{MINI_LOGO}\n{VERSION_BANNER}"
        else:
            return f"{ASCII_LOGO}\n{VERSION_BANNER}"
    return VERSION_BANNER