from bs4 import BeautifulSoup
import os, pymysql, paramiko, ast, subprocess
from datetime import datetime
from tqdm import tqdm

# Open the HTML file

def files_from_folders(dir_image):
    image_list = []
    for image in os.listdir(dir_image):
        if image.endswith('jpg') or image.endswith('JPG') or image.endswith('png') or image.endswith('PNG'):
            image_list.append(image)
            sorted_filenames = sorted(image_list, key=lambda x: int(x.split('.')[0]))
    return sorted_filenames

def create_directory_and_upload(local_file_path, target_directory, new_filename, ssh_host, ssh_port, ssh_username, ssh_password):
    # Create SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to SSH server
        ssh_client.connect(hostname=ssh_host, port=ssh_port, username=ssh_username, password=ssh_password)

        # Create SFTP session
        
        sftp_client = ssh_client.open_sftp()

         # Create target directory if it doesn't exist
        try:
            sftp_client.mkdir(target_directory)
            sftp_client.put(local_file_path, f'{target_directory}/{new_filename}')
            #print('Create Directory')
        except IOError:
            #print('Already Directory')
            sftp_client.chdir(target_directory)
            #print(os.path.join(target_directory, new_filename))
            sftp_client.put(local_file_path, f'{target_directory}/{new_filename}')
        # Upload file to target directory
        

        # Close SFTP session
        sftp_client.close()
        
        #print("File uploaded and renamed successfully.")
    
    except Exception as e:
        print("Error:", e)
    
    finally:
        # Close SSH connection
        ssh_client.close()

def generate_insert_query(values, query):
    if query == 'POST':
        query_template = "INSERT INTO `frontend_post`(`id`, `name_id`, `title`, `stock`, `slug`, `price`, `year`, `description`, `model`, `vin`, `vehicle_title`, `mileage`, `fuel`, `transmission`, `body_style`, `engine_size`, `exterior_color`, `interior_color`, `date`, `status`) VALUES ({})"
    elif query == 'IMAGE':
        query_template = "INSERT INTO `frontend_image`(`id`, `product_id`, `image`) VALUES ({})"
    
    # Format the values into the query template
    formatted_query = query_template.format(', '.join(["%s"] * len(values)))
    
    return formatted_query

