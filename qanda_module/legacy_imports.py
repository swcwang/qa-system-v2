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

# ADDED: Import V3 parser
from .v3_parser import enhance_document_metadata

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
        
        # MODIFIED: V3 parser integration instead of episode ID prefixes
        enhanced_docs = []
        for text, meta in zip(results["documents"][0], results["metadatas"][0]):
            doc = Document(page_content=text, metadata=meta)            
            #print(f"🔍 PARSER DEBUG - Before: {doc.page_content[:100]}")
            enhance_document_metadata(doc, meta)
            #print(f"🔍 PARSER DEBUG - After: {doc.page_content[:100]}")
            enhanced_docs.append(doc)
        
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
            for _, row in valid_links.iterrows():
                name = row["name"]
                url = row["link"]
                if name and name.strip():
                    self.name_to_url[name.strip().upper()] = {
                        'original': name.strip(),
                        'url': url
                    }

            print(f"Loaded {len(self.name_to_url)} panelist profile URLs")
        else:
            print(
                "Warning: 'link' column not found in df_guests - panelist URLs will not be available"
            )

        # Print some stats about the data
        panellist_count = self.df_reply[self.df_reply["speaker_type"] == 3].shape[0]
        print(f"Total panellist responses: {panellist_count}")
        missing_sid = self.df_reply[
            (self.df_reply["speaker_type"] == 3) & (self.df_reply["speaker_id"].isna())
        ].shape[0]
        print(f"Panellist responses with missing speaker_id: {missing_sid}")

        self.panelist_lookup = {}
        if "link" in self.df_guests.columns:
            for _, row in self.df_guests.iterrows():
                name = row["name"]
                profession = row.get("profession", "Politician")  
                url = row["link"]
                if pd.notna(name) and name.strip():
                    # Store as tuple for UI: (profession, url)
                    self.panelist_lookup[name.strip()] = (
                        profession if pd.notna(profession) else "Politician",
                        url if pd.notna(url) else None
                    )
            print(f"Created panelist_lookup with {len(self.panelist_lookup)} entries for UI display")

    def get_episode_id(self, ep_label):
        """Helper to get episode ID from label."""
        return self.episode_lookup.get(ep_label)

    def get_panellists_by_episode(self, ep_label):
        """Get list of panellists for an episode, focusing on speaker_type=3 with valid IDs."""
        # REMOVED: Debug print
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
        # REMOVED: Debug print
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
        # REMOVED: Debug prints
        if not ep_label or panellist_name is None:
            return []

        # Get the episode ID
        ep_id = self.get_episode_id(ep_label)
        if ep_id is None:
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
        return sorted(topics)

    def get_panellists_by_subtopic(self, ep_label, subtopic):
        """Get list of panellists for a subtopic in an episode, filtering for speaker_type=3."""
        # REMOVED: Debug prints
        if not ep_label or subtopic is None:
            return []

        # Get the episode ID
        ep_id = self.get_episode_id(ep_label)
        if ep_id is None:
            return []

        # Filter for panellists discussing this subtopic
        df_filtered = self.df_reply[
            (self.df_reply["episode_id"] == ep_id)
            & (self.df_reply["subtopic"].str.upper() == subtopic.upper())
            & (self.df_reply["speaker_type"] == 3)
        ]

        # Get panellist names directly from the filtered data
        panellists = df_filtered["speaker_name"].dropna().unique().tolist()
        return sorted(panellists)

    def format_response_with_links(self, full_answer, docs):
        """
        Format response with hyperlinks and numbered citations - V3 COMPATIBLE.
        Combines sophisticated panelist linking with numbered episode citations.
        """
        import re
        
        # ========================
        # STAGE 1: NUMBERED CITATIONS (V3 COMPATIBLE)
        # ========================
        # Extract episode IDs from both old and new formats
        episode_ids = []
        
        # V3 format: "Ep 615" -> extract 615
        v3_episodes = re.findall(r'\bEp (\d+)\b', full_answer)
        episode_ids.extend(v3_episodes)
        
        # Legacy format: "Episode ID: 615" -> extract 615  
        legacy_episodes = re.findall(r'Episode ID: (\d+)', full_answer)
        episode_ids.extend(legacy_episodes)
        
        # Create sequential mapping
        episode_to_ref = {}
        unique_episodes = []
        
        for episode_id in episode_ids:
            if episode_id not in episode_to_ref:
                ref_num = len(unique_episodes) + 1
                episode_to_ref[episode_id] = ref_num
                unique_episodes.append(episode_id)
        
        # Replace episode citations with numbered superscript citations
        for episode_id in episode_ids:
            if episode_id in episode_to_ref:
                ref_num = episode_to_ref[episode_id]
                replacement = f'<sup>[{ref_num}]</sup>'
                
                # Replace V3 format: "Ep 615" -> "<sup>[1]</sup>"
                pattern_v3 = f"Ep {episode_id}"
                full_answer = full_answer.replace(pattern_v3, replacement, 1)
                
                # Replace legacy format: "Episode ID: 615" -> "<sup>[1]</sup>"
                pattern_legacy = f"Episode ID: {episode_id}"
                full_answer = full_answer.replace(pattern_legacy, replacement, 1)
        
        # Remove any remaining "Sources Used:" sections from AI
        full_answer = re.sub(r'\*\*Sources Used:\*\*.*$', '', full_answer, flags=re.DOTALL).strip()
        
        # ========================
        # STAGE 2: PANELIST LINKING (V3 COMPATIBLE)
        # ========================
        # Collect all unique speakers in the results
        speakers_in_results = {}
        for doc in docs:
            # V3 compatible metadata access
            speaker_name = doc.metadata.get("speaker_name") or doc.metadata.get("spk")
            if speaker_name:
                normalized = speaker_name.title()
                speakers_in_results[normalized] = speaker_name

        # Track what we've already linked
        already_linked = set()

        # Add hyperlinks for panellist names using case-insensitive matching
        for normalized_speaker, original_speaker in speakers_in_results.items():
            if normalized_speaker.upper() in already_linked:
                continue

            # Try case-insensitive matching using the original speaker name
            upper_speaker = original_speaker.upper()
            if upper_speaker in self.name_to_url:
                info = self.name_to_url[upper_speaker]
                original_name = info['original']
                profile_url = info['url']

                # Try multiple patterns to match how the AI might format names
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
                    matches_before = len(
                        re.findall(pattern, full_answer, re.IGNORECASE | re.MULTILINE)
                    )

                    if matches_before > 0:
                        full_answer = re.sub(
                            pattern,
                            replacement,
                            full_answer,
                            count=1,  # Only replace first occurrence
                            flags=re.IGNORECASE | re.MULTILINE,
                        )
                        replacement_made = True
                        already_linked.add(normalized_speaker.upper())
                        break

        # ========================
        # STAGE 3: EPISODE SOURCES (V3 COMPATIBLE)
        # ========================
        # Build numbered source list matching the citations
        episode_links = []
        
        if unique_episodes and episode_to_ref:
            print(f"🔍 unique_episodes from AI: {unique_episodes}")
            print(f"🔍 episode_to_ref mapping: {episode_to_ref}")
            print(f"🔍 Total docs to check: {len(docs)}")
            
            episode_details = {}
            for i, doc in enumerate(docs):
                eid_v1 = doc.metadata.get('episode_id')
                eid_v2 = doc.metadata.get('eid')
                eid = eid_v1 or eid_v2
                
                #(f"🔍 Doc {i}: episode_id={eid_v1}, eid={eid_v2}, final eid={eid}")
                
                    #print(f"✅ Match found! Doc {i} matches episode {eid}")
                    # Build episode details (add this part):
                title = (doc.metadata.get("episode_title") or 
                        doc.metadata.get("title") or 
                        doc.metadata.get("ttl", ""))
                date = doc.metadata.get("episode_date") or doc.metadata.get("dt", "")
                if title:
                    episode_details[str(eid)] = {'title': title, 'date': date}

            
            #print(f"🔍 Final episode_details: {episode_details}")
            
            # Remove the duplicate loop that starts with "episode_details = {}"
            
            # Build numbered source links matching citation order
            for episode_id in unique_episodes:
                if episode_id in episode_details:
                    ref_num = episode_to_ref[episode_id]
                    details = episode_details[episode_id]
                    title = details['title']
                    date = details['date']
                    
                    url = self.episode_url_lookup.get(title)
                    if url:
                        episode_links.append(f"{ref_num}. [{date}: {title}]({url})")
                    else:
                        episode_links.append(f"{ref_num}. {date}: {title}")
        else:
            # Fallback: use smart episode filtering for non-cited episodes
            episodes_mentioned = identify_relevant_episodes(full_answer, docs)
            for episode_info in episodes_mentioned:
                title = episode_info["title"]
                date = episode_info["date"]
                url = self.episode_url_lookup.get(title)
                if url:
                    episode_links.append(f"- [{date} — {title}]({url})")
                else:
                    episode_links.append(f"- {date} — {title}")

        # Format sources for display
        source_md = "<br>".join(episode_links) if episode_links else ""

        return full_answer, source_md

