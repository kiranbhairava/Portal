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
#         Enhanced LinkedIn Job Scraper (no login required)
#         """
#         self.headless = headless
#         self.slow_mode = slow_mode
#         self.driver = None
#         self.jobs_data = []

#         # Rotate user agents to reduce detection
#         self.user_agents = [
#             'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#             'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15',
#             'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
#         ]

#     # -------------------- WebDriver Setup --------------------
#     def setup_driver(self):
#         """Set up Selenium WebDriver"""
#         chrome_options = Options()
#         if self.headless:
#             chrome_options.add_argument("--headless=new")
#         chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--disable-dev-shm-usage")
#         chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#         chrome_options.add_argument("--disable-extensions")
#         chrome_options.add_argument("--window-size=1920,1080")

#         # Anti-detection tweaks
#         chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#         chrome_options.add_experimental_option("useAutomationExtension", False)

#         service = Service(ChromeDriverManager().install())
#         driver = webdriver.Chrome(service=service, options=chrome_options)
#         driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
#             "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
#         })
#         self.driver = driver
#         return driver

#     def human_like_delay(self, min_seconds=1, max_seconds=3):
#         """Simulate human-like random delays"""
#         if self.slow_mode:
#             time.sleep(random.uniform(min_seconds, max_seconds))

#     # -------------------- Job Search --------------------
#     def search_jobs(self, keywords, location, limit=25, experience_level=None, job_type=None):
#         """
#         Scrape LinkedIn job listings without login.
#         Now collects detailed metadata and company info.
#         """
#         if self.driver is None:
#             self.setup_driver()

#         base_url = "https://www.linkedin.com/jobs/search/?"
#         params = {
#             "keywords": keywords.replace(" ", "%20"),
#             "location": location.replace(" ", "%20"),
#             "trk": "public_jobs_jobs-search-bar_search-submit",
#         }
#         url = base_url + "&".join([f"{key}={value}" for key, value in params.items()])

#         print(f"\n🔍 Searching for '{keywords}' jobs in '{location}'")
#         print(f"URL: {url}\n")

#         try:
#             self.driver.get(url)
#             self.human_like_delay(3, 5)

#             job_urls = []
#             jobs_seen = set()
#             last_height = 0

#             # Scroll and collect job links
#             while len(job_urls) < limit:
#                 soup = BeautifulSoup(self.driver.page_source, 'html.parser')
#                 job_cards = soup.select("div.job-search-card")

#                 for job in job_cards:
#                     link_elem = job.select_one("a.base-card__full-link")
#                     if not link_elem:
#                         continue

#                     job_url = link_elem.get("href").split("?")[0]
#                     if job_url in jobs_seen:
#                         continue
#                     jobs_seen.add(job_url)

#                     title_elem = job.select_one("h3.base-search-card__title")
#                     company_elem = job.select_one("h4.base-search-card__subtitle")
#                     location_elem = job.select_one("span.job-search-card__location")
#                     time_elem = job.select_one("time")

#                     job_data = {
#                         "title": title_elem.text.strip() if title_elem else "N/A",
#                         "company": company_elem.text.strip() if company_elem else "N/A",
#                         "location": location_elem.text.strip() if location_elem else "N/A",
#                         "posted_time": time_elem.text.strip() if time_elem else "N/A",
#                         "job_url": job_url,
#                     }

#                     job_urls.append(job_data)
#                     if len(job_urls) >= limit:
#                         break

#                 self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#                 self.human_like_delay(2, 4)
#                 new_height = self.driver.execute_script("return document.body.scrollHeight")
#                 if new_height == last_height:
#                     break
#                 last_height = new_height

#             print(f"🧭 Found {len(job_urls)} job listings. Fetching detailed info...\n")

#             # Visit each job URL for full detail
#             for i, job in enumerate(job_urls[:limit], start=1):
#                 try:
#                     self.driver.get(job["job_url"])
#                     WebDriverWait(self.driver, 10).until(
#                         EC.presence_of_element_located((By.CSS_SELECTOR, "h1.topcard__title, h1.job-details-jobs-unified-top-card__job-title"))
#                     )
#                     self.human_like_delay(2, 4)

#                     details = self.extract_job_details(self.driver)
#                     job.update(details)

#                     self.jobs_data.append(job)
#                     print(f"✅ [{i}/{limit}] {job['title']} at {job['company']}")

#                 except Exception as e:
#                     print(f"⚠️ Error fetching job details for {job.get('job_url')}: {e}")
#                     traceback.print_exc()
#                     continue

