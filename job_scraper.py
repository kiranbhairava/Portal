# import os
# import time
# import random
# import pandas as pd
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from bs4 import BeautifulSoup
# from datetime import datetime
# from webdriver_manager.chrome import ChromeDriverManager
# import traceback

# class LinkedInJobScraper:
#     def __init__(self, headless=True, slow_mode=True):
#         """
#         Initialize the LinkedIn Job Scraper
        
#         Args:
#             headless: Run browser in headless mode
#             slow_mode: Add random delays to appear more human-like
#         """
#         self.headless = headless
#         self.slow_mode = slow_mode
#         self.driver = None
#         self.jobs_data = []
        
#         # User agents rotation to avoid detection
#         self.user_agents = [
#             'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
#             'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15',
#             'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.76',
#             'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
#         ]
    
#     def setup_driver(self):
#         """Set up the Selenium WebDriver with appropriate options"""
#         chrome_options = Options()
#         if self.headless:
#             chrome_options.add_argument("--headless=new")
        
#         # Add a random user agent
#         chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        
#         # Additional options to make scraping more robust
#         chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#         chrome_options.add_argument("--disable-extensions")
#         chrome_options.add_argument("--disable-gpu")
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--disable-dev-shm-usage")
#         chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#         chrome_options.add_experimental_option("useAutomationExtension", False)
        
#         # Install and set up Chrome driver
#         service = Service(ChromeDriverManager().install())
#         driver = webdriver.Chrome(service=service, options=chrome_options)
        
#         # Set window size - a normal size helps avoid detection
#         driver.set_window_size(1920, 1080)
        
#         # Execute CDP commands to prevent detection
#         driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
#             "source": """
#                 Object.defineProperty(navigator, 'webdriver', {
#                     get: () => undefined
#                 });
#             """
#         })
        
#         self.driver = driver
#         return driver
    
#     def human_like_delay(self, min_seconds=1, max_seconds=3):
#         """Add random delay to appear more human-like"""
#         if self.slow_mode:
#             time.sleep(random.uniform(min_seconds, max_seconds))
    
#     def search_jobs(self, keywords, location, limit=25, experience_level=None, job_type=None):
#         """
#         Search for jobs on LinkedIn with given parameters
        
#         Args:
#             keywords: Job title or keywords
#             location: Job location
#             limit: Maximum number of jobs to scrape
#             experience_level: Experience level filter
#             job_type: Job type filter
            
#         Returns:
#             DataFrame with job listings
#         """
#         if self.driver is None:
#             self.setup_driver()
        
#         # Build the LinkedIn search URL with filters
#         base_url = "https://www.linkedin.com/jobs/search/?"
        
#         # Required parameters
#         params = {
#             "keywords": keywords.replace(" ", "%20"),
#             "location": location.replace(" ", "%20"),
#             "f_TPR": "r86400", # Last 24 hours
#             "position": 1,
#             "pageNum": 0
#         }
        
#         # Experience level and job type filters...
#         # [Code for filters remains the same]
        
#         # Construct the URL
#         url = base_url + "&".join([f"{key}={value}" for key, value in params.items()])
        
#         print(f"Searching for {keywords} jobs in {location}...")
#         print(f"URL: {url}")
        
#         try:
#             self.driver.get(url)
#             self.human_like_delay(3, 6)
            
#             # Print page title to check if we're on the right page
#             print(f"Page title: {self.driver.title}")
            
#             # IMPORTANT NEW APPROACH: Scrape basic info and URLs first, then visit each URL directly
#             job_urls = []
            
#             # Get all job listings on the page
#             soup = BeautifulSoup(self.driver.page_source, 'html.parser')
#             job_cards = soup.select("div.job-search-card")
            
#             print(f"Found {len(job_cards)} job cards")
            
#             # Extract basic info and URLs from all cards
#             for job in job_cards:
#                 if len(job_urls) >= limit:
#                     break
                
#                 try:
#                     # Extract basic job information
#                     job_data = {}
                    
