import json
import logging
from typing import List
import pydantic_core
import requests
from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.store_api_gateway import StoreGateway

class StoreApiAdapter(StoreGateway):
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]):
        try:
            # Prepare the data to be sent as JSON
            data = [json.loads(agent_data.json()) for agent_data in processed_agent_data_batch]
            response = requests.post(self.api_base_url + "/processed_agent_data/", json=data)
            
            # Check if the request was successful (status code 2xx)
            if response.status_code // 100 == 2:
                logging.info("Data successfully saved to the store API")
                return True
            else:
                logging.error(f"Failed to save data to the store API. Status code: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            logging.error(f"Error occurred while saving data to the store API: {e}")
            return False