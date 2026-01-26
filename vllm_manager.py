"""
vLLM Manager - Start, stop, and check status of vLLM server in WSL2.

This tool manages the vLLM server running in WSL2 to free GPU memory when not needed.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from kb_config import (
    is_vllm_running, start_vllm, stop_vllm, vllm_status,
    VLLM_MODEL, VLLM_URL, WSL_DISTRO
)

def show_status():
    """Display vLLM status."""
    status = vllm_status()

    print("\n" + "=" * 50)
    print("vLLM STATUS")
    print("=" * 50)
    print(f"  WSL Distro:    {WSL_DISTRO}")
    print(f"  URL:           {VLLM_URL}")
    print(f"  Expected Model: {VLLM_MODEL}")
    print("-" * 50)
    print(f"  Process Running: {'Yes' if status['running'] else 'No'}")
    print(f"  API Responsive:  {'Yes' if status['responsive'] else 'No'}")
    if status['model']:
        print(f"  Loaded Model:    {status['model']}")
    print("=" * 50)

    if status['running'] and status['responsive']:
        print("\n  Status: ONLINE - GPU memory in use")
        print("  Run 'python vllm_manager.py stop' to free GPU memory")
    elif status['running']:
        print("\n  Status: STARTING - Model may still be loading")
    else:
        print("\n  Status: OFFLINE - GPU memory is free")
        print("  Run 'python vllm_manager.py start' to start vLLM")

def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("vLLM Manager - Control vLLM server in WSL2")
        print("=" * 50)
        print("\nUsage:")
        print("  python vllm_manager.py <command>")
        print("\nCommands:")
        print("  status   Show vLLM status")
        print("  start    Start vLLM server (loads model into GPU)")
        print("  stop     Stop vLLM server (frees GPU memory)")
        print("\nNotes:")
        print(f"  - vLLM runs in WSL2 ({WSL_DISTRO})")
        print(f"  - Model: {VLLM_MODEL}")
        print(f"  - URL: {VLLM_URL}")
        return

    cmd = sys.argv[1].lower()

    if cmd == 'status':
        show_status()

    elif cmd == 'start':
        print("Starting vLLM server...")
        if start_vllm():
            print("vLLM started successfully")
            show_status()
        else:
            print("Failed to start vLLM - check WSL2 and GPU")

    elif cmd == 'stop':
        print("Stopping vLLM server...")
        if stop_vllm():
            print("vLLM stopped - GPU memory freed")
        else:
            print("Failed to stop vLLM")

    else:
        print(f"Unknown command: {cmd}")
        print("Run without arguments for help.")

if __name__ == "__main__":
    main()
