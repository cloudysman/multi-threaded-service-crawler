import time
import json
import os
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
import threading
import queue

class ServiceWorker:
    """Worker class to handle individual service extraction with its own WebDriver instance"""
    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.init_driver()
        
    def init_driver(self):
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize the WebDriver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 10)
    
    def extract_service_detail_popup(self, service_title):
        """Extract detailed information from the popup window"""
        try:
            # Wait for popup to be visible and extract data
            popup = self.wait.until(EC.visibility_of_element_located((By.ID, "popupChitietTTHC")))
            
            # Extract additional information from popup
            popup_data = {}
            
            # Extract procedure code
            try:
                procedure_code_row = popup.find_element(By.XPATH, ".//div[contains(@class, 'info-row')][1]")
                procedure_code = procedure_code_row.find_element(By.XPATH, ".//div[2]").text.strip()
                popup_data["Mã thủ tục"] = procedure_code
            except NoSuchElementException:
                popup_data["Mã thủ tục"] = ""
            
            # Extract decision number
            try:
                decision_row = popup.find_element(By.XPATH, ".//div[contains(@class, 'info-row')][2]")
                decision_number = decision_row.find_element(By.XPATH, ".//div[2]").text.strip()
                popup_data["Số quyết định"] = decision_number
            except NoSuchElementException:
                popup_data["Số quyết định"] = ""
            
            # Extract implementation level
            try:
                level_row = popup.find_element(By.XPATH, ".//div[contains(@class, 'info-row')][4]")
                level = level_row.find_element(By.XPATH, ".//div[2]").text.strip()
                popup_data["Cấp thực hiện"] = level
            except NoSuchElementException:
                popup_data["Cấp thực hiện"] = ""
            
            # Extract procedure type
            try:
                type_row = popup.find_element(By.XPATH, ".//div[contains(@class, 'info-row')][5]")
                proc_type = type_row.find_element(By.XPATH, ".//div[2]").text.strip()
                popup_data["Loại thủ tục"] = proc_type
            except NoSuchElementException:
                popup_data["Loại thủ tục"] = ""
            
            # Extract field
            try:
                field_row = popup.find_element(By.XPATH, ".//div[contains(@class, 'info-row')][6]")
                field = field_row.find_element(By.XPATH, ".//div[2]").text.strip()
                popup_data["Lĩnh vực"] = field
            except NoSuchElementException:
                popup_data["Lĩnh vực"] = ""
            
            # Extract subject
            try:
                subject_row = popup.find_element(By.XPATH, ".//div[contains(@class, 'info-row')][contains(.//div[1], 'Đối tượng thực hiện')]")
                subject = subject_row.find_element(By.XPATH, ".//div[2]").text.strip()
                popup_data["Đối tượng thực hiện"] = subject
            except NoSuchElementException:
                popup_data["Đối tượng thực hiện"] = ""
            
            # Extract implementing agency
            try:
                agency_row = popup.find_element(By.XPATH, ".//div[contains(@class, 'info-row')][contains(.//div[1], 'Cơ quan thực hiện')]")
                agency = agency_row.find_element(By.XPATH, ".//div[2]").text.strip()
                popup_data["Cơ quan thực hiện"] = agency
            except NoSuchElementException:
                popup_data["Cơ quan thực hiện"] = ""
            
            # Extract authorized agency
            try:
                authorized_row = popup.find_element(By.XPATH, ".//div[contains(@class, 'info-row')][contains(.//div[1], 'Cơ quan có thẩm quyền')]")
                authorized = authorized_row.find_element(By.XPATH, ".//div[2]").text.strip()
                popup_data["Cơ quan có thẩm quyền"] = authorized
            except NoSuchElementException:
                popup_data["Cơ quan có thẩm quyền"] = ""
            
            # Extract result
            try:
                result_row = popup.find_element(By.XPATH, ".//div[contains(@class, 'info-row')][contains(.//div[1], 'Kết quả thực hiện')]")
                result = result_row.find_element(By.XPATH, ".//div[2]").text.strip()
                popup_data["Kết quả thực hiện"] = result
            except NoSuchElementException:
                popup_data["Kết quả thực hiện"] = ""
                
            # Extract legal basis
            try:
                legal_basis_rows = popup.find_elements(By.XPATH, ".//div[contains(@class, 'info-row')][contains(.//div[1], 'Căn cứ pháp lý')]//table//tbody//tr")
                legal_basis_list = []
                for row in legal_basis_rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:
                            doc_number = cells[0].text.strip()
                            doc_title = cells[1].text.strip()
                            doc_date = cells[2].text.strip()
                            agency = cells[3].text.strip() if len(cells) > 3 else ""
                            legal_basis_list.append({
                                "Số ký hiệu": doc_number,
                                "Trích yếu": doc_title,
                                "Ngày ban hành": doc_date,
                                "Cơ quan ban hành": agency
                            })
                    except Exception as e:
                        continue
                popup_data["Căn cứ pháp lý"] = legal_basis_list
            except Exception as e:
                popup_data["Căn cứ pháp lý"] = []
            
            # Close the popup
            try:
                close_button = popup.find_element(By.XPATH, ".//div[@class='close']//span[@class='-ap icon icon-close']")
                close_button.click()
                time.sleep(1)
            except Exception as e:
                print(f"Could not close popup for {service_title}: {e}")
                # Try to click elsewhere or press ESC
                try:
                    self.driver.find_element(By.TAG_NAME, "body").send_keys('\ue00c')  # ESC key
                    time.sleep(1)
                except:
                    pass
            
            return popup_data
            
        except Exception as e:
            print(f"Error extracting popup details for {service_title}: {e}")
            return {}

    def extract_service_details(self, service_url):
        """Extract detailed information for a specific service"""
        try:
            self.driver.get(service_url)
            time.sleep(2)  # Wait for page to load
            
            # Get service title
            service_title = self.driver.find_element(By.CSS_SELECTOR, "h1.main-title.-none").text.strip()
            
            # Initialize service data
            service_data = {
                "title": service_title,
                "url": service_url,
                "details": {}
            }
            
            # Click "Xem chi tiết" to open popup
            try:
                detail_link = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.url[data-toggle='modal']")))
                detail_link.click()
                time.sleep(2)  # Wait for popup to load
                
                # Extract data from popup
                popup_data = self.extract_service_detail_popup(service_title)
                service_data["meta"] = popup_data
            except (TimeoutException, ElementClickInterceptedException) as e:
                print(f"Could not open detail popup for {service_title}: {e}")
                service_data["meta"] = {}
            
            # Extract "Trình tự thực hiện"
            try:
                trinh_tu_element = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'Trình tự thực hiện')]/following-sibling::div")
                trinh_tu_content = trinh_tu_element.text.strip()
                service_data["details"]["Trình tự thực hiện"] = trinh_tu_content
            except NoSuchElementException:
                service_data["details"]["Trình tự thực hiện"] = ""
            
            # Extract "Cách thức thực hiện"
            try:
                cach_thuc_element = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'Cách thức thực hiện')]/following-sibling::table")
                cach_thuc_content = cach_thuc_element.text.strip()
                service_data["details"]["Cách thức thực hiện"] = cach_thuc_content
            except NoSuchElementException:
                service_data["details"]["Cách thức thực hiện"] = ""
            
            # Extract "Thành phần hồ sơ"
            try:
                thanh_phan_element = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'Thành phần hồ sơ')]/following-sibling::div[@class='list-expand']")
                thanh_phan_content = thanh_phan_element.text.strip()
                service_data["details"]["Thành phần hồ sơ"] = thanh_phan_content
            except NoSuchElementException:
                service_data["details"]["Thành phần hồ sơ"] = ""
            
            # Extract "Giấy tờ phải nộp"
            try:
                # Find all list-expand divs in the "Thành phần hồ sơ" section
                ho_so_items = self.driver.find_elements(By.XPATH, "//h2[contains(text(), 'Thành phần hồ sơ')]/following-sibling::div[@class='list-expand']/div[@class='item']")
                for item in ho_so_items:
                    title_element = item.find_element(By.XPATH, ".//div[@class='title']")
                    title_text = title_element.text.strip()
                    if "Giấy tờ phải nộp" in title_text:
                        content_element = item.find_element(By.XPATH, ".//div[@class='content']")
                        content_text = content_element.text.strip()
                        service_data["details"]["Giấy tờ phải nộp"] = content_text
                        break
            except NoSuchElementException:
                service_data["details"]["Giấy tờ phải nộp"] = ""
            
            # Extract "Giấy tờ phải xuất trình"
            try:
                ho_so_items = self.driver.find_elements(By.XPATH, "//h2[contains(text(), 'Thành phần hồ sơ')]/following-sibling::div[@class='list-expand']/div[@class='item']")
                for item in ho_so_items:
                    title_element = item.find_element(By.XPATH, ".//div[@class='title']")
                    title_text = title_element.text.strip()
                    if "Giấy tờ phải xuất trình" in title_text:
                        content_element = item.find_element(By.XPATH, ".//div[@class='content']")
                        content_text = content_element.text.strip()
                        service_data["details"]["Giấy tờ phải xuất trình"] = content_text
                        break
            except NoSuchElementException:
                service_data["details"]["Giấy tờ phải xuất trình"] = ""
            
            # Extract "Lưu ý"
            try:
                ho_so_items = self.driver.find_elements(By.XPATH, "//h2[contains(text(), 'Thành phần hồ sơ')]/following-sibling::div[@class='list-expand']/div[@class='item']")
                for item in ho_so_items:
                    title_element = item.find_element(By.XPATH, ".//div[@class='title']")
                    title_text = title_element.text.strip()
                    if "Lưu ý" in title_text:
                        content_element = item.find_element(By.XPATH, ".//div[@class='content']")
                        content_text = content_element.text.strip()
                        service_data["details"]["Lưu ý"] = content_text
                        break
            except NoSuchElementException:
                service_data["details"]["Lưu ý"] = ""
            
            # Extract "Cơ quan thực hiện"
            try:
                co_quan_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'item')]/div[contains(@class, 'title') and contains(text(), 'Cơ quan thực hiện')]/following-sibling::div[@class='content']/div[@class='article']")
                co_quan_content = co_quan_element.text.strip()
                service_data["details"]["Cơ quan thực hiện"] = co_quan_content
            except NoSuchElementException:
                try:
                    # Alternative way to find the element
                    co_quan_element = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'Cơ quan thực hiện')]/following-sibling::div[@class='article']")
                    co_quan_content = co_quan_element.text.strip()
                    service_data["details"]["Cơ quan thực hiện"] = co_quan_content
                except NoSuchElementException:
                    service_data["details"]["Cơ quan thực hiện"] = ""
            
            # Extract "Yêu cầu, điều kiện thực hiện"
            try:
                yeu_cau_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'item')]/div[contains(@class, 'title') and contains(text(), 'Yêu cầu, điều kiện')]/following-sibling::div[@class='content']/div[@class='article cls-requires']")
                yeu_cau_content = yeu_cau_element.text.strip()
                service_data["details"]["Yêu cầu, điều kiện thực hiện"] = yeu_cau_content
            except NoSuchElementException:
                try:
                    # Alternative way to find the element
                    yeu_cau_element = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'Yêu cầu, điều kiện thực hiện')]/following-sibling::div[@class='article']")
                    yeu_cau_content = yeu_cau_element.text.strip()
                    service_data["details"]["Yêu cầu, điều kiện thực hiện"] = yeu_cau_content
                except NoSuchElementException:
                    service_data["details"]["Yêu cầu, điều kiện thực hiện"] = ""
            
            print(f"Worker {self.worker_id}: Extracted details for: {service_title}")
            return service_data
            
        except Exception as e:
            print(f"Worker {self.worker_id}: Error extracting service details: {e}")
            return None
    
    def close(self):
        """Close the WebDriver"""
        if hasattr(self, 'driver'):
            self.driver.quit()


