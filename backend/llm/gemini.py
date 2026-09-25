import logging
from google import genai
from google.genai.errors import APIError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from backend.config import settings

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    """
    A simple abstraction around the new official google-genai SDK.
    """
    def __init__(self):
        # Validate that the API key exists before trying to configure the client
        if not settings.gemini_api_key:
            logger.error("GEMINI_API_KEY is missing from the environment.")
            raise ValueError("GEMINI_API_KEY is not set. Please check your .env file.")
        
        try:
            # Initialize the new SDK Client
            self.client = genai.Client(api_key=settings.gemini_api_key)
            self.model_name = settings.gemini_model
        except Exception as e:
            logger.error(f"Failed to initialize the Gemini client: {e}")
            raise RuntimeError("Could not initialize LLM Client.") from e

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=15),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(APIError),
        before_sleep=lambda retry_state: logger.warning(
            f"Google API overloaded (503). Retrying in {retry_state.next_action.sleep}s..."
        )
    )
    def generate_response(self, prompt: str) -> str:
        """
        Sends a prompt to the Gemini model and returns the generated text.
        Automatically retries with exponential backoff if the API is overloaded.
        """
        try:
            # Send the request over the network using the new models.generate_content API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # Extract and return the text
            return response.text
            
        except APIError as e:
            # If it's a 503, tenacity will catch it and retry automatically.
            # If retries are exhausted, or it's a different API Error, it raises.
            if e.code == 503:
                raise # Pass up to tenacity to retry
            logger.error(f"Gemini API Error: {e}")
            raise RuntimeError(f"The model API returned an error: {e}")
            
        except Exception as e:
            # Catch network errors, timeouts, or API outages
            logger.error(f"Gemini API Error: {str(e)}")
            raise RuntimeError(f"Failed to communicate with the LLM: {str(e)}")