def identify_relevant_episodes(full_answer, docs):
    """Identify which episodes were actually referenced in the answer."""
    import re
    
    # Get all episodes from docs
    all_episodes = {}
    for doc in docs:
        # MODIFIED: V3 compatible metadata access
        title = doc.metadata.get("title") or doc.metadata.get("episode_title") or doc.metadata.get("ttl")
        date = doc.metadata.get("episode_date") or doc.metadata.get("dt")
        speaker = doc.metadata.get("speaker_name") or doc.metadata.get("spk")
        
        if title and title not in all_episodes:
            all_episodes[title] = {
                "title": title,
                "date": date or "",
                "speakers": set()
            }
        if speaker:
            all_episodes[title]["speakers"].add(speaker)
    
    # Smart filtering - only include episodes that are actually mentioned
    relevant_episodes = []
    
    for title, info in all_episodes.items():
        include_episode = False
        
        # Check if any speaker from this episode is mentioned in the answer
        for speaker in info["speakers"]:
            if re.search(rf'\b{re.escape(speaker)}\b', full_answer, re.IGNORECASE):
                include_episode = True
                break
        
        # Check if episode date is mentioned
        if info["date"] and info["date"] in full_answer:
            include_episode = True
            
        if include_episode:
            relevant_episodes.append({
                "title": info["title"],
                "date": info["date"]
            })
    
    # Fallback: if no episodes identified, return the most recent 3
    if not relevant_episodes:
        sorted_episodes = sorted(all_episodes.values(), 
                               key=lambda x: x.get("date", ""), reverse=True)
        relevant_episodes = [{"title": ep["title"], "date": ep["date"]} 
                           for ep in sorted_episodes[:3]]
    
    return relevant_episodes