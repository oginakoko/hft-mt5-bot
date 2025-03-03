import MetaTrader5 as mt5
import time

def test_mt5_connection():
    print("\n=== Testing MT5 Connection ===")
    
    # First shutdown any existing connections
    mt5.shutdown()
    
    print("\nInitializing MT5...")
    if not mt5.initialize():
        print(f"Initialize failed. Error: {mt5.last_error()}")
        return False
        
    print("\nGetting terminal info...")
    terminal_info = mt5.terminal_info()
    if terminal_info is not None:
        print(f"MetaTrader5 version: {mt5.__version__}")
        print(f"Terminal info:")
        print(f"  Company: {terminal_info.company}")
        print(f"  Name: {terminal_info.name}")
        print(f"  Connected: {terminal_info.connected}")
        print(f"  Path: {terminal_info.path}")
    else:
        print("Failed to get terminal info")
        return False
    
    print("\nAttempting login...")
    login_result = mt5.login(
        login=307731644,
        password="@Philomgaza1",
        server="XMGlobal-MT5 6"
    )
    
    if not login_result:
        error = mt5.last_error()
        print(f"Login failed. Error code: {error[0]}, Message: {error[1]}")
        mt5.shutdown()
        return False
    
    print("\nGetting account info...")
    account_info = mt5.account_info()
    if account_info is not None:
        print(f"Account: {account_info.login}")
        print(f"Name: {account_info.name}")
        print(f"Server: {account_info.server}")
        print(f"Balance: ${account_info.balance:.2f}")
        print(f"Equity: ${account_info.equity:.2f}")
    else:
        print("Failed to get account info")
        return False
    
    print("\nConnection test successful!")
    return True

if __name__ == "__main__":
    try:
        test_mt5_connection()
    finally:
        print("\nShutting down MT5...")
        mt5.shutdown() 