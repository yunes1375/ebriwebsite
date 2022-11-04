import csv
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import shutil
import os
from bs4 import BeautifulSoup
from datetime import datetime
from twocaptcha import TwoCaptcha
import undetected_chromedriver as uc
import pymongo
import random
from furl import furl

if __name__ == '__main__':
    driver = uc.Chrome()
    links_screen=driver.current_window_handle
    driver.execute_script("window.open()")
    links_screen = driver.window_handles[0]
    images_screen = driver.window_handles[1]
    driver.switch_to.window(links_screen)
    def images_link_extractor(driver, images_url, tries):
        driver.get(images_url)
        try:
            time.sleep(10)
            images_page_soup = BeautifulSoup(driver.page_source, "html.parser")
            images_links_divs = images_page_soup.find_all("li", {"class": "grid-gallery-item"})
            images_links = []
            for image_link_div in images_links_divs:
                if image_link_div.find("img")['src']:
                    images_links.append(image_link_div.find("img")['src'])
                else:
                    print('("img") error')
            return "extracted", images_links, tries
        except Exception as e:
            print(e)
            if "validate.perfdrive.com" in driver.current_url:
                try:
                    captcha_solver(driver)
                    print("captcha_solved", [], tries + 1)
                    return "captcha_solved", [], tries + 1
                except Exception as e:
                    print(e)
                    print("captcha_error", [], tries + 1)
                    return "captcha_error", [], tries + 1
            else:
                print("error", [], tries + 1)
                return "error", [], tries + 1


    def images_downloader(images_links, add_number):
        counter = 1
        downloaded_images = []
        for link in images_links:
            r = requests.get(
                url=link,
                stream=True,
                timeout=15
            )
            if r.status_code == 200:
                customer_floder = os.path.join('./images')
                if not os.path.isdir(customer_floder):
                    os.mkdir(customer_floder)
                main_source_path = customer_floder + '/' + str(add_number) + "_" + str(counter) + '.jpg'
                with open(main_source_path, 'wb') as out_file:
                    shutil.copyfileobj(r.raw, out_file)
                downloaded_images.append(main_source_path)
                counter = counter + 1
        return downloaded_images


    def csv_reader():
        with open("./links.csv", 'r', encoding="utf-8") as file:
            csvreader = csv.reader(file)
            links = {}
            row_counter = 1
            for row in csvreader:
                links[row_counter] = row[0]
                row_counter += 1
        links_situation = {}
        for key in links.keys():
            links_situation[key] = False
        return links,links_situation


    def mongo_result_checker(result):
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["scraping"]
        mycol = mydb["adds"]
        myquery = {"ad_number": result['ad_number']}
        mydoc = mycol.find_one(myquery)
        if mydoc == None:
            print("False")
            return False
        else:
            print("True")
            return True
    def mongo_id_checker(item_id):
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["scraping"]
        mycol = mydb["adds"]
        myquery = {"item_id": item_id}
        mydoc = mycol.find_one(myquery)
        if mydoc == None:
            return False
        else:
            return True
    def mongo_inserter(result):
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["scraping"]
        mycol = mydb["adds"]
        mydict = result
        if mongo_result_checker(result) == False:
            mycol.insert_one(mydict)
            print("inserted")
        else:
            print("absent")


    def captcha_solver(driver):
        print("started captcha solver")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        solver = TwoCaptcha('75964407b715857c698dae97ccdcd332')
        url = soup.find("div", {"class": "h-captcha"}).iframe['src']
        sitekey = soup.find("div", {"class": "h-captcha"})['data-sitekey']
        print(sitekey, url)
        try:
            captcha_result = solver.hcaptcha(
                sitekey=sitekey,
                url=url)
            print("response recieved")
            _id = soup.find("textarea", {"name": "h-captcha-response"})['id']
            code = captcha_result['code']
            print("code")
            driver.execute_script("document.getElementById(" + "'" + _id + "'" + ").innerHTML =" + "'" + code + "'")
            try:
                driver.find_element("css selector",
                                    "body > div.wrapper > div > div:nth-child(2) > div > form > center > input").click()
                print("clicked")
            except Exception as e:
                print(e)
                pass
        except Exception as e:
            print(e)
            return ("failed")
    def data_exteactor(result,opened_section_soup,images_url):
            if opened_section_soup.find("div", {"class": "price"}):
                try:
                    price = opened_section_soup.find("div", {"class": "price"}).text.strip()
                    result['price'] = price
                    print(price)
                except:
                    print("149")
            if opened_section_soup.find("div",{"class":"info_items"}):
                info_items_section=opened_section_soup.find("div",{"class":"info_items"})
                if info_items_section.find("dl",{"class":"info_item"}):
                    info_items=info_items_section.find_all("dl",{"class":"info_item"})
                    for info_item in info_items:
                        if info_item.find("dd").text.strip() and info_item.find("dt").text.strip():
                            result[info_item.find("dt").text.strip()]=info_item.find("dd").text.strip()
                            print("doneeee")
            if opened_section_soup.find("div", {"class": "right_col"}):
                try:
                    right_col = opened_section_soup.find("div", {"class": "right_col"})
                    title = right_col.find("span", {"class": "title"}).text.strip()
                    result['title'] = title
                except:
                    print("156")
            if right_col.find("span", {"class": "subtitle"}):
                try:
                    subtitle = right_col.find("span", {"class": "subtitle"}).text.strip()
                    result['subtitle'] = subtitle
                except:
                    print("162")
            if opened_section_soup.find("div", {"class": "middle_col"}):
                middle_col = opened_section_soup.find("div", {"class": "middle_col"})
                middle_col_options = middle_col.find_all("div")
            if opened_section_soup.find("div", {"class": "profitability_container"}):
                profitable_cols=opened_section_soup.find_all("div", {"class": "info_container"})
                trade_arrays=[]
                try:
                    for profitable_col in profitable_cols:
                        profitable_options=profitable_col.find_all("span",{"class":"details_fields"})
                        trade_result={}
                        if profitable_options[0]:
                            trade_result['date']=profitable_options[0].text.strip()
                        if profitable_options[1]:
                            trade_result['address'] = profitable_options[1].text.strip()
                        if profitable_options[2]:
                            trade_result['rooms'] = profitable_options[2].text.strip()
                        if profitable_options[3]:
                            trade_result['price'] = profitable_options[3].text.strip()
                        trade_arrays.append(trade_result)
                except: 
                    print("183")
                result['trades'] = trade_arrays
            for option in middle_col_options:
                try:
                    if option.find("span", {"class": "val"}) and option.find("span", {"class": "key"}):
                        result[option.find("span", {"class": "key"}).text.strip()] = option.find("span", {
                            "class": "val"}).text.strip()
                except:
                    print("191")
            if opened_section_soup.find("div", {"class": "ad_about_wide"}):
                try:
                    ad_about = opened_section_soup.find("div", {"class": "ad_about_wide"}).p.text.strip()
                    result['ad_about'] = ad_about
                except:
                    print("196")
            if opened_section_soup.find("div", {"class": "items_container"}):
                try:
                    items_container_options = opened_section_soup.find("div", {"class": "items_container"})
                    item_containers = items_container_options.find_all("div", {"class": "info_feature"})
                    for item_container in item_containers:
                        features = item_container['class']
                        if 'delete' in features:
                            result[item_container.find("span").text.strip()] = False
                        else:
                            result[item_container.find("span").text.strip()] = True
                except:
                    print("208")

            else:
                print("error in all_fine")
            if opened_section_soup.find("span", {"class": "num_ad"}):
                try:
                    ad_num = opened_section_soup.find("span", {"class": "num_ad"})
                    result['ad_number'] = [int(s) for s in ad_num.text.strip().split() if s.isdigit()][0]
                except:
                    print("217")
                tries = 0
                images_links = []
                _status = None
                if not mongo_result_checker(result):
                    print("")
                    driver.switch_to.window(images_screen)
                    time.sleep(0.5)
                    while _status != "extracted" and tries <= 2:
                        _status, images_links, tries = images_link_extractor(driver, images_url,
                                                                             tries)
                else:
                    pass
                driver.switch_to.window(links_screen)
                print("images_links",images_links)
                result['images'] = images_downloader(images_links, add_number=result['ad_number'])
                f=furl(links[link_num])
                query_params={}
                for x in f.args:
                    query_params[x]=f.args[x]
                result["query_params"]=query_params

            return result

    links,links_situation = csv_reader()
    while(False in links_situation.values()):
        for link_num in links.keys():
            if links_situation[link_num] == False:
                try:
                    driver.get(links[link_num])
                    time.sleep(random.uniform(7, 10))
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    if soup.find("button", {"class": "page-num"}):
                        pages_numbers = int(soup.find("button", {"class": "page-num"}).text.strip())
                    else:
                        pages_numbers = 1
                    print("pages_numbers", pages_numbers)
                    for page_number in range(1, pages_numbers + 1):
                        if page_number != 1:
                            print("page_number", page_number)
                            driver.get(links[link_num] + "&page=" + str(page_number))
                        WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, '#__layout > div > div > div')))
                        all_page_soup = BeautifulSoup(driver.page_source, "html.parser")
                        print("all_page_created")
                        scrap_sections = driver.find_elements(By.CLASS_NAME, "rows")
                        print(len(scrap_sections))
                        for scrap_section_number in range(0,len(scrap_sections)-1):
                            try:
                                result={}
                                item_id = all_page_soup.find("div", {"id": "feed_item_"+str(scrap_section_number)})["item-id"]
                                if mongo_id_checker(item_id)==False:
                                    print(item_id)
                                    result['item_id']=item_id
                                    images_url = links[link_num] + "&open-item-id=" + item_id + "&view=image-gallery"
                                    print(scrap_section_number)
                                    driver.execute_script("arguments[0].scrollIntoView(true);", scrap_sections[scrap_section_number])
                                    time.sleep(random.uniform(2, 4))
                                    driver.execute_script("arguments[0].click();", scrap_sections[scrap_section_number])
                                    time.sleep(random.uniform(7.5, 12.25))
                                    print("opened")
                                    try:
                                        driver.find_element(By.CLASS_NAME,"contact_seller_button").click()
                                    except:
                                        print("300")
                                    try:
                                        driver.find_element(By.CLASS_NAME,"contact-seller-btn").click()
                                    except:
                                        print("300")
                                    time.sleep(random.uniform(5.12, 8.36))
                                    data_section=driver.find_element(By.ID,"feed_item_"+str(scrap_section_number))
                                    try:
                                        result['seller_name']=BeautifulSoup(data_section.find_element(By.CLASS_NAME,"name").get_attribute('innerHTML'),"html.parser").text.strip()
                                    except:
                                        try:
                                            result['seller_name']=BeautifulSoup(data_section.find_element(By.CLASS_NAME,"header").get_attribute('innerHTML'),"html.parser").text.strip()
                                        except:
                                            pass
                                            print("310")
                    
                                    try:
                                        phone_number=BeautifulSoup(data_section.find_element(By.CLASS_NAME,"rs-contact-seller-list").get_attribute('innerHTML'),"html.parser").text.strip()
                                        result['phone']= "".join(i for i in phone_number if i in "0123456789-\n")
                                        print(phone_number,result['phone'])
                                    except Exception as e:
                                        # print(e)
                                        try:
                                            phone_number=BeautifulSoup(data_section.find_element(By.CLASS_NAME,"block").get_attribute('innerHTML'),"html.parser").text.strip()
                                            result['phone']="".join(i for i in phone_number if i in "0123456789-\n")
                                            print(phone_number,result['phone'])
                                        except Exception as e:
                                            pass
                                            print("324")
                                    opened_section_data = BeautifulSoup(driver.find_element(By.ID,"feed_item_"+str(scrap_section_number)).get_attribute('innerHTML'), "html.parser")
                                    result=data_exteactor(result,opened_section_data,images_url)
                                    driver.execute_script("arguments[0].click();", scrap_sections[scrap_section_number])
                                    time.sleep(random.uniform(2.25,5))
                                    mongo_inserter(result)
                                    print("closed")
                                    
                                else:
                                    print("absence")
                            except Exception as e:
                                print("first circle")
                                print(e)
                except Exception as e:
                    if "validate.perfdrive.com" in driver.current_url:
                        try:
                            captcha_solver(driver)
                            links_situation[link_num]=False
                        except Exception as e:
                            print(e)
                            pass
                    else:
                        print(e)
                        pass

    driver.quit()
