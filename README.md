
# Folder Sync Tool

A Python-based tool that periodically synchronizes a source folder with a replica folder. The tool copies new or updated files, deletes files from the replica if they’re removed from the source, and optionally logs the operations.

## Features

- **Asynchronous Synchronization**: Uses `asyncio` to run the sync process at user-defined intervals.
- **Incremental Sync**: Only copies files that are new or have been modified.
- **Deletion Handling**: Removes files from the replica that no longer exist in the source.
- **Interactive Configuration**: Prompts the user for folder paths, synchronization interval, and log file settings.
- **Logging (Optional)**: Can log file operations to a log file or the console.

## Requirements

- Python 3.13 or higher
- Uses only built-in Python modules (e.g., `os`, `asyncio`, `shutil`, `re`, and `enum`)

## Installation

1. **Clone the Repository**
   
   ### bash
   ```bash
   git clone https://github.com/yourusername/folder-sync-tool.git
   ```
   
   ### Github Desktop
   Simply install GitHub Desktop, sign in with your GitHub account, and then use the “Clone a repository” option.
   
   ### Downloading the ZIP File
      - You can download the repository as a ZIP file directly from GitHub.
      - On the repository page, click on the “Code” button and then select “Download ZIP”.
      - After downloading, extract the contents to work on them locally.