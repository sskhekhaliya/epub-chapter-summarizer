import openai
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .chunker import Chunker

# Retry configuration for LLM calls
llm_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((openai.APIConnectionError, openai.APITimeoutError)),
    reraise=True
)

class Summarizer:
    def __init__(self, model_url="http://localhost:11434/v1", model_name="llama3", api_key="nopass"):
        # Use explicit httpx client to avoid "proxies" argument issues in some environments
        self.client = openai.OpenAI(
            base_url=model_url,
            api_key=api_key,
            http_client=httpx.Client(timeout=120.0)
        )
        self.model_name = model_name
        self.chunker = Chunker()
        
        self.system_prompt = (
            "You are a master of literary analysis and narrative reconstruction. "
            "Your task is to summarize chapters while meticulously mimicking the specific author's prose style, "
            "narrative tone, vocabulary, AND NARRATIVE PERSPECTIVE (POV). "
            "If the original text uses first-person ('I', 'we'), write your summary in first-person. "
            "If the original uses third-person ('he', 'she', 'they'), write in third-person. "
            "The summary should feel like reading a condensed version of the book itself, not a description about the book. "
            "Avoid generic emotional clichés; instead, capture the underlying mood and themes as the author originally expressed them."
        )
        
        self.extraction_system_prompt = (
            "You are an expert editor and book reviewer. Your goal is to identify and extract the most "
            "compelling, insightful, and memorable highlights from a given text. Focus on profound "
            "philosophical insights, actionable life lessons, and pivotal character developments. "
            "Be generous but discerning; extract anything that would make a reader stop and think."
        )

    def summarize_chapter(self, text):
        """Summarizes text using the LLM. Handles chunking and merging."""
        chunks = self.chunker.chunk(text)
        
        if not chunks:
            return ""
            
        if len(chunks) == 1:
            return self._generate_summary(chunks[0])
        
        # If multiple chunks, summarize each and then merge
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            # Contextual prompt for chunks could be better, but we stick to the core request
            print(f"  Summarizing chunk {i+1}/{len(chunks)}...")
            summary = self._generate_summary(chunk)
            chunk_summaries.append(summary)
            
        if len(chunks) > 3:
            print(f"  Skipping merge for large chapter ({len(chunks)} chunks) to preserve detail.")
            return "\n\n***\n\n".join(chunk_summaries)
            
        # Merge summaries
        return self._merge_summaries(chunk_summaries)

    def generate_book_description(self, chapter_summaries):
        """Generates an overall book description based on chapter summaries."""
        if not chapter_summaries:
            return ""
            
        # Combine summaries into a single text block
        # Use only titles and content for context
        combined_text = "\n\n".join([f"Chapter: {ch.get('title')}\n{ch.get('summary')}" for ch in chapter_summaries])
        
        prompt = (
            "Based on the following chapter summaries, write a compelling, high-level book description "
            "suitable for a back-cover blurb. It should be approximately two paragraphs long, focusing on "
            "the overarching plot, core themes, and the protagonist's journey. \n\n"
            "INSTRUCTIONS:\n"
            "1. Output ONLY the description text. Do NOT include any introductory phrases like \"Here is a description\".\n"
            "2. Ensure the prose is seamless, engaging, and enthusiastic.\n\n"
            f"CHAPTER SUMMARIES:\n{combined_text}"
        )
        
        try:
            @llm_retry
            def fetch_description():
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.extraction_system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
            response = fetch_description()
            content = response.choices[0].message.content
            return self._strip_introductory_phrases(content)
        except Exception as e:
            print(f"Error generating book description: {e}")
            return ""

    def _generate_summary(self, text):
        prompt = (
            "Summarize the following chapter text. The summary MUST mimic the author's specific voice, "
            "sentence structure, and narrative style. Capture the story's core essence without adding "
            "generic emotional coloring or dramatic flourishes not present in the original prose.\n\n"
            "CRITICAL CONSTRAINTS:\n"
            "1. Output ONLY the summary text.\n"
            "2. Do NOT use introductory phrases (e.g., 'Here is a summary', 'This chapter tells', 'In this chapter').\n"
            "3. PRESERVE THE NARRATIVE POV: If the text uses first-person ('I saw', 'I walked'), write your summary in first-person. "
            "If it uses third-person ('He saw', 'She walked'), use third-person. The reader should feel they are reading the actual book, just condensed.\n"
            "4. Start the summary IMMEDIATELY with the narrative content, maintaining the same POV as the original.\n"
            "5. Maintain a unified, novel-like narrative voice throughout - this is a condensed book, NOT a book report.\n\n"
            f"TEXT TO SUMMARIZE:\n{text}"
        )
        
        try:
            @llm_retry
            def fetch_summary():
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
            response = fetch_summary()
            content = response.choices[0].message.content
            return self._strip_introductory_phrases(content)
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return "Summary generation failed."

    def extract_highlights(self, text):
        """Extracts key highlights/takeaways from the text."""
        # For highlights, we can use a single chunk or a representative sample if it's too long
        # But to be thorough, we'll use the chunker and summarize the takeaways
        chunks = self.chunker.chunk(text)
        
        if not chunks:
            return []
            
        all_highlights = []
        for i, chunk in enumerate(chunks):
            if len(chunks) > 1:
                print(f"  Extracting highlights from chunk {i+1}/{len(chunks)}...")
            highlights = self._generate_highlights(chunk)
            all_highlights.extend(highlights)
            
        # If we have too many, we might want to consolidate, but for now we'll just return them
        # Let's deduplicate or prune if it's a massive list
        if len(all_highlights) > 10:
            return self._consolidate_highlights(all_highlights)
            
        return all_highlights

    def _generate_highlights(self, text):
        prompt = (
            "Review the following book text and extract a set of insightful highlights, memorable quotes, "
            "or key takeaways. \n\n"
            "GUIDELINES:\n"
            "- Focus on profound realizations, philosophical depth, or pivotal moments.\n"
            "- Each highlight should be a concise, stand-alone sentence.\n"
            "- Aim to extract multiple highlights if the content is rich.\n"
            "- Output MUST be a valid JSON list of strings.\n\n"
            f"TEXT:\n{text}"
        )
        
        try:
            @llm_retry
            def fetch_highlights():
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.extraction_system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
            response = fetch_highlights()
            content = response.choices[0].message.content
            return self._parse_json_response(content)
        except Exception as e:
            print(f"Error calling LLM for highlights: {e}")
            return []

    def _parse_json_response(self, content):
        """Robustly parses JSON from LLM response, handling common errors and formats."""
        import json
        import re
        
        if not content or not content.strip():
            return []
            
        # Clean potential markdown code blocks
        content = re.sub(r'^```json\s*', '', content.strip())
        content = re.sub(r'\s*```$', '', content)
            
        # 1. Try direct parsing first
        try:
            data = json.loads(content)
            # If it's an empty object, return empty list
            if isinstance(data, dict) and not data:
                return []
            return self._extract_list_from_data(data)
        except json.JSONDecodeError:
            pass
            
        # 2. Try cleaning common minor syntax errors (like trailing commas)
        cleaned = re.sub(r',\s*([\]}])', r'\1', content)
        try:
            data = json.loads(cleaned)
            return self._extract_list_from_data(data)
        except json.JSONDecodeError:
            pass
            
        # 3. Try extracting JSON block using regex if model included extra text
        try:
            # Try to find array first [ ... ]
            array_match = re.search(r'\[.*\]', content, re.DOTALL)
            if array_match:
                try:
                    data = json.loads(array_match.group())
                    return self._extract_list_from_data(data)
                except: pass
                
            # Try to find object { ... }
            obj_match = re.search(r'\{.*\}', content, re.DOTALL)
            if obj_match:
                try:
                    data = json.loads(obj_match.group())
                    return self._extract_list_from_data(data)
                except: pass
        except Exception as e:
            print(f"Failed to extract JSON using regex: {e}")
            
        print(f"Critical error: Failed to parse JSON response from LLM: {content[:100]}...")
        return []

    def _extract_list_from_data(self, data):
        """Helper to get a list of strings from parsed JSON object or list."""
        
        def extract_text_from_item(item):
            """Extracts text from a single item, handling dicts smarter."""
            if isinstance(item, str):
                return item
            elif isinstance(item, dict):
                # Priority keys to look for
                for key in ['quote', 'key takeaway', 'insight', 'text', 'Text', 'highlight', 'summary']:
                    if key in item and item[key]:
                        return str(item[key])
                # If no known key, fallback to string representation of values or the dict itself
                # But let's try to be clean first.
                return str(item)
            else:
                return str(item)

        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Check common keys or just take the first list found
            found_list = False
            for key in ['highlights', 'notes', 'takeaways', 'data', 'items']:
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    found_list = True
                    break
            # Fallback: search all values for a list
            if not found_list:
                for val in data.values():
                    if isinstance(val, list):
                        items = val
                        break
        
        return [extract_text_from_item(x) for x in items if x]

    def _consolidate_highlights(self, highlights):
        """Consolidates a large list of highlights into a more manageable set."""
        joined_highlights = "\n".join([f"- {h}" for h in highlights])
        prompt = (
            "Below is a list of highlights extracted from various chapters of a book. "
            "Your task is to consolidate these into a cohesive, high-quality list of the 'Top 10-15' "
            "most impactful insights. \n\n"
            "CONSOLIDATION RULES:\n"
            "- Remove near-duplicates or redundant points.\n"
            "- Combine related minor insights into single, more powerful sentences.\n"
            "- Prioritize depth and 'ah-ha' moments over routine plot descriptions.\n"
            "- Maintain the core wisdom and beauty of the original text.\n"
            "- Return a JSON list of strings.\n\n"
            f"HIGHLIGHTS:\n{joined_highlights}"
        )
        
        try:
            @llm_retry
            def fetch_consolidated():
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.extraction_system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
            response = fetch_consolidated()
            content = response.choices[0].message.content
            return self._parse_json_response(content) or highlights[:15]
        except Exception as e:
            print(f"Error consolidating highlights: {e}")
            return highlights[:15]

    def _merge_summaries(self, summaries):
        joined_summaries = "\n\n".join(summaries)
        prompt = (
            "Merge the following sequential parts of a chapter into one single, seamless, and coherent "
            "narrative summary. Ensure the transition between parts is invisible and the overall "
            "voice matches the author's specific tone and prose style.\n\n"
            "CRITICAL CONSTRAINTS:\n"
            "1. Output ONLY the final merged summary.\n"
            "2. Do NOT include any meta-talk or introductory remarks.\n"
            "3. Start the response IMMEDIATELY with the narrative content.\n"
            "4. Maintain the literary quality of the original author's voice.\n\n"
            f"CHAPTER PARTS:\n{joined_summaries}"
        )
        
        try:
            @llm_retry
            def fetch_merged():
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
            response = fetch_merged()
            content = response.choices[0].message.content
            return self._strip_introductory_phrases(content)
        except Exception as e:
             return joined_summaries # Fallback to concatenated summaries

    def _strip_introductory_phrases(self, text):
        """Removes common LLM introductory phrases using aggressive regex."""
        if not text:
            return ""
            
        import re
        
        # Regex to catch "Here is a summary..." and preceding meta-talk
        bad_patterns = [
            r"here\s+is\s+(?:a|the)\s+summary",
            r"here's\s+(?:a|the)\s+summary",
            r"attempt\s+at\s+summarizing",
            r"summary\s+of\s+the\s+chapter",
            r"summary\s+that\s+captures",
            r"author's\s+voice\s+is",
            r"voice\s+and\s+sentence\s+structure",
            r"mimic\s+it",
            r"mimic\s+the",
            r"in\s+the\s+same\s+voice",
            r"here\s+it\s+is"
        ]
        
        combined_pattern = re.compile("|".join(bad_patterns), re.IGNORECASE)
        
        # Specific pattern for the book description issue
        description_pattern = re.compile(
            r"here(?:'s| is) a (?:compelling|high-level|brief)?\s*book description.*?(?:\n|:)", 
            re.IGNORECASE | re.DOTALL
        )

        
        lines = text.split('\n')
        # Filter out lines that match the bad patterns strongly
        valid_lines = []
        # We only really care about the START of the text. 
        # But sometimes they put a title, then the meta talk.
        # Let's strip from the top until we hit real content.
        
        # However, checking every line is safer if the meta talk is mixed in.
        # But we must be careful not to delete story content. 
        # The meta talk usually doesn't look like narrative.
        
        for line in lines:
            if not line.strip():
                continue # Skip empty lines for now, we'll join later
                
            # If a line has a strong match, we skip it.
            if combined_pattern.search(line):
                continue
            
            # Check for the specific description pattern
            if description_pattern.search(line):
                # If it matches, we might want to just remove the match part if it's at the start
                # But often these are standalone lines. Let's try to remove just the match.
                line = description_pattern.sub("", line)
                if not line.strip():
                    continue
                
            valid_lines.append(line)
            
        # Re-join with single newlines or double? Original was likely double if paragraphs.
        # But summarizer usually outputs blocks.
        # Let's try to preserve paragraph structure if possible, but safe fallback is join('\n\n')
        # if the input had generic newlines.
        
        result = "\n".join(valid_lines).strip()
        return result
