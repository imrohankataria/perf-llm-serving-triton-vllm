"""
Locust load testing file for LLM serving benchmarks

Usage:
    locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10
"""

from locust import HttpUser, task, between
import random


class LLMUser(HttpUser):
    """Simulates a user making requests to an LLM serving endpoint."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompts = [
            "Explain the concept of machine learning in simple terms.",
            "Write a short story about a robot learning to feel emotions.",
            "What are the key differences between supervised and unsupervised learning?",
            "Describe the architecture of a transformer model.",
            "How does attention mechanism work in neural networks?",
            "Explain the concept of transfer learning.",
            "What are the advantages of using pre-trained language models?",
            "Describe the process of fine-tuning a large language model.",
            "What are some ethical considerations when deploying AI systems?",
            "How can we measure the performance of language models?",
        ]
    
    @task(3)
    def generate_completion(self):
        """Generate a text completion (most common operation)."""
        prompt = random.choice(self.prompts)
        
        payload = {
            "model": "meta-llama/Llama-2-7b-chat-hf",
            "prompt": prompt,
            "max_tokens": 128,
            "temperature": 0.7,
            "top_p": 0.9,
        }
        
        with self.client.post(
            "/v1/completions",
            json=payload,
            catch_response=True,
            name="generate_completion"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Check server health (less frequent)."""
        with self.client.get("/health", catch_response=True, name="health_check") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed with status {response.status_code}")
    
    @task(2)
    def chat_completion(self):
        """Generate a chat completion (alternative format)."""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            },
            {
                "role": "user",
                "content": random.choice(self.prompts)
            }
        ]
        
        payload = {
            "model": "meta-llama/Llama-2-7b-chat-hf",
            "messages": messages,
            "max_tokens": 128,
            "temperature": 0.7,
        }
        
        with self.client.post(
            "/v1/chat/completions",
            json=payload,
            catch_response=True,
            name="chat_completion"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