#                     # Get job title
#                     title_elem = job.select_one("h3.base-search-card__title")
#                     job_data['title'] = title_elem.text.strip() if title_elem else "N/A"
                    
#                     # Get company name
#                     company_elem = job.select_one("h4.base-search-card__subtitle")
#                     job_data['company'] = company_elem.text.strip() if company_elem else "N/A"
                    
#                     # Get location
#                     location_elem = job.select_one("span.job-search-card__location")
#                     job_data['location'] = location_elem.text.strip() if location_elem else "N/A"
                    
#                     # Get posted time
#                     posted_time_elem = job.select_one("time")
#                     job_data['posted_time'] = posted_time_elem.text.strip() if posted_time_elem else "N/A"
                    
#                     # Get job URL
#                     job_link_elem = job.select_one("a.base-card__full-link")
#                     if job_link_elem and job_link_elem.get('href'):
#                         job_url = job_link_elem.get('href').split('?')[0]  # Remove query parameters
#                         job_data['job_url'] = job_url
#                         job_data['job_id'] = job_url.split('-')[-1]
                        
#                         # Store the job URL and basic data for later processing
#                         job_urls.append((job_url, job_data))
#                         print(f"Added job URL: {job_data['title']} at {job_data['company']}")
                    
#                 except Exception as e:
#                     print(f"Error extracting data from job card: {str(e)}")
            
#             # Visit each job URL directly to get details
#             jobs_scraped = 0
#             for job_url, job_data in job_urls:
#                 if jobs_scraped >= limit:
#                     break
                
#                 try:
#                     print(f"Visiting job URL: {job_url}")
#                     self.driver.get(job_url)
#                     self.human_like_delay(2, 4)
                    
#                     # Wait for job details to load
#                     WebDriverWait(self.driver, 10).until(
#                         EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-description__content"))
#                     )
                    
#                     # Extract job description
#                     try:
#                         description_elem = self.driver.find_element(By.CSS_SELECTOR, ".jobs-description__content")
#                         job_data['description'] = description_elem.text if description_elem else "N/A"
#                     except:
#                         # Try alternative selector
#                         try:
#                             description_elem = self.driver.find_element(By.CSS_SELECTOR, ".jobs-box__html-content")
#                             job_data['description'] = description_elem.text if description_elem else "N/A"
#                         except:
#                             job_data['description'] = "N/A"
                    
#                     # Extract criteria (seniority, employment type, etc)
#                     try:
#                         criteria_list = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-unified-top-card__job-insight")
#                         criteria_text = []
#                         for criteria in criteria_list:
#                             criteria_text.append(criteria.text.strip())
                        
#                         job_data['criteria'] = " | ".join(criteria_text) if criteria_text else "N/A"
#                     except:
#                         job_data['criteria'] = "N/A"
                    
#                     # Add to our data collection
#                     self.jobs_data.append(job_data)
#                     jobs_scraped += 1
                    
#                     print(f"Scraped {jobs_scraped}/{limit}: {job_data.get('title')} at {job_data.get('company')}")
                    
#                 except Exception as e:
#                     print(f"Error processing job URL {job_url}: {str(e)}")
#                     traceback.print_exc()
            
#             print(f"Successfully scraped {len(self.jobs_data)} jobs")
            
#             # Convert to DataFrame
#             if self.jobs_data:
#                 df = pd.DataFrame(self.jobs_data)
#                 return df
#             else:
#                 print("No jobs were scraped.")
#                 return pd.DataFrame()
            
#         except Exception as e:
#             print(f"An error occurred during job search: {str(e)}")
#             traceback.print_exc()
#             return pd.DataFrame()
#         finally:
#             # Keep the browser open for debugging if needed
#             if not self.headless:
#                 input("Press Enter to close the browser...")
#             else:
#                 self.driver.quit()
    
#     def save_to_csv(self, filename=None):
#         """Save the scraped job data to a CSV file"""
#         if not self.jobs_data:
#             print("No data to save")
#             return
            
