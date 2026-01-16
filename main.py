__license__   = 'GPL v3'
__copyright__ = '2024, Anareaty <reatymain@gmail.com>'
__docformat__ = 'restructuredtext en'


import json, time, re, os, errno, operator, shutil
from calibre_plugins.koreader_metadata_sync.slpp import slpp as lua
import sqlite3 as sqlite
from contextlib import closing
from calibre.library import db as calibre_db
from calibre_plugins.koreader_metadata_sync.config import prefs
import xml.etree.ElementTree as ET
from datetime import datetime



def set_globals(data):

    

    global calibreAPI
   
    global device_main_storage
    global device_metadata_main
    global device_card
    global device_metadata_card

    global storage_prefix_main
    global storage_prefix_card

    global koreader_folder

    current_db = calibre_db(data["dbpath"])
    calibreAPI = current_db.new_api




    
    
    device_main_storage = data["device_storages"]["main"]
    device_metadata_path_main = device_main_storage + "metadata.calibre"
    with open(device_metadata_path_main, "r") as file_main:
        device_metadata_main = json.load(file_main)

    
    

    device_card = None
    if data["device_storages"].get("card"):
        device_card = data["device_storages"]["card"]
        device_metadata_path_card = device_card + "metadata.calibre"
        with open(device_metadata_path_card, "r") as file_card:
            device_metadata_card = json.load(file_card)






    device_name = data["device_name"]
    device_paths = get_device_paths(device_name)

    storage_prefix_main = device_paths["storage_prefix_main"]
    storage_prefix_card = None
    if device_card:
        storage_prefix_card = device_paths["storage_prefix_card"]

    koreader_folder = device_paths["koreader_folder"]


    










    global status_mappings

    status_mappings = {
        "new": prefs['new_status'],
        "reading": prefs['reading_status'],
        "abandoned": prefs['abandoned_status'],
        "complete": prefs['complete_status']
    }


    global kr_collections
    kr_collections = None

    global sync_read
    sync_read = None
    global read_statuses
    read_statuses = None
    all_field_keys = current_db.all_field_keys()
    read_lookup_name = prefs['read_lookup_name']
    if read_lookup_name in all_field_keys:
        sync_read = True
        read_statuses = current_db.metadata_for_field(read_lookup_name)["display"]["enum_values"]



    global sync_fav
    sync_fav = None
    if prefs['fav_lookup_name'] in current_db.all_field_keys():
        sync_fav = True


    
    global sync_shelf
    sync_shelf = None
    if prefs['shelf_lookup_name'] in current_db.all_field_keys():
        sync_shelf = True



    global sync_rating
    sync_rating = None
    if prefs['rating_lookup_name'] in current_db.all_field_keys():
        sync_rating = True


    global sync_percent
    sync_percent = None
    if prefs['percent_lookup_name'] in current_db.all_field_keys():
        sync_percent = True

    global sync_pages
    sync_pages = None
    if prefs['pages_lookup_name'] in current_db.all_field_keys():
        sync_pages = True

    global sync_review
    sync_review = None
    if prefs['review_lookup_name'] in current_db.all_field_keys():
        sync_review = True

    global load_an
    load_an = None
    if prefs['an_lookup_name'] in current_db.all_field_keys():
        load_an = True


    global sync_pos
    sync_pos = None
    if prefs['position_lookup_name'] in current_db.all_field_keys():
        sync_pos = True


    global sync_collections
    sync_collections = None
    if sync_shelf or sync_fav:
        sync_collections = True



    





    





