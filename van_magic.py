# -*- coding: utf-8 -*-
#!/anaconda/bin python

from urlparse import urljoin
from bs4 import BeautifulSoup
import requests
import re
import string
import tqdm
import pandas as pd
import os
import datetime
import sqlite3
from PIL import Image
import matplotlib.image as mpimg
from matplotlib import pyplot as plt

def getLastDate(cur):
    cur.execute('SELECT date_added FROM vans ORDER BY date(date_added) DESC')
    try:
        most_recent = datetime.datetime.strptime(cur.fetchone()[0], '%Y-%m-%d %H:%M:%S')
    except:
        most_recent = datetime.datetime(2016,12,1)
    return most_recent

def updateData(table):
    if table == 'vans':
        query = string.Template('https://www.ksl.com/auto/search/index?p=&priceFrom=1&priceTo=20000&miles=25&keyword=van&page=$page_num&cx_navSource=hp_search')
    else:
        query = string.Template('http://www.ksl.com/auto/search/index?p=&priceFrom=1&priceTo=20000&miles=50&newUsed[]=Used&sellerType[]=For%20Sale%20By%20Owner&page=$page_num&cx_navSource=hp_search')

    query_page = requests.get(query.substitute(page_num=0))
    soup = BeautifulSoup(query_page.text)
    BASE_URL = 'https://www.ksl.com'

    conn = sqlite3.connect("cars.db")
    cur = conn.cursor()
    
    last_date = getLastDate(cur)

    last_page = int(soup.find(title='Go to last page').text)
    data = []
    number_added = 0
    for page_num in tqdm.tqdm(range(last_page)):
        query_text = query.substitute(page_num=page_num)
        query_page = requests.get(query_text)
        page = BeautifulSoup(query_page.text)
        listings = page.find_all(class_='listing')
        for add in listings:
            try:
                query_page = requests.get(urljoin(BASE_URL, add.find('a')['href']))
                sub_soup = BeautifulSoup(query_page.text)

                car_data = {}

                listing_specs = sub_soup.find('ul', class_='listing-specifications')
                for row in listing_specs.find_all('li'):
                    label = row.find(class_='title').text.lower().replace(':','').replace(' ','_')
                    s = row.find(class_='value').text.rstrip().lower()
                    value = re.sub(r'\W+', '', s)
                    car_data[label] = value

                price = sub_soup.find('h3', class_='price cXenseParse').text
                price = int(''.join(re.findall('\d+', price)))
                car_data['price'] = price

                loc_str = sub_soup.find('h2', class_='location').text
                loc_str = loc_str.split('Posted ')[1]
                date = datetime.datetime.strptime(loc_str, '%B %d, %Y')
                car_data['date_added'] = date
                
                # check if already have info
                if (date - last_date).days < -1:
                    conn.commit()
                    print "Added: %d" % number_added
                    return

                vdp = sub_soup.find_all('ul', class_='vdp-contact-list')[1]

                page_views =  vdp.find(class_="vdp-info-key", text='Page Views').parent.find(class_="vdp-info-value")
                page_views =  int(re.findall('\d+', page_views.text)[0])
                car_data['page_views'] = page_views

                fav_num = vdp.find(class_="vdp-info-key", text='Favorite of').parent.find(class_="vdp-info-value")
                fav_num =  int(re.findall('\d+', fav_num.text)[0])
                car_data['fav_num'] = fav_num

                description = sub_soup.find('div', class_='short').text.strip().replace('\n',' ').lower()
                car_data['description'] = description
                data.append(car_data)

                # Add to database
                columns = ', '.join(car_data.keys())
                placeholders = ':'+', :'.join(car_data.keys())
                q = 'INSERT INTO {} ({}) VALUES ({})'.format(table, columns, placeholders)
                try:
                    cur.execute(q, car_data)
                    print "Added: %s" %car_data['model']
                    number_added += 1
                except sqlite3.IntegrityError as e:
                    conn.commit()
                    print e
                    # return

                #images
                try:
                    path =  './images/{}'.format(car_data['vin'])
                    if not os.path.isdir(path):
                        os.mkdir(path)
                        slider = sub_soup.find('ul', class_='slides').find_all('li')
                        for i, pic in enumerate(slider):
                            image = requests.get(pic.img['src'])
                            with open('./images/{}/{}.jpg'.format(car_data['vin'], i), 'wb') as f:
                                f.write(image.content)
                except:
                    pass
            except:
                pass
        conn.commit()

    conn.commit()
    conn.close()
    return

def findPictures(vin):
    cwd = os.getcwd()
    image_dir = os.path.join(cwd, 'images', vin)
    for image in os.listdir(image_dir):
        img = mpimg.imread(os.path.join(cwd,'images',vin,image))
        imgplot = plt.imshow(img)
        plt.axis('off')
        plt.show()

if __name__ == '__main__':
    updateData('cars')