class HoaBinhServiceCrawler:
    def __init__(self, max_workers=4):
        self.base_url = "https://dichvucong.gov.vn/p/home/dvc-dich-vu-cong-truc-tuyen-ds.html?pCoQuanId=387628"
        self.data = []
        self.max_workers = max_workers  # Số lượng worker tối đa
        self.data_lock = threading.Lock()  # Lock để bảo vệ việc ghi dữ liệu
        self.total_records = 0
        
        # Khởi tạo driver chính để quét toàn bộ danh sách
        self.init_main_driver()
        
    def init_main_driver(self):
        """Initialize the main WebDriver for pagination and link collection"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 10)
        
    def navigate_to_page(self, page_number):
        """Navigate to a specific page number"""
        try:
            script = f"doSearch({page_number});"
            self.driver.execute_script(script)
            
            # Đợi đủ thời gian để trang tải dữ liệu qua AJAX
            time.sleep(5)
            
            # Xác minh rằng trang đã thay đổi
            try:
                active_page = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".pagination .active"))
                )
                if active_page.text.strip() == str(page_number):
                    print(f"Đã chuyển thành công đến trang {page_number}")
                    return True
                else:
                    print(f"Trang hiện tại là {active_page.text} thay vì {page_number}")
            except:
                pass
                
            # Kiểm tra xem danh sách dịch vụ có được tải không
            service_elements = self.driver.find_elements(By.CSS_SELECTOR, "ul.list-document li a")
            if service_elements:
                print(f"Tìm thấy {len(service_elements)} dịch vụ trên trang {page_number}")
                return True
            else:
                print(f"Không tìm thấy dịch vụ nào trên trang {page_number}")
                return False
                
        except Exception as e:
            print(f"Lỗi khi chuyển đến trang {page_number}: {e}")
            return False
            
    def get_service_links(self):
        """Get all service links on the current page"""
        try:
            service_elements = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.list-document li a"))
            )
            return [element.get_attribute("href") for element in service_elements]
        except TimeoutException:
            print("Could not find service links on current page")
            return []
            
    def get_total_pages(self):
        """Get the total number of pages"""
        try:
            # Find the text showing total records
            total_records_text = self.driver.find_element(By.XPATH, "//span[@id='totalRecord']").text
            # Extract the total number of records
            self.total_records = int(total_records_text)
            # Calculate total pages (assuming 50 records per page)
            records_per_page = int(self.driver.find_element(By.CSS_SELECTOR, "#pageSize").get_attribute("value"))
            total_pages = (self.total_records + records_per_page - 1) // records_per_page
            return total_pages
        except Exception as e:
            print(f"Error getting total pages: {e}")
            return 0
    
    def process_service_batch(self, service_links, page_number):
        """Process a batch of service links with multiple threads"""
        # Tạo queue chứa các service links
        service_queue = queue.Queue()
        for link in service_links:
            service_queue.put(link)
        
        # Khởi tạo list để lưu trữ result của mỗi thread
        results = []
        
        # Tạo và khởi động các worker threads
        threads = []
        workers = []
        
        for i in range(min(self.max_workers, len(service_links))):
            worker = ServiceWorker(i)
            workers.append(worker)
            
            thread = threading.Thread(
                target=self.worker_thread_function,
                args=(worker, service_queue, results)
            )
            thread.daemon = True
            threads.append(thread)
            thread.start()
        
        # Đợi tất cả các thread hoàn thành
        for thread in threads:
            thread.join()
            
        # Đóng tất cả các worker
        for worker in workers:
            worker.close()
            
        # Thêm kết quả vào danh sách dữ liệu chính
        with self.data_lock:
            self.data.extend(results)
            
        # Lưu dữ liệu trang hiện tại
        self.save_data(f"hoabinh_services_page_{page_number}.json", results)
        
        return len(results)
        
    def worker_thread_function(self, worker, service_queue, results):
        """Function executed by each worker thread"""
        while not service_queue.empty():
            try:
                # Lấy service link từ queue
                link = service_queue.get(block=False)
                
                # Trích xuất thông tin chi tiết
                service_data = worker.extract_service_details(link)
                
                # Nếu trích xuất thành công, thêm vào danh sách kết quả
                if service_data:
                    results.append(service_data)
                    
                # Đánh dấu task đã hoàn thành
                service_queue.task_done()
                
            except queue.Empty:
                break
            except Exception as e:
                print(f"Error in worker thread: {e}")
                try:
                    service_queue.task_done()
                except:
                    pass
    
    def crawl(self):
        """Main crawling function"""
        try:
            # Truy cập trang và thiết lập kích thước trang
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Thiết lập kích thước trang và lấy tổng số trang
            page_size_select = self.driver.find_element(By.CSS_SELECTOR, "#pageSize")
            for option in page_size_select.find_elements(By.TAG_NAME, "option"):
                if option.text == "50":
                    option.click()
                    time.sleep(2)
                    break
            
            total_pages = self.get_total_pages()
            print(f"Total records: {self.total_records}, Total pages: {total_pages}")
            
            # Lặp qua từng trang và xử lý
            for page in range(1, total_pages + 1):
                print(f"Processing page {page} of {total_pages}")
                
                if page > 1:
                    # Điều hướng đến trang tiếp theo
                    self.navigate_to_page(page)
                
                # Lấy danh sách các link dịch vụ
                service_links = self.get_service_links()
                print(f"Found {len(service_links)} services on page {page}")
                
                if service_links:
                    # Xử lý các link song song với nhiều thread
                    processed_count = self.process_service_batch(service_links, page)
                    print(f"Processed {processed_count} services from page {page}")
                
                # Lưu dữ liệu đã thu thập được cho đến hiện tại
                self.save_data("hoabinh_services_current.json")
            
            # Lưu kết quả cuối cùng
            self.save_data("hoabinh_services_complete.json")
            print(f"Crawling completed. Total services extracted: {len(self.data)}")
            
        except Exception as e:
            print(f"Error during crawling: {e}")
        finally:
            self.driver.quit()
            
    def save_data(self, filename, data_to_save=None):
        """Save the crawled data to a JSON file"""
        with self.data_lock:
            data_to_write = data_to_save if data_to_save is not None else self.data
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_write, f, ensure_ascii=False, indent=4)
            print(f"Data saved to {filename}")
        
if __name__ == "__main__":
    # Sử dụng 4 luồng song song, có thể thay đổi tùy theo số lõi CPU và băng thông mạng
    crawler = HoaBinhServiceCrawler(max_workers=4)
    crawler.crawl()