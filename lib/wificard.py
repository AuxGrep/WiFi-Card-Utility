import sys
import time
import os
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import box
from typing import Tuple, Optional

console = Console()
card_check = []

class NetCard:
    @staticmethod
    def check_adapter(adapter: str) -> Tuple[str, Optional[str]]:
        try:
            # Check if adapter exists
            interfaces = os.listdir("/sys/class/net")
            if adapter not in interfaces:
                return f"[red]✖ Adapter '{adapter}' not found[/red]", None
                
            # Display progress
            with Progress(transient=True) as progress:
                task = progress.add_task(f"[cyan]Checking {adapter}...", total=100)
                
                # Check current mode
                cmd = subprocess.run(['iwconfig', adapter], capture_output=True, text=True)
                progress.update(task, advance=30)
                
                if cmd.returncode != 0:
                    return f"[red]✖ Error checking adapter '{adapter}'[/red]", None
                
                output = cmd.stdout.strip()
                card_check.append(output)
                time.sleep(1)
                progress.update(task, advance=20)
                
                # Case 1: Already in Monitor mode
                if 'Mode:Monitor' in output:
                    with open('monitor.txt', 'w') as f:
                        f.write(adapter)
                    progress.update(task, completed=100)
                    return f"[green]✔ Adapter '{adapter}' is already in Monitor mode[/green]", adapter

                # Case 2: Not in Monitor mode nita switch it
                console.print(f"[yellow]🔄 Enabling monitor mode for '{adapter}'...[/yellow]")
                subprocess.Popen(['airmon-ng', 'check', 'kill'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
                subprocess.Popen(['airmon-ng', 'start', adapter], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Wait and check for new interface
                for _ in range(5):
                    time.sleep(1)
                    progress.update(task, advance=10)
                    
                # Detect new monitor interface
                interfaces_after = os.listdir("/sys/class/net")
                mon_iface = None
                for iface in interfaces_after:
                    if iface.startswith(adapter) and iface != adapter:
                        mon_iface = iface
                        break
                        
                if not mon_iface:
                    progress.update(task, completed=100)
                    return f"[red]⚠ Could not detect monitor interface after enabling monitor mode[/red]", None

                # Final confirmation
                cmd = subprocess.run(['iwconfig', mon_iface], capture_output=True, text=True)
                progress.update(task, advance=20)
                
                if 'Mode:Monitor' in cmd.stdout:
                    with open('monitor.txt', 'w') as f:
                        f.write(mon_iface)
                    progress.update(task, completed=100)
                    return f"[green]✔ Monitor mode enabled on '{mon_iface}'[/green]", mon_iface
                else:
                    progress.update(task, completed=100)
                    return f"[red]✖ Failed to enable monitor mode on '{adapter}'[/red]", None

        except subprocess.CalledProcessError as e:
            return f"[red]✖ airmon-ng failed: {str(e)}[/red]", None
        except Exception as e:
            return f"[red]An error occurred: {str(e)}[/red]", None

class VIF:
    @staticmethod
    def check_vif(adapter: str) -> str:
        try:
            with console.status("[cyan]Checking VIF support...[/cyan]", spinner="dots"):
                vif_name = "mon_test"
                subprocess.run(['iw', 'dev', adapter, 'interface', 'add', vif_name, 'type', 'monitor'], 
                             check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                interfaces = os.listdir("/sys/class/net")
                if vif_name in interfaces:
                    result = f"[green]✔ Virtual Interface '{vif_name}' created successfully. VIF is supported.[/green]"
                    subprocess.run(['iw', 'dev', vif_name, 'del'], 
                                 check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    return result
                else:
                    return f"[red]✖ Virtual interface creation failed. VIF might not be supported.[/red]"
                    
        except subprocess.CalledProcessError:
            return "[red]✖ VIF creation failed. Adapter may not support VIF or permission issue.[/red]"
        except Exception as e:
            return f"[red]An error occurred while checking VIF: {str(e)}[/red]"

class InjectionTest:
    @staticmethod
    def check_injection(adapter: str) -> str:
        try:
            with console.status("[cyan]Testing packet injection...[/cyan]", spinner="dots"):
                console.print("[yellow]This may take a few seconds...[/yellow]")
                cmd = subprocess.run(['aireplay-ng', '--test', adapter], 
                                    capture_output=True, text=True, timeout=30)
                output = cmd.stdout.strip()
                
                if "Injection is working" in output:
                    return "[green]✔ Packet injection is supported.[/green]"
                elif "Injection failed" in output:
                    return "[red]✖ Packet injection test failed.[/red]"
                else:
                    return "[yellow]⚠ Packet injection status unknown. Check manually.[/yellow]"
                    
        except subprocess.TimeoutExpired:
            return "[red]✖ Packet injection test timed out.[/red]"
        except FileNotFoundError:
            return "[red]✖ aireplay-ng not found. Install aircrack-ng package.[/red]"
        except Exception as e:
            return f"[red]An error occurred during injection test: {str(e)}[/red]"

def unique_report(test_name: str, result: str) -> Table:
    table = Table(box=box.ROUNDED, show_header=False)
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="magenta")
    table.add_row("Test", test_name)
    table.add_row("Result", result)
    return table