#             df = pd.DataFrame(self.jobs_data)
#             print(f"\n✅ Successfully scraped {len(df)} detailed jobs.\n")
#             return df

#         except Exception as e:
#             print(f"❌ Error during scraping: {str(e)}")
#             traceback.print_exc()
#             return pd.DataFrame()

#         finally:
#             if self.driver:
#                 self.driver.quit()

#     # -------------------- Extract Job Details --------------------
#     def extract_job_details(self, driver):
#         """Extract detailed job and company info"""
#         soup = BeautifulSoup(driver.page_source, "html.parser")

#         # Job Description
#         desc_elem = soup.select_one(".show-more-less-html__markup")
#         description = desc_elem.get_text("\n", strip=True) if desc_elem else "N/A"

#         # Job Metadata
#         job_criteria = soup.select(".description__job-criteria-text")
#         criteria_labels = soup.select(".description__job-criteria-subheader")
#         details = {}
#         for label, value in zip(criteria_labels, job_criteria):
#             details[label.get_text(strip=True)] = value.get_text(strip=True)

#         # Company Info
#         company_elem = soup.select_one(".topcard__org-name-link, .job-details-jobs-unified-top-card__company-name a")
#         company_url = company_elem['href'] if company_elem and 'href' in company_elem.attrs else None

#         company_logo_elem = soup.select_one(".artdeco-entity-image")
#         company_logo = (
#             company_logo_elem.get("data-delayed-url") or company_logo_elem.get("src")
#             if company_logo_elem else None
#         )

#         company_about = ""
#         company_stats = []
#         if company_url:
#             company_about_data = self.scrape_company_about(company_url)
#             company_about = company_about_data.get("about", "")
#             company_stats = company_about_data.get("company_stats", [])

#         return {
#             "description": description,
#             "employment_type": details.get("Employment type", "N/A"),
#             "seniority_level": details.get("Seniority level", "N/A"),
#             "industries": details.get("Industries", "N/A"),
#             "job_function": details.get("Job function", "N/A"),
#             "company_url": company_url,
#             "company_logo": company_logo,
#             "company_about": company_about,
#             "company_stats": "; ".join(company_stats),
#         }

#     # -------------------- Company About Page --------------------
#     def scrape_company_about(self, company_url):
#         """Scrape company's About section"""
#         try:
#             if not company_url:
#                 return {}

#             if "linkedin.com" not in company_url:
#                 return {}

#             self.driver.get(company_url + "about/")
#             WebDriverWait(self.driver, 6).until(
#                 EC.presence_of_element_located((By.CSS_SELECTOR, ".org-top-card-summary-info-list__info-item"))
#             )
#             self.human_like_delay(2, 3)

#             soup = BeautifulSoup(self.driver.page_source, "html.parser")
#             about_text = soup.select_one(".core-section-container__content p")
#             about = about_text.get_text("\n", strip=True) if about_text else "N/A"

#             stats = [li.get_text(strip=True) for li in soup.select(".org-top-card-summary-info-list__info-item")]
#             return {"about": about, "company_stats": stats}

#         except Exception:
#             return {}

#     # -------------------- Save Methods --------------------
#     def save_to_csv(self, filename=None):
#         if not self.jobs_data:
#             return None
#         if not filename:
#             filename = f"linkedin_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
#         pd.DataFrame(self.jobs_data).to_csv(filename, index=False)
#         return filename

#     def save_to_excel(self, filename=None):
#         if not self.jobs_data:
#             return None
#         if not filename:
#             filename = f"linkedin_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
#         pd.DataFrame(self.jobs_data).to_excel(filename, index=False)
#         return filename

