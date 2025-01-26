import asyncio
import os
import json
from typing import Set, Dict
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig

async def extract_links(base_url, crawler, config):
    """Extrai links internos da página."""
    result = await crawler.arun(url=base_url, config=config)
    if not result.success:
        return []
    links = result.links.get("internal", [])
    full_links = [urljoin(base_url, link["href"]) for link in links if "href" in link]
    domain = urlparse(base_url).netloc
    return [link for link in full_links if urlparse(link).netloc == domain]

async def crawl_page(url, depth, max_depth, visited, to_visit, semaphore, crawler, config, site_content):
    """Crawla uma página e explora links internos."""
    async with semaphore:
        if url in visited or depth > max_depth:
            return
        result = await crawler.arun(url=url, config=config)
        if not result.success:
            return
        if result.markdown:
            site_content.append(result.markdown)
        visited.add(url)
        links = await extract_links(url, crawler, config)
        for link in links:
            if link not in visited:
                to_visit.append((link, depth + 1))

async def crawl_documentation(base_url, output_dir, max_depth=3, max_concurrent=5):
    """Crawla a documentação e organiza os arquivos conforme a estrutura desejada."""
    config = CrawlerRunConfig(bypass_cache=True)
    visited: Set[str] = set()
    to_visit = [(base_url, 0)]
    site_content = []

    domain = urlparse(base_url).netloc
    sites_json = {}

    # Criar diretório base MD_links se não existir
    md_links_dir = os.path.join(output_dir, "MD_links")
    os.makedirs(md_links_dir, exist_ok=True)

    # Criar diretório específico para o site
    site_dir = os.path.join(md_links_dir, domain)
    os.makedirs(site_dir, exist_ok=True)

    semaphore = asyncio.Semaphore(max_concurrent)
    async with AsyncWebCrawler() as crawler:
        while to_visit:
            tasks = []
            while to_visit and len(tasks) < max_concurrent:
                current_url, depth = to_visit.pop(0)
                if current_url not in visited and depth <= max_depth:
                    tasks.append(
                        crawl_page(current_url, depth, max_depth, visited, to_visit, 
                                 semaphore, crawler, config, site_content)
                    )
            if tasks:
                await asyncio.gather(*tasks)

    # Salvar conteúdo combinado em um único arquivo .md
    md_file_path = os.path.join(site_dir, f"{domain}.md")
    with open(md_file_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(site_content))

    # Atualizar o JSON com as informações do site
    json_path = os.path.join(md_links_dir, "sites.json")
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            sites_json = json.load(f)
    
    sites_json[domain] = {
        "site_name": domain,
        "file_path": md_file_path
    }

    # Salvar o JSON atualizado
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(sites_json, f, indent=4)

async def crawl_single_page(base_url, output_dir):
    """Crawla uma única página e organiza os arquivos conforme a estrutura desejada."""
    config = CrawlerRunConfig(bypass_cache=True)
    domain = urlparse(base_url).netloc
    
    # Criar diretório base MD_links se não existir
    md_links_dir = os.path.join(output_dir, "MD_links")
    os.makedirs(md_links_dir, exist_ok=True)

    # Criar diretório específico para o site
    site_dir = os.path.join(md_links_dir, domain)
    os.makedirs(site_dir, exist_ok=True)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=base_url, config=config)
        if not result.success:
            print(f"Failed to crawl {base_url}. Error: {result.error_message}")
            return False

        # Salvar conteúdo em um arquivo .md
        md_file_path = os.path.join(site_dir, f"{domain}.md")
        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write(result.markdown or "")

        # Atualizar o JSON com as informações do site
        json_path = os.path.join(md_links_dir, "sites.json")
        sites_json = {}
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                sites_json = json.load(f)

        sites_json[domain] = {
            "site_name": domain,
            "file_path": md_file_path
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(sites_json, f, indent=4)

        return True