import time
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import mysql.connector

driver = webdriver.Firefox()
driver.get("https://www.chrono24.com/")

def closecookie():
    try:
        # net is slow - so sleep.
        time.sleep(5)
        cookie_button = driver.find_element(By.XPATH, "//button[contains(text(), 'OK')]")
        time.sleep(2)
        driver.execute_script("arguments[0].click();", cookie_button)
    except:
        pass
closecookie()

search_box = driver.find_element('id', "query")
search_query = input('what are you looking for?\n------------\n')    
search_box.send_keys(search_query)
search_box.send_keys(Keys.RETURN)

def closeemailpopup():
    try:
        time.sleep(5)
        email_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Close')]")
        time.sleep(1)
        driver.execute_script("arguments[0].click();", email_button)    
    except:
        pass

closeemailpopup()


sqluser = input('enter sql username:\n')
sqlpassw = input('enter sql passw:\n')

def dbaccess():
    
    mydb = mysql.connector.connect(
        host="localhost",
        user=f"{sqluser}",
        password=f"{sqlpassw}"
        )

    
    try: 
        mycursor = mydb.cursor()
        mycursor.execute("CREATE DATABASE LuxuryWatch")

    
    except:
        pass

    mydb = mysql.connector.connect(
    host = "localhost",
    user = f"{sqluser}",
    password = f"{sqlpassw}",
    database = "LuxuryWatch"
    )

    return mydb

mydb = dbaccess()


results_page_html = driver.page_source #class str

soup = BeautifulSoup(results_page_html, 'html.parser')

page_count = soup.find_all('ul', {'class': "pagination list-unstyled d-flex pull-xs-none pull-sm-right"})[-1].text.split()[-2]


def extract_items():
    items = soup.find_all('div', {'class': 'js-article-item-container article-item-container wt-search-result article-image-carousel'})
    return items



try:
    
    mycursor = mydb.cursor()
    tblnm = search_query.replace(' ', '_')
    mycursor.execute(f"CREATE TABLE {tblnm} (manufacturer VARCHAR(255), boldname VARCHAR(255), Model VARCHAR(255), Price VARCHAR(255), Shipping_price VARCHAR(255), Location VARCHAR(255), url VARCHAR(255))")
    
    mycursor = mydb.cursor()
    mycursor.execute(f"ALTER TABLE {tblnm} ADD COLUMN unq_prod_id INT AUTO_INCREMENT PRIMARY KEY")

    int('aa') # intentional - i could use Raise, but this one was simpler.

except:
    items = extract_items()
    def scrapthispage():
        for item in items: 
            product_link = item.find_all('a', {'class': 'js-article-item article-item block-item rcard'})[0]['href']
            print(product_link, end = '')

            manufac = item.find_all('a', {'class': 'js-article-item article-item block-item rcard'})[0]['data-manufacturer']
            print(manufac, end = '')

            boldname = item.find_all('div', attrs = {"class": 'text-sm text-sm-md text-bold text-ellipsis'}, limit = 1)[0].text 
            print(boldname, end = '')

            model = item.find_all('div', attrs = {'class': "text-sm text-sm-md text-ellipsis m-b-2"}, limit = 1)[0].text
            print(model, end = '')

            price = item.find_all('div', attrs = {'class': "text-bold"})[1].text
            print('\n', price, end = '')

            shipping = item.find_all('div', attrs = {'class': "text-muted text-sm"}, limit = 1)[0].text
            print(shipping, end = '')

            location = item.find_all('span', attrs = {'class': "text-sm text-uppercase"}, limit = 1)[0].text
            print(location)

            mycursor = mydb.cursor()

            mycursor.execute("SHOW TABLES")
            tables = mycursor.fetchall()

            new_record = {
                'url': f'{product_link}', 
            }

            exists = False
            for table in tables:
                table_name = table[0]
                

                query = "SELECT * FROM {} WHERE ".format(table_name)
                conditions = []
                for key, value in new_record.items():
                    conditions.append("{}='{}'".format(key, value))
                
                query += " AND ".join(conditions)
                
                
                mycursor.execute(query)
                result = mycursor.fetchall()
                if len(result) > 0:
                    exists = True
                    print("Record already exists in table: ", table_name)    
                    break
                
            if not exists:
                mycursor = mydb.cursor()
                sql = f"INSERT INTO {tblnm} (manufacturer, boldname, Model, Price, Shipping_price, Location, url) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                val = (f"{manufac}",f"{boldname}", f"{model}", f"{price}", f"{shipping}", f"{location}", f"{product_link}")                    
                
                mycursor.execute(sql, val)
                mydb.commit()

                print('New record added')

        
    pages = int(input(f"number of results page(s): {page_count}\n\n how many pages would you like to scrap?\n"))
    closeemailpopup()
    for i in range(pages):    
        scrapthispage()
        next_page_url = soup.find('a', {'class': 'paging-next'})['href']
        if i == pages - 1:
            print('Done, enjoy!')
            break
        print('next page loading...: ', next_page_url)
        next_page_html = driver.get(next_page_url)
        closecookie()
        closeemailpopup()
        next_page_html = driver.page_source       
        soup = BeautifulSoup(next_page_html, 'html.parser')
        items = extract_items()

driver.quit()
