# Coursera - MS-CS Course Management Automation  
**Capstone Project (CSCI 4308)**  
Developed in collaboration with **Dustin Hooks**  

---

## **About the Project**  
The **MS-CS on Coursera Course Management: Automating Course Readiness and Monitoring** project focuses on optimizing the growing MS-CS program on Coursera. This project automates the extraction, validation, and monitoring of course content to ensure readiness, identify issues (e.g., broken links, missing multimedia), and streamline course management.  

**Contributors:**  
- **Alexander Archer**  
- **Aniket Chauhan**  
- **Clement Canal**  
- **Jesse Black**  
- **Nasir Naqvi**  

---

## **Getting Started**  

### **Prerequisites**  
- **Python 3.10 or higher**  
- [**Poetry**](https://python-poetry.org/docs/) for dependency management.  
- [**Poetry-dotenv plugin**](https://pypi.org/project/poetry-dotenv-plugin/) for managing environment variables.  


## Building The Project
1.  Install Python 3.10 or higher
2.  Install [Poetry](https://python-poetry.org/docs/) using any
    method; `pipx install poetry` is easiest if you already have pipx installed.
3.  Install the Poetry-dotenv [plugin](https://pypi.org/project/poetry-dotenv-plugin/)
    with `poetry self add poetry-dotenv-plugin`.
4.  Clone this project into a folder on your machine. `cd` to that folder.
5.  Create a new file, `.env`, in the root directory of this project. That file should
    contain the environment variables needed to run this project locally. It will
    look like this:
    ```sh
    [insert required .env elements here]

    ```
6.  Run `poetry install --sync` to install the dependencies for this project,
    including development and testing dependencies, into a virtual environment
    managed by Poetry. Ensure the Python version of the venv is at least 3.10
    (you should get a warning if that is not the case).
7.  Run `poetry shell` to spawn a subshell with the virtual environment activated
    and the environment variables loaded from the `.env` file.
8.  Run `pre-commit install` to install the pre-commit hooks. These will prevent
    un-linted changes from being committed.
9.  Run `make` to run tests and linters, or `make lint` to skip tests and run linters.
10. Follow Conventiona Commits (https://www.conventionalcommits.org/en/v1.0.0/#specification) when pushing changes


## Publishing and Creating Releases
1. On every push to a branch, new artifacts will be created and pushed as artifacts from the run to verify they work
2. On every push to the main branch, a new release will be created and pushed to the repository