import tempfile, subprocess, traceback, sys, os, logging
import openai
import streamlit as st
from streamlit.components.v1 import html

import langchain.agents as lc_agents
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain, SimpleSequentialChain
from langchain.memory import ConversationBufferMemory
from langchain.llms import AzureOpenAI

from datetime import datetime
from io import StringIO
from dotenv import load_dotenv

# Load the environment variables
load_dotenv(override=True)

# Azure OpenAI key
openai.api_type = os.getenv("OPENAI_API_TYPE")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Azure OpenAI LLM
deployment_id = os.getenv("LLM_DEPLOYMENT_ID")
model_name= os.getenv("LLM_MODEL_NAME")
temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
max_tokens = int(os.getenv("LLM_MAX_TOKENS", "800"))
top_p = float(os.getenv("LLM_TOP_P", "0.95"))
frequency_penalty = int(os.getenv("LLM_FREQUENCY_PENALTY", "0"))
presence_penalty = int(os.getenv("LLM_PERSENCE_PENALTY", "0"))


global generated_code

LANGUAGE_CODES = {
    'Python': 'python3'
}

# App title and description
st.title("Architecutre Builder 🦜🔗")
code_uml_class_diagram_prompt = st.text_area("Enter CLASS diagrams")
code_uml_activity_diagram_enter_point = st.text_area("Enter ACTIVITY diagrams of enterance point",
                                                     disabled=True)
code_language = st.selectbox("Select a language", list(LANGUAGE_CODES.keys()))

# Generate and Run Buttons
button_generate = st.button("Generate Code")
code_file = st.text_input("Enter file name:")
button_save = st.button("Save Code")

compiler_mode = st.radio("Compiler Mode", ("Online", "Offline"))
button_run = st.button("Run Code")


# Prompt Templates
template="""\
You are a software engineer.
Your task is understand the UML diagram wrapped by triple backticks below.
Then give code in {code_language} based on it.
```
{code_topic}
```
"""

code_template = PromptTemplate(
    input_variables=['code_language', 'code_topic'],
    template=template
)

code_fix_template = PromptTemplate(
    input_variables=['code_topic'],
    template='Fix any error in the following code in ' +
    f'{code_language} language' + ' for {code_topic}'
)


# Memory for the conversation
memory = ConversationBufferMemory(
    input_key='code_topic', memory_key='chat_history')


# Create an OpenAI LLM model
open_ai_llm = AzureOpenAI(
    deployment_id=deployment_id,
    model_name=model_name,
    temperature=temperature,
    #max_tokens=max_tokens,
    top_p=top_p,
    frequency_penalty=frequency_penalty,
    presence_penalty=presence_penalty)


# Create a chain that generates the code
code_chain = LLMChain(llm=open_ai_llm, prompt=code_template,
                      output_key='code', memory=memory, verbose=True)

# Create a chain that fixes the code
code_fix_chain = LLMChain(llm=open_ai_llm, prompt=code_fix_template,
                          output_key='code_fix', memory=memory, verbose=True
                          )

# Create a sequential chain that combines the two chains above
sequential_chain = SequentialChain(chains=[code_chain, code_fix_chain]
                                   , input_variables=['code_language','code_topic']
                                   , output_variables=['code', 'code_fix']
                                   )


