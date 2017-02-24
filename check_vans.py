from send_mail import sendMail
from datetime import date, timedelta
import numpy as np
import tqdm
import pandas as pd
import sqlite3
import pickle
import os

DATABASE = './data/cars.db'

def get_image_paths(vin):
    cwd = os.getcwd()
    image_dir = os.path.join(cwd, 'car_images', vin)
    image_paths = []
    for image in os.listdir(image_dir):
        image_paths.append(os.path.join(cwd,'car_images',vin,image))
    return image_paths

def get_new_data():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    q_date = date(2017, 2, 12) 
    q_date = date.today() - timedelta(days=7)
    data = pd.read_sql_query('SELECT * FROM vans WHERE date_added > "{}";'.format(q_date), conn)
    return data


def clean_data(data):
    # Drop not so great columns
    data.drop(['model', 'index', 'cylinders', 'dealer_license', 'exterior_color', 'interior_color', 'fuel_type', 'liters', 'number_of_doors', 'stock_number','trim'], axis=1, inplace=True)

    # CLean messy labels
    data.drive_type.replace(['fwd', 'awd', '4wheeldrive'], ['4wd']*3, inplace=True)
    data.drive_type.replace(['2wheeldrive', 'rwd'], ['2wd']*2, inplace=True)

    categorical_data = [
        'body',
        'interior_condition',
        'exterior_condition',
        'title_type',
        'transmission',
        'drive_type',
        'make']

    def one_hotify(data, key, unique_set):
	one_hot = np.zeros((data.shape[0], len(unique_set)))
	column_names = []
	for i, item in enumerate(data[key]):
	    for j, notion in enumerate(unique_set):
		if notion == item:
		    one_hot[i, j] = 1
		    
	one_hot_df =  pd.DataFrame(one_hot, columns=list(unique_set))
	new_data = pd.concat([data, one_hot_df], axis=1)
        new_data.drop(key, axis=1, inplace=True)
        return new_data

    unique_sets_dict = pickle.load(open('data/unique_sets_dict.p', 'rb'))
    for column in categorical_data:
        data = one_hotify(data, column, unique_sets_dict[column])

    data.drop(['vin', 'description', 'date_added'], axis=1, inplace=True)

    # Drop nan values
    data['mileage'] = data['mileage'].replace('notspecified', np.nan)
    data['year'] = data['year'].replace('notspecified', np.nan)
    data.dropna(axis=0, inplace=True)

    data.drop(['fav_num','page_views'], axis=1, inplace=True)
    return data


def predict(data):
    model = pickle.load(open('./models/model.p', 'rb'))
    return model.predict(data.as_matrix())


if __name__ == '__main__':

   original_data = get_new_data() 
   van_data = clean_data(original_data)
   predictions = predict(van_data)

   print('-- Found %d New Vans ---' % van_data[predictions].shape[0])
   print('Sending Mail...')
   for i, car in tqdm.tqdm(original_data[predictions].iterrows()):
       image_paths = get_image_paths(car['vin'])
       text = car['description'].encode('utf-8') + '\n\n\n' + '-'*45 + car.to_string().encode('utf-8')
       sendMail(text, image_paths)
