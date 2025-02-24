import asyncio
import os
import re
import shutil
import time
from enum import Enum

VERSION = 1.0

class FileType(str, Enum):
    Txt = "txt"

class TimeUnit(int, Enum):
    seconds = 1
    minutes = 60
    hours = 3600

class ActionType(str, Enum):
    Start = "SYNC START"
    End = "SYNC END"
    Copied_file = "COPIED FILE"
    Created_folder = "CREATED FOLDER"
    Deleted_file = "DELETED FILE"
    Deleted_folder = "DELETED FOLDER"
    Resetting_Replica_folder = "RESETTING REPLICA FOLDER"

class SyncManager:
    time_unit = TimeUnit.seconds

class Config:
    version = 1.0

class FileManager:
    """variables"""
    use_log_file = False
    log_file_path = ""

    """ Private Methods """
    @staticmethod
    def _create_folders(source_path: str, replica_path: str):
        """
        Copies the folders from the source path to the replica path.\n
        Args:
            source_path (str): path to the source directory.
            replica_path (str): path to the replica directory.
        """
        for root, _, _ in os.walk(source_path):
            subdir_relative_path = os.path.relpath(root, source_path)
            replica_dir_path = os.path.join(replica_path, subdir_relative_path)
            if not os.path.exists(replica_dir_path):
                FileManager.log_change(ActionType.Created_folder, replica_dir_path, subdir_relative_path)
                os.makedirs(replica_dir_path)

    @staticmethod
    def _copy_files(source_path: str, replica_path: str):
        """
        Copies files from source to replica if they are newer or missing.\n
        Args:
            source_path (str): path to the source directory.
            replica_path (str): path to the replica directory.

        """
        for root, _, files in os.walk(source_path):
            subdir_relative_path = os.path.relpath(root, source_path)
            replica_root = os.path.join(replica_path, subdir_relative_path)

            for file in files:
                source_file = os.path.join(root, file)
                replica_file = os.path.join(replica_root, file)

                if not os.path.exists(replica_file) or os.path.getmtime(source_file) > os.path.getmtime(replica_file):
                    FileManager.log_change(ActionType.Copied_file, replica_file, file)
                    shutil.copy2(source_file, replica_file)

    @staticmethod
    def _delete_removed_files(source_path: str, replica_path: str):
        """
        Delete files from the replica that no longer exist in the source.
        Args:
            source_path (str): path to the source directory.
            replica_path (str): path to the replica directory.
        """
        for root, _, files in os.walk(replica_path, topdown=False):
            relative_path = os.path.relpath(root, replica_path)
            source_root = os.path.join(source_path, relative_path)

            for file in files:
                replica_file = os.path.join(root, file)
                source_file = os.path.join(source_root, file)

                if not os.path.exists(source_file):
                    FileManager.log_change(ActionType.Deleted_file, root, file)
                    os.remove(replica_file)

            if not os.path.exists(source_root):
                FileManager.log_change(ActionType.Deleted_folder, root, relative_path)
                shutil.rmtree(root)

    @staticmethod
    def log_change(action_type: ActionType, full_path="", relative_path=""):
        """
        Logs the action performed on a file or folder, including the time and date of the action,
        and writes the log entry to a specified log file.

        Parameters:
            action_type (ActionType): The type of action being performed (e.g., "Start", "Copied_file", "Created_folder", "Deleted_folder", "Deleted_file").
            full_path (str, optional): The full path to the file or folder affected by the action. Default is None.
            relative_path (str, optional): The relative path to the file or folder affected by the action. Default is an empty string.
        """
        log_entry = ""

        if action_type == ActionType.Start:
            log_entry += "\n--------------------------------------------------------------------------------------------------"

        current_time = time.strftime("%H:%M:%S")
        current_date = time.strftime("%d/%m/%Y")

        log_entry += f"\n[{current_time} - {current_date}] - "

        log_entry += action_type.value

        if action_type == ActionType.Copied_file:
            log_entry += f"    - Copied file '{relative_path}' to '{full_path}'"
        elif action_type == ActionType.Created_folder:
            log_entry += f" - Created folder '{relative_path}' in '{full_path}'"
        elif action_type == ActionType.Deleted_folder:
            log_entry += f" - Deleted folder '{relative_path}' in '{full_path}'"
        elif action_type == ActionType.Deleted_file:
            log_entry += f"   - Deleted file '{relative_path}' in '{full_path}'"

        if action_type == ActionType.End:
            log_entry += "\n--------------------------------------------------------------------------------------------------"

        with open(FileManager.log_file_path, 'a') as log_file:
            log_file.write(log_entry)

        print(log_entry)

    """ Public Methods """
    @staticmethod
    def clear_folder(folder_path: str):
        """
        Removes all files and subdirectories inside the specified folder.

        Args:
            folder_path (str): The path to the folder to be cleared.

        Raises:
            FileNotFoundError: If the specified folder does not exist.
            PermissionError: If there are insufficient permissions to delete files.
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"The folder '{folder_path}' does not exist.")

        FileManager.log_change(ActionType.Resetting_Replica_folder)
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            try:
                if os.path.isfile(file_path):
                    FileManager.log_change(ActionType.Deleted_file, file_path, relative_path=file)
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    FileManager.log_change(ActionType.Deleted_folder, file_path, relative_path=file)
                    shutil.rmtree(file_path)
            except PermissionError:
                print(f"Permission denied: Could not delete '{file_path}'")

    @staticmethod
    async def sync_folders(source_path: str,replica_path: str):
        """
        Sync folders by creating directories, copying files, and deleting removed files.\n
        Args:
            source_path (str): path to the source directory.
            replica_path (str): path to the replica directory.
        """
        FileManager.log_change(ActionType.Start)
        FileManager._create_folders(source_path, replica_path)
        FileManager._copy_files(source_path, replica_path)
        FileManager._delete_removed_files(source_path, replica_path)
        FileManager.log_change(ActionType.End)

    @staticmethod
    def create_file(path_to_folder: str, file_name: str, file_type: FileType) -> str:
        """
        Creates a new file in the specified folder with a sanitized name and the given file type.

        This function prompts the user to input a file name, sanitizes the name to remove any invalid
        characters, and appends the appropriate file extension based on the provided `file_type`.
        If the folder exists and the file creation is successful, the function returns the full file path.

        Args:
            path_to_folder (str): The path to the folder where the file should be created.
            file_name (str): the name of the file to be created (used in the prompt).
            file_type (FileType): The type of file to create (used to determine the file extension).

        Returns:
            str: The full path to the created file, including the sanitized name and file extension.

        """
        while True:
            user_input = input(f"insert file name for {file_name}: ")
            sanitized_name = sanitize_filename(user_input)

            if not sanitized_name:
                print("Invalid filename. Please enter a valid name.")
                continue
            else:
                break

        sanitized_name += "." + file_type.value
        whole_path = os.path.join(path_to_folder, sanitized_name)

        if os.path.exists(path_to_folder) and not os.path.exists(whole_path) and FileManager.use_log_file:
            with open(whole_path, "x") as f:
                print(f"file {file_name} created at {whole_path}")

        return whole_path

"""Setting up program"""

def get_sync_interval()-> float:
    """
    Prompts the user to select a time unit (seconds, minutes, hours) and an interval for synchronization.

    Returns:
        float: The interval time in seconds.
    """
    print("Now we will set up the interval between synchronizations")
    valid_units = {"seconds": TimeUnit.seconds, "minutes": TimeUnit.minutes, "hours": TimeUnit.hours}

    while True:
        time_measure = input(f"insert the type of time measure desired (seconds/minutes/hours) ").lower().strip()
        if time_measure in valid_units:
            SyncManager.time_unit = valid_units[time_measure]
            break
        else:
            print("Invalid input. Please enter 'seconds', 'minutes', or 'hours'.")


    while True:
        interval = input(f"insert the amount of {time_measure} between interval between synchronizations: ")
        try:
            interval = float(interval)
            if interval > 0:
                return interval * SyncManager.time_unit.value
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

def get_folder_path(folder_name: str) -> str:
    while True:
        path = input(f"insert folder path for {folder_name}: ")

        #if the folder exists it returns the path to the folder
        if os.path.exists(path) and os.path.isdir(path):
            return path

        print("Please insert a valid folder name.")

def get_file_path(file_name: str) -> str:
    """
    Prompts the user to input a valid file path and ensures that the file exists or can be created.

    This function repeatedly asks the user to input a file path. It performs several checks:
        1. If the file exists at the provided path, it returns the file's path.
        2. If the provided path is not a directory, it attempts to create the directory.
        3. If the path exists and is a valid directory, it prompts the user if they want to create the file in that directory.
        4. If the path is not valid, it will ask the user to try again.

    Args:
        file_name (str): The name of the file the user wants to access or create.

    Returns:
        str: The path to the file if it's valid or created successfully.
    """
    while True:
        path = input(f"insert file path for {file_name}: ")

        if os.path.exists(path) and os.path.isfile(path):
            return path

        if not os.path.isdir(path):
            path = os.path.dirname(path)

        if os.path.exists(path) and os.path.isdir(path):
            result = prompt_for_file_creation(file_name, path)
            if result is not None:
                return result

        print("Please insert a valid file path.")
        print("")

def prompt_for_file_creation(file_name: str, path_to_folder: str)-> str | None:
    """
    Prompts the user to confirm if they want to create a new file in the specified directory.

    This function will display a message asking if the user would like to create a new file
    in the given folder. If the user responds with 'y', the function will call `create_file`
    to create the file. If the user responds with 'n', it returns `None`. If the response is
    anything other than 'y' or 'n', it will recursively prompt the user again.

    Args:
        file_name (str): The name of the file that the user is being prompted to create.
        path_to_folder (str): The path to the folder where the file is intended to be created.

    Returns:
        str | None:
            - Returns the result of `create_file` (a string of the path) if the user confirms
              creation.
            - Returns `None` if the user denies creation.
            - Recursively calls itself if the response is invalid.
    """
    print("file isn't valid but the path to the file exists.")
    print(f"would you like to create the {file_name}?")
    response = input(f"on the directory {path_to_folder} ? (y/n)")
    response = response.strip()

    if response.lower() == "y":
        return FileManager.create_file(path_to_folder,file_name,FileType.Txt)
    elif response.lower() == "n":
        return None
    else:
         return prompt_for_file_creation(file_name, path_to_folder)

def configure_log_file() -> str | None:
    while True:
        print("##### Want the program to use a log file (y/n) ####")
        response = input("").strip().lower()

        if response.lower() == "y" or response.lower() == "yn":
            FileManager.use_log_file = (response == "y")
        else:
            print("invalid input. Please enter 'y' or 'n'.")
            continue

        if FileManager.use_log_file:
            return get_file_path("log file")
        else:
            return None

def get_source_replica_paths():
    """
    Prompts the user to provide paths for source and replica folders, ensuring
    that they are not the same.

    Returns:
        tuple: A tuple containing the source and replica paths.
    """
    source_path = get_folder_path("source folder")
    replica_path = get_folder_path("replica folder")

    while source_path == replica_path:
        print("source_path and the replica path cannot be the same.")
        source_path = get_folder_path("source folder")
        replica_path = get_folder_path("replica folder")

    return source_path, replica_path

def set_up_log_file(sync_interval: float,source_path: str,replica_path: str):

    content = (f"LOG FILE FOR - Sync files program (v{Config.version})\n "
               "\n"
               "VARIABLES:\n"
               f"sync interval - {sync_interval} {SyncManager.time_unit.name}\n"
               f"source path - {source_path}\n"
               f"C:replica path - {replica_path}\n")

    with open(FileManager.log_file_path, "w", encoding="utf-8") as file:
        file.write(content)

def print_program_intro():
    print("\n==============================")
    print(f"  Sync Files Program (v{Config.version})")
    print("==============================")
    print("This program keeps a replica folder in sync with a source folder.")
    print("Files will be copied, updated, or deleted based on changes in the source.")
    print("Follow the prompts to configure synchronization.\n")

""" Util """

def sanitize_filename(file_name: str) -> str:
    """
    Sanitizes the input filename by removing invalid characters.

    This function removes leading and trailing whitespace from the filename
    and then removes characters that are not allowed in file names on most
    operating systems (such as `<`, `>`, `:`, `"`, `/`, `\\`, `|`, `?`, and `*`).

    Args:
        file_name (str): The filename to sanitize.

    Returns:
        str: A sanitized version of the input filename, with invalid characters removed.
    """
    file_name = file_name.strip()
    file_name = re.sub(r'[<>:"/\\|?*]', '', file_name)
    return file_name

async def run_every_n_seconds(func, interval: float,*args):
    """
    Runs a given function repeatedly every `interval` seconds.

    ARGS:
        func (function): The function to be executed repeatedly.
        interval (float): The number of seconds to wait between each function execution.
        *args (tuple): Optional arguments to be passed to the function when executed.

    This function runs indefinitely in a loop, executing the provided function (`func`)
    every `interval` seconds. If the function execution takes too long and exceeds the `timeout`,
    it will skip the next execution. If the function is canceled (via `CancelledError`), the loop exits gracefully.

    Exceptions:
        asyncio.TimeoutError: If the function execution exceeds the `timeout` limit.
        asyncio.CancelledError: If the synchronization is canceled, the loop will exit cleanly.
    """
    while True:
        try:
            await asyncio.wait_for(func(*args), timeout=interval)
        except asyncio.TimeoutError:
            print("Function took too long, skipping next run.")
        except asyncio.CancelledError:
            print("Synchronization interval was canceled. Exiting gracefully...")
            break
        await asyncio.sleep(interval)

async def start_program():

    print_program_intro()

    FileManager.log_file_path = configure_log_file()

    sync_interval = get_sync_interval()

    source_path, replica_path = get_source_replica_paths()

    if FileManager.use_log_file:
        set_up_log_file(sync_interval, source_path, replica_path)

    FileManager.clear_folder(replica_path)
    await run_every_n_seconds(FileManager.sync_folders, sync_interval, source_path, replica_path)


if __name__ == '__main__':
    try:
        asyncio.run(start_program())
    except KeyboardInterrupt:
        print("Program interrupted. Exiting gracefully...")
    except Exception as e:
        print("\nAn unexpected error occurred:", e)

