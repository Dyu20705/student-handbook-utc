import sys
import os
import urllib.request

# Tránh bị trùng tên file script với thư viện 'arxiv'
script_dir = os.path.dirname(os.path.abspath(__file__))
if sys.path and sys.path[0] == script_dir:
    sys.path.pop(0)

import arxiv

def download_biblo(arxiv_id, save_dir="docs"):
    print(f"download_biblo in arXiv ID: {arxiv_id} using 'arxiv' package...\n")
    
    # Construct the default API client.
    client = arxiv.Client()

    # Search for the paper with the given ID.
    search = arxiv.Search(id_list=[arxiv_id.strip()])

    try:
        paper = next(client.results(search))
        
        print(f"Title: {paper.title}")
        print(f"Authors: {', '.join(author.name for author in paper.authors)}")
        print(f"Published: {paper.published}")
        print(f"Summary: {paper.summary[:200]}...") # truncate for brevity
        print(f"PDF URL: {paper.pdf_url}")

        os.makedirs(save_dir, exist_ok=True)
        filename = f"{paper.get_short_id()}.pdf"
        filepath = os.path.join(save_dir, filename)
        print(f"Downloading PDF to {filepath}...")
        urllib.request.urlretrieve(paper.pdf_url, filepath)
        print(f"Successfully downloaded: {filepath} ({os.path.getsize(filepath)} bytes)")
        return filepath
        
    except StopIteration:
        print("No paper found for this ID.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    biblo_id = input()
    print(f"Downloading {biblo_id} ....")
    download_biblo(biblo_id)