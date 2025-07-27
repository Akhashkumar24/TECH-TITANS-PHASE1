# cli/cli_utils.py
import os

# Try to import optional packages with fallbacks
try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False
    print("Warning: tabulate not installed. Using basic table formatting.")

try:
    from colorama import init, Fore, Style
    init()
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    print("Warning: colorama not installed. Using plain text output.")
    # Create dummy color constants
    class Fore:
        CYAN = ""
        GREEN = ""
        RED = ""
        YELLOW = ""
        BLUE = ""
    
    class Style:
        RESET_ALL = ""

class CLIUtils:
    @staticmethod
    def print_header(title: str):
        """Print a formatted header"""
        if COLORAMA_AVAILABLE:
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{title.center(60)}")
            print(f"{'='*60}{Style.RESET_ALL}\n")
        else:
            print(f"\n{'='*60}")
            print(f"{title.center(60)}")
            print(f"{'='*60}\n")
    
    @staticmethod
    def print_success(message: str):
        """Print success message"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
        else:
            print(f"SUCCESS: {message}")
    
    @staticmethod
    def print_error(message: str):
        """Print error message"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
        else:
            print(f"ERROR: {message}")
    
    @staticmethod
    def print_warning(message: str):
        """Print warning message"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")
        else:
            print(f"WARNING: {message}")
    
    @staticmethod
    def print_info(message: str):
        """Print info message"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")
        else:
            print(f"INFO: {message}")
    
    @staticmethod
    def print_table(data: list, headers: list, title: str = None):
        """Print formatted table"""
        if title:
            if COLORAMA_AVAILABLE:
                print(f"\n{Fore.CYAN}{title}{Style.RESET_ALL}")
            else:
                print(f"\n{title}")
        
        if not data:
            CLIUtils.print_warning("No data to display")
            return
        
        if TABULATE_AVAILABLE:
            print(tabulate(data, headers=headers, tablefmt="grid"))
        else:
            # Fallback table formatting
            CLIUtils._print_basic_table(data, headers)
    
    @staticmethod
    def _print_basic_table(data: list, headers: list):
        """Basic table formatting without tabulate"""
        # Calculate column widths
        col_widths = [len(str(header)) for header in headers]
        for row in data:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Print header
        header_row = " | ".join(str(headers[i]).ljust(col_widths[i]) for i in range(len(headers)))
        print(header_row)
        print("-" * len(header_row))
        
        # Print data rows
        for row in data:
            data_row = " | ".join(str(row[i]).ljust(col_widths[i]) if i < len(row) else "".ljust(col_widths[i]) for i in range(len(headers)))
            print(data_row)
    
    @staticmethod
    def get_input(prompt: str, required: bool = True) -> str:
        """Get user input with validation"""
        while True:
            value = input(f"{prompt}: ").strip()
            if not required or value:
                return value
            CLIUtils.print_error("This field is required!")
    
    @staticmethod
    def get_choice(prompt: str, choices: list) -> str:
        """Get user choice from a list"""
        while True:
            print(f"\n{prompt}")
            for i, choice in enumerate(choices, 1):
                print(f"{i}. {choice}")
            
            try:
                choice_num = int(input("\nEnter your choice: "))
                if 1 <= choice_num <= len(choices):
                    return choices[choice_num - 1]
                else:
                    CLIUtils.print_error("Invalid choice!")
            except ValueError:
                CLIUtils.print_error("Please enter a valid number!")
    
    @staticmethod
    def confirm(message: str) -> bool:
        """Get yes/no confirmation"""
        while True:
            response = input(f"{message} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                CLIUtils.print_error("Please enter 'y' or 'n'")
    
    @staticmethod
    def clear_screen():
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def press_enter_to_continue():
        """Wait for user to press enter"""
        if COLORAMA_AVAILABLE:
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
        else:
            input(f"\nPress Enter to continue...")