import random
import logging
import asyncio
from playwright.async_api import async_playwright

class NewsScraper:
    """
    A class to scrape news from JavaScript-rendered websites.
    Uses Playwright for browser automation with enhanced stealth settings.
    """

    def __init__(self, base_url):
        """
        Initializes the NewsScraper with a base URL.

        :param base_url: The base URL of the website to scrape.
        """
        self.base_url = base_url
        self.context = None
        self.browser = None
        self.page = None
        self._setup_logging()
        self.cookies = {}

    def _setup_logging(self):
        """Configure logging for the scraper"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    async def _initialize_browser(self, headless=True):
        """
        Initialize the Playwright browser instance with enhanced stealth settings.
        
        :param headless: Whether to run browser in headless mode
        """
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                ]
            )
            
            # Enhanced stealth settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                java_script_enabled=True,
                bypass_csp=True,
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'DNT': '1',
                }
            )

            # Add stealth scripts
            await self.context.add_init_script("""
                // Override properties that expose automation
                Object.defineProperty(navigator, 'webdriver', { get: () => false });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                
                // Add random mouse movements
                const originalQuery = document.querySelector;
                document.querySelector = (...args) => {
                    const result = originalQuery.apply(document, args);
                    if (result) {
                        const box = result.getBoundingClientRect();
                        const x = box.left + (Math.random() * box.width);
                        const y = box.top + (Math.random() * box.height);
                        window.dispatchEvent(new MouseEvent('mousemove', { clientX: x, clientY: y }));
                    }
                    return result;
                };
            """)
            
            self.page = await self.context.new_page()
            await self._setup_request_interception()

    async def _setup_request_interception(self):
        """Configure request interception with resource filtering"""
        await self.page.route("**/*", lambda route: self._handle_route(route))

    async def _handle_route(self, route):
        """
        Handle request interception with enhanced resource filtering
        and request headers modification.
        """
        request = route.request
        resource_type = request.resource_type
        
        # Block unnecessary resources to improve performance and stealth
        if resource_type in ['image', 'media', 'font', 'other']:
            await route.abort()
            return
            
        if resource_type in ['stylesheet', 'script']:
            if any(tracker in request.url for tracker in ['google-analytics', 'doubleclick', 'facebook']):
                await route.abort()
                return
        
        # Add randomized headers
        headers = {
            **request.headers,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
        }
        
        # Add cookies if available
        if self.cookies:
            headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in self.cookies.items()])
        
        await route.continue_(headers=headers)

    async def _load_cookies(self):
        """Load cookies from storage if available"""
        try:
            cookies = await self.page.context.cookies()
            self.cookies = {cookie['name']: cookie['value'] for cookie in cookies}
        except Exception as e:
            logging.warning(f"Failed to load cookies: {str(e)}")

    async def _save_cookies(self):
        """Save cookies after successful page load"""
        try:
            cookies = await self.page.context.cookies()
            self.cookies = {cookie['name']: cookie['value'] for cookie in cookies}
        except Exception as e:
            logging.warning(f"Failed to save cookies: {str(e)}")

    async def fetch_page(self, url_path, wait_for_selector=None, timeout=30000, retry_count=3, retry_delay=5):
        """
        Fetches the content of a JavaScript-rendered webpage with enhanced stealth.

        :param url_path: The path part of the URL to fetch (appended to base_url)
        :param wait_for_selector: CSS selector to wait for before considering page loaded
        :param timeout: Maximum time to wait for page load in milliseconds
        :param retry_count: Number of times to retry on failure
        :param retry_delay: Initial delay between retries in seconds
        :return: The page content after JavaScript execution
        """
        if not self.browser:
            await self._initialize_browser()

        full_url = f"{self.base_url}{url_path}"
        last_error = None

        for attempt in range(retry_count):
            try:
                # Add randomized delay between retries
                if attempt > 0:
                    jitter = random.uniform(0.1, 1.0)
                    await asyncio.sleep(retry_delay * (2 ** attempt) * jitter)
                
                # Load cookies from previous session if available
                await self._load_cookies()
                
                # Add random mouse movements and scrolling
                await self.page.evaluate("""
                    () => {
                        const randomScroll = () => {
                            window.scrollTo({
                                top: Math.random() * document.body.scrollHeight,
                                behavior: 'smooth'
                            });
                        };
                        setInterval(randomScroll, Math.random() * 1000 + 500);
                    }
                """)
                
                # Navigate to the page with stealth settings
                response = await self.page.goto(
                    full_url,
                    wait_until='networkidle',
                    timeout=timeout
                )
                
                if not response.ok:
                    raise Exception(f"Failed to load page: {response.status}")

                # Wait for specific content if selector provided
                if wait_for_selector:
                    await self.page.wait_for_selector(wait_for_selector, timeout=timeout)
                
                # Additional wait for dynamic content
                await self.page.wait_for_load_state('networkidle')
                
                # Add random human-like interactions
                await self.page.mouse.move(
                    x=random.randint(100, 700),
                    y=random.randint(100, 700)
                )
                
                # Random scroll
                await self.page.evaluate("""
                    window.scrollTo({
                        top: Math.random() * document.body.scrollHeight,
                        behavior: 'smooth'
                    });
                """)
                
                # Save cookies for future requests
                await self._save_cookies()
                
                # Get the rendered content
                content = await self.page.content()
                return content

            except Exception as e:
                last_error = e
                logging.warning(f"Attempt {attempt + 1}/{retry_count} failed: {str(e)}")
                
                # Reset browser context on error
                await self._reset_context()
                
                if attempt < retry_count - 1:
                    logging.info(f"Retrying in {retry_delay * (2 ** attempt)} seconds...")
                
        error_msg = f"Failed to fetch {full_url} after {retry_count} retries. Last error: {str(last_error)}"
        logging.error(error_msg)
        raise Exception(error_msg)

    async def _reset_context(self):
        """Reset the browser context while preserving cookies"""
        if self.context:
            # Save cookies before closing
            await self._save_cookies()
            await self.context.close()
            
            # Create new context with saved cookies
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            
            # Restore cookies
            if self.cookies:
                await self.context.add_cookies([
                    {'name': k, 'value': v, 'domain': self.base_url.split('//')[1], 'path': '/'}
                    for k, v in self.cookies.items()
                ])
            
            self.page = await self.context.new_page()
            await self._setup_request_interception()

    async def close(self):
        """Cleanup browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()


# Example usage
if __name__ == "__main__":
    async def main():
        base_url = "https://iinvest.cogencis.com"
        scraper = NewsScraper(base_url)
        
        try:
            # First visit homepage to establish cookies
            content = await scraper.fetch_page("/", timeout=60000)
            print("Successfully loaded homepage")
            
            # Then visit the target page
            content = await scraper.fetch_page(
                "/nifty/nsi/nifty/nifty-50",
                wait_for_selector="a.stock-title",
                timeout=60000
            )
            
            print("Successfully fetched the target page!")
            print(f"Content length: {len(content)} bytes")

            # return page content to be parsed with beautifulsoup
            return content



            # # get all the items with a.stock-title selector
            # items = await scraper.page.query_selector_all("a.stock-title")
            
            # for item in items:
            #     text = await item.inner_text()
            #     href = await item.get_attribute('href')
            #     print(f"Text: {text}, Link: {href}")
            
            
        except Exception as e:
            print(f"Failed to fetch page: {e}")
            logging.error(f"Error: {str(e)}")
            
        finally:
            await scraper.close()

    asyncio.run(main())