# Generate Dynamic HTML for JDoodle Compiler iFrame Embedding.
def generate_dynamic_html(language, code_uml_class_diagram_prompt):
    logger = logging.getLogger(__name__)
    logger.info("Generating dynamic HTML for language: %s", language)
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Python App with JavaScript</title>
    </head>
    <body>
        <div data-pym-src='https://www.jdoodle.com/plugin' data-language="{language}"
            data-version-index="0" data-libs="">
            {script_code}
        </div>
        <script src="https://www.jdoodle.com/assets/jdoodle-pym.min.js" type="text/javascript"></script>
    </body>
    </html>
    """.format(language=LANGUAGE_CODES[language], script_code=code_uml_class_diagram_prompt)
    return html_template

# Setup logging method.


def setup_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%H:%M:%S",
        filename=log_file,  # Add this line to save logs to a file
        filemode='a',  # Append logs to the file
    )


# Setup logging
log_file = __file__.replace(".py", ".log")
setup_logging(log_file)


# Create a class
class PythonREPL:
    # Define the initialization method
    def __init__(self):
        pass

    # Define the run method
    def run(self, command: str) -> str:
        # Store the current value of sys.stdout
        old_stdout = sys.stdout
        # Create a new StringIO object
        sys.stdout = mystdout = StringIO()
        # Try to execute the code
        try:
            # Execute the code
            exec(command, globals())
            sys.stdout = old_stdout
            output = mystdout.getvalue()
        # If an error occurs, print the error message
        except Exception as e:
            # Restore the original value of sys.stdout
            sys.stdout = old_stdout
            # Get the error message
            output = str(e)
        return output

# Define the Run query function


def run_query(query, model_kwargs, max_iterations):
    # Create a AzureOpenAI object
    llm = AzureOpenAI(**model_kwargs)
    # Create the python REPL tool
    python_repl = lc_agents.Tool("Python REPL", PythonREPL(
    ).run, "A Python shell. Use this to execute python commands.")
    # Create a list of tools
    tools = [python_repl]
    # Initialize the agent
    agent = lc_agents.initialize_agent(tools, llm, agent=lc_agents.AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                                       model_kwargs=model_kwargs, verbose=True, max_iterations=max_iterations)
    # Run the agent
    response = agent.run(query)
    return response

# Define the Run code function


def run_code(code, language):
    logger = logging.getLogger(__name__)
    logger.info(f"Running code: {code} in language: {language}")

    if language == "Python":
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=True) as f:
            f.write(code)
            f.flush()

            logger.info(f"Input file: {f.name}")
            output = subprocess.run(
                ["python", f.name], capture_output=True, text=True)
            logger.info(f"Runner Output execution: {output.stdout + output.stderr}")
            return output.stdout + output.stderr

    elif language == "C" or language == "C++":
        ext = ".c" if language == "C" else ".cpp"
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=True) as src_file:
            src_file.write(code)
            src_file.flush()

            logger.info(f"Input file: {src_file.name}")

            with tempfile.NamedTemporaryFile(mode="w", suffix="", delete=True) as exec_file:
                compile_output = subprocess.run(
                    ["gcc" if language == "C" else "g++", "-o", exec_file.name, src_file.name], capture_output=True, text=True)

                if compile_output.returncode != 0:
                    return compile_output.stderr

                logger.info(f"Output file: {exec_file.name}")
                run_output = subprocess.run(
                    [exec_file.name], capture_output=True, text=True)
                logger.info(f"Runner Output execution: {run_output.stdout + run_output.stderr}")
                return run_output.stdout + run_output.stderr

    elif language == "JavaScript":
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=True) as f:
            f.write(code)
            f.flush()

            logger.info(f"Input file: {f.name}")
            output = subprocess.run(
                ["node", f.name], capture_output=True, text=True)
            logger.info(f"Runner Output execution: {output.stdout + output.stderr}")
            return output.stdout + output.stderr

    else:
        return "Unsupported language."

# Generate the code


def generate_code():
    logger = logging.getLogger(__name__)
    try:
        st.session_state.generated_code = code_chain.run(
            {
                "code_language":code_language,
                "code_topic": code_uml_class_diagram_prompt 
            }
        )
        st.session_state.code_language = code_language
        st.code(st.session_state.generated_code,
                language=st.session_state.code_language.lower())

        with st.expander('Message History'):
            st.info(memory.buffer)
    except Exception as e:
        st.write(traceback.format_exc())
        logger.error(f"Error in code generation: {traceback.format_exc()}")

# Save the code to a file


def save_code():
    logger = logging.getLogger(__name__)
    try:
        file_name = code_file
        logger.info(f"Saving code to file: {file_name}")
        if file_name:
            with open(file_name, "w") as f:
                f.write(st.session_state.generated_code)
            st.success(f"Code saved to file {file_name}")
            logger.info(f"Code saved to file {file_name}")
        st.code(st.session_state.generated_code,
                language=st.session_state.code_language.lower())

    except Exception as e:
        st.write(traceback.format_exc())
        logger.error(f"Error in code saving: {traceback.format_exc()}")

# Execute the code


def execute_code(compiler_mode: str):
    logger = logging.getLogger(__name__)
    logger.info(f"Executing code: {st.session_state.generated_code} in language: {st.session_state.code_language} with Compiler Mode: {compiler_mode}")

    try:
        if compiler_mode == "online":
            html_template = generate_dynamic_html(
                st.session_state.code_language, st.session_state.generated_code)
            html(html_template, width=720, height=800, scrolling=True)

        else:
            output = run_code(st.session_state.generated_code,
                              st.session_state.code_language)
            logger.info(f"Output execution: {output}")

            if "error" in output.lower() or "exception" in output.lower() or "SyntaxError" in output.lower() or "NameError" in output.lower():

                logger.error(f"Error in code execution: {output}")
                response = sequential_chain(
                    {   
                        'code_language': st.session_state.code_language,
                        'code_topic': st.session_state.generated_code
                    }
                )
                fixed_code = response['code_fix']
                st.code(fixed_code, language=st.session_state.code_language.lower())

                with st.expander('Message History'):
                    st.info(memory.buffer)
                logger.warning(f"Trying to run fixed code: {fixed_code}")
                output = run_code(fixed_code, st.session_state.code_language)
                logger.warning(f"Fixed code output: {output}")

            st.code(st.session_state.generated_code,
                    language=st.session_state.code_language.lower())
            st.write("Execution Output:")
            st.write(output)
            logger.info(f"Execution Output: {output}")

    except Exception as e:
        st.write("Error in code execution:")
        # Output the stack trace
        st.write(traceback.format_exc())
        logger.error(f"Error in code execution: {traceback.format_exc()}")


# Main method
if __name__ == "__main__":

    # Session state variables
    if "generated_code" not in st.session_state:
        st.session_state.generated_code = ""

    if "code_language" not in st.session_state:
        st.session_state.code_language = ""

    # Generate the code
    if button_generate and code_uml_class_diagram_prompt:
        generate_code()

    # Save the code to a file
    if button_save and st.session_state.generated_code:
        save_code()

    # Execute the code
    if button_run and code_uml_class_diagram_prompt:
        code_state_option = "online" if compiler_mode == "Online" else "offline"
        execute_code(code_state_option)
