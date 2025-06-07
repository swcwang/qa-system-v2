import re
import os
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import gradio as gr

import time
from typing import List, Dict, Any, Optional, Tuple
from tqdm import tqdm
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI 
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever
from langchain.prompts import PromptTemplate
from pydantic import Field
import logging

"""
Placeholder for legacy imports - you'll need to copy these from your old project.
"""
def setup_qa_chain(
    collection, config: Dict[str, Any], custom_prompt=None
) -> RetrievalQA:
    """
    Set up QA chain with retriever and LLM.

    Args:
        collection: Chroma collection to query
        config: Configuration dictionary with settings
        custom_prompt: Optional custom prompt template. If None, uses a simple prompt.

    Returns:
        RetrievalQA chain
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Please set it as an environment variable."
        )

    # Initialize retriever if collection is provided
    if collection:
        retriever = ChromaManualRetriever(
            collection=collection,
            embedder=SentenceTransformer(config["embedding_model_name"]),
            k=config["n_chunks_to_retrieve_k"],
        )
    else:
        retriever = None  # Will be set later

    llm = ChatOpenAI(
        model_name=config["chat_model_name"],
        temperature=config["temperature"],
        streaming=True,
        callbacks=[],
        openai_api_key=openai_api_key,
    )

    # Use a simple prompt that won't cause compatibility issues
    prompt = PromptTemplate(
        template="Please answer the question based on the context.\n\nContext: {context}\n\nQuestion: {question}",
        input_variables=["context", "question"]
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    return qa_chain

class ChromaManualRetriever(BaseRetriever):
    """Custom retriever for ChromaDB that uses sentence transformers for embedding."""

    collection: Any = Field(exclude=True)
    embedder: SentenceTransformer = Field(exclude=True)
    k: int = 5

    @property
    def search_kwargs(self):
        return {"k": self.k}

    def _get_relevant_documents(self, query: str) -> List[Document]:
        """Retrieve relevant documents by encoding query and querying collection."""
        embedding = self.embedder.encode(query)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=self.k,
            include=["documents", "metadatas"],
        )
        # NEW: Add episode ID prefixes to content
        enhanced_docs = []
        for text, meta in zip(results["documents"][0], results["metadatas"][0]):
            episode_id = meta.get('episode_id', 'Unknown')
            prefixed_content = f"[Episode ID: {episode_id}] {text}"
            enhanced_docs.append(Document(page_content=prefixed_content, metadata=meta))
        
        return enhanced_docs

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Async version of _get_relevant_documents."""
        return self._get_relevant_documents(query)

