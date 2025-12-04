from dataclasses import dataclass
from typing import List, Optional
import argparse
import re
import requests
from bs4 import BeautifulSoup
import time
import random
import json
from urllib.parse import quote
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


@dataclass
class JobData:
    title: str
    company: str
    location: str
    job_link: str
    posted_date: str
    description: Optional[str] = None


class ScraperConfig:
    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    JOBS_PER_PAGE = 25
    MIN_DELAY = 0.5  # Reduced from 2
    MAX_DELAY = 1.5  # Reduced from 5
    RATE_LIMIT_DELAY = 30
    RATE_LIMIT_THRESHOLD = 10

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",
        "Cache-Control": "no-cache",
    }


class LinkedInJobsScraper:
    def __init__(self, max_workers: int = 8):
        self.session = self._setup_session()
        self.max_workers = max_workers
        self.lock = threading.Lock()  # Thread-safe access to shared resources

    def _setup_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def _build_search_url(self, keywords: str, location: str, start: int = 0, time_range_seconds: Optional[int] = None) -> str:
        params = {
            "keywords": keywords,
            "location": location,
            "start": start,
        }
        base = f"{ScraperConfig.BASE_URL}?{'&'.join(f'{k}={quote(str(v))}' for k, v in params.items())}"
        if time_range_seconds and int(time_range_seconds) > 0:
            # LinkedIn uses f_TPR=r{seconds} for time posted range
            base = base + f"&f_TPR=r{int(time_range_seconds)}"
        return base

    def _clean_job_url(self, url: str) -> str:
        return url.split("?")[0] if "?" in url else url

    def _extract_job_data(self, job_card: BeautifulSoup) -> Optional[JobData]:
        try:
            title = job_card.find("h3", class_="base-search-card__title").text.strip()
            company = job_card.find(
                "h4", class_="base-search-card__subtitle"
            ).text.strip()
            location = job_card.find(
                "span", class_="job-search-card__location"
            ).text.strip()
            job_link = self._clean_job_url(
                job_card.find("a", class_="base-card__full-link")["href"]
            )
            posted_date = job_card.find("time", class_="job-search-card__listdate")
            posted_date = posted_date.text.strip() if posted_date else "N/A"

            return JobData(
                title=title,
                company=company,
                location=location,
                job_link=job_link,
                posted_date=posted_date,
            )
        except Exception as e:
            print(f"Failed to extract job data: {str(e)}")
            return None

    def _fetch_job_page(self, url: str) -> BeautifulSoup:
        try:
            response = self.session.get(url, headers=ScraperConfig.HEADERS)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch data: Status code {response.status_code}"
                )
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {str(e)}")

    def _fetch_job_detail(self, url: str) -> BeautifulSoup:
        """Fetch the job detail page and return a BeautifulSoup object."""
        try:
            response = self.session.get(url, headers=ScraperConfig.HEADERS)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch job detail: Status code {response.status_code}"
                )
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {str(e)}")

    def _extract_description_from_soup(self, soup: BeautifulSoup) -> Optional[str]:
        """Try several strategies to extract the job description from a job detail page."""
        # 1) JSON-LD structured data
        try:
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "{}")
                    if isinstance(data, dict) and "description" in data:
                        desc = data.get("description")
                        if desc:
                            return desc.strip()
                except Exception:
                    continue
        except Exception:
            pass

        # 2) Common HTML selectors seen on LinkedIn job pages
        selectors = [
            "div.show-more-less-html__markup",
            "div.description__text",
            "div.job-description__content",
            "div.jobs-description__container",
            "section.description",
            "div.job-description",
            "div.description",
            "div#job-details",
            "article",
            "div[class*='description']",
            "div[class*='job-detail']",
        ]
        for sel in selectors:
            try:
                node = soup.select_one(sel)
                if node:
                    text = node.get_text(separator="\n").strip()
                    if text and len(text) > 50:  # Must be substantial
                        return text
            except:
                continue

        # 3) Meta description tag
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            desc = meta.get("content").strip()
            if len(desc) > 50:
                return desc

        # 4) OG description
        og = soup.find("meta", attrs={"property": "og:description"})
        if og and og.get("content"):
            desc = og.get("content").strip()
            if len(desc) > 50:
                return desc

        # 5) Try to get any substantial text from body
        try:
            body = soup.find("body")
            if body:
                text = body.get_text(separator="\n").strip()
                # Extract a sensible chunk
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                substantial = [l for l in lines if len(l) > 20]
                if substantial:
                    return '\n'.join(substantial[:20])
        except:
            pass

        return None

    def _fetch_and_enrich_job(self, job_data: JobData) -> JobData:
        """Fetch job details and enrich the job data with description."""
        if not job_data.job_link:
            return job_data
        
        try:
            # Add small random delay to avoid hammering LinkedIn
            time.sleep(random.uniform(0.1, 0.3))
            
            response = self.session.get(job_data.job_link, headers=ScraperConfig.HEADERS, timeout=15)
            if response.status_code == 200:
                detail_soup = BeautifulSoup(response.text, "html.parser")
                description = self._extract_description_from_soup(detail_soup)
                if description and len(description) > 30:
                    job_data.description = description
            
            # If still no description, that's okay - we'll leave it as None/missing
        except Exception as e:
            # Silently fail for description fetch - listing data is still valuable
            pass
        
        return job_data

    def _fetch_page_jobs(self, keywords: str, location: str, start: int, time_range_seconds: Optional[int] = None) -> List[JobData]:
        """Fetch and extract jobs from a single page."""
        try:
            url = self._build_search_url(keywords, location, start, time_range_seconds=time_range_seconds)
            soup = self._fetch_job_page(url)
            job_cards = soup.find_all("div", class_="base-card")
            
            jobs = []
            for card in job_cards:
                job_data = self._extract_job_data(card)
                if job_data:
                    jobs.append(job_data)
            return jobs
        except Exception as e:
            print(f"Error fetching page at start={start}: {e}")
            return []

    def scrape_jobs(
        self, keywords: str, location: str, max_jobs: int = 100, fetch_description: bool = True, time_range_seconds: Optional[int] = None
    ) -> List[JobData]:
        all_jobs = []
        
        # Calculate how many pages we need
        pages_needed = (max_jobs // ScraperConfig.JOBS_PER_PAGE) + 2
        page_starts = [i * ScraperConfig.JOBS_PER_PAGE for i in range(pages_needed)]
        
        # Fetch multiple pages concurrently
        print(f"Fetching up to {pages_needed} pages concurrently...")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(
                    self._fetch_page_jobs, keywords, location, start, time_range_seconds
                ): start for start in page_starts
            }
            
            for future in as_completed(futures):
                try:
                    page_jobs = future.result()
                    all_jobs.extend(page_jobs)
                    print(f"Fetched {len(page_jobs)} jobs, total: {len(all_jobs)}")
                    
                    if len(all_jobs) >= max_jobs:
                        break
                except Exception as e:
                    print(f"Error processing page: {e}")
        
        # Trim to max_jobs before enriching
        all_jobs = all_jobs[:max_jobs]
        
        # Enrich with descriptions in parallel (if enabled)
        if fetch_description and all_jobs:
            print(f"\nFetching descriptions for {len(all_jobs)} jobs using {self.max_workers} threads...")
            enriched_jobs = []
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._fetch_and_enrich_job, job): job 
                    for job in all_jobs
                }
                
                completed = 0
                for future in as_completed(futures):
                    try:
                        enriched_job = future.result()
                        enriched_jobs.append(enriched_job)
                        completed += 1
                        if completed % 10 == 0:
                            print(f"Enriched {completed}/{len(all_jobs)} jobs...")
                    except Exception as e:
                        print(f"Error enriching job: {e}")
            
            return enriched_jobs
        
        return all_jobs

    def save_results(
        self, jobs: List[JobData], filename: str = "linkedin_jobs.json"
    ) -> None:
        if not jobs:
            return
        # Add search metadata to each job so saved JSON can be traced back to the query
        enriched = []
        for job in jobs:
            jd = vars(job).copy()
            # may have been set on the scraper instance or passed in externally
            if getattr(self, '_last_search_keywords', None):
                jd['search_keywords'] = self._last_search_keywords
            if getattr(self, '_last_search_location', None):
                jd['search_location'] = self._last_search_location
            enriched.append(jd)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(enriched, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(jobs)} jobs to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Simple LinkedIn jobs scraper (free).')
    parser.add_argument('--keywords', '-k', default='Engineering Manager', help='Search keywords')
    parser.add_argument('--location', '-l', default='London,uk', help='Location string')
    parser.add_argument('--max-jobs', '-n', type=int, default=10, help='Max jobs to fetch')
    parser.add_argument('--time-range', '-t', default=None, help='Time range (e.g. 1h, 24h, 7d or seconds like 3600)')
    parser.add_argument('--no-description', dest='fetch_description', action='store_false', help='Do not fetch job detail descriptions (much faster)')
    parser.add_argument('--dry-run', action='store_true', help='Show constructed search URL and exit (no network)')
    parser.add_argument('--workers', '-w', type=int, default=8, help='Number of worker threads for descriptions (default: 8)')
    args = parser.parse_args()

    def parse_time_range(s: Optional[str]) -> Optional[int]:
        if not s:
            return None
        s = str(s).strip().lower()
        # allow plain numbers (seconds)
        if s.isdigit():
            return int(s)
        m = re.match(r'^(\d+)([smhdw]?)$', s)
        if not m:
            raise ValueError(f"Invalid time range: {s}")
        num = int(m.group(1))
        unit = m.group(2) or 's'
        if unit == 's':
            return num
        if unit == 'm':
            return num * 60
        if unit == 'h':
            return num * 3600
        if unit == 'd':
            return num * 86400
        if unit == 'w':
            return num * 7 * 86400
        return None

    time_range_seconds = None
    try:
        time_range_seconds = parse_time_range(args.time_range)
    except ValueError as e:
        print(str(e))
        return

    params = {
        'keywords': args.keywords,
        'location': args.location,
        'max_jobs': args.max_jobs,
    }

    def slugify(s: Optional[str]) -> str:
        if not s:
            return ''
        s = str(s).strip()
        # remove characters that are not word chars, spaces, hyphens or dots
        s = re.sub(r"[^\w\s-]", '', s)
        # collapse whitespace/hyphens to underscores
        s = re.sub(r"[\s-]+", '_', s)
        return s[:120]

    scraper = LinkedInJobsScraper(max_workers=args.workers)
    # record the last search params onto the scraper so save_results can include them
    scraper._last_search_keywords = params['keywords']
    scraper._last_search_location = params['location']

    if args.dry_run:
        # Build one URL and print it without making network requests
        url = scraper._build_search_url(params['keywords'], params['location'], start=0, time_range_seconds=time_range_seconds)
        print('DRY RUN - constructed search URL:')
        print(url)
        # show planned output filename
        planned = f"{slugify(args.keywords)}__{slugify(args.location)}"
        if time_range_seconds:
            planned += f"_r{int(time_range_seconds)}"
        planned += ".json"
        print('\nPlanned output filename: ' + planned)
        return

    print(f"\n{'='*60}")
    print(f"Starting scrape with:")
    print(f"  Keywords: {params['keywords']}")
    print(f"  Location: {params['location']}")
    print(f"  Max jobs: {params['max_jobs']}")
    print(f"  Fetch descriptions: {args.fetch_description}")
    print(f"  Worker threads: {args.workers}")
    print(f"{'='*60}\n")

    jobs = scraper.scrape_jobs(
        params['keywords'], params['location'],
        max_jobs=params['max_jobs'],
        fetch_description=args.fetch_description,
        time_range_seconds=time_range_seconds,
    )

    out_name = f"{slugify(args.keywords)}__{slugify(args.location)}"
    if time_range_seconds:
        out_name += f"_r{int(time_range_seconds)}"
    out_name += ".json"

    scraper.save_results(jobs, filename=out_name)


if __name__ == "__main__":
    main()