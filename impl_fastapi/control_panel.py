from dataclasses import dataclass

from auth import *
from database import engine

@dataclass(slots=True)
class Colors:
    reset = "\033[0m"
    green = "\033[32m"
    orange = "\033[33m"
    blue = "\033[34m"

choice = "choice"
while choice:
    print("")
    print("Authentication Menu")
    print("1. Add user")
    print("2. Reset password")
    print("3. Change username")
    print("4. Change user access level")
    print("5. List users")
    print("6. Delete user")
    print("q. Quit")
    print("")
    choice = input("> ")
    match choice:
        case "1":
            new_username = input("Please provide the new username: ")
            new_password = token_bytes(8).hex()
            success, message = add_user(new_username, password=new_password)
            if success:
                print(f"{Colors.green}User added successfully{Colors.reset}")
                print(f"New password: {new_password}")
            else:
                print(f"{Colors.orange}Unable to add a new user!{Colors.reset}")
                print(f"Reason: {message}")
        case "2":
            username = str(input("Please provide the username to reset: "))
            new_password = token_bytes(8).hex()
            success, message = change_password(username, new_password=new_password)
            if success:
                print(f"Password reset to: {new_password}")
            else:
                print(f"{Colors.orange}Unable to reset password!{Colors.reset}")
                print(f"Reason: {message}")
        case "3":
            old = input("Old username: ")
            new = input("New username: ")
            success, message = change_username(old, new)
            if success:
                print(f"{Colors.green}Username changed{Colors.reset}")
            else:
                print(f"{Colors.orange}Unable to change username!{Colors.reset}")
                print(f"Reason: {message}")
        case "4":
            username = input("Username: ")
            access_level = input("New access level (0 being lowest access): ")
            try:
                access_level = int(access_level)
                success, message = change_access_level(username, access_level)
            except ValueError:
                success = False
                message = "Invalid access level (must be an integer)"
            if success:
                print(f"{Colors.green}Access level changed{Colors.reset}")
            else:
                print(f"{Colors.orange}Cannot change access level!{Colors.reset}")
                print(f"Reason: {message}")
        case "5":
            print("\nUsers:")
            for user, info in list_users().items():
                print()
                print(f"{Colors.blue}Name:{Colors.reset} {user}")
                for data_name, data in info.items():
                    print(f"{Colors.blue}*{Colors.reset} {data_name}: {data}")
        case "6":
            to_delete = input("Username to delete: ")
            success, message = remove_user(to_delete)
            if success:
                print(f"{Colors.green}User deleted{Colors.reset}")
            else:
                print(f"{Colors.orange}Cannot delete user!{Colors.reset}")
                print(f"Reason: {message}")
        case _:
            engine.dispose()
            break
