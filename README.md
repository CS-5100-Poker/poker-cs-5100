# Artificial Intelligence in Poker: A Comparative Analysis of Decision-Making Using Search Algorithms

Welcome to the repository for our comprehensive analysis of AI decision-making in poker, utilizing various search algorithms. This repository hosts the complete codebase used in our study. Each AI agent is implemented in its unique branch, ensuring smooth operation without merge conflicts as the agents do not compete directly against each other.

## Requirements

- **Python Version**: Python 3.11 or higher is required.
- **Environment**: If you are running the code in Pycharm, please configure the following:
  - Go to `Run | Edit Configurations...`
  - Under the 'Execution' section, ensure to check the 'Emulate terminal in output console' option for optimal performance.

## Running the Agents

To execute an agent, follow these steps:

1. **Check Out the Appropriate Branch**: Each agent is located in a separate branch. Use the following commands to switch to the desired agent's branch:
   - Expectiminimax Agent: `git checkout expectiminimax`
   - Monte Carlo Tree Search Agent: `git checkout monte-carlo-tree-search`
   - Deep Q-Learning Agent: `git checkout deep-q-learning`

2. **Install Dependencies**: Run the command `pip install -r requirements.txt` to install necessary dependencies.

3. **Execute the Program**: Start the agent by running `python3 -m src.main`.

## Acknowledgements

We extend our gratitude to Quinn Elery for the UI and gameplay foundation used in this project. The original work and repository by Quinn Elery have been instrumental in the development of this project.

[Quinn Elery's Original Repository](https://github.com/qelery/Command-Line-Poker)

---

Thank you for your interest in our AI poker analysis project. We hope this repository serves as a valuable resource in exploring the fascinating world of AI in strategic game environments.