def send_all(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == None:
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."

    to_load = {
        "position": {},
        "books_to_refresh": []
    }

    if sync_collections:
        get_kr_collections()
        create_missing_kr_collections()


    calibre_book_IDs = data["selected_ids"]

    for calibre_book_ID in calibre_book_IDs:
        book = SyncBook(calibre_book_ID)
        if book.device_book_metadata:
            book.get_kr_metadata()

            if sync_shelf:
                book.send_book_collections_kr()
            if sync_read:
                book.send_read_kr()
            if sync_fav:
                book.send_fav_kr()
            if sync_rating:
                book.send_rating_kr()
            if sync_review:
                book.send_review_kr()

            if sync_pos:
                book.get_kr_metadata()
                to_load_position_kr = book.kr_sync_position()
                if to_load_position_kr:
                    to_load["position"][calibre_book_ID] = to_load_position_kr
                    to_load["books_to_refresh"].append(calibre_book_ID)

    

    bookLists = calibreAPI.all_field_ids("#lists")
    timestamp = None
    
    for list in bookLists:
        books = calibreAPI.books_for_field("#lists", list)

        for book_id in books:
            firstBook = SyncBook(book_id)
            if firstBook.device_book_metadata:
                
                
                if timestamp != None:
                    break

        if timestamp == None:
            timestamp = int(time.time())

        for calibre_book_ID in books:
            book = SyncBook(calibre_book_ID)
            


    
    if kr_collections:
        update_kr_collections(kr_collections)
    done_msg = "Sending metadata finished"

    
    return to_load, done_msg 



def send_collections(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."

    if sync_shelf:
    
        get_kr_collections()
        create_missing_kr_collections()

        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:

            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                book.get_kr_metadata()
                book.send_book_collections_kr()

            

        update_kr_collections(kr_collections)
    done_msg = "Sending collections finished"
    return None, done_msg








def send_read(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."

    if sync_read:
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                book.get_kr_metadata()
                book.send_read_kr()

    done_msg = "Sending read finished"
    return None, done_msg






def send_favorite(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."

    if sync_fav:
        get_kr_collections()
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                book.send_fav_kr()

        update_kr_collections(kr_collections)
    done_msg = "Sending favorite finished"
    return None, done_msg






def send_ratings(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."
    
    if sync_rating:
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                book.get_kr_metadata()
                book.send_rating_kr()
    done_msg = "Sending ratings finished"
    return None, done_msg





def send_reviews(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."
    
    if sync_review:
        
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                book.get_kr_metadata()
                book.send_review_kr()
    done_msg = "Sending reviews finished"
    return None, done_msg





def load_all(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."

    to_load = {
        "shelf": {},
        "read": {},
        "fav": {},
        "ratings": {},
        "percents": {},
        "pages": {},
        "reviews": {},
        "position": {},
        "annotations": {},
        "books_to_refresh": []
    }


    if sync_collections:
        get_kr_collections()


    calibre_book_IDs = data["selected_ids"]

    for calibre_book_ID in calibre_book_IDs:
        book = SyncBook(calibre_book_ID)
        if book.device_book_metadata: 
            to_load_shelf = None
            to_load_read = None
            to_load_fav = None
            to_load_rating = None
            to_load_percent = None
            to_load_pages = None
            to_load_review = None
            
            
            book.get_kr_metadata()
            if book.book_row:
                if sync_shelf:
                    to_load_shelf = book.load_shelf_kr()
                
            if sync_read:
                book.get_kr_metadata()
                to_load_read_kr = book.load_read_kr()
                if to_load_read_kr:
                    to_load_read = to_load_read_kr
            if sync_fav:
                to_load_fav = book.load_fav_kr()
            if sync_rating:
                to_load_rating = book.load_rating_kr()
            if sync_percent:
                to_load_percent = book.load_percent_kr()
            if sync_review:
                to_load_review = book.load_review_kr()

            if to_load_shelf or to_load_read or to_load_fav or to_load_rating or to_load_percent or to_load_review:
                to_load["books_to_refresh"].append(calibre_book_ID)
            if to_load_shelf:
                to_load["shelf"][calibre_book_ID] = to_load_shelf
            if to_load_read:
                to_load["read"][calibre_book_ID] = to_load_read["status"]
            if to_load_fav:
                to_load["fav"][calibre_book_ID] = to_load_fav["status"]
            if to_load_pages:
                to_load["pages"][calibre_book_ID] = to_load_pages["status"]
            if to_load_rating:
                to_load["ratings"][calibre_book_ID] = to_load_rating
            if to_load_percent:
                to_load["percents"][calibre_book_ID] = to_load_percent
            if to_load_review:
                to_load["reviews"][calibre_book_ID] = to_load_review


            if sync_pos:
                book.get_kr_metadata()
                to_load_position_kr = book.kr_sync_position()
                if to_load_position_kr:
                    to_load["position"][calibre_book_ID] = to_load_position_kr
                    to_load["books_to_refresh"].append(calibre_book_ID)
            

            
            if load_an:
                book.get_kr_annotations()
            
            if len(book.new_annotations) > 0:
                book.generate_annotations_html()

        if book.annotations_html:
            try:
                book.annotations_html = book.annotations_html.decode("utf-8")
            except:
                pass

            to_load["annotations"][calibre_book_ID] = book.annotations_html
            to_load["books_to_refresh"].append(calibre_book_ID)

        
    done_msg = "Sending metadata finished"
    return to_load, done_msg

















def load_collections(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."
    
    to_load = {
        "shelf": {},
        "books_to_refresh": []
    }

    if sync_shelf:
        get_kr_collections()
        
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                to_load_shelf = None
                
                to_load_shelf = book.load_shelf_kr()
                if to_load_shelf:
                    to_load["shelf"][calibre_book_ID] = to_load_shelf
                    to_load["books_to_refresh"].append(calibre_book_ID)
        
    done_msg = "Loaded favorite"
    return to_load, done_msg






def load_read(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."
    
    to_load = {
        "read": {},
        "books_to_refresh": []
    }
    
    if sync_read:
        
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                to_load_read = None
               
                book.get_kr_metadata()
                to_load_read_kr = book.load_read_kr()
                if to_load_read_kr:
                    to_load_read = to_load_read_kr
                if to_load_read:
                    to_load["read"][calibre_book_ID] = to_load_read["status"]
                    to_load["books_to_refresh"].append(calibre_book_ID)
        
       
    done_msg = "Loaded read"
    return to_load, done_msg








def load_favorite(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."
    
    to_load = {
        "fav": {},
        "books_to_refresh": []
    }
    
    if sync_fav:
        get_kr_collections()
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                to_load_fav = None
                
                to_load_fav = book.load_fav_kr()
                if to_load_fav:
                    to_load["fav"][calibre_book_ID] = to_load_fav["status"]
                    to_load["books_to_refresh"].append(calibre_book_ID)
        
        
    done_msg = "Loaded favorite"
    return to_load, done_msg





def load_pages(data):
    
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."
    
    to_load = {
        "pages": {},
        "books_to_refresh": []
    }
    
    if sync_pages:
        
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                to_load_pages = None
               
                if to_load_pages:
                    to_load["pages"][calibre_book_ID] = to_load_pages["status"]
                    to_load["books_to_refresh"].append(calibre_book_ID)
      
    done_msg = "Loaded favorite"
    return to_load, done_msg






def load_reviews(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."

    to_load = {
        "reviews": {},
        "books_to_refresh": []
    }

    if sync_review:
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                to_load_review = None
                book.get_kr_metadata()
                to_load_review = book.load_review_kr()
                if to_load_review:
                    to_load["reviews"][calibre_book_ID] = to_load_review
                    to_load["books_to_refresh"].append(calibre_book_ID)

    done_msg = "Loaded reviews"
    return to_load, done_msg






def load_ratings(data):
    set_globals(data)

    to_load = {
        "ratings": {},
        "books_to_refresh": []
    }

    if sync_rating:
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                to_load_rating = None
                book.get_kr_metadata()
                to_load_rating = book.load_rating_kr()
                if to_load_rating:
                    to_load["ratings"][calibre_book_ID] = to_load_rating
                    to_load["books_to_refresh"].append(calibre_book_ID)
                    
    done_msg = "Loaded ratings"
    return to_load, done_msg







def load_percents(data):
    set_globals(data)

    to_load = {
        "percents": {},
        "books_to_refresh": []
    }

    if sync_percent:
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                to_load_percent = None
                book.get_kr_metadata()
                to_load_percent = book.load_percent_kr()
                if to_load_percent:
                    to_load["percents"][calibre_book_ID] = to_load_percent
                    to_load["books_to_refresh"].append(calibre_book_ID)
                    
    done_msg = "Loaded percents"
    return to_load, done_msg








def sync_position(data):
    set_globals(data)

    to_load = {
        "position": {},
        "books_to_refresh": []
    }
    if sync_pos:
        

        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                book.get_kr_metadata()
                to_load_position_kr = book.kr_sync_position()
                if to_load_position_kr:
                    to_load["position"][calibre_book_ID] = to_load_position_kr
                    to_load["books_to_refresh"].append(calibre_book_ID)

    done_msg = "Synced"
    return to_load, done_msg      







def force_position(data):
    set_globals(data)

    if sync_pos:
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                book.get_kr_metadata()
                book.kr_force_position()
    
    done_msg = "Synced"
    return None, done_msg   







def create_sidecars(data):
    set_globals(data)
    calibre_book_IDs = data["selected_ids"]
    for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                book.get_kr_metadata()
                if not book.kr_metadata:
                    book.generate_kr_sidecar()

    done_msg = "Sidecars creating done"
    return None, done_msg





def remove_sidecars(data):
    set_globals(data)
    calibre_book_IDs = data["selected_ids"]
    for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
                book.delete_kr_sidecar()

    done_msg = "Sidecars removal done"
    return None, done_msg











def extract_annotations(data):
    try:
        set_globals(data)
    except:
        return "error", "Can not reach device metadata, it is probably still updating. Try again later."
    
    if storage_prefix_main == None or koreader_folder == "None":
        return "error", "Can not find the KOReader folder. Try to set the override paths for your device."

    to_load = {
        "annotations": {},
        "books_to_refresh": []
    }

    if load_an:
        
        calibre_book_IDs = data["selected_ids"]

        for calibre_book_ID in calibre_book_IDs:
            book = SyncBook(calibre_book_ID)
            if book.device_book_metadata:
               
                book.get_kr_annotations()
                
                if len(book.new_annotations) > 0:
                    book.generate_annotations_html()
                
            if book.annotations_html:
                try:
                    book.annotations_html = book.annotations_html.decode("utf-8")
                except:
                    pass

                to_load["annotations"][calibre_book_ID] = book.annotations_html
                to_load["books_to_refresh"].append(calibre_book_ID)

    done_msg = "Loading annotations finished"
    return to_load, done_msg              
                










def get_int_timestamp(datetime):
    try:
        timestamp = int(datetime.timestamp())
    except:
        timestamp = int(time.mktime(datetime.timetuple()))
    return timestamp






def get_kr_collections():
    global kr_collections
    kr_collections = None
    kr_collections_path = device_main_storage + koreader_folder + "/settings/collection.lua"

    if os.path.exists(kr_collections_path):
        with open(kr_collections_path, 'r') as file:
            content = str(file.read())
        lua_content = re.sub('^[^{]*', '', content).strip()
        try:
            kr_collections = lua.decode(lua_content)
            if kr_collections == None:
                kr_collections = {}
        except:
            pass



def create_missing_kr_collections():
    global kr_collections
    if kr_collections != None:
        shelfs = calibreAPI.all_field_names(prefs["shelf_lookup_name"])
        kr_collections_list = list(kr_collections)

        for shelf in shelfs:
            if shelf not in kr_collections_list:
                kr_collections[shelf] = {}



def update_kr_collections(kr_collections):
    
    kr_collections_path = device_main_storage + koreader_folder + "/settings/collection.lua"
    sidecar_lua = lua.encode(kr_collections)
    sidecar_lua_formatted = "-- updated from Calibre\nreturn " + sidecar_lua + "\n"

    try:
        with open(kr_collections_path, "w", encoding="utf-8") as f:
            f.write(sidecar_lua_formatted)
    except:
        sidecar_lua_formatted = sidecar_lua_formatted.encode("utf-8")
        with open(kr_collections_path, "w") as f:
            f.write(sidecar_lua_formatted)






def make_dir(path):
    try:
        os.makedirs(path, exist_ok=True)  # Python>3.2
    except TypeError:
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise






def get_device_paths(device_name):

    device_paths = {
        "storage_prefix_main": None,
        "storage_prefix_card": None,
        "koreader_folder": ""
    }

    # Need to add more device options in order to support various devices
    
    
    if device_name in ['Kobo Aura', 'Kobo Aura Edition 2', 'Kobo Aura HD', 'Kobo Aura H2O', 'Kobo Aura H2O Edition 2', 'Kobo Aura ONE', 'Kobo Clara HD', 'Kobo Clara 2E', 'Kobo Clara BW', 'Kobo Clara Colour', 'Kobo Elipsa', 'Kobo Elipsa 2E', 'Kobo Forma', 'Kobo Glo', 'Kobo Glo HD', 'Kobo Libra H2O', 'Kobo Libra 2', 'Kobo Libra Colour', 'Kobo Mini', 'Kobo Nia', 'Kobo Sage', 'Tolino Shine 5', 'Tolino Shine Color', 'Kobo Touch', 'Kobo Touch 2', 'Tolino Vision Color']:
        device_paths["storage_prefix_main"] = "/mnt/onboard"
        device_paths["storage_prefix_card"] = "/mnt/sd"
        device_paths["koreader_folder"] = ".adds/koreader"
    

    elif device_name in ['Pocketbook', 'PocketBook HD', 'PocketBook 360']:
        device_paths["storage_prefix_main"] = "/mnt/ext1"
        device_paths["storage_prefix_card"] = "/mnt/ext2"
        device_paths["koreader_folder"] = "applications/koreader"
    
    
    if prefs["storage_prefix_main_override"]:
        device_paths["storage_prefix_main"] = prefs["storage_prefix_main_override"]

    if prefs["storage_prefix_card_override"]:
        device_paths["storage_prefix_card"] = prefs["storage_prefix_card_override"]

    if prefs["koreader_folder_override"]:
        device_paths["koreader_folder"] = prefs["koreader_folder_override"]

    return device_paths







        



class SyncBook():

    def __init__(self, calibre_book_ID):
        self.calibre_book_ID = calibre_book_ID
        self.book_row = None
        self.get_device_book_metadata()
        self.new_annotations = {}
        self.annotations_html = None
        
        
            

    def get_device_book_metadata(self):
        # Find the book in Calibre metadata objects on device. We must check both the main storage and the card, it it is exist.
        self.device_book_metadata = next((bookData for bookData in device_metadata_main if bookData["application_id"] == self.calibre_book_ID), None)
        storage_prefix = storage_prefix_main                

        if self.device_book_metadata == None and device_card:
            self.device_book_metadata = next((bookData for bookData in device_metadata_card if bookData["application_id"] == self.calibre_book_ID), None)
            storage_prefix = storage_prefix_card

        if self.device_book_metadata:
            bookPath = self.device_book_metadata["lpath"]
            self.book_fullpath = storage_prefix + "/" + bookPath
            self.book_filesize = self.device_book_metadata["size"]

            # Get the filename an folder of the book

            self.bookPath_file = self.book_fullpath.rsplit('/', 1)[1].replace("'", r"''")
            self.bookPath_folder = self.book_fullpath.rsplit('/', 1)[0].replace("'", r"''")

    


  


  



    def get_kr_metadata(self):
    
        self.kr_metadata = None
        format = self.book_fullpath.rsplit('.', 1)[1]

        # Look for sidecar in book folder
        sidecar_path_device = self.book_fullpath.rsplit('.', 1)[0] + ".sdr/metadata." + format + ".lua"
        self.sidecar_path = sidecar_path_device.replace(storage_prefix_main + "/", device_main_storage)
        
        if storage_prefix_card:
            self.sidecar_path = sidecar_path_device.replace(storage_prefix_card + "/", device_card)

        if not os.path.exists(self.sidecar_path):
            # Look for sidecar in docsettings folder
            self.sidecar_path = device_main_storage + koreader_folder + "/docsettings" + sidecar_path_device

        if os.path.exists(self.sidecar_path):
            with open(self.sidecar_path, 'r') as file:
                content = str(file.read())
            lua_content = re.sub('^[^{]*', '', content).strip()
            try:
                self.kr_metadata = lua.decode(lua_content)
            except:
                pass




    



    def update_kr_sidecar(self):
        
        sidecar_lua = lua.encode(self.kr_metadata)
        sidecar_lua_formatted = "-- updated from Calibre\nreturn " + sidecar_lua + "\n"
        try:
            with open(self.sidecar_path, "w", encoding="utf-8") as f:
                f.write(sidecar_lua_formatted)
        except:
            sidecar_lua_formatted = sidecar_lua_formatted.encode("utf-8")
            with open(self.sidecar_path, "w") as f:
                f.write(sidecar_lua_formatted)




    def generate_kr_sidecar(self):
        self.sidecar_path = None
        format = self.book_fullpath.rsplit('.', 1)[1]
        kr_settings_reader_path = device_main_storage + koreader_folder + "/settings.reader.lua"

        if os.path.exists(kr_settings_reader_path):
            with open(kr_settings_reader_path, 'r') as file:
                content = str(file.read())
                lua_content = re.sub('^[^{]*', '', content).strip()
            try:
                settings = lua.decode(lua_content)
                metadata_folder = settings["document_metadata_folder"]
                sidecar_path_device = self.book_fullpath.rsplit('.', 1)[0] + ".sdr/metadata." + format + ".lua"
                if metadata_folder == "doc":
                    self.sidecar_path = sidecar_path_device.replace(storage_prefix_main + "/", device_main_storage)
                    if storage_prefix_card:
                        self.sidecar_path = sidecar_path_device.replace(storage_prefix_card + "/", device_card)
                elif metadata_folder == "dir":
                    self.sidecar_path = device_main_storage + koreader_folder + "/docsettings" + sidecar_path_device
                else:
                    pass
            except:
                pass

        if self.sidecar_path:
            self.kr_metadata = {
                "cre_dom_version": 20240114,
                "doc_path": self.book_fullpath
            }

            dir = os.path.split(self.sidecar_path)[0]
            make_dir(dir)

            self.update_kr_sidecar()








    def delete_kr_sidecar(self):
        # Look for sidecar in book folder
        sidecar_folder_path_device = self.book_fullpath.rsplit('.', 1)[0] + ".sdr"
        sidecar_folder_path = sidecar_folder_path_device.replace(storage_prefix_main + "/", device_main_storage)
        
        if storage_prefix_card:
            sidecar_folder_path = sidecar_folder_path_device.replace(storage_prefix_card + "/", device_card)

        if not os.path.exists(sidecar_folder_path):
            # Look for sidecar in docsettings folder
            sidecar_folder_path = device_main_storage + koreader_folder + "/docsettings" + sidecar_folder_path_device

        if os.path.exists(sidecar_folder_path):
            shutil.rmtree(sidecar_folder_path)
            

            










    

    def send_book_collections_kr(self):
        
        global kr_collections
        if kr_collections:
            calibreBookShelfNames = calibreAPI.field_for(prefs["shelf_lookup_name"], self.calibre_book_ID, default_value=[])

            for c in kr_collections:
                collection = kr_collections[c]
                file_key = None
                fixed = {}
                count = 1
                if c == "favorites":
                    pass
                elif c in calibreBookShelfNames:
                    # Проверить, есть ли книга в коллекции, если нет, то добавить

                    if "settings" not in collection:
                        fixed["settings"] = {"order": 1}
                    for key in collection:
                        if key == "settings":
                            fixed["settings"] = collection[key]
                        else:
                            fixed[count] = collection[key]
                            count = count + 1
                            if "file" in collection[key] and collection[key]["file"] == self.book_fullpath:
                                file_key = key
                    if file_key == None:
                        next_key = len(fixed)
                        fixed[next_key] = {"file": self.book_fullpath, "order": next_key}
                    kr_collections[c] = fixed
                else:
                    # Проверить, есть ли книга в коллекции, если да, то удалить
                    for key in collection:
                        if key == "settings":
                            fixed["settings"] = collection[key]
                        elif "file" in collection[key] and collection[key]["file"] == self.book_fullpath:
                            pass
                        else:
                            fixed[count] = collection[key]
                            count = count + 1
                    kr_collections[c] = fixed






    def send_read_kr(self):
        if self.kr_metadata:
            read = "new"
            read_status = "new"
            read = calibreAPI.field_for(prefs['read_lookup_name'], self.calibre_book_ID, default_value="new")

            if read in status_mappings.values():
                for key, value in status_mappings.items():
                    if value == read:
                        read_status = key
                        break
            
            if not read_status:
                read_status = "new"

            if "summary" not in self.kr_metadata:
                self.kr_metadata["summary"] = {}

            if "status" not in self.kr_metadata["summary"] or self.kr_metadata["summary"]["status"] != read_status:
                self.kr_metadata["summary"]["status"] = read_status
                self.update_kr_sidecar()








    def send_fav_kr(self):
        global kr_collections
        if kr_collections:
            favorite = calibreAPI.field_for(prefs['fav_lookup_name'], self.calibre_book_ID, default_value=None)
            if "favorites" in kr_collections:
                favorites = kr_collections["favorites"]
            else:
                favorites = {}
            file_key = None
            favorites_fixed = {}
            count = 1
            if "settings" not in favorites:
                favorites_fixed["settings"] = {"order": 1}
            for key in favorites:
                if key == "settings":
                    favorites_fixed["settings"] = favorites[key]
                elif "file" in favorites[key] and favorites[key]["file"] == self.book_fullpath:
                    file_key = key
                    if favorite:
                        favorites_fixed[count] = favorites[key]
                        count = count + 1
                    else:
                        pass
                else:
                    favorites_fixed[count] = favorites[key]
                    count = count + 1

            if file_key == None and favorite:
                next_key = len(favorites_fixed)
                favorites_fixed[next_key] = {"file": self.book_fullpath, "order": next_key}
                
            kr_collections["favorites"] = favorites_fixed





    def send_rating_kr(self):
        rating = None
        if self.kr_metadata:
            rating = calibreAPI.field_for(prefs['rating_lookup_name'], self.calibre_book_ID, default_value=None)
            if rating:
                rating = rating/2
                if rating % 1 != 0:
                    rating = None
                else: 
                    rating = int(rating)
        if rating:
            if self.kr_metadata["summary"] == None:
                self.kr_metadata["summary"] = {}
            if "rating" not in self.kr_metadata["summary"] or self.kr_metadata["summary"]["rating"] != rating:
                self.kr_metadata["summary"]["rating"] = rating
                self.update_kr_sidecar()
        else:
            if self.kr_metadata and "summary" in self.kr_metadata and "rating" in self.kr_metadata["summary"]:
                self.kr_metadata["summary"].pop("rating")
                self.update_kr_sidecar()



    def send_review_kr(self):
        review = None
        if self.kr_metadata:
            review = calibreAPI.field_for(prefs["review_lookup_name"], self.calibre_book_ID, default_value=None)
        if review:
            review = review.replace("\n", "\\\n")
            if self.kr_metadata["summary"] == None:
                self.kr_metadata["summary"] = {}
            if "note" not in self.kr_metadata["summary"] or self.kr_metadata["summary"]["note"] != review:
                self.kr_metadata["summary"]["note"] = review
                self.update_kr_sidecar()






    




    def load_shelf_kr(self):
        to_load_shelf = None
        
        if kr_collections and not prefs["composite_collections"]:
            update_shelfs_in_Calibre = False
            kr_collections_list = []
            calibreBookShelfNames = calibreAPI.field_for(prefs["shelf_lookup_name"], self.calibre_book_ID, default_value=[])
            calibreBookShelfNamesList = list(calibreBookShelfNames)

            for c in kr_collections:
                collection = kr_collections[c]
                if c == "favorites":
                    pass
                else:
                    for key in collection:
                        if "file" in collection[key] and collection[key]["file"] == self.book_fullpath:
                            try:
                                kr_collections_list.append(c.decode("utf-8"))
                            except:
                                kr_collections_list.append(c)
                            
                            if c not in calibreBookShelfNamesList:
                                update_shelfs_in_Calibre = True
                            else:
                                calibreBookShelfNamesList.remove(c)
            if len(calibreBookShelfNamesList) > 0:
                update_shelfs_in_Calibre = True

            if update_shelfs_in_Calibre:
                to_load_shelf = kr_collections_list

        return to_load_shelf







    def load_read_kr(self):
        to_load_read = None

        if self.kr_metadata:

            status = None
            if "summary" in self.kr_metadata:
                if "status" in self.kr_metadata["summary"]:
                    status = self.kr_metadata["summary"]["status"]

            

            status_name = status_mappings.get(status)

            

            if not status_name:
                status_name = status

            if not status_name in read_statuses:
                status_name = None

            read = calibreAPI.field_for(prefs["read_lookup_name"], self.calibre_book_ID)

            if read != status_name:
                to_load_read = {"status": status_name}

        return to_load_read
    





















    def load_fav_kr(self):
        to_load_fav = None
        if kr_collections: 
            status = False 
            if "favorites" in kr_collections:
                favorites = kr_collections["favorites"]
                for key in favorites:
                    if "file" in favorites[key] and favorites[key]["file"] == self.book_fullpath:
                        status = True
            fav = calibreAPI.field_for(prefs["fav_lookup_name"], self.calibre_book_ID)
            if fav != status:
                to_load_fav = {"status": status}
        return to_load_fav

















    
    def load_rating_kr(self):
        to_load_rating = None
        if self.kr_metadata:
            if "summary" in self.kr_metadata:
                if "rating" in self.kr_metadata["summary"]:
                    rating = self.kr_metadata["summary"]["rating"] * 2
                    calibre_rating = calibreAPI.field_for(prefs['rating_lookup_name'], self.calibre_book_ID, default_value=None)
                    if rating != calibre_rating:
                        to_load_rating = rating
        return to_load_rating












    def load_percent_kr(self):
        to_load_percent = None
        if self.kr_metadata:
            if "summary" in self.kr_metadata:

                if "status" in self.kr_metadata["summary"]:
                    status = self.kr_metadata["summary"]["status"]
                    percent = 0
                    if status == "complete":
                        percent = 100
                    elif "percent_finished" in self.kr_metadata:
                        percent = self.kr_metadata["percent_finished"]
                        if percent:
                            percent = int(percent * 100)
                    calibre_percent = calibreAPI.field_for(prefs['percent_lookup_name'], self.calibre_book_ID, default_value=None)
                    if percent != calibre_percent:
                        to_load_percent = percent
        return to_load_percent










    def load_review_kr(self):
        to_load_review = None
        if self.kr_metadata:
            if "summary" in self.kr_metadata:
                if "note" in self.kr_metadata["summary"]:
                    try:
                        review = self.kr_metadata["summary"]["note"].decode("utf-8").replace("\\\n", "\n")
                    except:
                        review = self.kr_metadata["summary"]["note"].replace("\\\n", "\n")
                    calibre_review = calibreAPI.field_for(prefs['review_lookup_name'], self.calibre_book_ID, default_value=None)
                    if review != calibre_review:
                        to_load_review = review
        return to_load_review







            







    def get_kr_annotations(self):
        self.get_kr_metadata()

        if self.kr_metadata and "annotations" in self.kr_metadata:
            annotations = self.kr_metadata["annotations"]
            pages = self.kr_metadata["doc_pages"]

            for key in annotations:
                if 'pos0' in annotations[key] or 'note' in annotations[key]:
                    annotation = {}

                    for a_key in ['text', 'note', 'color']:
                        if a_key in annotations[key]:
                            annotation[a_key] = annotations[key][a_key]
                    
                    if 'datetime' in annotations[key]:
                        datestring = annotations[key]["datetime"]
                        timestamp = get_int_timestamp(datetime.strptime(datestring,'%Y-%m-%d %H:%M:%S'))
                        annotation["timestamp"] = timestamp
                    
                    if 'pageno' in annotations[key]:
                        page = annotations[key]['pageno']
                    else:
                        page = 0
                    
                    if 'chapter' in annotations[key]:
                        chapter = annotations[key]['chapter']
                    else:
                        chapter = ""


                    start_pos_num = int(annotations[key]["page"].rsplit('.', 1)[1])

                    annotation["text"] = annotation["text"].replace("\\\n", "<br>")
                    annotation["title"] = chapter + " - <span style='white-space: nowrap'>p. " + str(page) + "</span>"
                    annotation["location_sort"] = int(page * 100000 / pages) * 10000 + start_pos_num
                    annotation["id"] = "kr_" + str(annotation["timestamp"])
                    
                    self.new_annotations[annotation["id"]] = annotation





    






    def generate_annotations_html(self):
        self.get_existing_annotations()


        kr_annotations = []


        for id in self.existing_annotations:
            if id not in self.new_annotations:
                an_obj = self.existing_annotations[id]

                app = id[0:2]


                if app == "kr":
                    kr_annotations.append(an_obj)







        for id in self.new_annotations:
            annotation = self.new_annotations[id]
            datestring = datetime.fromtimestamp(annotation["timestamp"]).strftime('%c').rsplit(":", 1)[0]
            an_el = ''
            an_el += '<div id="' + id + '" data-sort="' + str(annotation["location_sort"]) + '">\n'
            an_el += '<table width="100%" bgcolor="#f4e681"><tbody>\n'
            an_el += '<tr>\n'
            an_el += '<td><p><strong>' + annotation["title"] + '</strong></p></td>\n'
            an_el += '<td align="right"><p><strong>' + datestring + '</strong></p></td>\n'
            an_el += '</tr>\n'
            an_el += '</tbody></table>\n'
            an_el += '<p style="margin-left: 15px">' + annotation["text"] + '</p>\n' 
            if "note" in annotation:
                an_el += '<p><i>' + annotation["note"] + '</i></p>\n'
            an_el += '<hr width="80%" style="background-color:#777;"></div>\n'

            an_obj = {
                "location_sort": annotation["location_sort"],
                "html": an_el
            }

            app = id[0:2]




            if app == "kr":
                kr_annotations.append(an_obj)




        kr_annotations.sort(key=operator.itemgetter('location_sort'))


        self.annotations_html = "<div>\n"



        for an_obj in kr_annotations:
            self.annotations_html += an_obj["html"]


        
        self.annotations_html += "</div>"


        

















    def get_existing_annotations(self):
        self.existing_annotations = {}
        raw_annotations = calibreAPI.field_for(prefs["an_lookup_name"], self.calibre_book_ID)

        if (raw_annotations):
            raw_annotations = raw_annotations.replace("<br>", "<br></br>").replace('<hr width="80%" style="background-color:#777;">', '<hr width="80%" style="background-color:#777;"></hr>')
            root = ET.fromstring(raw_annotations)

            for an in root:
                id = an.get('id')
                location_sort = int(an.get('data-sort'))
   
                try:
                    an_str = ET.tostring(an, encoding='utf-8').replace("</br>", "").replace("</hr>", "")
                except:
                    an_str = ET.tostring(an, encoding='unicode').replace("</br>", "").replace("</hr>", "")

                an_obj = {
                    "location_sort": location_sort,
                    "html": an_str
                }
                self.existing_annotations[id] = an_obj












    def kr_sync_position(self):

        if self.kr_metadata:

            calibre_position_string = calibreAPI.field_for(prefs["position_lookup_name"], self.calibre_book_ID)
            kr_position = None
            calibre_position = None

            if calibre_position_string != None:
                calibre_position = calibre_position_string.split("_TIMESTAMP_")[0]
                calibre_ts = int(calibre_position_string.split("_TIMESTAMP_")[1])

            if "last_xpointer" in self.kr_metadata:
                kr_position = self.kr_metadata["last_xpointer"]
                kr_ts = int(os.path.getmtime(self.sidecar_path))
                kr_position_string = kr_position + "_TIMESTAMP_" + str(kr_ts)

            # В калибре нет информации о позиции, а в коридере есть
            if kr_position and calibre_position_string == None:
                return kr_position_string
            
            # В калибре есть информация о позиции, а в коридере нет
            elif kr_position == None and calibre_position:
                self.kr_metadata["last_xpointer"] = calibre_position
                self.update_kr_sidecar()


            # И в калибре, и в коридере есть информация о позиции, но она не совпадает
            elif kr_position and calibre_position and calibre_position_string != kr_position_string:
                if calibre_ts > kr_ts:
                    self.kr_metadata["last_xpointer"] = calibre_position
                    self.update_kr_sidecar()
                elif calibre_ts < kr_ts:
                    return kr_position_string
            
        return None
            










    def kr_force_position(self):

        if self.kr_metadata:

            calibre_position_string = calibreAPI.field_for(prefs["position_lookup_name"], self.calibre_book_ID)
            kr_position = None
            calibre_position = None

            if calibre_position_string != None:
                calibre_position = calibre_position_string.split("_TIMESTAMP_")[0]

            if "last_xpointer" in self.kr_metadata:
                kr_position = self.kr_metadata["last_xpointer"]
        
            if calibre_position and kr_position != calibre_position:
                self.kr_metadata["last_xpointer"] = calibre_position
                self.update_kr_sidecar()

        return None
            








    


        