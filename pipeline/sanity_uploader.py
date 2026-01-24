import os
import requests
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("NEXT_PUBLIC_SANITY_PROJECT_ID")
DATASET = "production" # Assuming 'production' dataset, customize if needed
API_TOKEN = os.getenv("SANITY_API_TOKEN")

class SanityUploader:
    def __init__(self):
        if not PROJECT_ID or not API_TOKEN:
            print("Warning: Sanity credentials not found. Skipping upload.")
            self.enabled = False
        else:
            self.enabled = True
            self.url = f"https://{PROJECT_ID}.api.sanity.io/v2021-06-07/data/mutate/{DATASET}"
            self.headers = {
                "Authorization": f"Bearer {API_TOKEN}",
                "Content-Type": "application/json"
            }

    def get_document(self, doc_id):
        """Fetches a document from Sanity by ID."""
        if not self.enabled:
            return None
        
        # Query URL for a single document by ID
        query = f'*[_id == "{doc_id}"][0]'
        url = f"https://{PROJECT_ID}.api.sanity.io/v2021-06-07/data/query/{DATASET}"
        params = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('result')
        except Exception as e:
            print(f"Error fetching document from Sanity: {e}")
            return None

    def get_document_by_slug(self, slug):
        """Fetches a document from Sanity by slug."""
        if not self.enabled:
            return None
        
        # Query for a book review with the matching slug
        query = f'*[_type == "bookReview" && slug.current == "{slug}"][0]'
        url = f"https://{PROJECT_ID}.api.sanity.io/v2021-06-07/data/query/{DATASET}"
        params = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('result')
        except Exception as e:
            print(f"Error fetching document by slug from Sanity: {e}")
            return None

    def upload_book_review(self, book_data):
        if not self.enabled:
            return None
        
        doc_id = book_data.get('_id')
        if doc_id:
            existing_doc = self.get_document(doc_id)
            if existing_doc:
                print(f"  - Document '{doc_id}' exists in Sanity. Merging fields...")
                # Fields to preserve from Sanity if they exist and are non-empty
                # We prioritize the existing Sanity content for these specific fields
                fields_to_preserve = ['yourReview', 'yourRating', 'affiliateLink', 'bookDescription', 'coverImage']
                for field in fields_to_preserve:
                    if field in existing_doc and existing_doc[field]:
                        # Special case for Portable Text (yourReview is usually a list)
                        if isinstance(existing_doc[field], list) and not existing_doc[field]:
                            continue
                        book_data[field] = existing_doc[field]
                        print(f"    - Preserved existing '{field}'")
        
        # Use createOrReplace to update or create
        mutations = [
            {
                "createOrReplace": book_data
            }
        ]
        
        return self._send_mutation(mutations)

    def patch_document(self, doc_id, set_fields):
        """Updates specific fields of an existing document."""
        if not self.enabled:
            return None
            
        mutations = [
            {
                "patch": {
                    "id": doc_id,
                    "set": set_fields
                }
            }
        ]
        return self._send_mutation(mutations)

    def upload_image_asset(self, image_bytes, filename="cover.jpg", mimetype="image/jpeg"):
        """Uploads an image asset to Sanity and returns the asset document."""
        if not self.enabled:
            return None
            
        print(f"Uploading image asset '{filename}' to Sanity...")
        
        # Sanity Asset Upload endpoint
        upload_url = f"https://{PROJECT_ID}.api.sanity.io/v2021-06-07/assets/images/{DATASET}"
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": mimetype
        }
        
        try:
            response = requests.post(upload_url, headers=headers, data=image_bytes)
            response.raise_for_status()
            asset_doc = response.json()
            print("Image Upload Success!")
            return asset_doc.get('document')
        except Exception as e:
            print(f"Error uploading image to Sanity: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Details: {e.response.text}")
            return None

    def create_update_log(self, book_title, book_slug, log_title=None, log_message=None, log_type="NEW_BOOK_SUMMARY"):
        """Creates an update log entry in Sanity."""
        if not self.enabled:
            return None
            
        print("Creating Update Log in Sanity...")
        
        # Use provided values or defaults
        final_title = log_title if log_title else f"Added summary: {book_title}"
        final_message = log_message if log_message else f"Added summary of {book_title}."
        
        log_entry = {
            "_type": "updateLog",
            "title": final_title,
            "message": final_message,
            "type": log_type,
            "targetType": "book",
            "targetSlug": book_slug,
            "importance": "normal",
            "createdAt": datetime.utcnow().isoformat() + "Z"
        }
        
        mutations = [
            {
                "create": log_entry
            }
        ]
        
        return self._send_mutation(mutations)

    def _send_mutation(self, mutations):
        payload = {"mutations": mutations}
        try:
            response = requests.post(self.url, headers=self.headers, json=payload)
            response.raise_for_status()
            print("Sanity Upload Success!")
            return response.json()
        except Exception as e:
            print(f"Error uploading to Sanity: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Details: {e.response.text}")
            return None
