
import streamlit as st
import pandas as pd
import io
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_maps_data(keyword, scroll_times=30):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    driver.get("https://www.google.com/maps")
    wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))

    search_box = driver.find_element(By.ID, "searchboxinput")
    search_box.send_keys(keyword)
    wait.until(EC.element_to_be_clickable((By.ID, "searchbox-searchbutton"))).click()
    time.sleep(4)

    scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="main"]')

    old_count = 0
    for _ in range(scroll_times):
        driver.execute_script("arguments[0].scrollTop += arguments[0].scrollHeight", scrollable_div)
        time.sleep(1)
        results = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
        if len(results) == old_count:
            break
        old_count = len(results)

    results = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
    data = []

    for i, result in enumerate(results):
        try:
            actions = ActionChains(driver)
            actions.move_to_element(result).perform()
            result.click()
            time.sleep(1.2)  # rút ngắn thời gian

            name = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf").text

            try:
                addr = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]').get_attribute("aria-label").replace("Địa chỉ: ", "")
            except:
                addr = ""

            try:
                phone = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id^="phone"]').get_attribute("aria-label").replace("Số điện thoại: ", "")
            except:
                phone = ""

            if not phone:
                driver.back()
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.Nv2PK")))
                results = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
                continue

            try:
                open_hours = driver.find_element(By.CSS_SELECTOR, 'div[aria-label*="Thứ Hai"]').get_attribute("aria-label")
            except:
                open_hours = ""

            try:
                website = driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]').get_attribute("href")
            except:
                website = ""

            gmail = ""
            try:
                desc_divs = driver.find_elements(By.CSS_SELECTOR, "div[jsaction*='pane']")
                for div in desc_divs:
                    text = div.text
                    if "@gmail.com" in text:
                        gmail = [w for w in text.split() if "@gmail.com" in w][0]
                        break
            except:
                gmail = ""

            data.append({
                "Từ khóa": keyword,
                "Tên": name,
                "Địa chỉ": addr,
                "Số điện thoại": phone,
                "Giờ mở cửa": open_hours,
                "Website": website,
                "Gmail": gmail
            })

            driver.back()
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.Nv2PK")))
            results = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")

        except Exception as e:
            continue

    driver.quit()
    return pd.DataFrame(data)

# Giao diện Streamlit
st.set_page_config(page_title="Google Maps Scraper Nâng cấp", layout="wide")
st.title("📍 Google Maps Scraper Pro (Nhanh + Thông minh)")

keywords_input = st.text_area("🔍 Nhập nhiều từ khóa tìm kiếm (mỗi dòng 1 từ khóa)")
scroll_times = st.slider("🔁 Tối đa số lần cuộn Google Maps", min_value=5, max_value=50, value=20)

if st.button("🚀 Bắt đầu tìm kiếm"):
    if not keywords_input.strip():
        st.warning("⚠️ Vui lòng nhập ít nhất một từ khóa.")
    else:
        all_data = pd.DataFrame()
        keyword_list = [kw.strip() for kw in keywords_input.strip().split("\n") if kw.strip()]

        with st.spinner("⏳ Đang tìm kiếm và trích xuất dữ liệu..."):
            for kw in keyword_list:
                st.info(f"🔎 Đang tìm: {kw}")
                df = get_maps_data(kw, scroll_times)
                all_data = pd.concat([all_data, df], ignore_index=True)

        st.success(f"🎉 Đã tìm thấy {len(all_data)} kết quả có số điện thoại!")

        if not all_data.empty:
            st.dataframe(all_data)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                all_data.to_excel(writer, index=False)
            processed_data = output.getvalue()

            st.download_button(
                label="⬇️ Tải kết quả Excel",
                data=processed_data,
                file_name="ket_qua_maps_nhanh.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
