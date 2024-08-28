import time
import json
import openai
import pandas as pd
import logging
import requests
from openai import OpenAI, OpenAIError


# basic error log
logging.basicConfig(
    filename='error_log.log',
    level=logging.ERROR,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Place your openai key here in the placemarker
api_key = 'YOUR_KEY_GOES_HERE'

openai.api_key = api_key
client = openai

# Define system level instructions to your model here. This is the most important part of the project - spend your time on this.
system_instructions = """
<instructions>

Place your instrictions here

</instructions>

# Give an example of the desired output here that must be followed, ensure it is valid JSON

The output you are expected to provide is a JSON containing, you must respect the following format for your response:
{"example" : {
    "body": ""
}
}


<example> 

{"example" : {
    "body": "example of a wonderful output"
}
}

Place an example of what a great output looks like here, go into high levels of detail and even include the sample user instructions given to render such an input


</example>
"""

# Read input data from CSV. Export your gong calls and ensure to have a primary key e.g. domain, and the transcript within this input
df = pd.read_csv('input.csv')


def generate_insights(system_instructions, user_instructions, model):
    try:
        start_time = time.time()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_instructions}
            ],
            response_format={ "type": "json_object" }
        )
        content = completion.choices[0].message.content
        print(content or "")
        json_obj = json.loads(content)
        end_time = time.time()
        elapse_time = end_time - start_time
        tokens = completion.usage.total_tokens
        
        if "4o-mini" in model:
            costs = 0.0012
        else:
            costs = 0.00

        prompt_cost = round(tokens / 1000 * costs, 5)

        monitoring_ = f"time elapse: {elapse_time:.2f} second, tokens used {tokens}, costs: ${prompt_cost}"


    
        # Define the keys to extract
        keys = [
            'example'
        ]

        # Extract the fields
        result = {key: json_obj[key]['body'] for key in keys}
        result.update({
        'elapse_time': elapse_time,
        'tokens_used': tokens,
        'costs': prompt_cost
        })

        print(monitoring_)

        return result

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error: {e}")
        return None
    except json.decoder.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e} with content: {content}")
        return None
    except KeyError as e:
        logging.error(f"Missing key in JSON response: {e} with JSON object: {json_obj}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during email generation: {e}")
        return None

model_4o_mini = "gpt-4o-mini"

# Process each row and write to CSV
try:
    with open('output.csv', 'a') as output_file:
        header_written = False
        for index, row in df.iterrows():
            print(index)
            system_instructions = system_instructions
            user_instructions = row['transcript']
            domain = row['domain']

            # Generate insights and capture results
            result = generate_insights(system_instructions, user_instructions, model_4o_mini)
            if result is None:
                logging.error(f"Skipping index {index} due to error in generating insights")
                continue

            result['index'] = index
            result['domain'] = domain

            # Convert the result to a DataFrame
            result_df = pd.DataFrame([result])
        

            # Write to CSV with header only once
            result_df.to_csv(output_file, header=not header_written, index=False)
            header_written = True

            print('-----')
            print('')
        
except Exception as e:
    logging.error(f"Unexpected error in processing CSV rows: {e}")