#         if filename is None:
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             filename = f"linkedin_jobs_{timestamp}.csv"
            
#         df = pd.DataFrame(self.jobs_data)
#         df.to_csv(filename, index=False)
#         print(f"Data saved to {filename}")
        
#         return filename
        
#     def save_to_excel(self, filename=None):
#         """Save the scraped job data to an Excel file"""
#         if not self.jobs_data:
#             print("No data to save")
#             return
            
#         if filename is None:
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             filename = f"linkedin_jobs_{timestamp}.xlsx"
            
#         df = pd.DataFrame(self.jobs_data)
#         df.to_excel(filename, index=False)
#         print(f"Data saved to {filename}")
        
#         return filename
    
import os
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
import traceback


class LinkedInJobScraper:
    def __init__(self, headless=True, slow_mode=True):
        """
        Enhanced LinkedIn Job Scraper (no login required)
        """
        self.headless = headless
        self.slow_mode = slow_mode
        self.driver = None
        self.jobs_data = []

        # Rotate user agents to reduce detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        ]

    # -------------------- WebDriver Setup --------------------
    def setup_driver(self):
        """Set up Selenium WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")

        # Anti-detection tweaks
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        self.driver = driver
        return driver

    def human_like_delay(self, min_seconds=1, max_seconds=3):
        """Simulate human-like random delays"""
        if self.slow_mode:
            time.sleep(random.uniform(min_seconds, max_seconds))

    # -------------------- Job Search --------------------
    def search_jobs(self, keywords, location, limit=25, experience_level=None, job_type=None):
        """
        Scrape LinkedIn job listings without login.
        Now collects detailed metadata and company info.
        """
        if self.driver is None:
            self.setup_driver()

        base_url = "https://www.linkedin.com/jobs/search/?"
        params = {
            "keywords": keywords.replace(" ", "%20"),
            "location": location.replace(" ", "%20"),
            "trk": "public_jobs_jobs-search-bar_search-submit",
        }
        url = base_url + "&".join([f"{key}={value}" for key, value in params.items()])

        print(f"\n🔍 Searching for '{keywords}' jobs in '{location}'")
        print(f"URL: {url}\n")

        try:
            self.driver.get(url)
            self.human_like_delay(3, 5)

            job_urls = []
            jobs_seen = set()
            last_height = 0

            # Scroll and collect job links
            while len(job_urls) < limit:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                job_cards = soup.select("div.job-search-card")

                for job in job_cards:
                    link_elem = job.select_one("a.base-card__full-link")
                    if not link_elem:
                        continue

                    job_url = link_elem.get("href").split("?")[0]
                    if job_url in jobs_seen:
                        continue
                    jobs_seen.add(job_url)

                    title_elem = job.select_one("h3.base-search-card__title")
                    company_elem = job.select_one("h4.base-search-card__subtitle")
                    location_elem = job.select_one("span.job-search-card__location")
                    time_elem = job.select_one("time")

                    job_data = {
                        "title": title_elem.text.strip() if title_elem else "N/A",
                        "company": company_elem.text.strip() if company_elem else "N/A",
                        "location": location_elem.text.strip() if location_elem else "N/A",
                        "posted_time": time_elem.text.strip() if time_elem else "N/A",
                        "job_url": job_url,
                    }

                    job_urls.append(job_data)
                    if len(job_urls) >= limit:
                        break

                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.human_like_delay(2, 4)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            print(f"🧭 Found {len(job_urls)} job listings. Fetching detailed info...\n")

            # Visit each job URL for full detail
            for i, job in enumerate(job_urls[:limit], start=1):
                try:
                    self.driver.get(job["job_url"])
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h1.topcard__title, h1.job-details-jobs-unified-top-card__job-title"))
                    )
                    self.human_like_delay(2, 4)

                    details = self.extract_job_details(self.driver)
                    job.update(details)

                    self.jobs_data.append(job)
                    print(f"✅ [{i}/{limit}] {job['title']} at {job['company']}")

                except Exception as e:
                    print(f"⚠️ Error fetching job details for {job.get('job_url')}: {e}")
                    traceback.print_exc()
                    continue

            df = pd.DataFrame(self.jobs_data)
            print(f"\n✅ Successfully scraped {len(df)} detailed jobs.\n")
            return df

        except Exception as e:
            print(f"❌ Error during scraping: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()

        finally:
            if self.driver:
                self.driver.quit()

    # -------------------- Extract Job Details --------------------
    def extract_job_details(self, driver):
        """Extract detailed job and company info"""
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Job Description
        desc_elem = soup.select_one(".show-more-less-html__markup")
        description = desc_elem.get_text("\n", strip=True) if desc_elem else "N/A"

        # Job Metadata
        job_criteria = soup.select(".description__job-criteria-text")
        criteria_labels = soup.select(".description__job-criteria-subheader")
        details = {}
        for label, value in zip(criteria_labels, job_criteria):
            details[label.get_text(strip=True)] = value.get_text(strip=True)

        # Company Info
        company_elem = soup.select_one(".topcard__org-name-link, .job-details-jobs-unified-top-card__company-name a")
        company_url = company_elem['href'] if company_elem and 'href' in company_elem.attrs else None

        company_logo_elem = soup.select_one(".artdeco-entity-image")
        company_logo = (
            company_logo_elem.get("data-delayed-url") or company_logo_elem.get("src")
            if company_logo_elem else None
        )

        company_about = ""
        company_stats = []
        if company_url:
            company_about_data = self.scrape_company_about(company_url)
            company_about = company_about_data.get("about", "")
            company_stats = company_about_data.get("company_stats", [])

        return {
            "description": description,
            "employment_type": details.get("Employment type", "N/A"),
            "seniority_level": details.get("Seniority level", "N/A"),
            "industries": details.get("Industries", "N/A"),
            "job_function": details.get("Job function", "N/A"),
            "company_url": company_url,
            "company_logo": company_logo,
            "company_about": company_about,
            "company_stats": "; ".join(company_stats),
        }

    # -------------------- Company About Page --------------------
    def scrape_company_about(self, company_url):
        """Scrape company's About section"""
        try:
            if not company_url:
                return {}

            if "linkedin.com" not in company_url:
                return {}

            self.driver.get(company_url + "about/")
            WebDriverWait(self.driver, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".org-top-card-summary-info-list__info-item"))
            )
            self.human_like_delay(2, 3)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            about_text = soup.select_one(".core-section-container__content p")
            about = about_text.get_text("\n", strip=True) if about_text else "N/A"

            stats = [li.get_text(strip=True) for li in soup.select(".org-top-card-summary-info-list__info-item")]
            return {"about": about, "company_stats": stats}

        except Exception:
            return {}

    # -------------------- Save Methods --------------------
    def save_to_csv(self, filename=None):
        if not self.jobs_data:
            return None
        if not filename:
            filename = f"linkedin_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        pd.DataFrame(self.jobs_data).to_csv(filename, index=False)
        return filename

    def save_to_excel(self, filename=None):
        if not self.jobs_data:
            return None
        if not filename:
            filename = f"linkedin_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        pd.DataFrame(self.jobs_data).to_excel(filename, index=False)
        return filename



# ```

# The key improvements in this new version are:

# 1. **Different scraping approach**: Instead of trying to click on job cards (which seems to be failing), the new approach:
#    - First extracts the direct URL for each job listing from the search results page
#    - Then visits each job URL directly to scrape the details

# 2. **Simplified selectors**: Focused on the specific selectors that were detected in your debug output (it found 60 job cards and 60 job titles)

# 3. **More robust error handling**: Better tracking of what's being extracted and what's failing

# Try replacing your `linkedin_job_scraper.py` file with this updated code and run it again with:
# ```
# python app.py -k "Python Developer" -l "Remote" --headless False