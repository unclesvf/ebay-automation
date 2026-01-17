"""
eBay Browser Automation Module
Uses Selenium to automate Chrome for eBay listing management
"""

import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from email_parser import EbayListingInfo


class EbayBrowser:
    """Browser automation for eBay listing management."""

    EBAY_LOGIN_URL = "https://signin.ebay.com"
    EBAY_SELLING_URL = "https://www.ebay.com/sh/lst/active"

    def __init__(self, headless: bool = False, profile_path: Optional[str] = None):
        """
        Initialize the browser.

        Args:
            headless: Run browser in headless mode (not recommended for eBay)
            profile_path: Path to Chrome profile to use existing session/cookies
        """
        self.driver = None
        self.headless = headless
        self.profile_path = profile_path
        self.wait_timeout = 10

    def start(self) -> bool:
        """Start the Chrome browser."""
        try:
            options = Options()

            if self.headless:
                options.add_argument("--headless")

            # Use existing Chrome profile if specified (keeps login sessions)
            if self.profile_path:
                options.add_argument(f"--user-data-dir={self.profile_path}")

            # Common options for stability
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-infobars")
            options.add_argument("--start-maximized")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            # Auto-download and use correct ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            # Reduce detection
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            return True

        except Exception as e:
            print(f"Failed to start browser: {e}")
            return False

    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def wait_for_element(self, by: By, value: str, timeout: int = None) -> Optional[any]:
        """Wait for an element to be present and return it."""
        timeout = timeout or self.wait_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None

    def wait_for_clickable(self, by: By, value: str, timeout: int = None) -> Optional[any]:
        """Wait for an element to be clickable and return it."""
        timeout = timeout or self.wait_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            return None

    def is_logged_in(self) -> bool:
        """Check if we're logged into eBay."""
        try:
            self.driver.get("https://www.ebay.com")
            time.sleep(2)

            # Look for sign-in indicators
            try:
                # If we find "Sign in" link prominently, we're not logged in
                sign_in = self.driver.find_element(By.LINK_TEXT, "Sign in")
                return False
            except NoSuchElementException:
                pass

            # Check for account menu or user greeting
            try:
                self.driver.find_element(By.ID, "gh-ug")
                return True
            except NoSuchElementException:
                pass

            return False

        except Exception as e:
            print(f"Error checking login status: {e}")
            return False

    def login(self, username: str = None, password: str = None) -> bool:
        """
        Navigate to eBay login page.
        If credentials provided, attempt auto-login.
        Otherwise, wait for manual login.
        """
        try:
            self.driver.get(self.EBAY_LOGIN_URL)
            time.sleep(2)

            if username and password:
                # Enter username
                user_input = self.wait_for_element(By.ID, "userid")
                if user_input:
                    user_input.clear()
                    user_input.send_keys(username)

                    # Click continue
                    continue_btn = self.wait_for_clickable(By.ID, "signin-continue-btn")
                    if continue_btn:
                        continue_btn.click()
                        time.sleep(2)

                        # Enter password
                        pass_input = self.wait_for_element(By.ID, "pass")
                        if pass_input:
                            pass_input.clear()
                            pass_input.send_keys(password)

                            # Click sign in
                            signin_btn = self.wait_for_clickable(By.ID, "sgnBt")
                            if signin_btn:
                                signin_btn.click()
                                time.sleep(3)
            else:
                print("\n" + "=" * 50)
                print("Please log in to eBay manually in the browser window.")
                print("Press Enter here when you're logged in...")
                print("=" * 50)
                input()

            # Verify login
            return self.is_logged_in()

        except Exception as e:
            print(f"Login error: {e}")
            return False

    def navigate_to_item(self, item_url: str) -> bool:
        """Navigate to an eBay item page."""
        try:
            self.driver.get(item_url)
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Error navigating to item: {e}")
            return False

    def get_item_revision_url(self, item_id: str) -> str:
        """Get the revision/edit URL for an item."""
        return f"https://www.ebay.com/lstng/{item_id}"

    def update_price(self, item_id: str, new_price: float) -> bool:
        """
        Update the price of an eBay listing.

        Args:
            item_id: eBay item ID
            new_price: New price to set

        Returns:
            True if successful
        """
        try:
            # Navigate to item revision page
            revision_url = self.get_item_revision_url(item_id)
            self.driver.get(revision_url)
            time.sleep(3)

            # Look for price input field
            # eBay's listing form can vary, so try multiple selectors
            price_selectors = [
                (By.NAME, "price"),
                (By.ID, "s0-1-1-24-7-@price-textbox"),
                (By.CSS_SELECTOR, "input[aria-label*='Price']"),
                (By.CSS_SELECTOR, "input[data-test-id='price-input']"),
                (By.XPATH, "//input[contains(@class, 'price')]"),
                (By.XPATH, "//label[contains(text(), 'Price')]/following::input[1]"),
            ]

            price_input = None
            for by, selector in price_selectors:
                try:
                    price_input = self.wait_for_element(by, selector, timeout=3)
                    if price_input:
                        break
                except:
                    continue

            if not price_input:
                print("Could not find price input field. Manual intervention needed.")
                print(f"Please update the price to ${new_price:.2f} manually.")
                input("Press Enter when done...")
                return True

            # Clear and enter new price
            price_input.clear()
            price_input.send_keys(str(new_price))
            time.sleep(1)

            # Look for save/update button
            save_selectors = [
                (By.XPATH, "//button[contains(text(), 'Update')]"),
                (By.XPATH, "//button[contains(text(), 'Save')]"),
                (By.XPATH, "//button[contains(text(), 'List item')]"),
                (By.CSS_SELECTOR, "button[data-test-id='submit-button']"),
            ]

            save_btn = None
            for by, selector in save_selectors:
                try:
                    save_btn = self.wait_for_clickable(by, selector, timeout=3)
                    if save_btn:
                        break
                except:
                    continue

            if save_btn:
                save_btn.click()
                time.sleep(3)
                print(f"Price updated to ${new_price:.2f}")
                return True
            else:
                print("Could not find save button. Please save manually.")
                input("Press Enter when done...")
                return True

        except Exception as e:
            print(f"Error updating price: {e}")
            return False

    def end_listing(self, item_id: str, reason: str = "OtherReason") -> bool:
        """
        End an eBay listing.

        Args:
            item_id: eBay item ID
            reason: Reason for ending (OtherReason, LostOrBroken, etc.)
        """
        try:
            # Navigate to end listing page
            end_url = f"https://www.ebay.com/bfl/end?item={item_id}"
            self.driver.get(end_url)
            time.sleep(3)

            print("Please complete ending the listing in the browser.")
            input("Press Enter when done...")
            return True

        except Exception as e:
            print(f"Error ending listing: {e}")
            return False

    def sell_similar(self, item_id: str, new_price: Optional[float] = None) -> bool:
        """
        Use Sell Similar to create a new listing based on an existing one.

        Args:
            item_id: eBay item ID to copy from
            new_price: Optional new price to set
        """
        try:
            # Navigate to sell similar page
            sell_similar_url = f"https://www.ebay.com/lstng/sl/{item_id}"
            self.driver.get(sell_similar_url)
            time.sleep(3)

            if new_price:
                # Try to update the price field
                print(f"Please verify the listing and update price to ${new_price:.2f} if needed.")
            else:
                print("Please review and complete the listing.")

            input("Press Enter when done...")
            return True

        except Exception as e:
            print(f"Error with sell similar: {e}")
            return False

    def process_listing(self, listing: EbayListingInfo) -> bool:
        """
        Process a listing based on the parsed action.

        Args:
            listing: EbayListingInfo object with item details and action
        """
        print(f"\n{'=' * 60}")
        print(f"Processing: {listing.item_title}")
        print(f"Item ID: {listing.item_id}")
        print(f"Action: {listing.action}")
        if listing.new_price:
            print(f"New Price: ${listing.new_price:.2f}")
        print(f"{'=' * 60}")

        if listing.action == 'update_price' and listing.new_price:
            return self.update_price(listing.item_id, listing.new_price)
        elif listing.action == 'end_listing':
            return self.end_listing(listing.item_id)
        elif listing.action == 'end_and_relist':
            if self.end_listing(listing.item_id):
                return self.sell_similar(listing.item_id, listing.new_price)
            return False
        elif listing.action == 'sell_similar':
            return self.sell_similar(listing.item_id, listing.new_price)
        else:
            print(f"Unknown action: {listing.action}")
            return False


def test_browser():
    """Test browser startup and eBay navigation."""
    browser = EbayBrowser()

    if browser.start():
        print("Browser started successfully")

        if browser.is_logged_in():
            print("Already logged into eBay")
        else:
            print("Not logged in, initiating login...")
            browser.login()

        input("Press Enter to close browser...")
        browser.close()
    else:
        print("Failed to start browser")


if __name__ == "__main__":
    test_browser()
