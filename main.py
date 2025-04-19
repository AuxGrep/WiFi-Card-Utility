# This is official coded by AuxGrep
# time: 1hr + bug fixing

import platform
import os
import sys
import time
import getpass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress
from rich.layout import Layout
from rich.text import Text
import subprocess
from rich import box
from lib.wificard import NetCard, InjectionTest, VIF, unique_report


console = Console()

def banner() -> Panel:
    banner = Text("""
    __        ___ _____ _    ____              _   _   _ _   _ _ _ _         
    \ \      / (_)  ___(_)  / ___|__ _ _ __ __| | | | | | |_(_) (_) |_ _   _ 
     \ \ /\ / /| | |_  | | | |   / _` | '__/ _` | | | | | __| | | | __| | | |
      \ V  V / | |  _| | | | |__| (_| | | | (_| | | |_| | |_| | | | |_| |_| |
       \_/\_/  |_|_|   |_|  \____\__,_|_|  \__,_|  \___/ \__|_|_|_|\__|\__, |
                                                                      |___/ 
                  Author: AuxGrep
                  Unique Cyber Club
                  @2025
    """)

    # my_damn color
    banner.stylize("bold cyan", 4, 12)    # "___ _____"
    banner.stylize("bold yellow", 13, 17) # "_    _"
    banner.stylize("bold green", 18, 23)  # "____"
    banner.stylize("bold red", 78, 85)    # "|___/"

    title_text = Text("\nWiFi Card Utility ", justify="center", style="bold magenta")
    subtitle = Text("Advanced Network Adapter Diagnostics", style="dim cyan", justify="center")

    return Panel(
        banner + title_text + subtitle,
        border_style="bright_blue",
        expand=False,
        padding=(1, 2)
    )

# my requirements checks
def system_checks() -> None:
    with console.status("[bold green]Running system checks...[/]", spinner="dots"):
        # OS Check
        if platform.system() != 'Linux':
            console.print("[red bold]✖ Error: Only Linux systems are supported[/]")
            sys.exit(1)

        # Root Check
        if os.geteuid() != 0:
            console.print("[red bold]✖ Error: This tool requires root privileges[/]")
            sys.exit(1)

        # Dependency Check
        try:
            subprocess.run(['airmon-ng', '--version'],
                           check=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("[red bold]✖ Error: aircrack-ng suite not found. Install with 'sudo apt install aircrack-ng'[/]")
            sys.exit(1)

        time.sleep(1)

# bring the net device interfaces
def display_interfaces() -> None:
    interfaces = os.listdir("/sys/class/net")
    console.print("\n[bold]Available Network Interfaces:[/]")
    for idx, iface in enumerate(interfaces, 1):
        console.print(f"  [cyan]{idx}.[/] [yellow]{iface}[/]")
    console.print("")

# user gonna select the adapter
def adapter_choice() -> str:
    while True:
        adapter = Prompt.ask("[bold green]Enter the adapter name[/] (e.g. wlan0)")
        if adapter in os.listdir("/sys/class/net"):
            return adapter
        console.print(f"[red]✖ Adapter '{adapter}' not found. Try again.[/]")

# function for monitor mode
def monitor_mode_test() -> None:
    os.system('clear')
    console.print(banner())
    display_interfaces()

    adapter = adapter_choice()
    console.rule("[bold green]Monitor Mode Test[/]", style="blue")

    # Netcard is constractor i made on the lib
    msg, monitor_iface = NetCard.check_adapter(adapter)
    console.print(unique_report("Monitor Mode", msg))

    # If successful, run injection test
    if monitor_iface:
        console.rule("[bold green]Packet Injection Test[/]", style="blue")
        inj_result = InjectionTest.check_injection(adapter=monitor_iface)
        console.print(unique_report("Packet Injection", inj_result))

# Handle Virtual Interface testing
def vif_test() -> None:
    os.system('clear')
    console.print(banner())

    try:
        with open('monitor.txt', 'r') as f:
            monitor_iface = f.read().strip()
            console.print(f"[green]✔ Found monitor interface: [bold]{monitor_iface}[/][/]")
    except FileNotFoundError:
        console.print("[yellow]⚠ No saved monitor interface found. Let's find one...[/]")
        display_interfaces()
        monitor_iface = adapter_choice()

    if not Confirm.ask(f"\n[bold]Test VIF on [cyan]{monitor_iface}[/]?[/]", default=True):
        display_interfaces()
        monitor_iface = adapter_choice()

    console.rule("[bold green]Virtual Interface Test[/]", style="blue")
    vif_result = VIF.check_vif(adapter=monitor_iface)
    console.print(unique_report("VIF Support", vif_result))

# my main menu choice display
def main_menu() -> int:
    options = [
        "Monitor Mode & Packet Injection Test",
        "Virtual Interface (VIF) Test",
        "Exit"
    ]

    while True:
        os.system('clear')
        console.print(banner())

        console.print("[bold]Main Menu:[/]\n")
        for idx, option in enumerate(options, 1):
            console.print(f"  [cyan]{idx}.[/] [yellow]{option}[/]")

        try:
            choice = int(Prompt.ask("\n[bold green]Select an option[/]", choices=["1", "2", "3"]))
            return choice
        except ValueError:
            console.print("[red]Please enter a valid number[/]")
            time.sleep(1)

# main enty point
def main():
    console.print(banner())
    console.print(f"\n[bold]👋 Welcome, [cyan]{getpass.getuser()}[/]![/]\n")
    system_checks()

    while True:
        choice = main_menu()
        if choice == 1:
            monitor_mode_test()
        elif choice == 2:
            vif_test()
        elif choice == 3:
            console.print("\n[bold green]✔ Exiting WiFi Card Utility...[/]\n")
            sys.exit(0)

        if not Confirm.ask("\n[bold]Run another test?[/]", default=True):
            console.print("\n[bold green]✔ Thank you for using WiFi Card Utility![/]\n")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]✖ Operation cancelled by user[/]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red bold]⚠ Unexpected error: {str(e)}[/]\n")
        sys.exit(1)