def main():
    #READING FROM JSON
    fileCredentials = open('credentials.json', 'r').read()          
    credential = ast.literal_eval(fileCredentials)
    db_hostname= credential['db_hostname']
    db_user = credential['db_user']
    db_password = credential['db_password']
    db = credential['db']
    db_port = int(credential['db_port'])
    sshhostname = credential['ssh_hostname']
    sshuser = credential['ssh_user']
    sshpassword = credential['ssh_password']
    sshport = credential['ssh_port']
    direc = credential['directory']
    upload_path = credential['upload_path']
    no_of_pics = credential['no_pictures']

    data_list = []
    directory = rf'{direc}'      
    print("[OK] Starting - Preparing data... ")
    files = [file for file in os.listdir(directory) if file.endswith('.html')]

    for filename in tqdm(files, desc="Processing HTML files:", unit="file"):

        filepath = os.path.join(directory, filename)
        if filepath.endswith('.html'):
            with open(filepath, 'r', encoding='utf-8') as file:
                html_content = file.read()
                
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            #print(text)
            lines = [line for line in text.splitlines() if line.strip()]  # Split text into lines and remove empty lines
            filtered_list = [item for item in lines if item not in ['. For Sellers', 'BODY STYLE']]
            cleaned_list = [item.replace('\xa0', ' ') for item in filtered_list]
            cleaned_list1 = [item.replace('\xa0', ' ') for item in cleaned_list if item not in ['. For Sellers', 'BODY STYLE', '©2024 eAutosDMS, LLC. All Rights Reserved.','Home :: About Us :: How it Works :: Privacy Policy  :: Terms of Use  :: Security Center :: Contact Us','Description - eAutoVTM Broker', '. For Buyers', '. Dealing on Classified Sites', '. 10 Day Money Back Guarantee', '. Frequently Asked Questions', '. Register to Start A Transaction', '. Check Your Transaction', '. Return Your Item', '. Personal Shopping Service Fees', '. Sell Your Vehicle Fees', '. Spoof Protection', '. Scams on Craigslist', '. Business Services', '. Our Services At Home', '. Shipping and Packing Services', '. Sell Your Vehicle', '. Dealing on Classified Sites', '. Personal Shopping Service', '. Fundraising Services', '. Large Item Service', '. Privacy Policy', '. Why eAutoVTM Broker', '. Locations', '. Policies', '. What Sells', 'ADDITIONAL LINKS', 'Stay Safe', 'Services', 'Locations', 'Fees', 'Security Center', 'Dealing on Classified Sites', 'Return my Item', 'Payment', 'OTHER INFORMATION', "Enter your Transaction ID# and click 'GO'", 'Brand your business or fundraising cause on Geebo', 'We Recycle:', '                    We help protect our environment by reusing packaging materials. Drop off your clean boxes, peanuts and bubble wrap anytime at our Philadelphia location.', 'Visit our Security Page for our latest news, articles, updates and scam alerts.', 'eAutoVTM Broker', 'Next page, we need your shipping information. This tells us where to ship the item.', 'Free Shipping Over $999 Purchase', '100% Money Back Guarantee', 'Best Price Guarantee', ' ENGINE ', ' TRANSMISSION ', ' DRIVE ', ' BODY STYLE ', ' EXTERIOR COLOR  ', ' FUEL TYPE ','Features', 'Model Description',' STOCK NUMBER ', ' VIN ', ' MILEAGE ']]
            #print(cleaned_list1)
            title = cleaned_list1[0]
            price = cleaned_list1[1].replace("Selling Price: $","").replace(",", "").split(".")[0]
            stock = cleaned_list1[2].replace(' ', '')
            year = title[:4]
            vin = cleaned_list1[3].replace(' ', '')
            mileage = cleaned_list1[4].replace(' ', '')
            engine = cleaned_list1[5].replace(' ', '')
            transmission = cleaned_list1[6].replace(' ', '')
            drive = cleaned_list1[7].replace(' ', '')
            body = cleaned_list1[8].replace(' ', '')
            ext_color = cleaned_list1[9] .replace(' ', '')
            fuel = cleaned_list1[10].replace(' ', '')
            description = cleaned_list1[11]
            #print(f'Title: {title}\nPrice: {price}')
            dir_image = os.path.join(directory, title)
            images = files_from_folders(dir_image)
            slug = title[5:].replace(' ', '-')

            
            data = {'title': title,
                    'price': price,
                    'stock': stock,
                    'slug': slug,
                    'year': year, 
                    'vehicle_title': 'Clear',
                    'vin': vin, 
                    'mileage': mileage, 
                    'engine': engine, 
                    'transmission': transmission, 
                    'drive': drive,
                    'body': body,
                    'color': ext_color,
                    'fuel': fuel,
                    'description': description,
                    'dir_image': dir_image,
                    'images': images
                    }
                
            data_list.append(data)    
    item = 0
    for data in tqdm(data_list, desc="Inserting Data: ", unit="item"):
        item +=1
        # MYSQL CONECTIONS
        try:
            connection = pymysql.connect(
            host = db_hostname,
            user= db_user,
            password= db_password,
            database= db,
            port= db_port,
            cursorclass=pymysql.cursors.DictCursor
            #auth_plugin = 'mysql_native_password'
        )
            cursor = connection.cursor()
            select_query = "SELECT id, name_id FROM frontend_post WHERE id = (SELECT MAX(id) FROM frontend_post)"
            # Execute the select query
            cursor.execute(select_query)
            # Fetch all rows from the result set
            rows = cursor.fetchone()
            nrOfrows = int(rows['id'])
            name_id = int(rows['name_id'])
            nextNumber = nrOfrows + 1
            current_date = datetime.now().date()
            values = (nextNumber, name_id, data['title'][5:], data['stock'], data['slug'], int(data['price']), int(data['year']), data['description'], '--',data['vin'],data['vehicle_title'],data['mileage'],data['fuel'],data['transmission'],'--',data['engine'],data['color'],'--',current_date,'Available')

            #print(values)
            insert_query = generate_insert_query(values, 'POST')
            cursor.execute(insert_query, values)
            select_query = "SELECT id FROM frontend_image WHERE id = (SELECT MAX(id) FROM frontend_image)"
            cursor.execute(select_query)
            row = cursor.fetchone()
            id_image = row['id']        
            current_dir = os.path.join(directory,data['title'])
            no_of_run = 0
            slug = data['slug']
            stock = data['stock']

            for img in data['images']:      
                if no_of_run < no_of_pics:
                    #print(img)
                    no_of_run +=1     
                    id_image +=1
                    local_file_path = os.path.join(current_dir, img)
                    target_directory= os.path.join(upload_path, stock)
                    new_filename = f'{slug}_{img}' 
                    ssh_host = sshhostname
                    ssh_port = sshport
                    ssh_username = sshuser
                    ssh_password = sshpassword
                    create_directory_and_upload(local_file_path, target_directory, new_filename, ssh_host, ssh_port, ssh_username, ssh_password)
                    values = (id_image, nextNumber,f'{stock}/{new_filename}')
                    insert_query = generate_insert_query(values, 'IMAGE')
                    cursor.execute(insert_query, values)
                    #print(values)

        

            # Close cursor and connection
            cursor.close()
            connection.close()
        except pymysql.Error as err:
            print("Something went wrong: {}".format(err))
            print("Press Enter to quit.")
            input()  # Wait for user to press Enter
            print("Exiting...")
            exit(16)
    print("Press Enter to quit.")
    input()  # Wait for user to press Enter
    print("Exiting...")
    exit()
if __name__ == '__main__':
    main()