##############################################################################################
import os
import time
import random
import pandas as pd
import re
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

    def extract_skills(self, description):
        """Extract technical skills from job description"""
        if not description:
            return []
        
        # Common tech skills to look for
        tech_skills = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue',
            'Node.js', 'Django', 'Flask', 'Spring', 'SQL', 'MongoDB', 'PostgreSQL',
            'AWS', 'Azure', 'Docker', 'Kubernetes', 'Git', 'Jenkins', 'CI/CD',
            'Machine Learning', 'Data Science', 'AI', 'TensorFlow', 'PyTorch',
            'HTML', 'CSS', 'REST API', 'GraphQL', 'Microservices', 'Agile', 'Scrum'
        ]
        
        found_skills = []
        description_lower = description.lower()
        
        for skill in tech_skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)
        
        return found_skills

    def extract_salary(self, description):
        """Extract salary information from description"""
        if not description:
            return "N/A"
        
        # Look for salary patterns
        salary_patterns = [
            r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:-|to)\s*₹?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(LPA|per\s*annum)',
            r'\$\s*(\d{1,3}(?:,\d{3})*)\s*(?:-|to)\s*\$?\s*(\d{1,3}(?:,\d{3})*)\s*(per\s*year|annually)',
            r'(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s*(LPA|lakhs)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return f"{match.group(1)} - {match.group(2)} {match.group(3)}"
        
        return "N/A"

    def extract_applicant_count(self, soup):
        """Extract number of applicants"""
        try:
            applicant_selectors = [
                ".num-applicants__caption",
                ".jobs-unified-top-card__applicant-count"
            ]
            
            for selector in applicant_selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    # Extract just the number
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        return f"{numbers[0]} applicants"
            
            return "N/A"
        except:
            return "N/A"

    # -------------------- Job Search --------------------
    def search_jobs(self, keywords, location, limit=25, experience_level=None, job_type=None):
        """
        Scrape LinkedIn job listings without login.
        Now collects detailed metadata and company info with IMPROVED accuracy.
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

            # Scroll and collect job links with IMPROVED selectors
            while len(job_urls) < limit:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # IMPROVED: Try multiple selectors for job cards
                job_cards = (soup.select("div.job-search-card") or 
                           soup.select("div.base-card") or 
                           soup.select("li.result-card"))

                for job in job_cards:
                    # IMPROVED: Try multiple selectors for job links
                    link_elem = (job.select_one("a.base-card__full-link") or
                               job.select_one("h3 a") or
                               job.select_one(".job-search-card__title a"))
                    
                    if not link_elem:
                        continue

                    job_url = link_elem.get("href").split("?")[0]
                    if job_url in jobs_seen:
                        continue
                    jobs_seen.add(job_url)

                    # IMPROVED: Try multiple selectors for job info
                    title_elem = (job.select_one("h3.base-search-card__title") or
                                job.select_one("h3") or 
                                job.select_one(".job-search-card__title"))
                    
                    company_elem = (job.select_one("h4.base-search-card__subtitle") or
                                  job.select_one("h4") or
                                  job.select_one(".job-search-card__subtitle"))
                    
                    location_elem = (job.select_one("span.job-search-card__location") or
                                   job.select_one(".base-search-card__location"))
                    
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
        """Extract detailed job and company info with IMPROVED data extraction"""
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # IMPROVED: Job Description with multiple selectors
        desc_selectors = [
            ".show-more-less-html__markup",
            ".jobs-description-content__text", 
            ".job-details-jobs-unified-top-card__job-description"
        ]
        
        description = "N/A"
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text("\n", strip=True)
                break

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

        # IMPROVED: Extract additional data
        skills = self.extract_skills(description)
        salary_info = self.extract_salary(description)
        applicant_count = self.extract_applicant_count(soup)

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
            # NEW IMPROVED FIELDS:
            "extracted_skills": ", ".join(skills) if skills else "N/A",
            "salary_range": salary_info,
            "applicant_count": applicant_count,
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


# Test the improved scraper
if __name__ == "__main__":
    scraper = LinkedInJobScraper(headless=False, slow_mode=True)
    
    try:
        df = scraper.search_jobs(
            keywords="Python Developer",
            location="Bangalore, India",
            limit=5
        )
        
        if not df.empty:
            print(f"\n✅ Successfully scraped {len(df)} jobs!")
            
            # Show enhanced data
            jobs_with_skills = df[df['extracted_skills'] != 'N/A']
            jobs_with_salary = df[df['salary_range'] != 'N/A']
            
            print(f"\n📊 IMPROVED Data Quality:")
            print(f"  - Jobs with skills: {len(jobs_with_skills)}/{len(df)}")
            print(f"  - Jobs with salary: {len(jobs_with_salary)}/{len(df)}")
            
            # Save files
            csv_file = scraper.save_to_csv()
            excel_file = scraper.save_to_excel()
            print(f"\n💾 Files saved: {csv_file}, {excel_file}")
            
            # Show sample data
            print(f"\n📋 Sample Jobs with IMPROVED data:")
            for i, job in enumerate(df.head(3).itertuples(), 1):
                print(f"\n{i}. {job.title} at {job.company}")
                if hasattr(job, 'extracted_skills') and job.extracted_skills != 'N/A':
                    print(f"   🔧 Skills: {job.extracted_skills}")
                if hasattr(job, 'salary_range') and job.salary_range != 'N/A':
                    print(f"   💰 Salary: {job.salary_range}")
                if hasattr(job, 'applicant_count') and job.applicant_count != 'N/A':
                    print(f"   👥 Applicants: {job.applicant_count}")
                
        else:
            print("❌ No jobs found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
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