class ImprovedQAHelpers:
    """Improved helper functions focusing on speaker_type=3 and using IDs for relationships."""

    def __init__(self, dataframes: Dict[str, pd.DataFrame]):
        self.df_reply = dataframes["fact_responses"]
        self.df_guests = dataframes["dim_panellist"]
        self.df_ep = dataframes["dim_episode"]

        # Create standard episode labels once
        self.df_ep["ep_label"] = self.df_ep["date"] + ": " + self.df_ep["title"]

        # Create mappings for episodes and panellists
        self.episode_lookup = dict(zip(self.df_ep["ep_label"], self.df_ep["id"]))

        # URL lookups
        self.episode_url_lookup = {}
        if "url" in self.df_ep.columns:
            self.episode_url_lookup = dict(zip(self.df_ep["title"], self.df_ep["url"]))

        # Panellist lookups
        self.id_to_name = dict(zip(self.df_guests["id"], self.df_guests["name"]))
        self.name_to_id = {name.lower(): id for id, name in self.id_to_name.items()}

        # Panellist URLs - FIX: Use 'link' column instead of 'url'
        self.name_to_url = {}
        if "link" in self.df_guests.columns:  # Changed from "url" to "link"
            # Only include non-null links
            valid_links = self.df_guests[~self.df_guests["link"].isna()]
            self.name_to_url = dict(zip(valid_links["name"], valid_links["link"]))
            print(f"Loaded {len(self.name_to_url)} panelist profile URLs")
        else:
            print(
                "Warning: 'link' column not found in df_guests - panelist URLs will not be available"
            )

        # # Panellist URLs
        # self.name_to_url = {}
        # if "link" in self.df_guests.columns:
        #     self.name_to_url = dict(zip(self.df_guests["name"], self.df_guests["link"]))

        # Print some stats about the data
        panellist_count = self.df_reply[self.df_reply["speaker_type"] == 3].shape[0]
        print(f"Total panellist responses: {panellist_count}")
        missing_sid = self.df_reply[
            (self.df_reply["speaker_type"] == 3) & (self.df_reply["speaker_id"].isna())
        ].shape[0]
        print(f"Panellist responses with missing speaker_id: {missing_sid}")

    def get_episode_id(self, ep_label):
        """Helper to get episode ID from label."""
        return self.episode_lookup.get(ep_label)



    def get_panellists_by_episode(self, ep_label):
        """Get list of panellists for an episode, focusing on speaker_type=3 with valid IDs."""
        print(f"DEBUG: get_panellists_by_episode called with ep_label={ep_label}")

        if not ep_label:
            return []

        # Get the episode ID
        ep_id = self.get_episode_id(ep_label)
        if ep_id is None:
            return []

        # Filter for panellists (speaker_type=3) with non-null speaker_id
        panellist_data = self.df_reply[
            (self.df_reply["episode_id"] == ep_id)
            & (self.df_reply["speaker_type"] == 3)
            & (~self.df_reply["speaker_id"].isna())
        ][["speaker_id", "speaker_name"]].drop_duplicates()

        # Use speaker_name directly from the filtered data
        panellists = panellist_data["speaker_name"].unique().tolist()
        return sorted(panellists)

    def get_subtopics_by_episode(self, ep_label):
        """Get list of subtopics for an episode, from all speaker types."""
        print(f"DEBUG: get_subtopics_by_episode called with ep_label={ep_label}")
        if not ep_label:
            return []

        # Get the episode ID
        ep_id = self.get_episode_id(ep_label)
        if ep_id is None:
            return []

        # Get all subtopics for this episode
        subtopics = (
            self.df_reply[self.df_reply["episode_id"] == ep_id]["subtopic"]
            .dropna()
            .unique()
            .tolist()
        )

        # Filter out empty strings
        subtopics = [topic for topic in subtopics if topic]
        return sorted(subtopics)

    def get_subtopics_by_panellist(self, ep_label, panellist_name):
        """Get list of subtopics for a panellist in an episode using direct matching."""
        print(
            f"DEBUG: get_subtopics_by_panellist: ep={ep_label}, panellist={panellist_name}"
        )
        print(f"🔍 Panelist: {panellist_name}", end="")

        if not ep_label or panellist_name is None:
            print(" → Subtopics: []")
            return []

        # Get the episode ID
        ep_id = self.get_episode_id(ep_label)
        if ep_id is None:
            print(" → Subtopics: []")
            return []

        # Filter for this panellist's responses in this episode using speaker_name
        df_filtered = self.df_reply[
            (self.df_reply["episode_id"] == ep_id)
            & (self.df_reply["speaker_name"] == panellist_name)
            & (self.df_reply["speaker_type"] == 3)
        ]

        topics = df_filtered["subtopic"].dropna().unique().tolist()
        # Filter out empty strings
        topics = [topic for topic in topics if topic]
        print(f" → Subtopics: {topics}")
        return sorted(topics)

    def get_panellists_by_subtopic(self, ep_label, subtopic):
        """Get list of panellists for a subtopic in an episode, filtering for speaker_type=3."""
        print(f"DEBUG: get_panellists_by_subtopic: ep={ep_label}, subtopic={subtopic}")
        print(f"🔍 Subtopic: {subtopic}", end="")

        if not ep_label or subtopic is None:
            print(" → Panellists: []")
            return []

        # Get the episode ID
        ep_id = self.get_episode_id(ep_label)
        if ep_id is None:
            print(" → Panellists: []")
            return []

        # Filter for panellists discussing this subtopic
        df_filtered = self.df_reply[
            (self.df_reply["episode_id"] == ep_id)
            & (self.df_reply["subtopic"].str.upper() == subtopic.upper())
            & (self.df_reply["speaker_type"] == 3)
        ]

        # Get panellist names directly from the filtered data
        panellists = df_filtered["speaker_name"].dropna().unique().tolist()
        print(f" → Panellists: {panellists}")
        return sorted(panellists)

    def format_response_with_links(self, full_answer, docs):
        """Format response with hyperlinks using case-insensitive matching."""
        # First, collect all unique speakers in the results
        # Store both original case and title case versions
        speakers_in_results = {}  # Maps normalized name -> original name from docs
        for doc in docs:
            speaker_name = doc.metadata.get("speaker_name")
            if speaker_name:
                # Store with title case as key for better matching
                normalized = speaker_name.title()
                speakers_in_results[normalized] = speaker_name

        print(f"Speakers found in results: {speakers_in_results}")

        # Debug: Check if name_to_url is populated
        print(f"Total panelist URLs available: {len(self.name_to_url)}")

        # Create case-insensitive URL mapping
        case_insensitive_lookup = {}
        for name, url in self.name_to_url.items():
            if url:  # Only include if URL exists
                case_insensitive_lookup[name.upper()] = (name, url)

        # Track what we've already linked to avoid double-linking
        already_linked = set()

        # Add hyperlinks for panellist names using case-insensitive matching
        for normalized_speaker, original_speaker in speakers_in_results.items():
            # Skip if we've already linked this speaker
            if normalized_speaker.upper() in already_linked:
                continue

            # Try case-insensitive matching using the original speaker name
            upper_speaker = original_speaker.upper()
            if upper_speaker in case_insensitive_lookup:
                original_name, profile_url = case_insensitive_lookup[upper_speaker]
                print(
                    f"Found URL for {original_speaker} via {original_name}: {profile_url}"
                )

                # Try multiple patterns to match how the AI might format names
                # Use the normalized (title case) version for matching in text
                patterns_to_try = [
                    # Pattern 1: Bold markdown (e.g., **Matt Canavan**)
                    (
                        rf"\*\*{re.escape(normalized_speaker)}\*\*",
                        f"**[{normalized_speaker}]({profile_url})**",
                    ),
                    # Pattern 2: Name with [Panelist/Host/Audience] tag
                    (
                        rf"\b{re.escape(normalized_speaker)}\b\s*\[(Panelist|Host|Audience)\]",
                        f"[{normalized_speaker}]({profile_url}) [\\1]",
                    ),
                    # Pattern 3: Plain name at start of sentence or after common punctuation
                    (
                        rf"(^|[.!?]\s+|:\s*){re.escape(normalized_speaker)}\b",
                        f"\\1[{normalized_speaker}]({profile_url})",
                    ),
                    # Pattern 4: Name followed by common verbs or said/stated
                    (
                        rf"\b{re.escape(normalized_speaker)}\b(\s+(?:said|stated|argued|emphasized|noted|explained|suggested|proposed|believes?|thinks?|expresse[ds]|advocate[ds]?|highlight(?:ed|s)?|point(?:ed|s)?\s+out))",
                        f"[{normalized_speaker}]({profile_url})\\1",
                    ),
                ]

                # Try each pattern
                replacement_made = False
                for pattern, replacement in patterns_to_try:
                    # Count occurrences before replacement
                    matches_before = len(
                        re.findall(pattern, full_answer, re.IGNORECASE | re.MULTILINE)
                    )

                    if matches_before > 0:
                        # Make the replacement (only first occurrence to avoid over-linking)
                        full_answer = re.sub(
                            pattern,
                            replacement,
                            full_answer,
                            count=1,  # Only replace first occurrence
                            flags=re.IGNORECASE | re.MULTILINE,
                        )
                        print(
                            f"  → Replaced {normalized_speaker} using pattern: {pattern[:30]}..."
                        )
                        replacement_made = True
                        already_linked.add(normalized_speaker.upper())
                        break

                if not replacement_made:
                    print(
                        f"  → WARNING: Could not find {normalized_speaker} in text with any pattern"
                    )
                    # Debug: Show where this name appears in the text
                    if normalized_speaker.lower() in full_answer.lower():
                        # Find the context where the name appears
                        for match in re.finditer(
                            re.escape(normalized_speaker), full_answer, re.IGNORECASE
                        ):
                            start = max(0, match.start() - 20)
                            end = min(len(full_answer), match.end() + 20)
                            context = full_answer[start:end]
                            print(f"    Found at: ...{context}...")
            else:
                print(f"No URL found for {original_speaker}")

        # Add episode links with date information
        # seen_titles = set()
        episode_links = []

        # Use smart filtering to show only relevant episodes
        episodes_mentioned = identify_relevant_episodes(full_answer, docs)

        # for doc in docs:
        #     title = doc.metadata.get("title")
        #     date = doc.metadata.get("episode_date", "")
        #     if title and title not in seen_titles:
        #         seen_titles.add(title)
        #         url = self.episode_url_lookup.get(title)
        #         if url:
        #             episode_links.append(f"- [{date} — {title}]({url})")

        for episode_info in episodes_mentioned:
            title = episode_info["title"]
            date = episode_info["date"]
            url = self.episode_url_lookup.get(title)
            if url:
                episode_links.append(f"- [{date} — {title}]({url})")
            else:
                # Still show the episode even if we don't have a URL
                episode_links.append(f"- {date} — {title}")

        # Use smaller font for sources and proper line breaks
        source_md = (
            "*Sources:*<br>" + "<br>".join(episode_links) if episode_links else ""
        )

        return full_answer, source_md

