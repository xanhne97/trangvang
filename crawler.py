import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

base_url = "https://trangvangvietnam.com"

# Hàm lấy tổng số trang trong kết quả tìm kiếm
def get_total_pages(soup):
    paging_div = soup.select_one("#paging")
    if not paging_div:
        return 1
    page_links = paging_div.select("a[href*='?page=']")
    page_numbers = [int(a.text.strip()) for a in page_links if a.text.strip().isdigit()]
    return max(page_numbers) if page_numbers else 1

# Hàm tải nội dung trang bằng Selenium
def get_page_html_with_selenium(url, driver):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.listings_center, div.listings_center_khongxacthuc"))
        )
        return driver.page_source
    except Exception as e:
        print(f"❌ Lỗi khi tải trang: {url}\n   → {e}")
        return ""

# Hàm lấy thông tin công ty theo ngành
def get_companies_in_industry(industry_name, industry_url):
    print(f"📂 Đang crawl ngành: {industry_name}")
    results = []

    # Cấu hình WebDriver cho Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    html = get_page_html_with_selenium(industry_url, driver)
    if not html:
        driver.quit()
        return results

    soup = BeautifulSoup(html, "html.parser")
    total_pages = get_total_pages(soup)

    # Duyệt qua các trang
    for page in range(1, total_pages + 1):
        page_url = f"{industry_url}?page={page}"
        html = get_page_html_with_selenium(page_url, driver)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        company_wrappers = soup.select("div.w-100.h-auto.shadow.rounded-3.bg-white")

        for company in company_wrappers:
            try:
                name_tag = company.select_one(".listings_center h2 a, .listings_center_khongxacthuc h2 a")
                name = name_tag.text.strip() if name_tag else ""
                detail_link = name_tag["href"] if name_tag else ""

                industry_tag = company.select_one(".nganh_listing_txt")
                industry = industry_tag.text.strip() if industry_tag else ""

                address_tag = company.select_one(".logo_congty_diachi div:nth-of-type(2) small")
                address = address_tag.text.strip() if address_tag else ""

                phones = [a.text.strip() for a in company.select("a[href^='tel']")]
                phone = phones[0] if phones else ""
                hotline = phones[1] if len(phones) > 1 else ""

                email_tag = company.select_one("a[href^='mailto']")
                email = email_tag["href"].replace("mailto:", "") if email_tag else ""

                website_tag = company.select_one("a[href^='http']:not([href*='trangvangvietnam'])")
                website = website_tag["href"] if website_tag else ""

                tax_branch_tag = company.select_one(".logo_congty_diachi div:nth-last-of-type(1)")
                tax_branch = tax_branch_tag.text.strip() if tax_branch_tag else ""

                desc_tag = company.select_one(".text_qc")
                description = desc_tag.text.strip().replace("\n", " ").replace("  ", " ") if desc_tag else ""

                logo_tag = company.select_one(".logo_congty img")
                logo_url = logo_tag["src"] if logo_tag else ""

                img_tag = company.select_one(".big_image img")
                image_url = img_tag["src"] if img_tag else ""

                results.append({
                    "Tên công ty": name,
                    "Ngành nghề": industry,
                    "Địa chỉ": address,
                    "Điện thoại": phone,
                    "Hotline": hotline,
                    "Email": email,
                    "Website": website,
                    "Mã số thuế & Chi nhánh": tax_branch,
                    "Mô tả": description,
                    "Logo": logo_url,
                    "Ảnh đại diện": image_url,
                    "Chi tiết": base_url + detail_link
                })
            except Exception as e:
                print(f"❌ Lỗi khi xử lý 1 công ty: {e}")
                continue

    driver.quit()
    print(f"✅ Đã crawl {len(results)} công ty trong ngành '{industry_name}'")
    return results

# Hàm lưu dữ liệu vào file Excel
def save_to_excel(data, filename="trangvang_data.xlsx"):
    if not data:
        print("⚠️ Không có dữ liệu để lưu.")
        return
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"📁 Đã lưu file Excel: {filename}")
