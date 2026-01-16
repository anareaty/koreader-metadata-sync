__license__   = 'GPL v3'
__copyright__ = '2024, Anareaty <reatymain@gmail.com>'
__docformat__ = 'restructuredtext en'


from calibre.customize import InterfaceActionBase

PLUGIN_NAME = 'KOReader Metadata Sync'
PLUGIN_VERSION_TUPLE = (1, 0, 0)
PLUGIN_VERSION = '.'.join([str(x) for x in PLUGIN_VERSION_TUPLE])



class KMSAction(InterfaceActionBase):
    name                    = PLUGIN_NAME
    description             = 'Sync KOReader collections, read statuses and favorite statuses with Calibre'
    supported_platforms     = ['windows', 'osx', 'linux']
    author                  = 'anareaty'
    version                 = PLUGIN_VERSION_TUPLE
    minimum_calibre_version = (3, 48, 0)

    actual_plugin           = 'calibre_plugins.koreader_metadata_sync.ui:InterfacePlugin'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.koreader_metadata_sync.config import ConfigWidget
        return ConfigWidget(self.actual_plugin_)

    def save_settings(self, config_widget):
        config_widget.save_settings()
        if self.actual_plugin_:
            self.actual_plugin_.rebuild_menus()

