This is **Architecture Builder**, a Streamlit app that utilizes LangChain and Azure OpenAI's LLM model to generate code from the architecture design of system. It supports using UML CLASS diagrams into Python code.

This is a project to experiment that if it is possible to make developers more focus on system design by shortening time of coding with GPT's help, so that the developers can avoid underdesigned software applications in an Agile team. In this experiment, we use UML diagrams to represent system design.

## Demo
### Prepare UML CLASS diagrams

## Requirements

This app requires the following libraries:

- streamlit
- langchain
- openai
- python-dotenv

## Python Version
This project is compatible with Python 3.10.11.

## Setup

```bash
$ git clone https://github.com/your-username/your-project.git
$ cd your-project
$ pip install -r requirements.txt
```

Set environment variables
```bash
$ export OPENAI_API_TYPE=azure
$ export OPENAI_API_KEY=<your API key>
$ export OPENAI_API_VERSION=<api version>
$ export OPENAI_API_BASE=<your API base>
$ export LLM_DEPLOYMENT_ID=<your llm deployment ID>
$ export LLM_MODEL_NAME=<your llm model name>
```

Run the application
```bash
$ streamlit run main.py
```

## Features:

- **Code Generation**: 

## Usage

To use Architecutre Builder, follow these steps:

1. Enter UML giagrams written by PlantUML commands to **Generate** the code.
2. Select the programming language.
3. Click on the **Generate Code** button to generate the code.
4. If you want to run the code, click on the **Run Code** button.
5. If you want to save the code to a file, enter a filename and click on the **Save Code** button.


## Credits
Original Project: <a href="https://github.com/haseeb-heaven/LangChain-Coder" target="_blank">LangChain-Coder
</a>

## Future Works
- Add a new prompt template to generate code entrance point by using UML ACTIVITY diagrams.
- Survey how to use UML to give the comment of APIs.
