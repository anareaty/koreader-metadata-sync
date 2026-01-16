

__license__   = 'GPL v3'
__copyright__ = '2024, Anareaty <reatymain@gmail.com>'
__docformat__ = 'restructuredtext en'

try:
    from qt.core import QVBoxLayout, QLabel, QLineEdit, QWidget, QCheckBox, Qt, QGridLayout, QGroupBox, QComboBox
except:
    try:
        from PyQt5.Qt import QVBoxLayout, QLabel, QLineEdit, QWidget, QCheckBox, Qt, QGridLayout, QGroupBox, QComboBox
    except:
        from PyQt4.Qt import QVBoxLayout, QLabel, QLineEdit, QWidget, QCheckBox, Qt,QGridLayout, QGroupBox, QComboBox

from calibre.utils.config import JSONConfig



prefs = JSONConfig('plugins/koreader_metadata_sync')

prefs.defaults['shelf_lookup_name'] = None
prefs.defaults['an_lookup_name'] = None
prefs.defaults['read_lookup_name'] = None
prefs.defaults['fav_lookup_name'] = None
prefs.defaults['position_lookup_name'] = None
prefs.defaults['pages_lookup_name'] = None
prefs.defaults['rating_lookup_name'] = None
prefs.defaults['percent_lookup_name'] = None
prefs.defaults['review_lookup_name'] = None

prefs.defaults['new_status'] = "new"
prefs.defaults['reading_status'] = "reading"
prefs.defaults['abandoned_status'] = "abandoned"
prefs.defaults['complete_status'] = "complete"

prefs.defaults['composite_collections'] = False

prefs.defaults["storage_prefix_main_override"] = None
prefs.defaults["storage_prefix_card_override"] = None
prefs.defaults["koreader_folder_override"] = None




