import requests
from bs4 import BeautifulSoup
import re
import sys
from urllib.parse import urljoin, urlparse
import time
import gzip
import io
import os


def get_url_level(url):
    # Analizza l'URL
    parsed_url = urlparse(url)
    
    # Ottiene il percorso dall'URL
    path = parsed_url.path
    
    # Rimuove eventuali slash finali per evitare conteggi errati
    path = path.rstrip('/')
    
    # Se il percorso è vuoto o solo una barra, significa che siamo alla radice
    if not path or path == '/':
        return 0
    
    # Conta il numero di segmenti nel percorso
    segments = path.split('/')
    
    # Restituisce il livello, che è il numero di segmenti meno uno
    return len(segments) - 1  # Sottraiamo 1 per considerare le pagine come livello 1


def sanitize_filename(url):
    # Sostituisce i caratteri non validi con un trattino
    filename = re.sub(r'[^a-zA-Z0-9]', '-', url)
    return filename + '.out.txt'


def write_to_file(filename, data):
    """Scrive i dati nel file specificato."""
    with open(filename, 'a') as f:
        f.write(data)
        f.write("\n")


def is_same_domain(url, base_url):
    return urlparse(url).netloc == urlparse(base_url).netloc


def extract_data(soup):
    emails = set()
    names = set()
    phones = set()
    links = set()
    comments= set()

    # Estrazione delle email
    emails.update(set(re.findall(r'(?:mailto:)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', soup.prettify())))

    # Estrazione dei nomi (esempio semplice)
    names.update(set(re.findall(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', soup.prettify())))

    # Estrazione dei numeri di telefono cell e fisso italiano e non
    phones.update(set(re.findall(r'^(\+?[1-9]\d{0,2}[ -]?)?(\(?\d{1,4}?\)?[ -]?\d{1,4}[ -]?\d{1,4}[ -]?\d{1,9})$', soup.prettify())))

    # Estrazione dei commenti HTML
    comments.update(set(re.findall(r'<!--(.*?)-->', soup.prettify())))
    
    # Estrazione dei link
    for link in soup.find_all('a', href=True):
        full_link = urljoin(base_url, link['href'])
        if is_same_domain(full_link, base_url):
            links.add(full_link)

    return emails, names, phones, comments, links


def decompress_content(response):
    """Decompress the content if it's gzipped."""
    if response.headers.get('Content-Encoding') == 'gzip':
        try:
            buf = io.BytesIO(response.content)
            with gzip.GzipFile(fileobj=buf) as f:
                return f.read().decode('utf-8')
        except Exception as e:
            print(f"Error in decompression: {e}")
            return response.text  # Restituisce il testo non compresso in caso di errore
    return response.text


def crawl_site(url, selected_level, max_retries=3):
    visited = set()  # Set per tenere traccia delle pagine già visitate
    to_visit = [url]
    all_emails = set()
    all_names = set()
    all_phones = set()
    all_comments = set()
    all_links = set()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    while to_visit:
        current_url = to_visit.pop(0)
        analyze=False
        level=0
        if current_url in visited:
            continue
            
        if selected_level>-1:
            # se selected_item>-1 allora guardo che livello sto analizzando e nel caso decido se analizzare o skippare l'analisi
            level=get_url_level(current_url)
            if level<=selected_level:
               analyze=True
            else:
               analyze=False
        else:
            # se selected_item=-1 allora devo analuzzare tutto il sito
            level="All"
            analyze=True       

        if analyze==True:
            # se devo analizzare la pagina
            print(f"Analyzing:[L-{level}] {current_url}")  # Output dell'URL attualmente analizzato
            retries = 0
            while retries < max_retries:
                try:
                    response = requests.get(current_url, headers=headers, timeout=10)  # Timeout dopo 10 secondi
                    response.raise_for_status()  # Controlla se ci sono errori nella richiesta
                    visited.add(current_url)

                    # Decompressione del contenuto se necessario
                    content = decompress_content(response)
                    soup = BeautifulSoup(content, 'html.parser')
                    emails, names, phones, comments, links = extract_data(soup)

                    all_emails.update(emails)
                    all_names.update(names)
                    all_phones.update(phones)
                    all_comments.update(comments)
                    all_links.update(links)

                    to_visit.extend(links - visited)  # Aggiungi nuovi link a visitare
                    break  # Esci dal ciclo di retry se la richiesta ha successo

                except requests.HTTPError as e:
                    print(f"HTTP error accessing {current_url}: {e}")
                    retries += 1
                    time.sleep(2)  # Aspetta 2 secondi prima di riprovare
            
                except requests.RequestException as e:
                    print(f"Error accessing {current_url}: {e}")
                    retries += 1
                    time.sleep(2)  # Aspetta 2 secondi prima di riprovare

            if retries == max_retries:
                print(f"Unable to access {current_url} after {max_retries} attempts. Treated as read.")

            visited.add(current_url)  # Aggiungi comunque l'URL alla lista dei visitati
        else:
            # non devo analizzare la pagina
            print(f"Skipping:[L-{level}] {current_url}")  # Output dell'URL attualmente analizzato
                             
    return all_emails, all_names, all_phones, all_comments, all_links

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Use: python {sys.argv[0]} <target url> [<level>]")
        print ("It explores all the web pages of a specific web site and extract from them: emails, Usernames, HTML comments, Telephone number and Links.")
        print ("Parameters:")
        print ("- <target_url>: url to extract information from")
        print ("- [<level>]: level at which to stop scanning pages. If not specified the entire site will be scanned")
        print (f"\nExample: {sys.argv[0]} https://targetSite.htb 3")
        sys.exit(1)

    base_url = sys.argv[1]
    selected_level = int(sys.argv[2]) if len(sys.argv) > 2 else -1
    filename = sanitize_filename(base_url)
    # Controlla se il file esiste già
    if os.path.exists(filename):
        os.remove(filename)    

    emails, names, phones, comments, links = crawl_site(base_url, selected_level)
    write_to_file(filename, "Web Data Extractor: " + base_url)
    print("\n\n")    
    print("== Email found:")
    write_to_file(filename, "== Email found:")
    for email in sorted(emails):  # Risultati univoci e ordinati
        print(email)
        write_to_file(filename, email)

    print("\n== Name found:")
    write_to_file(filename, "\n== Name found:")    
    for name in sorted(names):  # Risultati univoci e ordinati
        print(name)
        write_to_file(filename, name)  

    print("\n== Telephone number found:")
    write_to_file(filename, "\n== Telephone number found:")
    for phone in sorted(phones):  # Risultati univoci e ordinati
        print(phone)
        write_to_file(filename, phone)

    print("== HTML comments found:")
    write_to_file(filename, "== HTML comments found:")
    for comment in sorted(comments):  # Risultati univoci e ordinati
        print(comment)
        write_to_file(filename, comment)

    print("\n== Link found:")
    write_to_file(filename, "\n== Link found:")
    for link in sorted(links):  # Risultati univoci e ordinati
        print(link)
        write_to_file(filename, link)
