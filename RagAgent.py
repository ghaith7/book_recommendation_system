from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import numpy as np
import time
from datasets import load_from_disk
import faiss
import yaml

class RagAgent:

    def __init__(self, config_path):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.LoadVectorStore()
        self.SetupEmbeddingModel()
        self.SetupGenerationModel()

    def LoadVectorStore(self):
        self.index = faiss.read_index(self.config['vectorDBindex'])
        self.dataset = load_from_disk(self.config['metadata'])

    def SetupEmbeddingModel(self):
        self.Embedding_model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", trust_remote_code=True, device="cuda")
        self.Embedding_model.max_seq_length = self.config['Embedding_model_max_seq_length']
        self.reranker = CrossEncoder("BAAI/bge-reranker-base")

    def CreateVectorStore(self, summaries):
        embeddings = self.Embedding_model.encode(
            summaries,
            batch_size=16,
            show_progress_bar=True,
            normalize_embeddings=True
        )
        embeddings = np.asarray(embeddings, dtype="float32")
        embedding_dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(embedding_dim)
        index.add(embeddings)
        self.index = index

    def SetupGenerationModel(self):
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")
        self.Generation_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-8B", dtype=torch.float16, device_map="auto")

    def BuildPrompt(self, query, context):
        prompt = f"""
        You are a {self.config['agent_role']}.

        The user is looking for:
        {query}

        Here are the three most relevant books retrieved from the book database:

        {context}

        Based only on these books, recommend the most suitable books to the user.

        {self.config['notes']}
        """
        return prompt

    def query2prompt(self, query):
        query_embedding = self.Embedding_model.encode(
            [query],
            normalize_embeddings=True
        )
        query_embedding = np.asarray(query_embedding, dtype="float32")
        scores, indices = self.index.search(query_embedding, self.config['reranker_depth'])
        reranker_inputs = []

        for idx in indices[0]:
            book = self.dataset[int(idx)]

            reranker_inputs.append([
                query,
                book["summary"]
            ])
        reranker_scores = self.reranker.predict(
            reranker_inputs,
            show_progress_bar=True
        )
        ranked = sorted(
            zip(indices[0], reranker_scores),
            key=lambda x: x[1],
            reverse=True
        )
        top_books = []

        for idx, score in ranked[:3]:
            book = self.dataset[int(idx)]

            top_books.append({
                "title": book["title"],
                "author": book["author"],
                "pub_year": book["pub_year"],
                "summary": book["summary"],
                "score": float(score)
            })
        context = ""
        for i, book in enumerate(top_books, 1):
            context += f"""
        Book {i}:
        Title: {book['title']}
        Author: {book['author']}
        Publication year: {book['pub_year']}
        Summary: {book['summary']}
        """
        prompt = self.BuildPrompt(query, context)
        return prompt

    def generate_response(self, prompt):
        messages = [
            {"role": "user", "content": prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False
        )
        inputs = self.tokenizer( text,return_tensors="pt").to(self.Generation_model.device)
        with torch.no_grad():
            outputs = self.Generation_model.generate(
                **inputs,
                max_new_tokens=self.config['generation_model_max_new_tokens'],
                temperature=self.config['generation_model_temperature'],
                do_sample=True
            )

        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        )
        return response                                                                   