class ConfigWidget(QWidget):

    def __init__(self, plugin_action):

        

        self.gui = plugin_action.gui
        self.field_by_name = {"None": None}
        self.index_by_field = {}

        QWidget.__init__(self)

        layout = QVBoxLayout()
        self.setLayout(layout)



        extra_group = QGroupBox(self)
        extra_group.setTitle("Settings")
        layout.addWidget(extra_group)
        extra_layout = QGridLayout(extra_group)
        extra_layout.setColumnStretch(0,1)
        extra_layout.setColumnMinimumWidth(1, 150)


        self.composite_collections_checkbox = QCheckBox("Use composite column for collections")
        self.composite_collections_checkbox.setChecked(prefs['composite_collections'])
        self.composite_collections_checkbox.setToolTip("With composite column you can populate collections list from several sources, but will not be able to load collections back from the KOReader.")
        extra_layout.addWidget(self.composite_collections_checkbox, 0, 0, 1, 2)






        






        




        main_group = QGroupBox(self)
        main_group.setTitle("Columns")
        layout.addWidget(main_group)
        main_layout = QGridLayout(main_group)
        main_layout.setColumnStretch(0,1)
        main_layout.setColumnMinimumWidth(1, 150)


        shelf_label = QLabel('Collections column:')
        shelf_label.setWordWrap(True)
        main_layout.addWidget(shelf_label, 0, 0)
        self.shelf_combo = QComboBox(self)

        shelf_collection_type = "text"
        if prefs['composite_collections']:
            shelf_collection_type = "composite"
        
        self.shelf_combo.addItems(self.get_columns(shelf_collection_type, custom=True, multiple=True))
        self.shelf_combo.setCurrentIndex(self.get_index(prefs['shelf_lookup_name']))
        shelf_label.setBuddy(self.shelf_combo)
        main_layout.addWidget(self.shelf_combo, 0, 1)


        



        read_label = QLabel('Read statuses column:')
        read_label.setWordWrap(True)
        main_layout.addWidget(read_label, 2, 0)
        self.read_combo = QComboBox(self)
        self.read_combo.addItems(self.get_columns("enumeration", custom=True))
        self.read_combo.setCurrentIndex(self.get_index(prefs['read_lookup_name']))
        read_label.setBuddy(self.read_combo)
        main_layout.addWidget(self.read_combo, 2, 1)


        fav_label = QLabel('Favorite column:')
        fav_label.setWordWrap(True)
        self.fav_combo = QComboBox(self)
        self.fav_combo.addItems(self.get_columns("bool", custom=True))
        self.fav_combo.setCurrentIndex(self.get_index(prefs['fav_lookup_name']))
        fav_label.setBuddy(self.fav_combo)
        main_layout.addWidget(fav_label, 3, 0)
        main_layout.addWidget(self.fav_combo, 3, 1)




        an_label = QLabel('Annotations column:')
        an_label.setWordWrap(True)
        self.an_combo = QComboBox(self)
        self.an_combo.addItems(self.get_columns("comments", custom=True))
        self.an_combo.setCurrentIndex(self.get_index(prefs['an_lookup_name']))
        an_label.setBuddy(self.an_combo)
        main_layout.addWidget(an_label, 4, 0)
        main_layout.addWidget(self.an_combo, 4, 1)

        position_label = QLabel('Reading position column:')
        position_label.setWordWrap(True)
        self.position_combo = QComboBox(self)
        self.position_combo.addItems(self.get_columns("comments", custom=True))
        self.position_combo.setCurrentIndex(self.get_index(prefs['position_lookup_name']))
        position_label.setBuddy(self.position_combo)
        main_layout.addWidget(position_label, 5, 0)
        main_layout.addWidget(self.position_combo, 5, 1)




        pages_label = QLabel('Pages column:')
        pages_label.setWordWrap(True)
        self.pages_combo = QComboBox(self)
        self.pages_combo.addItems(self.get_columns("int", custom=False))
        self.pages_combo.setCurrentIndex(self.get_index(prefs['pages_lookup_name']))
        pages_label.setBuddy(self.pages_combo)
        main_layout.addWidget(pages_label, 6, 0)
        main_layout.addWidget(self.pages_combo, 6, 1)



        rating_label = QLabel('Rating column:')
        rating_label.setWordWrap(True)
        self.rating_combo = QComboBox(self)
        self.rating_combo.addItems(self.get_columns("rating", custom=False))
        self.rating_combo.setCurrentIndex(self.get_index(prefs['rating_lookup_name']))
        rating_label.setBuddy(self.rating_combo)
        main_layout.addWidget(rating_label, 7, 0)
        main_layout.addWidget(self.rating_combo, 7, 1)




        percent_label = QLabel('Percent read column:')
        percent_label.setWordWrap(True)
        self.percent_combo = QComboBox(self)
        self.percent_combo.addItems(self.get_columns("int", custom=False))
        self.percent_combo.setCurrentIndex(self.get_index(prefs['percent_lookup_name']))
        percent_label.setBuddy(self.percent_combo)
        main_layout.addWidget(percent_label, 8, 0)
        main_layout.addWidget(self.percent_combo, 8, 1)





        
        review_label = QLabel('Book review column:')
        review_label.setWordWrap(True)
        self.review_combo = QComboBox(self)
        self.review_combo.addItems(self.get_columns("comments", custom=True))
        self.review_combo.setCurrentIndex(self.get_index(prefs['review_lookup_name']))
        review_label.setBuddy(self.review_combo)
        main_layout.addWidget(review_label, 9, 0)
        main_layout.addWidget(self.review_combo, 9, 1)






        



        read_statuses_group = QGroupBox(self)
        read_statuses_group.setTitle("Read statuses")
        layout.addWidget(read_statuses_group)
        read_statuses_layout = QGridLayout(read_statuses_group)
        read_statuses_layout.setColumnStretch(0,1)
        read_statuses_layout.setColumnMinimumWidth(1, 150)

        new_status_label = QLabel('new')
        new_status_label.setWordWrap(True)
        read_statuses_layout.addWidget(new_status_label, 0, 0)
        self.new_status_input = QLineEdit(self)

        self.new_status_input.setText(prefs['new_status'])
        new_status_label.setBuddy(self.new_status_input)
        read_statuses_layout.addWidget(self.new_status_input, 0, 1)



        reading_status_label = QLabel('reading')
        reading_status_label.setWordWrap(True)
        read_statuses_layout.addWidget(reading_status_label, 1, 0)
        self.reading_status_input = QLineEdit(self)

        self.reading_status_input.setText(prefs['reading_status'])
        reading_status_label.setBuddy(self.reading_status_input)
        read_statuses_layout.addWidget(self.reading_status_input, 1, 1)


        abandoned_status_label = QLabel('abandoned')
        abandoned_status_label.setWordWrap(True)
        read_statuses_layout.addWidget(abandoned_status_label, 2, 0)
        self.abandoned_status_input = QLineEdit(self)

        self.abandoned_status_input.setText(prefs['abandoned_status'])
        abandoned_status_label.setBuddy(self.abandoned_status_input)
        read_statuses_layout.addWidget(self.abandoned_status_input, 2, 1)


        complete_status_label = QLabel('complete')
        complete_status_label.setWordWrap(True)
        read_statuses_layout.addWidget(complete_status_label, 3, 0)
        self.complete_status_input = QLineEdit(self)

        self.complete_status_input.setText(prefs['complete_status'])
        complete_status_label.setBuddy(self.complete_status_input)
        read_statuses_layout.addWidget(self.complete_status_input, 3, 1)










        override_group = QGroupBox(self)
        override_group.setTitle("Override paths")
        override_group.setToolTip("Set this paths manually if the plugin can not find KOReader folder on your device.")
        layout.addWidget(override_group)
        override_layout = QGridLayout(override_group)
        override_layout.setColumnStretch(0,1)
        override_layout.setColumnMinimumWidth(1, 150)


        storage_prefix_main_label = QLabel('Path to the main storage on device (ex.: "/mnt/ext1")')
        storage_prefix_main_label.setWordWrap(True)
        override_layout.addWidget(storage_prefix_main_label, 0, 0)
        self.storage_prefix_main_input = QLineEdit(self)

        self.storage_prefix_main_input.setText(prefs['storage_prefix_main_override'])
        storage_prefix_main_label.setBuddy(self.storage_prefix_main_input)
        override_layout.addWidget(self.storage_prefix_main_input, 0, 1)


        storage_prefix_card_label = QLabel('Path to the card storage on device if it exists (ex.: "/mnt/ext2")')
        storage_prefix_card_label.setWordWrap(True)
        override_layout.addWidget(storage_prefix_card_label, 1, 0)
        self.storage_prefix_card_input = QLineEdit(self)

        self.storage_prefix_card_input.setText(prefs['storage_prefix_card_override'])
        storage_prefix_card_label.setBuddy(self.storage_prefix_card_input)
        override_layout.addWidget(self.storage_prefix_card_input, 1, 1)


        koreader_folder_label = QLabel('Path to the KOReader folder in device storage (ex.: ".adds/koreader")')
        koreader_folder_label.setWordWrap(True)
        override_layout.addWidget(koreader_folder_label, 2, 0)
        self.koreader_folder_input = QLineEdit(self)

        self.koreader_folder_input.setText(prefs['koreader_folder_override'])
        koreader_folder_label.setBuddy(self.koreader_folder_input)
        override_layout.addWidget(self.koreader_folder_input, 2, 1)



        
        self.resize(self.sizeHint())
        








    def get_columns(self, type, custom=True, multiple=False):
        db = self.gui.current_db
        if custom:
            fields = db.custom_field_keys()
        else:
            fields = db.all_field_keys()
        type_fields = ["None"]
        for field in fields:
            field_data = db.metadata_for_field(field)
            
            if field_data['datatype'] == type and bool(field_data['is_multiple']) == multiple and field_data['name']:
                index = len(type_fields)
                type_fields.append(field_data['name'])
                self.field_by_name[field_data['name']] = field
                self.index_by_field[field] = index
        return type_fields
    

    def get_index(self, field):
        if field != None and field in self.index_by_field:
            return self.index_by_field[field]
        else:
            return 0




        



    def save_settings(self):

        prefs['shelf_lookup_name'] = self.field_by_name[self.shelf_combo.currentText()]


        
        prefs['read_lookup_name'] = self.field_by_name[self.read_combo.currentText()]
        prefs['fav_lookup_name'] = self.field_by_name[self.fav_combo.currentText()]
        prefs['an_lookup_name'] = self.field_by_name[self.an_combo.currentText()]
        prefs['position_lookup_name'] = self.field_by_name[self.position_combo.currentText()]
        prefs['pages_lookup_name'] = self.field_by_name[self.pages_combo.currentText()]
        prefs['rating_lookup_name'] = self.field_by_name[self.rating_combo.currentText()]
        prefs['percent_lookup_name'] = self.field_by_name[self.percent_combo.currentText()]
        prefs['review_lookup_name'] = self.field_by_name[self.review_combo.currentText()]

        prefs['composite_collections'] = self.composite_collections_checkbox.isChecked()
    
        prefs['new_status'] = self.new_status_input.text()
        prefs['reading_status'] = self.reading_status_input.text()
        prefs['abandoned_status'] = self.abandoned_status_input.text()
        prefs['complete_status'] = self.complete_status_input.text()

        prefs['storage_prefix_main_override'] = self.storage_prefix_main_input.text()
        prefs['storage_prefix_card_override'] = self.storage_prefix_card_input.text()
        prefs['koreader_folder_override'] = self.koreader_folder_input.text()


















