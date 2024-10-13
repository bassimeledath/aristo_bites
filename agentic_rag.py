# rag_workflow_module.py

import os
from typing import List
from pydantic import BaseModel
from openai import OpenAI
from llama_index.core.workflow import (
    StartEvent,
    StopEvent,
    Workflow,
    step,
    Event,
    Context
)
from llama_index.indices.managed.llama_cloud import LlamaCloudIndex
from llama_index.utils.workflow import draw_all_possible_flows
import nest_asyncio
import asyncio
from dotenv import load_dotenv

# Apply nest_asyncio to allow asyncio in environments like Jupyter
nest_asyncio.apply()

# Load environment variables from .env file if present
load_dotenv()

# Define Pydantic models for structured output
class SubQuestion(BaseModel):
    question: str

class SubQuestions(BaseModel):
    questions: List[SubQuestion]

class SubAnswer(BaseModel):
    question: str
    sub_answer: str

# Define Event classes
class SubQuestionsEvent(Event):
    questions: List[SubQuestion]

class SubAnswerEvent(Event):
    question: str
    sub_answer: str

# Define the Workflow class
class RAGWorkflow(Workflow):
    def __init__(self, llama_cloud_index: LlamaCloudIndex, openai_client: OpenAI, num_questions: int = 3):
        super().__init__()
        self.llama_cloud_index = llama_cloud_index
        self.openai_client = openai_client
        self.num_questions = num_questions  # Number of sub-questions to generate

    @step
    async def generate_sub_questions(self, ctx: Context, ev: StartEvent) -> SubQuestionsEvent:
        system_message = (
            f"You are an AI assistant that generates relevant philosophy based sub-questions to gather more information about a given topic. The questions should be distinct from one another and try to cover as much ground about the topic as possible. "
            f"Generate exactly {self.num_questions} clear and specific questions."
        )
        user_message = f"Generate {self.num_questions} sub-questions to gather more information about: {ev.query}"

        # Use OpenAI's structured output with Pydantic
        response = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            response_format=SubQuestions  # Specify the Pydantic model for parsing
        )

        # Extract questions from parsed response
        parsed_response = response.choices[0].message.parsed  # This is an instance of SubQuestions
        sub_questions = [sq.question for sq in parsed_response.questions]

        if len(sub_questions) != self.num_questions:
            raise ValueError(f"Expected {self.num_questions} sub-questions, but got {len(sub_questions)}")

        # Send each sub-question as a separate event
        for question in sub_questions:
            ctx.send_event(SubQuestionsEvent(questions=[SubQuestion(question=question)]))

        # Optionally, return the event
        return SubQuestionsEvent(questions=[SubQuestion(question=question) for question in sub_questions])

    @step(num_workers=3)  # Adjust num_workers based on num_questions if needed
    async def query_llama_cloud(self, ctx: Context, ev: SubQuestionsEvent) -> SubAnswerEvent:
        query = ev.questions[0].question
        if not query:
            return SubAnswerEvent(question="Unknown Question", sub_answer="Error: Empty query")

        try:
            query_engine = self.llama_cloud_index.as_query_engine()
            response = query_engine.query(query)
            return SubAnswerEvent(question=query, sub_answer=str(response))  # Include the question
        except Exception as e:
            return SubAnswerEvent(question=query, sub_answer=f"Error querying LlamaCloud: {str(e)}")

    @step
    async def combine_answers(self, ctx: Context, ev: SubAnswerEvent) -> StopEvent:
        # Collect 'num_questions' SubAnswerEvents
        result = ctx.collect_events(ev, [SubAnswerEvent] * self.num_questions)

        if result is None:
            return None

        # Combine the questions and answers
        combined_answer = "\n\n".join([
            f"Q: {event.question}\nA: {event.sub_answer}" 
            for event in result
        ])
        return StopEvent(result=combined_answer)

# Define the main processing function
def process_query(user_query: str, num_subquestions: int = 3) -> str:
    """
    Processes a user query by generating sub-questions, querying LlamaCloud for answers,
    and combining the results into a single formatted string.

    Args:
        user_query (str): The main query from the user.
        num_subquestions (int): The number of sub-questions to generate and process.

    Returns:
        str: The combined result containing all questions and their corresponding answers.
    """

    # Initialize LlamaCloudIndex
    api_key = os.getenv("LLAMAINDEX_API_KEY")
    if not api_key:
        raise EnvironmentError("LLAMAINDEX_API_KEY environment variable is not set.")

    llama_cloud_index = LlamaCloudIndex(
        name="aristobites-data", 
        project_name="Default",
        organization_id="74e91322-8d9b-4ba0-98c4-e7e68151879e",
        api_key=api_key
    )

    # Initialize OpenAI client
    openai_client = OpenAI()

    # Create the workflow with the specified number of sub-questions
    workflow = RAGWorkflow(llama_cloud_index, openai_client, num_questions=num_subquestions)

    # Define an asynchronous function to run the workflow
    async def run_workflow(query: str) -> str:
        result = await workflow.run(query=query)
        return result

    # Run the asynchronous workflow and get the result
    try:
        combined_result = asyncio.run(run_workflow(user_query))
        return combined_result
    except Exception as e:
        return f"An error occurred during processing: {str(e)}"
    

def visualize_workflow(workflow_class, filename="rag_workflow.html"):
    """
    Creates and saves a visualization of the given workflow class.

    Args:
        workflow_class: The workflow class to visualize.
        filename (str): The filename for the saved visualization (default: "rag_workflow.html").
    """
    draw_all_possible_flows(workflow_class, filename=filename)
    print(f"Workflow visualization saved as {filename}")

 
